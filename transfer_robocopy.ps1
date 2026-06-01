$targetIP = "192.168.1.180"
$targetUser = "$targetIP\Administrator"
$targetPassword = "Qwe123"
$serverDestUNC = "\\$targetIP\C`$\ProjectS\project-s-code"

Write-Host "=== Phase 2: Robocopy Transfer to SHAYANSKA-DL380 ===" -ForegroundColor Cyan
Write-Host "Source: C:\ProjectS-Unified" -ForegroundColor Yellow
Write-Host "Destination: $serverDestUNC" -ForegroundColor Yellow

# Step 1: Map network drive with credentials
Write-Host "`n[1/4] Mapping network drive..." -ForegroundColor Yellow
try {
    # Remove any existing mapping first
    net use \\$targetIP\C$ /delete /y 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    
    # Map with credentials
    $mapResult = net use \\$targetIP\C$ $targetPassword /user:$targetUser /persistent:no 2>&1
    Write-Host "  Map result: $mapResult" -ForegroundColor Gray
    
    Start-Sleep -Seconds 3
    
    # Test the connection
    $testResult = Test-Path $serverDestUNC
    if ($testResult) {
        Write-Host "  UNC path accessible: YES" -ForegroundColor Green
    } else {
        Write-Host "  UNC path test: FAIL - trying alternative approach..." -ForegroundColor Red
    }
} catch {
    Write-Host "  Network mapping failed: $_" -ForegroundColor Red
}

# Step 2: Ensure destination exists
Write-Host "[2/4] Ensuring destination directory exists..." -ForegroundColor Yellow
try {
    if (!(Test-Path $serverDestUNC)) {
        New-Item -Path $serverDestUNC -ItemType Directory -Force | Out-Null
        Write-Host "  Created destination directory" -ForegroundColor Green
    } else {
        Write-Host "  Destination directory exists" -ForegroundColor Green
    }
} catch {
    Write-Host "  Could not create/verify destination: $_" -ForegroundColor Red
}

# Step 3: Run robocopy with revised excludes
Write-Host "[3/4] Running robocopy..." -ForegroundColor Yellow

$excludeFiles = @("/XF", "*.exe", "*.apk", "*.msi", "*.dll", "*.zip", "*.rbxl", "*.rbxm", "*.rbxlx", "*.rbxmx", "*.pyc", "*.db", "*.sqlite", "*.sqlite3", "*.pkl", "*.png", "*.jpg", "*.jpeg", "*.gif", "*.pdf", "*.csv", "*.lock", "*.bak", "*.bak_cleanup", "*.html", "*.log", "*.tar", "*.gz", "*.7z", "*.rar", "*.bz2")
$excludeDirs = @("/XD", ".git", "__pycache__", ".pytest_cache", ".vscode", "node_modules", ".benchmarks", "audits", "bounty")

Write-Host "  robocopy C:\ProjectS-Unified $serverDestUNC /E /NFL /NDL /NP /NC /NS /R:3 /W:2 /MT:8" -ForegroundColor Gray

$robocopyOutput = robocopy "C:\ProjectS-Unified" $serverDestUNC @($excludeFiles, $excludeDirs) 2>&1

Write-Host "`n  robocopy output:" -ForegroundColor Yellow
$robocopyOutput | ForEach-Object { Write-Host "    $_" }

# Extract summary
$robocopyLines = $robocopyOutput -split "`n"
$summaryLines = $robocopyLines | Where-Object { $_ -match "^\s*(Dirs|Files|Bytes|Total|Speed|Ended)" }
if ($summaryLines) {
    Write-Host "`n  === robocopy Summary ===" -ForegroundColor Cyan
    $summaryLines | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
}

# Step 4: Verify transfer
Write-Host "`n[4/4] Verifying transfer..." -ForegroundColor Yellow

