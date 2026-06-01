# Configure TrustedHosts for WinRM
Write-Host "Configuring TrustedHosts..." -ForegroundColor Cyan
winrm set "winrm/config/client" "@{TrustedHosts=\"192.168.1.180\"}"
if ($LASTEXITCODE -eq 0) {
    Write-Host "TrustedHosts configured successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to configure TrustedHosts (exit code: $LASTEXITCODE)" -ForegroundColor Red
}