$source = "C:\ProjectS-Unified"
$destUNC = "\\192.168.1.180\ProjectSStage"
$userName = "192.168.1.180\Administrator"
$password = "Qwe123"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PHASE 2: ROBOCOPY TRANSFER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Map network drive
Write-Host "[1/4] Mapping network drive..." -ForegroundColor Yellow
net use $destUNC $password /user:$userName /persistent:no 2>&1 | Out-Null
Start-Sleep -Seconds 2

$uncTest = Test-Path $destUNC
Write-Host "  UNC path reachable: $uncTest" -ForegroundColor $(if($uncTest){"Green"}else{"Red"})

if (-not $uncTest) {
    Write-Host "  ERROR: UNC path not reachable. Aborting." -ForegroundColor Red
    exit 1
}

# Step 2: Run robocopy with revised excludes
Write-Host "[2/4] Running robocopy with revised excludes..." -ForegroundColor Yellow
Write-Host "  Source: $source" -ForegroundColor Gray
Write-Host "  Dest: $destUNC" -ForegroundColor Gray
Write-Host ""

$robocopyExcludes = @(
    "/XF",
    "*.exe", "*.apk", "*.msi", "*.dll", "*.zip",
    "*.rbxl", "*.rbxm", "*.rbxlx", "*.rbxmx",
    "*.pyc", "*.db", "*.sqlite", "*.sqlite3", "*.pkl",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.pdf",
    "*.csv", "*.lock", "*.bak", "*.bak_cleanup",
    "*.html", "*.log", "*.tar", "*.gz", "*.7z", "*.rar", "*.bz2",
    "*.ps1", "*.bat"
)

$robocopyDirExcludes = @(
    "/XD",
    ".git", "__pycache__", ".pytest_cache", ".vscode",
    "node_modules", ".benchmarks", "audits", "bounty"
)

$robocopyFlags = @("/E", "/NFL", "/NDL", "/NP", "/NC", "/NS", "/R:3", "/W:2", "/MT:8")

$allArgs = $robocopyFlags + $robocopyExcludes + $robocopyDirExcludes

Write-Host "  robocopy $source $destUNC" -ForegroundColor Gray
Write-Host "  Args: $($allArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

$robocopyOutput = robocopy $source $destUNC @allArgs 2>&1

Write-Host "  robocopy output:" -ForegroundColor Yellow
$robocopyOutput | ForEach-Object {
    if ($_ -match "^\s*(New Dir|New File|Total|Copied|Skipped|Mismatch|Failed|EXTRA|????)") {
        Write-Host "    $_" -ForegroundColor Green
    } elseif ($_ -match "^---") {
        Write-Host "    $_" -ForegroundColor Cyan
    } else {
        Write-Host "    $_" -ForegroundColor Gray
    }
}

# Extract summary
$robocopyLines = $robocopyOutput -split "`n"
$summaryLines = $robocopyLines | Where-Object { $_ -match "^\s*(Dirs|Files|Bytes|Total|Speed|Ended|Extra|Copied)" }
if ($summaryLines) {
    Write-Host ""
    Write-Host "  === robocopy Summary ===" -ForegroundColor Cyan
    $summaryLines | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
}

# Step 3: Verify transfer
Write-Host "[3/4] Verifying transfer on server..." -ForegroundColor Yellow

