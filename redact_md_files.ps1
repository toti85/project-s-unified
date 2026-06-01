$key = "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"
$redacted = "[REDACTED - EXPOSED KEY REMOVED]"
$files = @('DEPLOYMENT_SUMMARY.md','FIX_IMPLEMENTATION.md','IMPLEMENTATION_GUIDE.md','LAUNCH_GUIDE.md','README_FIX_INDEX.md','SERVER_HUNT_README.md','TEST_RESULTS.md')

foreach ($f in $files) {
    $p = "C:\ProjectS-Unified\" + $f
    if (Test-Path $p) {
        $c = Get-Content $p -Raw
        $n = $c -replace [regex]::Escape($key), $redacted
        Set-Content $p -Value $n -Encoding UTF8
        Write-Host ("Redacted: " + $p)
    } else {
        Write-Host ("Not found: " + $p)
    }
}

# Verify
Write-Host ""
Write-Host "=== Verification ===" -ForegroundColor Cyan
$remaining = Select-String -Path "C:\ProjectS-Unified\*.md" -Pattern 'sk-or-v1-' -List
if ($remaining) {
    Write-Host ("Still found in: " + ($remaining.Path | ForEach-Object { Split-Path $_ -Leaf }) -join ", ") -ForegroundColor Red
} else {
    Write-Host "All .md files cleaned." -ForegroundColor Green
}