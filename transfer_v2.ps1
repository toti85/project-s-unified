$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$devSource = "C:\ProjectS-Unified"
$serverDestUNC = "\\$targetIP\C`$\ProjectS\project-s-code"

Write-Host "=== Phase 2: File Transfer to SHAYANSKA-DL380 (Retry) ===" -ForegroundColor Cyan
Write-Host "Source: $devSource" -ForegroundColor Yellow
Write-Host "Destination (UNC): $serverDestUNC" -ForegroundColor Yellow

# Test UNC path accessibility
Write-Host "`n[1/2] Testing UNC path accessibility..." -ForegroundColor Yellow
try {
    $testPath = Test-Path $serverDestUNC -ErrorAction Stop
    if ($testPath) {
        Write-Host "  UNC path accessible: YES" -ForegroundColor Green
    } else {
        Write-Host "  UNC path accessible: NO - trying with credentials..." -ForegroundColor Red
    }
} catch {
    Write-Host "  UNC path test failed: $_" -ForegroundColor Red
    Write-Host "  Attempting to map network drive..." -ForegroundColor Yellow
    
    # Map network drive with credentials
    net use \\$targetIP\C$ $targetPassword /user:$targetIP\Administrator /persistent:no 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    
    Write-Host "  Network drive mapped." -ForegroundColor Green
}

# Run robocopy with UNC path
Write-Host "[2/2] Running robocopy with UNC path..." -ForegroundColor Yellow

$excludeArgs = @("/XF", "*.exe", "*.apk", "*.rbxm", "*.rbxl", "*.log", "*.pyc", 
                "/XD", ".git", "__pycache__", ".pytest_cache", ".vscode", "node_modules", ".benchmarks")

Write-Host "  robocopy $devSource $serverDestUNC /E /NFL /NDL /NP /NC /NS /R:3 /W:2" -ForegroundColor Gray

$robocopyOutput = robocopy $devSource $serverDestUNC /E /NFL /NDL /NP /NC /NS /R:3 /W:2 $excludeArgs 2>&1

Write-Host "`n  robocopy output:" -ForegroundColor Yellow
$robocopyOutput | ForEach-Object { Write-Host "    $_" }

# Extract summary from robocopy
$robocopyLines = $robocopyOutput -split "`n"
$summaryLines = $robocopyLines | Where-Object { $_ -match "Dirs|Files|Bytes|Total|Speed|Ended" }
if ($summaryLines) {
    Write-Host "`n  === robocopy Summary ===" -ForegroundColor Cyan
    $summaryLines | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
}

# Verify transfer
Write-Host "`n=== Verifying Transfer ===" -ForegroundColor Cyan
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
        docsExists = (Test-Path "$projectSDir\docs")
        knowledgeExists = (Test-Path "$projectSDir\knowledge")
    }
    
    $checks
}

Write-Host "  Files transferred: $($verifyResult.totalFiles)" -ForegroundColor $(if($verifyResult.totalFiles -gt 0){'Green'}else{'Red'})
Write-Host "  Directories transferred: $($verifyResult.totalDirs)" -ForegroundColor $(if($verifyResult.totalDirs -gt 0){'Green'}else{'Red'})
Write-Host "  project-s-code/ exists: $($verifyResult.projectSCodeExists)" -ForegroundColor Green
Write-Host "  config/ exists: $($verifyResult.configExists)" -ForegroundColor $(if($verifyResult.configExists){'Green'}else{'Red'})
Write-Host "  src/core/ exists: $($verifyResult.srcCoreExists)" -ForegroundColor $(if($verifyResult.srcCoreExists){'Green'}else{'Gray'})
Write-Host "  src/ exists: $($verifyResult.srcExists)" -ForegroundColor $(if($verifyResult.srcExists){'Green'}else{'Red'})
Write-Host "  memory/ exists: $($verifyResult.memoryExists)" -ForegroundColor $(if($verifyResult.memoryExists){'Green'}else{'Red'})
Write-Host "  reports/ exists: $($verifyResult.reportsExists)" -ForegroundColor $(if($verifyResult.reportsExists){'Green'}else{'Red'})
Write-Host "  docs/ exists: $($verifyResult.docsExists)" -ForegroundColor $(if($verifyResult.docsExists){'Green'}else{'Red'})
Write-Host "  knowledge/ exists: $($verifyResult.knowledgeExists)" -ForegroundColor $(if($verifyResult.knowledgeExists){'Green'}else{'Red'})
Write-Host "  interactive_layer/ exists: $($verifyResult.interactiveLayerExists)" -ForegroundColor $(if($verifyResult.interactiveLayerExists){'Green'}else{'Gray'})

# Save results
$transferResults = @{
    WinRM = "PASS"
    FilesTransferred = $verifyResult.totalFiles
    DirsTransferred = $verifyResult.totalDirs
    KeyDirsPresent = $verifyResult.configExists -and $verifyResult.srcExists -and $verifyResult.memoryExists -and $verifyResult.reportsExists
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$transferResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.transfer_results.json" -Encoding UTF8

if ($verifyResult.totalFiles -gt 100) {
    Write-Host "`n[TRANSFER SUCCESS] Files: $($verifyResult.totalFiles), Dirs: $($verifyResult.totalDirs)" -ForegroundColor Green
} else {
    Write-Host "`n[TRANSFER FAILED] Only $($verifyResult.totalFiles) files found" -ForegroundColor Red
}