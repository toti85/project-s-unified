$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== 1. Check Python syntax ===" -ForegroundColor Cyan
    $result = python -m py_compile C:\ProjectS\project-s-code\interactive_layer\sai_runner.py 2>&1 | Out-String
    Write-Host $result

    Write-Host "=== 2. Check module import ===" -ForegroundColor Cyan
    cd C:\ProjectS\project-s-code
    $result = python -c "import interactive_layer.sai_runner; print('Import OK')" 2>&1 | Out-String
    Write-Host $result

    Write-Host "=== 3. Check port 8000 ===" -ForegroundColor Cyan
    $ports = netstat -ano | findstr :8000
    if ($ports) {
        Write-Host "Port 8000 in use:" -ForegroundColor Red
        Write-Host $ports
    } else {
        Write-Host "Port 8000 free" -ForegroundColor Green
    }

    Write-Host "=== 4. Check Python processes ===" -ForegroundColor Cyan
    $pyProcs = Get-Process python -ErrorAction SilentlyContinue
    if ($pyProcs) {
        Write-Host ("Python processes: " + $pyProcs.Count)
        $pyProcs | ForEach-Object { Write-Host "  PID: $($_.Id) Name: $($_.ProcessName)" }
    } else {
        Write-Host "No Python processes running" -ForegroundColor Green
    }

    Write-Host "=== 5. Check server logs ===" -ForegroundColor Cyan
    $logDir = "C:\ProjectS\project-s-code\logs"
    if (Test-Path $logDir) {
        $latest = Get-ChildItem $logDir -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latest) {
            Write-Host ("Latest log: " + $latest.FullName)
            Get-Content $latest.FullName -Tail 30
        }
    }

    Write-Host "=== 6. Check server stdout ===" -ForegroundColor Cyan
    $stdoutFile = "C:\ProjectS\reports\SERVER_PHASE_4_3B_STDOUT_20260518.txt"
    if (Test-Path $stdoutFile) {
        Write-Host "Stdout file exists, last 20 lines:"
        Get-Content $stdoutFile -Tail 20
    }

    Write-Host "=== 7. Try starting server in foreground ===" -ForegroundColor Cyan
    Write-Host "Starting server in a new process and capturing output..."
    $proc = Start-Process python -ArgumentList "interactive_layer\start_server.py" -WorkingDirectory "C:\ProjectS\project-s-code" -PassThru -WindowStyle Hidden
    Write-Host "Server PID: $($proc.Id)"
    Start-Sleep -Seconds 10

    Write-Host "=== 8. Check if server is running ===" -ForegroundColor Cyan
    $proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Id -eq $proc.Id }
    if ($proc) {
        Write-Host "Server process still running" -ForegroundColor Green
    } else {
        Write-Host "Server process exited" -ForegroundColor Red
    }

    Write-Host "=== 9. Check port 8000 again ===" -ForegroundColor Cyan
    $ports = netstat -ano | findstr :8000
    if ($ports) {
        Write-Host "Port 8000 listening:" -ForegroundColor Green
        Write-Host $ports
    } else {
        Write-Host "Port 8000 NOT listening" -ForegroundColor Red
    }
} -ErrorAction Stop

Remove-PSSession $s