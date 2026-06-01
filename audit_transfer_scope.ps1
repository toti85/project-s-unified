$devSource = "C:\ProjectS-Unified"

# Exclude patterns from the original transfer
$excludePatterns = @(".git", "__pycache__", "*.pyc", ".pytest_cache", ".vscode", "*.exe", "*.apk", "*.rbxm", "*.rbxl", "node_modules", ".benchmarks", "*.log")

# Build file list with exclusions
$allFiles = Get-ChildItem -Path $devSource -Recurse -Force -File -ErrorAction SilentlyContinue
$includedFiles = @()
$excludedCount = 0
$ownScripts = @(".transfer_list.txt", "transfer_v4.ps1", "transfer_v3.ps1", "transfer_to_server.ps1", "prepare_transfer.ps1", "test_winrm.ps1", "verify_server.ps1", "transfer_v2.ps1", "audit_transfer_scope.ps1")

foreach ($file in $allFiles) {
    $relativePath = $file.FullName.Substring($devSource.Length + 1)
    $leafName = Split-Path $relativePath -Leaf
    if ($ownScripts -contains $relativePath -or $ownScripts -contains $leafName) {
        continue
    }
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            $excludedCount++
            break
        }
    }
    if (-not $shouldExclude) {
        $includedFiles += [PSCustomObject]@{
            Path = $relativePath
            Size = $file.Length
            Extension = $file.Extension
            Name = $file.Name
            Directory = (Split-Path $relativePath -Parent)
        }
    }
}

$totalSize = ($includedFiles | Measure-Object -Property Size -Sum).Sum
$totalCount = $includedFiles.Count

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TRANSFER SCOPE AUDIT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total included files: $totalCount" -ForegroundColor Yellow
Write-Host "Total included size: $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host "Excluded items: $excludedCount" -ForegroundColor Gray
Write-Host ""

# 1. Size breakdown by top-level directory
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BREAKDOWN BY TOP-LEVEL DIRECTORY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$dirBreakdown = $includedFiles | Group-Object {
    $dir = $_.Directory
    if ([string]::IsNullOrEmpty($dir)) { "ROOT" }
    else { ($dir -split "\\")[0] }
} | ForEach-Object {
    $group = $_
    $groupSize = ($group | Measure-Object -Property Size -Sum).Sum
    [PSCustomObject]@{
        Directory = $group.Name
        FileCount = $group.Count
        SizeMB = [math]::Round($groupSize / 1MB, 2)
    }
} | Sort-Object SizeMB -Descending

$dirBreakdown | Format-Table -AutoSize
Write-Host ""

# 2. Size breakdown by extension
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BREAKDOWN BY FILE EXTENSION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$extBreakdown = $includedFiles | Group-Object {
    $ext = $_.Extension
    if ([string]::IsNullOrEmpty($ext)) { "(no extension)" }
    else { $ext.ToLower() }
} | ForEach-Object {
    $group = $_
    $groupSize = ($group | Measure-Object -Property Size -Sum).Sum
    [PSCustomObject]@{
        Extension = $group.Name
        FileCount = $group.Count
        SizeMB = [math]::Round($groupSize / 1MB, 2)
    }
} | Sort-Object SizeMB -Descending

$extBreakdown | Format-Table -AutoSize
Write-Host ""

# 3. Top 20 largest files
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TOP 20 LARGEST FILES" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
$top20 = $includedFiles | Sort-Object Size -Descending | Select-Object -First 20
$top20 | Format-Table @{Name="File";Expression={$_.Name}}, @{Name="Directory";Expression={$_.Directory}}, @{Name="SizeMB";Expression={[math]::Round($_.Size/1MB, 2)}} -AutoSize
Write-Host ""

