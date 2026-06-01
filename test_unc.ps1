$shareName = "ProjectSStage"
$uncPath = "\\192.168.1.180\$shareName"

Write-Host "Testing UNC path: $uncPath" -ForegroundColor Cyan

# Test with Test-Path
try {
    $result = Test-Path $uncPath -ErrorAction Stop
    Write-Host "Test-Path result: $result" -ForegroundColor $(if($result){"Green"}else{"Red"})
} catch {
    Write-Host "Test-Path failed: $_" -ForegroundColor Red
}

# Try net use with explicit credentials
Write-Host ""
Write-Host "Trying net use..." -ForegroundColor Yellow
$userName = "192.168.1.180\Administrator"
$cmd = "net use"
$arg1 = $uncPath
$arg2 = "Qwe123"
$arg3 = "/user:192.168.1.180\Administrator"
Write-Host "  Running: net use $arg1 $arg2 $arg3" -ForegroundColor Gray
net use $arg1 $arg2 $arg3

Start-Sleep -Seconds 3

try {
    $result2 = Test-Path $uncPath -ErrorAction Stop
    Write-Host "Test-Path after net use: $result2" -ForegroundColor $(if($result2){"Green"}else{"Red"})
} catch {
    Write-Host "Test-Path failed after net use: $_" -ForegroundColor Red
}

# List contents if reachable
if ($result2) {
    Write-Host ""
    Write-Host "Contents of share:" -ForegroundColor Cyan
    Get-ChildItem $uncPath -ErrorAction SilentlyContinue | Format-Table Name, Length
}

# Cleanup
Write-Host ""
Write-Host "Cleaning up net use..." -ForegroundColor Gray
$delShare = $uncPath
net use $delShare /delete /y 2>$null
