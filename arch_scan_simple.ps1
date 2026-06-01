$dates = @("0809","0725","0723","0720","0714","0713","1225")
$total = 0

Write-Host "PROJECT-S DIRECTORY SCAN" -ForegroundColor Cyan
Write-Host "========================="

foreach ($d in $dates) {
    $path = "C:\$d"
    if (Test-Path $path) {
        $count = @(Get-ChildItem -Path $path -Filter "*.py" -Recurse -ErrorAction SilentlyContinue).Count
        $total = $total + $count
        $folders = @(Get-ChildItem -Path $path -Directory -ErrorAction SilentlyContinue).Name -join ", "
        Write-Host "$d : $count Python files [$folders]"
    }
}

Write-Host ""
Write-Host "Total Python files: $total"
