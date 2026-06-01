$targetIP = "192.168.1.180"
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
    Write-Host "=== WINRM LISTENER ENUM ===" -ForegroundColor Cyan
    winrm enumerate winrm/config/listener 2>&1
    
    Write-Host ""
    Write-Host "=== WINRM CONFIG ===" -ForegroundColor Cyan
    winrm get winrm/config 2>&1
    
    Write-Host ""
    Write-Host "=== WINRM SERVICE ===" -ForegroundColor Cyan
    Get-Service WinRM | Format-List *
    
    Write-Host ""
    Write-Host "=== TCP 5985 LISTENING ===" -ForegroundColor Cyan
    Get-NetTCPConnection -LocalPort 5985 -State Listen -ErrorAction SilentlyContinue | Format-List *
    
    Write-Host ""
    Write-Host "=== LOCALACCOUNTTOKENFILTERPOLICY ===" -ForegroundColor Cyan
    $val = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name LocalAccountTokenFilterPolicy -ErrorAction SilentlyContinue
    if ($val) { Write-Host "Value: $($val.LocalAccountTokenFilterPolicy)" -ForegroundColor Green }
    else { Write-Host "NOT SET (default=0)" -ForegroundColor Yellow }
}