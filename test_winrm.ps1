$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

try {
    $hostname = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock { hostname } -ErrorAction Stop
    Write-Host "Server hostname: $hostname" -ForegroundColor Green
    Write-Host "WinRM connectivity: VERIFIED" -ForegroundColor Green
} catch {
    Write-Host "WinRM connectivity FAILED: $_" -ForegroundColor Red
}