$verifyResult = Invoke-Command -ComputerName "192.168.1.180" -Credential (New-Object System.Management.Automation.PSCredential("$userName", (ConvertTo-SecureString $password -AsPlainText -Force))) -ScriptBlock {
    $sharePath = "C:\ProjectS\project-s-code"
    $fileCount = (Get-ChildItem -Path $sharePath -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $dirCount = (Get-ChildItem -Path $sharePath -Recurse -Force -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
    
    $totalSize = (Get-ChildItem -Path $sharePath -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    
    $specificFiles = @(
        "README.md",
        "config\CI_GATE_CONFIG.md",
        "src\core\async_execution_test.py",
        "interactive_layer\interactive_task.py",
        "interactive_layer\static\ui.html",
        "self_state.json",
        "ai_interactive.py",
        "PROJECT_S_OVERVIEW.md",
        "DECISIONS.md",
        "COMPONENT_INVENTORY.md",
        "memory\telemetry\executions.jsonl"
    )
    
    $fileChecks = @{}
    foreach ($sf in $specificFiles) {
        $fullPath = Join-Path $sharePath $sf
        $exists = Test-Path $fullPath
        $fileChecks[$sf] = $exists
        if ($exists) {
            $size = (Get-Item $fullPath).Length
            $fileChecks["${sf}_size"] = $size
        }
    }
    
    @{
        totalFiles = $fileCount
        totalDirs = $dirCount
        totalSizeBytes = $totalSize
        projectSCodeExists = (Test-Path $sharePath)
        configExists = (Test-Path "$sharePath\config")
        srcCoreExists = (Test-Path "$sharePath\src\core")
        interactiveLayerExists = (Test-Path "$sharePath\interactive_layer")
        srcExists = (Test-Path "$sharePath\src")
        uiHtmlExists = (Test-Path "$sharePath\interactive_layer\static\ui.html")
        specificFiles = $fileChecks
    }
}

Write-Host ""
Write-Host "  === Transfer Verification ===" -ForegroundColor Cyan
Write-Host "  Files transferred: $($verifyResult.totalFiles)" -ForegroundColor $(if($verifyResult.totalFiles -gt 100){"Green"}else{"Red"})
Write-Host "  Directories transferred: $($verifyResult.totalDirs)" -ForegroundColor $(if($verifyResult.totalDirs -gt 10){"Green"}else{"Red"})
Write-Host "  Total size: $([math]::Round($verifyResult.totalSizeBytes / 1MB, 2)) MB" -ForegroundColor $(if($verifyResult.totalSizeBytes -gt 50MB){"Green"}else{"Yellow"})
Write-Host "  project-s-code/ exists: $($verifyResult.projectSCodeExists)" -ForegroundColor Green
Write-Host "  config/ exists: $($verifyResult.configExists)" -ForegroundColor $(if($verifyResult.configExists){"Green"}else{"Red"})
Write-Host "  src/core/ exists: $($verifyResult.srcCoreExists)" -ForegroundColor $(if($verifyResult.srcCoreExists){"Green"}else{"Gray"})
Write-Host "  src/ exists: $($verifyResult.srcExists)" -ForegroundColor $(if($verifyResult.srcExists){"Green"}else{"Red"})
Write-Host "  interactive_layer/ exists: $($verifyResult.interactiveLayerExists)" -ForegroundColor $(if($verifyResult.interactiveLayerExists){"Green"}else{"Red"})
Write-Host "  interactive_layer/static/ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor $(if($verifyResult.uiHtmlExists){"Green"}else{"Red"})

Write-Host ""
Write-Host "  Specific file checks:" -ForegroundColor Yellow
$verifyResult.specificFiles.PSObject.Properties | Where-Object { $_.Name -match '\.jsonl$|\.md$|\.py$|\.json$' -and $_.Name -notmatch '_size' } | ForEach-Object {
    $status = if($_.Value){"OK"}else{"MISSING"}
    $color = if($_.Value){"Green"}else{"Red"}
    Write-Host "    [$status] $($_.Name)" -ForegroundColor $color
}

# Step 4: Cleanup
Write-Host "[4/4] Cleaning up network mapping..." -ForegroundColor Yellow
net use $destUNC /delete /y 2>&1 | Out-Null
Write-Host "  Network mapping removed." -ForegroundColor Gray

# Save results
$transferResults = @{
    Phase = "2 - Robocopy Transfer"
    FilesTransferred = $verifyResult.totalFiles
    DirsTransferred = $verifyResult.totalDirs
    TotalSizeMB = [math]::Round($verifyResult.totalSizeBytes / 1MB, 2)
    KeyDirsPresent = $verifyResult.configExists -and $verifyResult.srcExists -and $verifyResult.interactiveLayerExists
    UIHtmlExists = $verifyResult.uiHtmlExists
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$transferResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.transfer_results.json" -Encoding UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($verifyResult.totalFiles -gt 100 -and $verifyResult.uiHtmlExists) {
    Write-Host "[PHASE 2 ROBOCOPY SUCCESS]" -ForegroundColor Green
    Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Green
    Write-Host "  Dirs: $($verifyResult.totalDirs)" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($verifyResult.totalSizeBytes/1MB, 2)) MB" -ForegroundColor Green
    Write-Host "  ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor Green
} else {
    Write-Host "[PHASE 2 ROBOCOPY ISSUES]" -ForegroundColor Yellow
    Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Yellow
    Write-Host "  ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor Yellow
}
Write-Host "============================================" -ForegroundColor Cyan