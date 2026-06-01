$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

# Use existing session with user_id "toti"
$existingSession = "21894e89-cf06-4103-b371-6ec90e2be44a"

Write-Host "=== Testing POST /api/chat with user_id=toti ===" -ForegroundColor Cyan
$body = @{session_id=$existingSession; message="Say hello."; user_id="toti"} | ConvertTo-Json -Compress
Write-Host "Body: $body" -ForegroundColor Gray
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/chat" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 15 -UseBasicParsing
    Write-Host "Response: $($resp.Content)" -ForegroundColor Green
} catch {
    Write-Host "FAIL: $_" -ForegroundColor Red
    Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        Write-Host "Error body: $($reader.ReadToEnd())" -ForegroundColor Red
        $reader.Close()
    }
}

Remove-PSSession $sess