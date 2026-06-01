$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Latest system.log ===" -ForegroundColor Cyan
    $logFile = "C:\ProjectS\project-s-code\logs\system.log"
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail 50
    } else {
        Write-Host "Log file not found"
    }
    
    Write-Host "`n=== Check if server process running ===" -ForegroundColor Cyan
    $procs = Get-Process python -ErrorAction SilentlyContinue
    if ($procs) {
        $procs | ForEach-Object { Write-Host "PID: $($_.Id) CPU: $($_.CPU)s" }
    } else {
        Write-Host "No Python processes"
    }
    
    Write-Host "`n=== Port 8000 status ===" -ForegroundColor Cyan
    netstat -ano | findstr :8000
} -ErrorAction Stop

Remove-PSSession $s