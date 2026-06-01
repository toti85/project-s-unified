$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Step 1: Patch DEFAULT_TIMEOUT to 30s on server ===" -ForegroundColor Cyan
$patchScript = @'
import sys
sys.path.insert(0, r'C:\ProjectS\project-s-code')
from interactive_layer import sai_runner
sai_runner.DEFAULT_TIMEOUT = 30
print(f"Patched DEFAULT_TIMEOUT: was 600, now {sai_runner.DEFAULT_TIMEOUT}")
'@
$patchScript | Out-File -FilePath 'C:\ProjectS\patch_timeout.py' -Encoding ascii

Write-Host "=== Step 2: Deploy patch script ===" -ForegroundColor Cyan
Copy-Item -Path 'C:\ProjectS\patch_timeout.py' -Destination 'C:\ProjectS\project-s-code\patch_timeout.py' -ToSession $sess -Force

Write-Host "=== Step 3: Create test mission via API ===" -ForegroundColor Cyan
$existingSession = "21894e89-cf06-4103-b371-6ec90e2be44a"
$body = @{session_id=$existingSession; message="Generate an extremely long and complex response that will take more than 30 seconds to complete. Write at least 50 detailed paragraphs about the history of mathematics, covering every major discovery from ancient times to the modern era. Each paragraph should be at least 100 words long and include specific dates, names, and mathematical concepts."; user_id="gap030_test3"} | ConvertTo-Json -Compress
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15 -UseBasicParsing
    $result = $resp.Content | ConvertFrom-Json
    $missionId = $result.mission_id
    Write-Host "Mission created: $missionId" -ForegroundColor Green
} catch {
    Write-Host "FAIL to create mission: $_" -ForegroundColor Red
    $missionId = $null
}

if ($missionId) {
    Write-Host "`n=== Step 4: Polling mission status (max 120s) ===" -ForegroundColor Cyan
    $pollStart = Get-Date
    $finalState = "UNKNOWN"
    $count = 0
    $stateHistory = @()

    while ((Get-Date).Subtract($pollStart).TotalSeconds -lt 120) {
        Start-Sleep -Seconds 3
        $count++
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat/mission/$missionId/status" -TimeoutSec 5 -UseBasicParsing
            $status = $resp.Content | ConvertFrom-Json
            $state = $status.state
            $progress = $status.progress
            $elapsed = [int](Get-Date).Subtract($pollStart).TotalSeconds
            Write-Host "  [$count] [$elapsed s] $state (progress: $progress)" -ForegroundColor Yellow
            $stateHistory += "$state|$progress|$elapsed"
            $finalState = $state

            if (($state -eq "COMPLETE") -or ($state -eq "FAILED") -or ($state -eq "TIMEOUT")) {
                Write-Host "  -> Terminal state reached: $state at ${elapsed}s" -ForegroundColor Green
                break
            }
        } catch {
            Write-Host "  Poll error: $_" -ForegroundColor Red
        }
    }

    Write-Host "`n=== Step 5: Final Results ===" -ForegroundColor Cyan
    Write-Host "  Mission ID: $missionId" -ForegroundColor White
    Write-Host "  Final state: $finalState" -ForegroundColor $(if ($finalState -eq "TIMEOUT") { "Green" } elseif ($finalState -eq "EXECUTING") { "Red" } else { "Yellow" })
    
    $timeoutWithinWindow = $false
    if ($finalState -eq "TIMEOUT") {
        $lastEntry = $stateHistory[-1]
        $lastElapsed = $lastEntry.Split('|')[2]
        if ([int]$lastElapsed -le 90) {
            $timeoutWithinWindow = $true
            Write-Host "  Timeout within 90s window: YES" -ForegroundColor Green
        } else {
            Write-Host "  Timeout within 90s window: NO (took ${lastElapsed}s)" -ForegroundColor Yellow
        }
    }

    Write-Host "  State history entries: $($stateHistory.Count)" -ForegroundColor White
    foreach ($entry in $stateHistory) {
        Write-Host "    $entry" -ForegroundColor Gray
    }
} else {
    $finalState = "N/A (mission creation failed)"
}

Write-Host "`n=== Step 6: SQLite check ===" -ForegroundColor Cyan
$sqliteCheck = Invoke-Command -Session $sess -ScriptBlock {
    python -c "import sqlite3; conn=sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db'); rows=conn.execute('SELECT mission_id,state,progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall(); [print(f'{r[0]} | {r[1]} | {r[2]}') for r in rows]; conn.close()" 2>&1 | Out-String
}
Write-Host $sqliteCheck

Write-Host "`n=== Step 7: Post-test health ===" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "  Health: PASS ($($resp.StatusCode))" -ForegroundColor Green
    $healthAfter = $true
} catch {
    Write-Host "  Health: FAIL" -ForegroundColor Red
    $healthAfter = $false
}

# Save results
$results = @{
    mission_id = $missionId
    final_state = $finalState
    timeout_within_window = if ($missionId) { $timeoutWithinWindow } else { $null }
    state_history = $stateHistory
    health_after = if ($missionId) { $healthAfter } else { $null }
    validation_executed = if ($missionId) { $true } else { $false }
} | ConvertTo-Json -Depth 10
$results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_final_results.json" -Encoding UTF8

Write-Host "`n=== GAP_030 FINAL STATUS ===" -ForegroundColor Cyan
if ($finalState -eq "TIMEOUT" -and $timeoutWithinWindow -and $healthAfter) {
    Write-Host "  RESOLVED" -ForegroundColor Green
} else {
    Write-Host "  PARTIAL" -ForegroundColor Yellow
    Write-Host "  Details: state=$finalState timeout_window=$timeoutWithinWindow health=$healthAfter" -ForegroundColor Yellow
}

Remove-PSSession $sess