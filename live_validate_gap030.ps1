$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GAP_030 LIVE VALIDATION (via localhost)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Kill existing server
Write-Host "`n[1/7] Stopping existing server..." -ForegroundColor Yellow
Invoke-Command -Session $s -ScriptBlock {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*uvicorn*' } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-Host "  Old processes stopped"
}

# 2. Deploy updated code
Write-Host "[2/7] Deploying updated code..." -ForegroundColor Yellow
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\sai_runner.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\sai_runner.py" -ToSession $s -Force
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\start_server.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\start_server.py" -ToSession $s -Force
Write-Host "  Deployed: sai_runner.py, start_server.py"

# 3. Start server via batch wrapper
Write-Host "[3/7] Starting server..." -ForegroundColor Yellow
Invoke-Command -Session $s -ScriptBlock {
    $wrapper = @'
cd C:\ProjectS\project-s-code
python -u interactive_layer\start_server.py > C:\ProjectS\server_stdout.txt 2>&1
'@
    $wrapper | Out-File -FilePath "C:\ProjectS\start_server.bat" -Encoding ascii
    $proc = Start-Process "C:\ProjectS\start_server.bat" -PassThru
    Write-Host "  Server PID: $($proc.Id)"
}

# 4. Wait for server ready
Write-Host "[4/7] Waiting for server startup..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host "  Server ready (attempt $($i+1))" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
}
if (-not $ready) {
    Write-Host "  Server failed to start!" -ForegroundColor Red
    # Show captured output
    $stdout = Invoke-Command -Session $s -ScriptBlock {
        if (Test-Path "C:\ProjectS\server_stdout.txt") {
            Get-Content "C:\ProjectS\server_stdout.txt"
        } else { "(empty)" }
    }
    Write-Host "  Server output: $stdout" -ForegroundColor Red
}

# 5. Run validation via localhost
Write-Host "[5/7] Running GAP_030 validation (30s timeout)..." -ForegroundColor Yellow
$validationOutput = ""
if ($ready) {
    $validationOutput = Invoke-Command -Session $s -ScriptBlock {
        cd C:\ProjectS\project-s-code
        python validate_gap030_server.py 2>&1 | Out-String
    }
}

# 6. Check final mission state
Write-Host "[6/7] Checking final mission state..." -ForegroundColor Yellow
$finalState = Invoke-Command -Session $s -ScriptBlock {
    $script = @'
import sqlite3
conn = sqlite3.connect(r"C:\ProjectS\project-s-code\interactive_layer_data\interactive.db")
rows = conn.execute("SELECT mission_id, state, progress, error FROM missions ORDER BY updated_at DESC LIMIT 5").fetchall()
for r in rows:
    err = (r[3] or "")[:80]
    print(f"{r[0]} | {r[1]} | {r[2]} | {err}")
conn.close()
'@
    python -c $script 2>&1 | Out-String
}
Write-Host $finalState

# 7. Post-test health check
Write-Host "[7/7] Post-test health check..." -ForegroundColor Yellow
$healthAfter = $false
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-Host "  PASS" -ForegroundColor Green
        $healthAfter = $true
    }
} catch {
    Write-Host "  FAIL" -ForegroundColor Red
}

# Extract key results for report
$healthBefore = $ready
$finalStates = @()
foreach ($line in $finalState.Split([char[]]@("`n","`r"), [StringSplitOptions]::RemoveEmptyEntries)) {
    if ($line.Trim()) {
        $finalStates += $line.Trim()
    }
}
$lastMission = if ($finalStates.Count -gt 0) { $finalStates[-1] } else { "N/A" }

# Determine final state
$actualFinalState = "UNKNOWN"
foreach ($line in $finalStates) {
    if ($line -match '\| (TIMEOUT|COMPLETE|FAILED|EXECUTING|QUEUED) \|') {
        $actualFinalState = $Matches[1]
        break
    }
}

# Save results
$results = @{
    HealthBefore = $healthBefore
    ValidationOutput = $validationOutput
    FinalStates = $finalStates
    HealthAfter = $healthAfter
    LastMissionLine = $lastMission
    ActualFinalState = $actualFinalState
} | ConvertTo-Json -Depth 10

$results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_validation_results.json" -Encoding UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Health before: $healthBefore" -ForegroundColor $(if ($healthBefore) { "Green" } else { "Red" })
Write-Host "  Final state: $actualFinalState" -ForegroundColor $(if ($actualFinalState -eq "TIMEOUT") { "Green" } elseif ($actualFinalState -eq "EXECUTING") { "Red" } else { "Yellow" })
Write-Host "  Health after: $healthAfter" -ForegroundColor $(if ($healthAfter) { "Green" } else { "Red" })
Write-Host "========================================" -ForegroundColor Cyan

Remove-PSSession $s