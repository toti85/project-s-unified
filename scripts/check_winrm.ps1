# Check WinRM status and TrustedHosts
Write-Host "=== WinRM Diagnostic ===" -ForegroundColor Cyan

# Admin check
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "IsAdmin: $isAdmin" -ForegroundColor $(if ($isAdmin) { "Green" } else { "Yellow" })

# TrustedHosts check
Write-Host "--- TrustedHosts ---" -ForegroundColor Green
$th = Get-Item WSMan:\localhost\Client\TrustedHosts -ErrorAction SilentlyContinue
if ($th) {
    Write-Host "TrustedHosts: $($th.Value)" -ForegroundColor Green
} else {
    Write-Host "No TrustedHosts configured" -ForegroundColor Yellow
}

# WinRM service check
Write-Host "--- WinRM Service ---" -ForegroundColor Green
$winrm = Get-Service WinRM -ErrorAction SilentlyContinue
if ($winrm) {
    Write-Host "Status: $($winrm.Status)" -ForegroundColor $(if ($winrm.Status -eq 'Running') { "Green" } else { "Yellow" })
    Write-Host "StartType: $($winrm.StartType)"
} else {
    Write-Host "WinRM service not found" -ForegroundColor Red
}

# Test connection to 192.168.1.180
Write-Host "--- Port probe 192.168.1.180:5985 ---" -ForegroundColor Green
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $timeout = 2000
    $result = $tcp.BeginConnect("192.168.1.180", 5985, $null, $null)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    while (!$result.IsCompleted) { Start-Sleep -Milliseconds 100; if ($sw.ElapsedMilliseconds -gt $timeout) { break } }
    if ($tcp.Connected) { Write-Host "Port 5985 OPEN" -ForegroundColor Green } else { Write-Host "Port 5985 closed/timeout" -ForegroundColor Red }
    $tcp.EndConnect($result)
    $tcp.Close()
} catch {
    Write-Host "Port 5985 error: $_" -ForegroundColor Red
}