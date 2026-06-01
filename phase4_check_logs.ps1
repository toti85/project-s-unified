$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $logPath = "C:\ProjectS\project-s-code\logs"
    if (Test-Path $logPath) {
        $logs = Get-ChildItem $logPath -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5
        foreach ($log in $logs) {
            Write-Host "--- $($log.Name) ---" -ForegroundColor Cyan
            Get-Content $log.FullName -Tail 30
        }
    } else {
        Write-Host "No logs dir" -ForegroundColor Yellow
        $codePath = "C:\ProjectS\project-s-code"
        Get-ChildItem $codePath -Filter "*.log" -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "--- $($_.Name) ---" -ForegroundColor Cyan
            Get-Content $_.FullName -Tail 20
        }
    }
}