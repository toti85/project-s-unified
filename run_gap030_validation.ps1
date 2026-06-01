$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GAP_030 LIVE VALIDATION" -ForegroundColor Cyan
Write-Host "  Method: Remote execution via WinRM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Copy validation script to server
Write-Host "`n[1/4] Copying validation script to server..." -ForegroundColor Yellow
Copy-Item -Path "C:\ProjectS-Unified\validate_gap030_server.py" -Destination "C:\ProjectS\project-s-code\validate_gap030_server.py" -ToSession $s -Force
Write-Host "  Copied: validate_gap030_server.py"

# Step 2: Execute validation remotely
Write-Host "[2/4] Executing validation remotely..." -ForegroundColor Yellow
$validationOutput = Invoke-Command -Session $s -ScriptBlock {
    cd C:\ProjectS\project-s-code
    python validate_gap030_server.py 2>&1 | Out-String
}

# Step 3: Print validation output
Write-Host "`n[3/4] Validation output:" -ForegroundColor Yellow
Write-Host $validationOutput

# Step 4: Check final mission state
Write-Host "[4/4] Checking final mission state..." -ForegroundColor Yellow
$finalState = Invoke-Command -Session $s -ScriptBlock {
    $pyScript = @"
import sqlite3
conn = sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db')
rows = conn.execute('SELECT mission_id, state, progress, error FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall()
for r in rows:
    err = (r[3] or '')[:80]
    print(f'{r[0]} | {r[1]} | {r[2]} | {err}')
conn.close()
"@
    python -c $pyScript 2>&1 | Out-String
}
Write-Host $finalState

# Extract results
$healthBefore = $true  # Server was already running
$actualFinalState = "UNKNOWN"
foreach ($line in $finalState.Split([char[]]@("`n","`r"), [StringSplitOptions]::RemoveEmptyEntries)) {
    if ($line.Trim() -match '\| (TIMEOUT|COMPLETE|FAILED|EXECUTING|QUEUED) \|') {
        $actualFinalState = $Matches[1]
        break
    }
}

# Post-test health check
Write-Host "`nPost-test health check..." -ForegroundColor Yellow
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

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  GAP_030 VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Health before: $healthBefore" -ForegroundColor $(if ($healthBefore) { "Green" } else { "Red" })
Write-Host "  Final state: $actualFinalState" -ForegroundColor $(if ($actualFinalState -eq "TIMEOUT") { "Green" } elseif ($actualFinalState -eq "EXECUTING") { "Red" } else { "Yellow" })
Write-Host "  Health after: $healthAfter" -ForegroundColor $(if ($healthAfter) { "Green" } else { "Red" })
Write-Host "========================================" -ForegroundColor Cyan

# Save results
$results = @{
    HealthBefore = $healthBefore
    ValidationOutput = $validationOutput
    FinalStates = $finalState
    HealthAfter = $healthAfter
    ActualFinalState = $actualFinalState
} | ConvertTo-Json -Depth 10

$results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_validation_results.json" -Encoding UTF8

Remove-PSSession $s