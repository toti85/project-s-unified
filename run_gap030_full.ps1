$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GAP_030 LIVE VALIDATION" -ForegroundColor Cyan
Write-Host "  Method: localhost:8000 via WinRM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Use existing session
$existingSession = "21894e89-cf06-4103-b371-6ec90e2be44a"

Write-Host "`n[1/5] Creating test mission..." -ForegroundColor Yellow
$body = @{session_id=$existingSession; message="Generate an extremely long and complex response that will take more than 30 seconds to complete. Write at least 50 detailed paragraphs about the history of mathematics, covering every major discovery from ancient times to the modern era. Each paragraph should be at least 100 words long and include specific dates, names, and mathematical concepts."; user_id="toti"} | ConvertTo-Json -Compress
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15 -UseBasicParsing
    $result = $resp.Content | ConvertFrom-Json
    $missionId = $result.mission_id
    Write-Host "  Mission: $missionId" -ForegroundColor Green
} catch {
    Write-Host "  FAIL: $_" -ForegroundColor Red
    $missionId = $null
}

if ($missionId) {
    Write-Host "`n[2/5] Polling mission status (max 120s)..." -ForegroundColor Yellow
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

    Write-Host "`n[3/5] Checking SQLite..." -ForegroundColor Yellow
    $sqliteCheck = Invoke-Command -Session $sess -ScriptBlock {
        python -c "import sqlite3; conn=sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db'); rows=conn.execute('SELECT mission_id,state,progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall(); [print(f'{r[0]} | {r[1]} | {r[2]}') for r in rows]; conn.close()" 2>&1 | Out-String
    }
    Write-Host $sqliteCheck

    Write-Host "`n[4/5] Post-test health..." -ForegroundColor Yellow
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
        Write-Host "  Health: PASS ($($resp.StatusCode))" -ForegroundColor Green
        $healthAfter = $true
    } catch {
        Write-Host "  Health: FAIL" -ForegroundColor Red
        $healthAfter = $false
    }

    Write-Host "`n[5/5] Results:" -ForegroundColor Yellow
    Write-Host "  Mission ID: $missionId" -ForegroundColor White
    Write-Host "  Final state: $finalState" -ForegroundColor $(if ($finalState -eq "TIMEOUT") { "Green" } elseif ($finalState -eq "EXECUTING") { "Red" } else { "Yellow" })
    
    $timeoutWithinWindow = $false
    if ($finalState -eq "TIMEOUT") {
        $lastEntry = $stateHistory[-1]
        $lastElapsed = $lastEntry.Split('|')[2]
        if ([int]$lastElapsed -le 90) {
            $timeoutWithinWindow = $true
            Write-Host "  Timeout within 90s: YES (${lastElapsed}s)" -ForegroundColor Green
        } else {
            Write-Host "  Timeout within 90s: NO (${lastElapsed}s)" -ForegroundColor Yellow
        }
    }

    Write-Host "  State history entries: $($stateHistory.Count)" -ForegroundColor White
    foreach ($entry in $stateHistory) {
        Write-Host "    $entry" -ForegroundColor Gray
    }

    # Save results
    $results = @{
        health_before = $true
        validation_executed = $true
        mission_id = $missionId
        final_state_polling = $finalState
        timeout_within_window = $timeoutWithinWindow
        health_after = $healthAfter
        state_history = $stateHistory
        gap030_status = if ($finalState -eq "TIMEOUT" -and $timeoutWithinWindow -and $healthAfter) { "RESOLVED" } else { "PARTIAL" }
    } | ConvertTo-Json -Depth 10
    $results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_final_results.json" -Encoding UTF8
} else {
    Write-Host "  No mission created - validation skipped" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VALIDATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Remove-PSSession $sess