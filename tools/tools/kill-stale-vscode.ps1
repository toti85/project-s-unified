# Kill background/stale VS Code processes but keep the current window
# Usage: Right-click > Run with PowerShell (or run in a terminal)

$ErrorActionPreference = 'SilentlyContinue'

# Try to keep the active workspace window (adjust pattern if needed)
$keep = Get-Process Code | Where-Object { $_.MainWindowTitle -match 'v2_architecture' } | Select-Object -First 1

Write-Host "Keeping PID $($keep.Id) - $($keep.MainWindowTitle)" -ForegroundColor Green

# Find stale Code.exe processes
$stale = Get-Process Code | Where-Object {
  $_.Id -ne $keep.Id -and (
    $_.MainWindowTitle -eq '' -or $_.StartTime -lt (Get-Date).AddHours(-6)
  )
}

if ($stale) {
  Write-Host "Stopping stale VS Code processes:" -ForegroundColor Yellow
  $stale | Select-Object Id, MainWindowTitle, StartTime | Format-Table -AutoSize
  $stale | Stop-Process -Force
  Write-Host "Done." -ForegroundColor Green
} else {
  Write-Host "No stale VS Code processes found." -ForegroundColor Green
}
