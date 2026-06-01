$extIP = "46.253.140.72"
$extPort = 15985
$securePass = ConvertTo-SecureString "Qwe123" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("Administrator", $securePass)

$s = New-PSSession -ComputerName $extIP -Port $extPort -Credential $cred -ErrorAction Stop

Invoke-Command -Session $s -ScriptBlock {
    Write-Host "=== Capturing server startup error ===" -ForegroundColor Cyan
    
    # Run server and capture ALL output including errors
    $proc = Start-Process python -ArgumentList "interactive_layer\start_server.py" `
        -WorkingDirectory "C:\ProjectS\project-s-code" `
        -RedirectStandardOutput "C:\ProjectS\server_stdout_capture.txt" `
        -RedirectStandardError "C:\ProjectS\server_stderr_capture.txt" `
        -PassThru
    
    Write-Host "Server PID: $($proc.Id)"
    Start-Sleep -Seconds 12
    
    # Check if still running
    $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($stillRunning) {
        Write-Host "Server still running!" -ForegroundColor Green
    } else {
        Write-Host "Server exited with code: $($proc.ExitCode)" -ForegroundColor Red
    }
    
    # Show output
    Write-Host "`n=== STDOUT ===" -ForegroundColor Cyan
    if (Test-Path "C:\ProjectS\server_stdout_capture.txt") {
        Get-Content "C:\ProjectS\server_stdout_capture.txt"
    } else {
        Write-Host "(empty)"
    }
    
    Write-Host "`n=== STDERR ===" -ForegroundColor Cyan
    if (Test-Path "C:\ProjectS\server_stderr_capture.txt") {
        Get-Content "C:\ProjectS\server_stderr_capture.txt"
    } else {
        Write-Host "(empty)"
    }
} -ErrorAction Stop

Remove-PSSession $s