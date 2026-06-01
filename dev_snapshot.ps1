$ts = Get-Date -Format 'yyyy-MM-dd-HHmm'
$bak = "C:\ProjectS-Backups\$ts-pre-server-migration"
New-Item -ItemType Directory $bak -Force | Out-Null
Write-Host "Backup dir created: $bak" -ForegroundColor Green

$files = @(
    "C:\ProjectS-Unified\self_state.json",
    "C:\ProjectS-Unified\PROJECT_S_OVERVIEW.md",
    "C:\ProjectS-Unified\PROJECT_S_STATUS_AND_JOURNAL.md",
    "C:\ProjectS-Unified\memory\intelligence\meta_evidence.jsonl",
    "C:\ProjectS-Unified\interactive_layer_data\interactive.db"
)

$copied = 0
$skipped = 0
foreach ($f in $files) {
    if (Test-Path $f) {
        $destDir = Join-Path $bak (Split-Path $f -Parent | Split-Path -Leaf)
        New-Item -ItemType Directory $destDir -Force | Out-Null
        Copy-Item $f $bak -Force | Out-Null
        Write-Host "COPIED: $f" -ForegroundColor Green
        $copied++
    } else {
        Write-Host "SKIPPED (not found): $f" -ForegroundColor Yellow
        $skipped++
    }
}

Write-Host "`nBackup summary: $copied files copied, $skipped skipped" -ForegroundColor Cyan
Write-Host "Backup location: $bak" -ForegroundColor Cyan