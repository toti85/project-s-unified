$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Server health check ===" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "Health: $($resp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Health FAIL: $_" -ForegroundColor Red
}

Write-Host "`n=== Creating session ===" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/sessions" -Method POST -ContentType "application/json" -Body '{"user_id":"gap030_test2"}' -TimeoutSec 10 -UseBasicParsing
    $sessionJson = $resp.Content | ConvertFrom-Json
    $sessionId = $sessionJson.session_id
    Write-Host "Session: $sessionId" -ForegroundColor Green
} catch {
    Write-Host "Session FAIL: $_" -ForegroundColor Red
    $sessionId = $null
}

if ($sessionId) {
    Write-Host "`n=== Launching mission ===" -ForegroundColor Cyan
    $prompt = "Write 3 short sentences about why documentation is important."
    $body = @{session_id=$sessionId; message=$prompt; user_id="gap030_test2"} | ConvertTo-Json
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10 -UseBasicParsing
        $missionJson = $resp.Content | ConvertFrom-Json
        $missionId = $missionJson.mission_id
        Write-Host "Mission: $missionId" -ForegroundColor Green
    } catch {
        Write-Host "Mission FAIL: $_" -ForegroundColor Red
        $missionId = $null
    }

    if ($missionId) {
        Write-Host "`n=== Polling for state (max 90s) ===" -ForegroundColor Cyan
        $pollStart = Get-Date
        $maxWait = 90
        $finalState = "UNKNOWN"
        $stateHistory = @()

        while ((Get-Date).Subtract($pollStart).TotalSeconds -lt $maxWait) {
            Start-Sleep -Seconds 3
            try {
                $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat/mission/$missionId/status" -TimeoutSec 5 -UseBasicParsing
                $statusJson = $resp.Content | ConvertFrom-Json
                $state = $statusJson.state
                $progress = $statusJson.progress
                $elapsed = [int](Get-Date).Subtract($pollStart).TotalSeconds
                Write-Host "  [$elapsed s] $state (progress: $progress)" -ForegroundColor Yellow
                $stateHistory += "$state|$progress|$elapsed"
                $finalState = $state

                if (($state -eq "COMPLETE") -or ($state -eq "FAILED") -or ($state -eq "TIMEOUT")) {
                    Write-Host "  -> Terminal state reached: $state" -ForegroundColor Green
                    break
                }
            } catch {
                Write-Host "  Poll error: $_" -ForegroundColor Red
            }
        }

        Write-Host "`n=== Final state: $finalState ===" -ForegroundColor Cyan
        Write-Host "State history:" -ForegroundColor Cyan
        foreach ($entry in $stateHistory) {
            Write-Host "  $entry" -ForegroundColor Gray
        }
    }
}

Write-Host "`n=== Checking SQLite ===" -ForegroundColor Cyan
$sqliteCheck = Invoke-Command -Session $sess -ScriptBlock {
    $py = @"
import sqlite3
conn = sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db')
rows = conn.execute('SELECT mission_id, state, progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall()
for r in rows:
    print(f'{r[0]} | {r[1]} | {r[2]}')
conn.close()
"@
    python -c $py 2>&1 | Out-String
}
Write-Host $sqliteCheck

Write-Host "`n=== Post-test health ===" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "Health after: $($resp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Health after FAIL: $_" -ForegroundColor Red
}

Remove-PSSession $sess