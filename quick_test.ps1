$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

# Use existing session
$existingSession = "21894e89-cf06-4103-b371-6ec90e2be44a"

Write-Host "=== Testing POST /api/chat ===" -ForegroundColor Cyan
$body = @{session_id=$existingSession; message="Write 3 short sentences about why documentation is important."; user_id="gap030_test"} | ConvertTo-Json -Compress
Write-Host "Body: $body" -ForegroundColor Gray
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15 -UseBasicParsing
    $result = $resp.Content | ConvertFrom-Json
    Write-Host "Response: $($resp.Content)" -ForegroundColor Green
    $missionId = $result.mission_id
    Write-Host "Mission ID: $missionId" -ForegroundColor Green
} catch {
    Write-Host "FAIL: $_" -ForegroundColor Red
    $missionId = $null
}

if ($missionId) {
    Write-Host "`n=== Polling mission status (max 90s) ===" -ForegroundColor Cyan
    $pollStart = Get-Date
    $finalState = "UNKNOWN"
    $count = 0

    while ((Get-Date).Subtract($pollStart).TotalSeconds -lt 90) {
        Start-Sleep -Seconds 3
        $count++
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat/mission/$missionId/status" -TimeoutSec 5 -UseBasicParsing
            $status = $resp.Content | ConvertFrom-Json
            $state = $status.state
            $progress = $status.progress
            $elapsed = [int](Get-Date).Subtract($pollStart).TotalSeconds
            Write-Host "  [$count] [$elapsed s] $state (progress: $progress)" -ForegroundColor Yellow
            $finalState = $state

            if (($state -eq "COMPLETE") -or ($state -eq "FAILED") -or ($state -eq "TIMEOUT")) {
                Write-Host "  -> Terminal state: $state" -ForegroundColor Green
                break
            }
        } catch {
            Write-Host "  Poll error: $_" -ForegroundColor Red
        }
    }

    Write-Host "`n=== Final state: $finalState ===" -ForegroundColor Cyan
}

Write-Host "`n=== SQLite check ===" -ForegroundColor Cyan
$sqliteCheck = Invoke-Command -Session $sess -ScriptBlock {
    python -c "import sqlite3; conn=sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db'); rows=conn.execute('SELECT mission_id,state,progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall(); [print(f'{r[0]} | {r[1]} | {r[2]}') for r in rows]; conn.close()" 2>&1 | Out-String
}
Write-Host $sqliteCheck

Write-Host "`n=== Post-test health ===" -ForegroundColor Cyan
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "Health: $($resp.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Health FAIL: $_" -ForegroundColor Red
}

Remove-PSSession $sess