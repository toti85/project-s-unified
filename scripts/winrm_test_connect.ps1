# Quick WinRM connectivity test to 192.168.1.180
# Using iLO credentials as server password (trial)

$targetIP = "192.168.1.180"
$password = ConvertTo-SecureString "PTSYK7BF" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential ("$targetIP\Administrator", $password)

Write-Host "=== WinRM Test Connection to $targetIP ===" -ForegroundColor Cyan
Write-Host "Using credentials: $targetIP\Administrator" -ForegroundColor Yellow
Write-Host ""

try {
    $result = Invoke-Command -ComputerName $targetIP -Credential $cred -ScriptBlock {
        $env:COMPUTERNAME
    } -ErrorAction Stop
    Write-Host "SUCCESS! Hostname: $result" -ForegroundColor Green
} catch {
    Write-Host "FAILED: $_" -ForegroundColor Red
}