$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Patching sai_runner.py DEFAULT_TIMEOUT to 30 ===" -ForegroundColor Cyan
$patchCode = @'
import sys
sys.path.insert(0, r'C:\ProjectS\project-s-code')
with open(r'C:\ProjectS\project-s-code\interactive_layer\sai_runner.py', 'r') as f:
    content = f.read()
content = content.replace('DEFAULT_TIMEOUT = 600', 'DEFAULT_TIMEOUT = 30')
with open(r'C:\ProjectS\project-s-code\interactive_layer\sai_runner.py', 'w') as f:
    f.write(content)
print("Patched DEFAULT_TIMEOUT to 30")
'@
$patchCode | Out-File -FilePath 'C:\ProjectS\patch_sai_runner.py' -Encoding ascii
Copy-Item -Path 'C:\ProjectS\patch_sai_runner.py' -Destination 'C:\ProjectS\project-s-code\patch_sai_runner.py' -ToSession $sess -Force

Invoke-Command -Session $sess -ScriptBlock {
    python C:\ProjectS\project-s-code\patch_sai_runner.py 2>&1 | Out-String
} | Write-Host

Write-Host "`n=== Killing old server ===" -ForegroundColor Cyan
Invoke-Command -Session $sess -ScriptBlock {
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 3
}

Write-Host "=== Starting server with patched code ===" -ForegroundColor Cyan
Invoke-Command -Session $sess -ScriptBlock {
    $env:PYTHONUNBUFFERED = "1"
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "python"
    $startInfo.Arguments = "-u C:\ProjectS\project-s-code\interactive_layer\start_server.py"
    $startInfo.WorkingDirectory = "C:\ProjectS\project-s-code"
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($startInfo)
    Write-Host "  Server started (PID: $($proc.Id))"
}

Write-Host "=== Waiting for server ===" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -UseBasicParsing
        if ($resp.StatusCode -eq 200) {
            Write-Host "  Server ready after $($i * 2)s" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
}

if ($ready) {
    Write-Host "`n=== Creating test mission ===" -ForegroundColor Cyan
    $existingSession = "21894e89-cf06-4103-b371-6ec90e2be44a"
    $body = @{session_id=$existingSession; message="Write a very detailed and comprehensive analysis of the history of mathematics from ancient times to the modern era. Include at least 20 paragraphs covering every major discovery, mathematician, and concept. Each paragraph should be detailed and thorough, including specific dates, names, and mathematical concepts. Be extremely verbose and detailed in your response."; user_id="toti"} | ConvertTo-Json -Compress
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
        Write-Host "`n=== Polling (max 90s) ===" -ForegroundColor Cyan
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
                $elapsed = [int](Get-Date).Subtract($pollStart).TotalSeconds
                Write-Host "  [$count] [$elapsed s] $state" -ForegroundColor Yellow
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

        # SQLite check
        $sqliteCheck = Invoke-Command -Session $sess -ScriptBlock {
            python -c "import sqlite3; conn=sqlite3.connect(r'C:\ProjectS\project-s-code\interactive_layer_data\interactive.db'); rows=conn.execute('SELECT mission_id,state,progress FROM missions ORDER BY updated_at DESC LIMIT 5').fetchall(); [print(f'{r[0]} | {r[1]} | {r[2]}') for r in rows]; conn.close()" 2>&1 | Out-String
        }
        Write-Host "SQLite:" -ForegroundColor Cyan
        Write-Host $sqliteCheck

        # Health check
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
            gap030_status = if ($finalState -eq "TIMEOUT" -and $healthAfter) { "RESOLVED" } else { "PARTIAL" }
        } | ConvertTo-Json -Depth 10
        $results | Out-File -FilePath "C:\ProjectS-Unified\.gap030_timeout_patch_results.json" -Encoding UTF8
    }
}

Remove-PSSession $sess