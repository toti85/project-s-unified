$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== GAP_030 LIVE VALIDATION - DEPLOY + TEST ===" -ForegroundColor Cyan

# 1. Kill existing
Write-Host "`n[1] Stopping existing server..." -ForegroundColor Yellow
Invoke-Command -Session $s -ScriptBlock {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*uvicorn*' } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
}

# 2. Deploy ALL updated files
Write-Host "[2] Deploying updated code..." -ForegroundColor Yellow
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\sai_runner.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\sai_runner.py" -ToSession $s -Force
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\start_server.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\start_server.py" -ToSession $s -Force
Copy-Item -Path "C:\ProjectS-Unified\validate_gap030_server.py" -Destination "C:\ProjectS\project-s-code\validate_gap030_server.py" -ToSession $s -Force
Write-Host "  Deployed: sai_runner.py, start_server.py, validate_gap030_server.py"

# 3. Verify start_server.py has the fix
Write-Host "[3] Verifying sys.path fix..." -ForegroundColor Yellow
$hasFix = Invoke-Command -Session $s -ScriptBlock {
    $content = Get-Content "C:\ProjectS\project-s-code\interactive_layer\start_server.py" -Raw
    $content -match 'sys\.path\.insert'
}
if ($hasFix) {
    Write-Host "  sys.path fix confirmed" -ForegroundColor Green
} else {
    Write-Host "  sys.path fix NOT found!" -ForegroundColor Red
}

# 4. Start server
Write-Host "[4] Starting server..." -ForegroundColor Yellow
Invoke-Command -Session $s -ScriptBlock {
    cd C:\ProjectS\project-s-code
    $proc = Start-Process python -ArgumentList "interactive_layer\start_server.py" -PassThru -WindowStyle Hidden
    Write-Host "Server PID: $($proc.Id)"
}

# 5. Wait for server
Write-Host "[5] Waiting for server startup..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://46.253.140.72:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host "  Server ready (attempt $($i+1))" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
}
if (-not $ready) {
    Write-Host "  Server failed to start!" -ForegroundColor Red
}

# 6. Run validation
Write-Host "[6] Running validation (30s timeout test)..." -ForegroundColor Yellow
$validationOutput = ""
if ($ready) {
    $validationOutput = Invoke-Command -Session $s -ScriptBlock {
        cd C:\ProjectS\project-s-code
        python validate_gap030_server.py 2>&1 | Out-String
    }
}

# 7. Check final state
Write-Host "[7] Checking final mission state..." -ForegroundColor Yellow
$finalState = Invoke-Command -Session $s -ScriptBlock {
    $db = "C:\ProjectS\project-s-code\interactive_layer_data\interactive.db"
    $script = @'
import sqlite3
conn = sqlite3.connect(r"C:\ProjectS\project-s-code\interactive_layer_data\interactive.db")
rows = conn.execute("SELECT mission_id, state, progress, error FROM missions ORDER BY updated_at DESC LIMIT 3").fetchall()
for r in rows:
    err = (r[3] or "")[:60]
    print(f"{r[0]} | {r[1]} | {r[2]} | {err}")
conn.close()
'@
    python -c $script 2>&1 | Out-String
}

# 8. Post-test health
Write-Host "[8] Post-test health check..." -ForegroundColor Yellow
$healthAfter = $false
try {
    $resp = Invoke-WebRequest -Uri "http://46.253.140.72:8000/health" -TimeoutSec 5 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-Host "  PASS" -ForegroundColor Green
        $healthAfter = $true
    }
} catch {
    Write-Host "  FAIL" -ForegroundColor Red
}

# Save results
$results = @{
    HealthBefore = $ready
    ValidationOutput = $validationOutput
    FinalState = $finalState
    HealthAfter = $healthAfter
} | ConvertTo-Json -Depth 5

$results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_validation_results.json" -Encoding UTF8

Write-Host "`n=== VALIDATION OUTPUT ===" -ForegroundColor Cyan
Write-Host $validationOutput

Write-Host "`n=== FINAL STATES ===" -ForegroundColor Cyan
Write-Host $finalState

Remove-PSSession $s