# 4. Specific checks
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SPECIFIC CHECKS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$auditChecks = @(
    @{ Name = "audits_or_bounty_dirs"; Script = { $includedFiles | Where-Object { $_.Directory -like "*audit*" -or $_.Directory -like "*bounty*" } } },
    @{ Name = "meta_evidence_jsonl"; Script = { $includedFiles | Where-Object { $_.Name -like "*meta_evidence*" } } },
    @{ Name = "large_SQLite_DB_files"; Script = { $includedFiles | Where-Object { $_.Extension -in @(".db", ".sqlite", ".sqlite3") } } },
    @{ Name = "Playwright_browser_caches"; Script = { $includedFiles | Where-Object { $_.Directory -like "*playwright*" -or $_.Directory -like "*browser*" -or $_.Directory -like "*screenshot*" } } },
    @{ Name = "Roblox_assets"; Script = { $includedFiles | Where-Object { $_.Extension -in @(".rbxl", ".rbxm", ".rbxlx") } } },
    @{ Name = "Backups"; Script = { $includedFiles | Where-Object { $_.Extension -in @(".bak", ".old", ".orig") } } },
    @{ Name = "Large_archives_zip"; Script = { $includedFiles | Where-Object { $_.Extension -eq ".zip" } } },
    @{ Name = "EventLog_csv"; Script = { $includedFiles | Where-Object { $_.Name -eq "EventLog.csv" } } },
    @{ Name = "tech_news_db"; Script = { $includedFiles | Where-Object { $_.Name -eq "tech_news.db" } } },
    @{ Name = "SessionKeyPoC_zip"; Script = { $includedFiles | Where-Object { $_.Name -eq "SessionKeyPoC.zip" } } }
)

foreach ($check in $auditChecks) {
    $result = & $check.Script
    if ($result.Count -gt 0) {
        $checkSize = ($result | Measure-Object -Property Size -Sum).Sum
        Write-Host "  [FOUND] $($check.Name): $($result.Count) files, $([math]::Round($checkSize/1MB, 2)) MB" -ForegroundColor Red
        $result | Select-Object -First 5 Name, Directory, @{Name="SizeMB";Expression={[math]::Round($_.Size/1MB, 2)}} | Format-Table -AutoSize -HideTableHeaders | ForEach-Object { Write-Host "    $_" }
    } else {
        Write-Host "  [NONE]  $($check.Name)" -ForegroundColor Green
    }
}
Write-Host ""

# 5. Summary
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AUDIT SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Total files to transfer: $totalCount" -ForegroundColor White
Write-Host "  Total size: $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""

# Check specific categories
$hasAudit = $false
$hasMetaEvidence = $false
$hasRoblox = $false
$hasArchives = $false
$hasDB = $false
$hasMedia = $false
$hasInstallers = $false

foreach ($f in $includedFiles) {
    if ($f.Directory -like "*audit*" -or $f.Directory -like "*bounty*") { $hasAudit = $true }
    if ($f.Name -like "*meta_evidence*") { $hasMetaEvidence = $true }
    if ($f.Extension -in @(".rbxl", ".rbxm")) { $hasRoblox = $true }
    if ($f.Extension -eq ".zip") { $hasArchives = $true }
    if ($f.Extension -in @(".db", ".sqlite")) { $hasDB = $true }
    if ($f.Extension -in @(".png", ".jpg", ".jpeg")) { $hasMedia = $true }
    if ($f.Extension -in @(".exe", ".apk")) { $hasInstallers = $true }
}

Write-Host "  Bounty/audit directories included: $hasAudit" -ForegroundColor $(if($hasAudit){'Red'}else{'Green'})
Write-Host "  meta_evidence.jsonl included: $hasMetaEvidence" -ForegroundColor $(if($hasMetaEvidence){'Red'}else{'Green'})
Write-Host "  Roblox assets included: $hasRoblox" -ForegroundColor $(if($hasRoblox){'Red'}else{'Green'})
Write-Host "  Archives (.zip) included: $hasArchives" -ForegroundColor $(if($hasArchives){'Red'}else{'Green'})
Write-Host "  DB files included: $hasDB" -ForegroundColor $(if($hasDB){'Red'}else{'Green'})
Write-Host "  Media (.png/.jpg) included: $hasMedia" -ForegroundColor $(if($hasMedia){'Red'}else{'Green'})
Write-Host "  Installers (.exe/.apk) included: $hasInstallers" -ForegroundColor $(if($hasInstallers){'Red'}else{'Green'})
Write-Host ""

