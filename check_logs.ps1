$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$sess = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Write-Host "=== Server logs (last 100 lines) ===" -ForegroundColor Cyan
$logs = Invoke-Command -Session $sess -ScriptBlock {
    if (Test-Path 'C:\ProjectS\project-s-code\logs\system.log') {
        Get-Content 'C:\ProjectS\project-s-code\logs\system.log' -Tail 100 -Raw
    } else {
        "No system.log found"
    }
}
Write-Host $logs

Write-Host "`n=== Server stdout (last 50 lines) ===" -ForegroundColor Cyan
$stdout = Invoke-Command -Session $sess -ScriptBlock {
    if (Test-Path 'C:\ProjectS\server_stdout.txt') {
        Get-Content 'C:\ProjectS\server_stdout.txt' -Tail 50 -Raw
    } else {
        "No server_stdout.txt found"
    }
}
Write-Host $stdout

Write-Host "`n=== Python process check ===" -ForegroundColor Cyan
$procs = Invoke-Command -Session $sess -ScriptBlock {
    $p = Get-Process python -ErrorAction SilentlyContinue
    if ($p) {
        $p | Format-Table Id, ProcessName, StartTime, WorkingSet -AutoSize | Out-String
    } else {
        "No python processes"
    }
}
Write-Host $procs

Remove-PSSession $sess