# Use PowerShell remoting to verify
$verifyCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", (ConvertTo-SecureString $targetPassword -AsPlainText -Force))
$verifyResult = Invoke-Command -ComputerName $targetIP -Credential $verifyCred -ScriptBlock {
    $projectSDir = "C:\ProjectS\project-s-code"
    $fileCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $dirCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
    
    $specificFiles = @(
        "README.md",
        "config\CI_GATE_CONFIG.md",
        "src\core\async_execution_test.py",
        "interactive_layer\interactive_task.py",
        "interactive_layer\static\ui.html",
        "self_state.json",
        "ai_interactive.py",
        "PROJECT_S_OVERVIEW.md",
        "DECISIONS.md"
    )
    
    $fileChecks = @{}
    foreach ($sf in $specificFiles) {
        $fullPath = Join-Path $projectSDir $sf
        $fileChecks[$sf] = (Test-Path $fullPath)
    }
    
    @{
        totalFiles = $fileCount
        totalDirs = $dirCount
        projectSCodeExists = (Test-Path $projectSDir)
        configExists = (Test-Path "$projectSDir\config")
        srcCoreExists = (Test-Path "$projectSDir\src\core")
        interactiveLayerExists = (Test-Path "$projectSDir\interactive_layer")
        srcExists = (Test-Path "$projectSDir\src")
        uiHtmlExists = (Test-Path "$projectSDir\interactive_layer\static\ui.html")
        specificFiles = $fileChecks
    }
}

Write-Host "`n  === Transfer Verification ===" -ForegroundColor Cyan
Write-Host "  Files transferred: $($verifyResult.totalFiles)" -ForegroundColor $(if($verifyResult.totalFiles -gt 100){'Green'}else{'Red'})
Write-Host "  Directories transferred: $($verifyResult.totalDirs)" -ForegroundColor $(if($verifyResult.totalDirs -gt 10){'Green'}else{'Red'})
Write-Host "  project-s-code/ exists: $($verifyResult.projectSCodeExists)" -ForegroundColor Green
Write-Host "  config/ exists: $($verifyResult.configExists)" -ForegroundColor $(if($verifyResult.configExists){'Green'}else{'Red'})
Write-Host "  src/core/ exists: $($verifyResult.srcCoreExists)" -ForegroundColor $(if($verifyResult.srcCoreExists){'Green'}else{'Gray'})
Write-Host "  src/ exists: $($verifyResult.srcExists)" -ForegroundColor $(if($verifyResult.srcExists){'Green'}else{'Red'})
Write-Host "  interactive_layer/ exists: $($verifyResult.interactiveLayerExists)" -ForegroundColor $(if($verifyResult.interactiveLayerExists){'Green'}else{'Red'})
Write-Host "  interactive_layer/static/ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor $(if($verifyResult.uiHtmlExists){'Green'}else{'Red'})

Write-Host "`n  Specific file checks:" -ForegroundColor Yellow
$verifyResult.specificFiles.PSObject.Properties | ForEach-Object {
    $status = if($_.Value){'OK'}else{'MISSING'}
    $color = if($_.Value){'Green'}else{'Red'}
    Write-Host "    [$status] $($_.Name)" -ForegroundColor $color
}

# Save results
$transferResults = @{
    Phase = "2 - Robocopy Transfer"
    WinRM = "PASS"
    FilesTransferred = $verifyResult.totalFiles
    DirsTransferred = $verifyResult.totalDirs
    KeyDirsPresent = $verifyResult.configExists -and $verifyResult.srcExists -and $verifyResult.interactiveLayerExists
    UIHtmlExists = $verifyResult.uiHtmlExists
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$transferResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.transfer_results.json" -Encoding UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
if ($verifyResult.totalFiles -gt 100) {
    Write-Host "[PHASE 2 ROBOCOPIER SUCCESS]" -ForegroundColor Green
    Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Green
    Write-Host "  Dirs: $($verifyResult.totalDirs)" -ForegroundColor Green
    Write-Host "  ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor Green
} else {
    Write-Host "[PHASE 2 ROBOCOPIER FAILED]" -ForegroundColor Red
    Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

# Cleanup: unmap network drive
Write-Host "`nCleaning up network mapping..." -ForegroundColor Gray
net use \\$targetIP\C$ /delete /y 2>&1 | Out-Null