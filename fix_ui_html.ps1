$source = "C:\ProjectS-Unified"
$destUNC = "\\192.168.1.180\ProjectSStage"
$userName = "192.168.1.180\Administrator"
$password = "Qwe123"

Write-Host "=== Fixing ui.html transfer ===" -ForegroundColor Cyan

# Map network drive
net use $destUNC $password /user:$userName /persistent:no 2>$null
Start-Sleep -Seconds 2

# Copy ui.html specifically
$uiSource = Join-Path $source "interactive_layer\static\ui.html"
$uiDest = Join-Path $destUNC "interactive_layer\static"

Write-Host "Source: $uiSource" -ForegroundColor Gray
Write-Host "Dest: $uiDest" -ForegroundColor Gray

if (Test-Path $uiSource) {
    if (!(Test-Path $uiDest)) {
        New-Item -Path $uiDest -ItemType Directory -Force | Out-Null
        Write-Host "Created directory: $uiDest" -ForegroundColor Green
    }
    Copy-Item -Path $uiSource -Destination $uiDest -Force
    Write-Host "ui.html copied successfully" -ForegroundColor Green
    
    # Verify
    $verifyDest = Join-Path $uiDest "ui.html"
    if (Test-Path $verifyDest) {
        $size = (Get-Item $verifyDest).Length
        Write-Host "Verified: $verifyDest ($size bytes)" -ForegroundColor Green
    }
} else {
    Write-Host "Source ui.html not found at: $uiSource" -ForegroundColor Red
}

# Cleanup
net use $destUNC /delete /y 2>$null