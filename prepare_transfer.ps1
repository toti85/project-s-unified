$devSource = "C:\ProjectS-Unified"
$excludePatterns = @(".git", "__pycache__", "*.pyc", ".pytest_cache", ".vscode", "*.exe", "*.apk", "*.rbxm", "*.rbxl", "node_modules", ".benchmarks", "*.log")

$transferList = @()
$allItems = Get-ChildItem -Path $devSource -Recurse -Force -ErrorAction SilentlyContinue
foreach ($item in $allItems) {
    $relativePath = $item.FullName.Substring($devSource.Length + 1)
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    if (-not $shouldExclude) {
        $transferList += $relativePath
    }
}

Write-Host "Files to transfer: $($transferList.Count)" -ForegroundColor Green

# Save transfer list
$transferList | Out-File -FilePath "C:\ProjectS-Unified\.transfer_list.txt" -Encoding UTF8
Write-Host "Transfer list saved to .transfer_list.txt" -ForegroundColor Green

# Show directory structure summary
$dirs = $transferList | Where-Object { $_ -notlike "*.*" -or $_ -like "*\*" }
$fileItems = $transferList | Where-Object { $_ -like "*.*" }
Write-Host "Directories in transfer: $($dirs.Count)" -ForegroundColor Yellow
Write-Host "Files in transfer: $($fileItems.Count)" -ForegroundColor Yellow

# Show top-level directories
Write-Host "`nTop-level structure:" -ForegroundColor Cyan
Get-ChildItem -Path $devSource -Force | Select-Object Name, Mode | Format-Table -AutoSize