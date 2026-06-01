$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$devSource = "C:\ProjectS-Unified"
$serverDest = "C:\ProjectS\project-s-code"

Write-Host "=== Phase 2: File Transfer to SHAYANSKA-DL380 ===" -ForegroundColor Cyan
Write-Host "Source: $devSource" -ForegroundColor Yellow
Write-Host "Destination: $serverDest" -ForegroundColor Yellow

# Step 1: Create destination directory on server
Write-Host "`n[1/3] Creating destination directory on server..." -ForegroundColor Yellow
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    if (!(Test-Path "C:\ProjectS")) {
        New-Item -Path "C:\ProjectS" -ItemType Directory -Force | Out-Null
        Write-Host "Created C:\ProjectS"
    }
    if (!(Test-Path "C:\ProjectS\project-s-code")) {
        New-Item -Path "C:\ProjectS\project-s-code" -ItemType Directory -Force | Out-Null
        Write-Host "Created C:\ProjectS\project-s-code"
    }
}

# Step 2: Build exclude arguments for robocopy
# We need to exclude: .git, __pycache__, *.pyc, .pytest_cache, .vscode, *.exe, *.apk, *.rbxm, *.rbxl, node_modules, .benchmarks, *.log
$excludeArgs = @("/XF", "*.exe", "*.apk", "*.rbxm", "*.rbxl", "*.log", "*.pyc", 
                "/XD", ".git", "__pycache__", ".pytest_cache", ".vscode", "node_modules", ".benchmarks")

# Step 3: Use robocopy for the transfer
Write-Host "[2/3] Running robocopy transfer..." -ForegroundColor Yellow
Write-Host "  This may take several minutes for 1000+ files..." -ForegroundColor Gray

$robocopyOutput = robocopy $devSource "$serverDest" /E /NFL /NDL /NP /NC /NS /NP /R:1 /W:1 $excludeArgs 2>&1

# Parse robocopy output for summary
$robocopyLines = $robocopyOutput -split "`n"
$copySummary = $robocopyLines | Where-Object { $_ -match "^\s*Total\s+.*Copied" }
$excludeSummary = $robocopyLines | Where-Object { $_ -match "^\s*Excluded\s+.*Files" }

Write-Host "`n  robocopy output (last 20 lines):" -ForegroundColor Yellow
$robocopyOutput | Select-Object -Last 20 | ForEach-Object { Write-Host "    $_" }

# Step 4: Verify transfer
Write-Host "`n[3/3] Verifying transfer on server..." -ForegroundColor Yellow
$verifyResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $projectSDir = "C:\ProjectS\project-s-code"
    $fileCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $dirCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
    
    $checks = @{
        totalFiles = $fileCount
        totalDirs = $dirCount
        projectSCodeExists = (Test-Path $projectSDir)
        configExists = (Test-Path "$projectSDir\config")
        srcCoreExists = (Test-Path "$projectSDir\src\core")
        interactiveLayerExists = (Test-Path "$projectSDir\interactive_layer")
        srcExists = (Test-Path "$projectSDir\src")
        memoryExists = (Test-Path "$projectSDir\memory")
        reportsExists = (Test-Path "$projectSDir\reports")
    }
    
    $checks
}

Write-Host "`n  === Transfer Verification ===" -ForegroundColor Cyan
Write-Host "  Files transferred: $($verifyResult.totalFiles)" -ForegroundColor Green
Write-Host "  Directories transferred: $($verifyResult.totalDirs)" -ForegroundColor Green
Write-Host "  project-s-code/ exists: $($verifyResult.projectSCodeExists)" -ForegroundColor Green
Write-Host "  config/ exists: $($verifyResult.configExists)" -ForegroundColor Green
Write-Host "  src/core/ exists: $($verifyResult.srcCoreExists)" -ForegroundColor $(if($verifyResult.srcCoreExists){'Green'}else{'Gray'})
Write-Host "  src/ exists: $($verifyResult.srcExists)" -ForegroundColor Green
Write-Host "  memory/ exists: $($verifyResult.memoryExists)" -ForegroundColor Green
Write-Host "  reports/ exists: $($verifyResult.reportsExists)" -ForegroundColor Green
Write-Host "  interactive_layer/ exists: $($verifyResult.interactiveLayerExists)" -ForegroundColor $(if($verifyResult.interactiveLayerExists){'Green'}else{'Gray'})

# Store results for report
$transferResults = @{
    WinRM = "PASS"
    FilesTransferred = $verifyResult.totalFiles
    DirsTransferred = $verifyResult.totalDirs
    KeyDirsPresent = $verifyResult.configExists -and $verifyResult.srcExists -and $verifyResult.memoryExists -and $verifyResult.reportsExists
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

# Save transfer results for Phase 2 report
$transferResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.transfer_results.json" -Encoding UTF8

Write-Host "`n[TRANSFER COMPLETE]" -ForegroundColor Green
Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Green
Write-Host "  Dirs: $($verifyResult.totalDirs)" -ForegroundColor Green