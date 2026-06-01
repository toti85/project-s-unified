# Archaeological Analysis Script
# Direct filesystem enumeration of all dated directories

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PROJECT-S ARCHAEOLOGY: FILESYSTEM STRUCTURE ANALYSIS          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$dates = @("0809", "0725", "0723", "0720", "0714", "0713", "0712", "0703", "0630", "0616", "1225")
$results = @()

foreach ($d in $dates) {
    $path = "C:\$d"
    
    if (Test-Path -Path $path -PathType Container) {
        # Count Python files
        $pythonFiles = @(Get-ChildItem -Path $path -Filter "*.py" -Recurse -ErrorAction SilentlyContinue)
        $pyCount = $pythonFiles.Count
        
        # Get top-level folder structure
        $topFolders = @(Get-ChildItem -Path $path -Directory -ErrorAction SilentlyContinue -WarningAction SilentlyContinue).Name | Sort-Object
        
        # Check for key components
        $hasSrc = Test-Path "$path\src"
        $hasTools = Test-Path "$path\tools"
        $hasCore = Test-Path "$path\src\core"
        $hasArchive = Test-Path "$path\archive"
        
        $result = @{
            Date = $d
            PyCount = $pyCount
            Folders = $topFolders -join ", "
            HasSrc = $hasSrc
            HasTools = $hasTools
            HasCore = $hasCore
            HasArchive = $hasArchive
        }
        $results += $result
        
        # Print summary
        Write-Host "`n[OK] C:\$d"
        Write-Host "  Python files: $pyCount"
        Write-Host "  Folders: $($topFolders -join ', ')"
        if ($hasSrc) { Write-Host "  [OK] Has src/" -ForegroundColor Green }
        if ($hasTools) { Write-Host "  [OK] Has tools/" -ForegroundColor Green }
        if ($hasCore) { Write-Host "  [OK] Has src/core/" -ForegroundColor Green }
    }
}

Write-Host "`n" + "="*70
Write-Host "SUMMARY"
Write-Host "="*70
Write-Host "Directories analyzed: $($results.Count)"
Write-Host "With src/ folder: $($results | Where-Object { $_.HasSrc } | Measure-Object).Count"
Write-Host "With tools/ folder: $($results | Where-Object { $_.HasTools } | Measure-Object).Count"
Write-Host "With core/ subfolder: $($results | Where-Object { $_.HasCore } | Measure-Object).Count"

Write-Host "`nTotal Python files across all versions: $(($results.PyCount | Measure-Object -Sum).Sum)"
