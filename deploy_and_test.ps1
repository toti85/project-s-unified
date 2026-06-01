$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Deploying FK fix ===" -ForegroundColor Cyan
Copy-Item -Path "C:\ProjectS-Unified\interactive_layer\main.py" -Destination "C:\ProjectS\project-s-code\interactive_layer\main.py" -ToSession $sess -Force
Write-Host "  Deployed: main.py (FK fix)"

Write-Host "`n=== Restarting server ===" -ForegroundColor Cyan
Invoke-Command -Session $sess -ScriptBlock {
    taskkill /F /IM python.exe /T 2>&1 | Out-Null
    Start-Sleep -Seconds 3
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
    Write-Host "`n=== Testing POST /api/chat ===" -ForegroundColor Cyan
    $existingSession = "21894e89-cf06-4103-b371-6ec90e2be44a"
    $body = @{session_id=$existingSession; message="Say hello."; user_id="toti"} | ConvertTo-Json -Compress
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15 -UseBasicParsing
        $result = $resp.Content | ConvertFrom-Json
        $missionId = $result.mission_id
        Write-Host "  Mission created: $missionId" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: $_" -ForegroundColor Red
    }
}

Remove-PSSession $sess