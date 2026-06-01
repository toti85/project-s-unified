$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Firewall rules for port 8000 ===" -ForegroundColor Cyan
    $rules = netsh advfirewall firewall show rule name=all | Select-String "8000"
    if ($rules) {
        Write-Host $rules
    } else {
        Write-Host "No firewall rules for port 8000" -ForegroundColor Red
    }
    
    Write-Host "`n=== All listening ports ===" -ForegroundColor Cyan
    netstat -ano | findstr LISTENING
    
    Write-Host "`n=== Create firewall rule ===" -ForegroundColor Cyan
    netsh advfirewall firewall add rule name="Interactive Layer HTTP" dir=in action=allow protocol=TCP localport=8000
    Write-Host "Firewall rule created" -ForegroundColor Green
    
    Write-Host "`n=== Verify rule ===" -ForegroundColor Cyan
    netsh advfirewall firewall show rule name="Interactive Layer HTTP"
} -ErrorAction Stop

Remove-PSSession $s