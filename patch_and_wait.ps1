$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Patching DEFAULT_TIMEOUT to 30s on running server ===" -ForegroundColor Cyan

# Create a Python script that patches the running server's DEFAULT_TIMEOUT
$patchScript = @'
import sys
sys.path.insert(0, r"C:\ProjectS\project-s-code")
from interactive_layer import sai_runner
print(f"Before: DEFAULT_TIMEOUT = {sai_runner.DEFAULT_TIMEOUT}")
sai_runner.DEFAULT_TIMEOUT = 30
print(f"After: DEFAULT_TIMEOUT = {sai_runner.DEFAULT_TIMEOUT}")
'@
$patchScript | Out-File -FilePath 'C:\ProjectS\patch_timeout_live.py' -Encoding ascii

Copy-Item -Path 'C:\ProjectS\patch_timeout_live.py' -Destination 'C:\ProjectS\project-s-code\patch_timeout_live.py' -ToSession $sess -Force

# Run the patch
$patchResult = Invoke-Command -Session $sess -ScriptBlock {
    python C:\ProjectS\project-s-code\patch_timeout_live.py 2>&1 | Out-String
}
Write-Host $patchResult

Write-Host "`n=== Waiting for mission to timeout (max 90s) ===" -ForegroundColor Cyan
$missionId = "0b9cb9b0-2630-417e-b531-b2117f7f609b"
$pollStart = Get-Date
$finalState = "UNKNOWN"

while ((Get-Date).Subtract($pollStart).TotalSeconds -lt 90) {
    Start-Sleep -Seconds 3
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat/mission/$missionId/status" -TimeoutSec 5 -UseBasicParsing
        $status = $resp.Content | ConvertFrom-Json
        $state = $status.state
        $elapsed = [int](Get-Date).Subtract($pollStart).TotalSeconds
        Write-Host "  [$elapsed s] $state" -ForegroundColor Yellow
        $finalState = $state
        
        if ($state -in @("COMPLETE", "FAILED", "TIMEOUT")) {
            Write-Host "  -> Terminal state: $state at ${elapsed}s" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  Poll error: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== Final state: $finalState ===" -ForegroundColor Cyan

# Check SQLite
$sqliteCheck = Invoke-Command -Session $sess -ScriptBlock {
    python -c "import sqlite3; conn=sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db'); rows=conn.execute('SELECT mission_id,state,progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall(); [print(f'{r[0]} | {r[1]} | {r[2]}') for r in rows]; conn.close()" 2>&1 | Out-String
}
Write-Host "SQLite:" -ForegroundColor Cyan
Write-Host $sqliteCheck

# Post-test health
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "Health after: PASS ($($resp.StatusCode))" -ForegroundColor Green
    $healthAfter = $true
} catch {
    Write-Host "Health after: FAIL" -ForegroundColor Red
    $healthAfter = $false
}

# Save results
$results = @{
    mission_id = $missionId
    final_state = $finalState
    health_after = $healthAfter
    timeout_triggered = ($finalState -eq "TIMEOUT")
} | ConvertTo-Json -Depth 10
$results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_timeout_patch_results.json" -Encoding UTF8

Remove-PSSession $sess