# 6. Calculate minimal transfer
$minimalFiles = $includedFiles | Where-Object {
    $skip = $false
    if ($_.Directory -like "*audit*" -or $_.Directory -like "*bounty*") { $skip = $true }
    if ($_.Directory -like "*reports*" -or $_.Name -like "browser_automation_report*" -or $_.Name -like "ultra_optimized*") { $skip = $true }
    if ($_.Name -like "test_output*" -or $_.Name -like "debug_output*" -or $_.Name -like "d_output*" -or $_.Name -like "e_output*" -or $_.Name -like "qwen_full_run*" -or $_.Name -like "strategic_output*" -or $_.Name -like "test_strategic*") { $skip = $true }
    if ($_.Extension -in @(".png", ".jpg", ".jpeg", ".gif", ".mp4", ".avi", ".mov", ".wav", ".ico")) { $skip = $true }
    if ($_.Extension -in @(".zip", ".tar", ".gz", ".7z", ".rar")) { $skip = $true }
    if ($_.Extension -in @(".msi", ".msix", ".appx", ".exe", ".dll")) { $skip = $true }
    if ($_.Extension -in @(".rbxl", ".rbxm", ".rbxlx", ".rbxmx")) { $skip = $true }
    if ($_.Extension -in @(".apk", ".aab")) { $skip = $true }
    if ($_.Extension -in @(".db", ".sqlite", ".sqlite3")) { $skip = $true }
    if ($_.Name -like "*meta_evidence*") { $skip = $true }
    if ($_.Name -eq "EventLog.csv") { $skip = $true }
    if ($_.Name -eq "tech_news.db") { $skip = $true }
    if ($_.Name -eq "SessionKeyPoC.zip") { $skip = $true }
    if ($_.Name -like "Delta*") { $skip = $true }
    if ($_.Name -like "BlueStacks*") { $skip = $true }
    if ($_.Name -like "tiktok*") { $skip = $true }
    if ($_.Name -eq "Home - Roblox.html") { $skip = $true }
    if ($_.Extension -eq ".csv" -and $_.Directory -ne "") { $skip = $true }
    if ($_.Name -like "*.lock") { $skip = $true }
    if ($_.Directory -like "*benchmarks*") { $skip = $true }
    -not $skip
}

$minimalSize = ($minimalFiles | Measure-Object -Property Size -Sum).Sum
$minimalCount = $minimalFiles.Count

Write-Host "  === MINIMAL TRANSFER ALTERNATIVE ===" -ForegroundColor Yellow
Write-Host "  Files: $totalCount -> $minimalCount (reduction: $([math]::Round((1 - $minimalCount/$totalCount)*100))%)" -ForegroundColor White
Write-Host "  Size: $([math]::Round($totalSize/1MB, 2)) MB -> $([math]::Round($minimalSize/1MB, 2)) MB (reduction: $([math]::Round((1 - $minimalSize/$totalSize)*100))%)" -ForegroundColor White

# Save audit results
$auditResults = @{
    TotalFiles = $totalCount
    TotalSizeMB = [math]::Round($totalSize / 1MB, 2)
    ExcludedCount = $excludedCount
    MinimalFiles = $minimalCount
    MinimalSizeMB = [math]::Round($minimalSize / 1MB, 2)
    DirBreakdown = $dirBreakdown | ForEach-Object { @{ dir = $_.Directory; files = $_.FileCount; sizeMB = $_.SizeMB } }
    HasAudit = $hasAudit
    HasMetaEvidence = $hasMetaEvidence
    HasRoblox = $hasRoblox
    HasArchives = $hasArchives
    HasDB = $hasDB
    HasMedia = $hasMedia
    HasInstallers = $hasInstallers
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$auditResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.audit_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AUDIT COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan