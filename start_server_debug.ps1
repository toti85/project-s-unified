$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Debug: Start server with output capture ===" -ForegroundColor Cyan
    
    # Create a wrapper script that captures all output
    $wrapper = @'
cd C:\ProjectS\project-s-code
python -u interactive_layer\start_server.py > C:\ProjectS\server_debug_output.txt 2>&1
'@
    
    # Write wrapper to file
    $wrapper | Out-File -FilePath "C:\ProjectS\start_server_debug.bat" -Encoding ascii
    
    # Start via batch file
    $proc = Start-Process "C:\ProjectS\start_server_debug.bat" -PassThru
    Write-Host "Server PID: $($proc.Id)"
    
    # Wait
    Start-Sleep -Seconds 15
    
    # Check if running
    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($stillRunning) {
        Write-Host "Server still running!" -ForegroundColor Green
    } else {
        Write-Host "Server exited with code: $($proc.ExitCode)" -ForegroundColor Red
    }
    
    # Show captured output
    Write-Host "`n=== CAPTURED OUTPUT ===" -ForegroundColor Cyan
    if (Test-Path "C:\ProjectS\server_debug_output.txt") {
        Get-Content "C:\ProjectS\server_debug_output.txt"
    } else {
        Write-Host "(no output file)"
    }
    
    # Check port
    Write-Host "`n=== Port 8000 ===" -ForegroundColor Cyan
    $ports = netstat -ano | findstr :8000
    if ($ports) {
        Write-Host $ports -ForegroundColor Green
    } else {
        Write-Host "Port 8000 not listening" -ForegroundColor Red
    }
} -ErrorAction Stop

Remove-PSSession $s