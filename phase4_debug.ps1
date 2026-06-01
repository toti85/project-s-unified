$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    Write-Host "=== Process check ===" -ForegroundColor Cyan
    $pyProcs = Get-Process python -ErrorAction SilentlyContinue
    if ($pyProcs) {
        $pyProcs | Format-Table Id, ProcessName, StartTime, WorkingSet64 -AutoSize
    } else {
        Write-Host "  No python processes running" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "=== .env file check ===" -ForegroundColor Cyan
    $envPath = "C:\ProjectS\project-s-code\.env"
    if (Test-Path $envPath) {
        Write-Host "  File exists" -ForegroundColor Green
        $lines = Get-Content $envPath
        Write-Host "  Lines: $($lines.Count)" -ForegroundColor Gray
        foreach ($line in $lines) {
            if ($line -match '^[A-Z_]+=' -and $line -notmatch '^#') {
                $name = ($line -split '=')[0]
                Write-Host "  VAR: $name" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  File NOT found" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "=== Listening ports (8000) ===" -ForegroundColor Cyan
    $ports = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($ports) {
        $ports | Format-Table LocalAddress, LocalPort, State, OwningProcess -AutoSize
    } else {
        Write-Host "  No listener on port 8000" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "=== All listening ports ===" -ForegroundColor Cyan
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -lt 10000 -and $_.LocalPort -gt 100 } | Format-Table LocalAddress, LocalPort, State -AutoSize
    
    Write-Host ""
    Write-Host "=== Server log check ===" -ForegroundColor Cyan
    $logPath = "C:\ProjectS\project-s-code\logs"
    if (Test-Path $logPath) {
        $logs = Get-ChildItem $logPath -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
        foreach ($log in $logs) {
            Write-Host "  Last log: $($log.Name)" -ForegroundColor Gray
            Get-Content $log.FullName -Tail 20
        }
    } else {
        Write-Host "  No logs directory" -ForegroundColor Gray
    }
}