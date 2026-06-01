$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$devSource = "C:\ProjectS-Unified"
$serverDest = "C:\ProjectS\project-s-code"

# Exclude patterns
$excludePatterns = @(".git", "__pycache__", "*.pyc", ".pytest_cache", ".vscode", "*.exe", "*.apk", "*.rbxm", "*.rbxl", "node_modules", ".benchmarks", "*.log")

Write-Host "=== Phase 2: File Transfer to SHAYANSKA-DL380 (PowerShell Remoting) ===" -ForegroundColor Cyan
Write-Host "Source: $devSource" -ForegroundColor Yellow
Write-Host "Destination: $serverDest (via WinRM)" -ForegroundColor Yellow

# Step 1: Build file list
Write-Host "`n[1/4] Building file list with exclusions..." -ForegroundColor Yellow
$filesToTransfer = @()
$dirsToCreate = @()
$excludedCount = 0
$skippedFiles = @(".transfer_list.txt", "transfer_v3.ps1", "transfer_to_server.ps1", "prepare_transfer.ps1", "test_winrm.ps1", "verify_server.ps1", "transfer_v2.ps1")

$allItems = Get-ChildItem -Path $devSource -Recurse -Force -ErrorAction SilentlyContinue
foreach ($item in $allItems) {
    $relativePath = $item.FullName.Substring($devSource.Length + 1)
    
    # Skip our own scripts and temp files
    if ($skippedFiles -contains $relativePath -or (Split-Path $relativePath -Leaf) -in $skippedFiles) {
        $excludedCount++
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
    
    if ($item.PSIsContainer) {
        if (-not $shouldExclude) {
            $dirsToCreate += $relativePath
        }
    } else {
        if (-not $shouldExclude) {
            $filesToTransfer += $relativePath
        }
    }
}

Write-Host "  Files to transfer: $($filesToTransfer.Count)" -ForegroundColor Green
Write-Host "  Directories to create: $($dirsToCreate.Count)" -ForegroundColor Green
Write-Host "  Excluded: $excludedCount items" -ForegroundColor Gray

# Step 2: Create directory structure on server
Write-Host "`n[2/4] Creating directory structure on server..." -ForegroundColor Yellow
$dirChunkSize = 200
for ($i = 0; $i -lt $dirsToCreate.Count; $i += $dirChunkSize) {
    $chunk = $dirsToCreate[$i..([Math]::Min($i + $dirChunkSize - 1, $dirsToCreate.Count - 1))]
    Invoke-Command -ComputerName $targetIP -Credential $targetCred -ArgumentList $chunk -ScriptBlock {
        param($chunk)
        foreach ($d in $chunk) {
            $fullPath = "C:\ProjectS\project-s-code\$d"
            if (!(Test-Path $fullPath)) {
                New-Item -Path $fullPath -ItemType Directory -Force | Out-Null
            }
        }
    }
    $progress = [math]::Min($i + $dirChunkSize, $dirsToCreate.Count)
    Write-Host "  Created directories: $progress / $($dirsToCreate.Count)" -NoNewline -ForegroundColor Gray
    Write-Host " [`r"]
}
Write-Host "  Directory structure complete." -ForegroundColor Green

# Step 3: Copy files via base64 encoding
Write-Host "`n[3/4] Copying files via WinRM (base64 encoding)..." -ForegroundColor Yellow
Write-Host "  This will take several minutes for $($filesToTransfer.Count) files..." -ForegroundColor Gray

$transferProgress = 0
$batchSize = 3
$startTime = Get-Date
$failedFiles = @()

for ($i = 0; $i -lt $filesToTransfer.Count; $i += $batchSize) {
    $chunk = $filesToTransfer[$i..([Math]::Min($i + $batchSize - 1, $filesToTransfer.Count - 1))]
    
    $remoteScript = {
        param($filesBase64, $sourceBase, $destBase)
        $decoded = [System.Convert]::FromBase64String($filesBase64)
        $files = [System.Text.Encoding]::UTF8.GetString($decoded) -split "`u{001E}"
        
        foreach ($f in $files) {
            if ($f -eq "") { continue }
            $src = Join-Path $sourceBase $f
            $dst = Join-Path $destBase $f
            $dstDir = Split-Path $dst -Parent
            if (!(Test-Path $dstDir)) {
                New-Item -Path $dstDir -ItemType Directory -Force | Out-Null
            }
            Copy-Item -Path $src -Destination $dst -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Encode file list as base64
    $fileListStr = $chunk -join "`u{001E}"
    $fileListBytes = [System.Text.Encoding]::UTF8.GetBytes($fileListStr)
    $fileListBase64 = [System.Convert]::ToBase64String($fileListBytes, 0, $fileListBytes.Length, [System.Base64FormattingOptions]::UseLineBreakEncoding)
    
    try {
        Invoke-Command -ComputerName $targetIP -Credential $targetCred -ArgumentList $fileListBase64, $devSource, $serverDest -ScriptBlock $remoteScript -ErrorAction Stop
    } catch {
        foreach ($f in $chunk) {
            $failedFiles += $f
        }
    }
    
    $transferProgress += $chunk.Count
    $percent = [math]::Round($transferProgress / $filesToTransfer.Count * 100, 1)
    $elapsed = (Get-Date) - $startTime
    $etaSeconds = [math]::Round($elapsed.TotalSeconds * ($filesToTransfer.Count / $transferProgress - 1))
    Write-Host "  Progress: $transferProgress / $($filesToTransfer.Count) ($percent%) - ETA: ~${etaSeconds}s" -NoNewline -ForegroundColor Gray
    Write-Host " [`r"]
    
    Start-Sleep -Milliseconds 300
}

$elapsed = (Get-Date) - $startTime
Write-Host "`n  Copy completed in $([math]::Round($elapsed.TotalSeconds, 1))s" -ForegroundColor Green
if ($failedFiles.Count -gt 0) {
    Write-Host "  Failed files: $($failedFiles.Count)" -ForegroundColor Red
    $failedFiles | Select-Object -First 10 | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
}

# Step 4: Verify transfer
Write-Host "`n[4/4] Verifying transfer on server..." -ForegroundColor Yellow
$verifyResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $projectSDir = "C:\ProjectS\project-s-code"
    $fileCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $dirCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
    
    # Check some specific files
    $specificFiles = @(
        "README.md",
        "config\CI_GATE_CONFIG.md",
        "src\core\async_execution_test.py",
        "interactive_layer\interactive_task.py",
        "memory\meta_evidence.jsonl",
        "reports\INDEX_PHASE_5_SUCCESS.md"
    )
    
    $fileChecks = @{}
    foreach ($sf in $specificFiles) {
        $fullPath = Join-Path $projectSDir $sf
        $fileChecks[$sf] = (Test-Path $fullPath)
    }
    
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
        specificFiles = $fileChecks
    }
    
    $checks
}

Write-Host "`n  === Transfer Verification ===" -ForegroundColor Cyan
Write-Host "  Files transferred: $($verifyResult.totalFiles)" -ForegroundColor $(if($verifyResult.totalFiles -gt 100){'Green'}else{'Red'})
Write-Host "  Directories transferred: $($verifyResult.totalDirs)" -ForegroundColor $(if($verifyResult.totalDirs -gt 10){'Green'}else{'Red'})
Write-Host "  project-s-code/ exists: $($verifyResult.projectSCodeExists)" -ForegroundColor Green
Write-Host "  config/ exists: $($verifyResult.configExists)" -ForegroundColor $(if($verifyResult.configExists){'Green'}else{'Red'})
Write-Host "  src/core/ exists: $($verifyResult.srcCoreExists)" -ForegroundColor $(if($verifyResult.srcCoreExists){'Green'}else{'Gray'})
Write-Host "  src/ exists: $($verifyResult.srcExists)" -ForegroundColor $(if($verifyResult.srcExists){'Green'}else{'Red'})
Write-Host "  memory/ exists: $($verifyResult.memoryExists)" -ForegroundColor $(if($verifyResult.memoryExists){'Green'}else{'Red'})
Write-Host "  reports/ exists: $($verifyResult.reportsExists)" -ForegroundColor $(if($verifyResult.reportsExists){'Green'}else{'Red'})
Write-Host "  interactive_layer/ exists: $($verifyResult.interactiveLayerExists)" -ForegroundColor $(if($verifyResult.interactiveLayerExists){'Green'}else{'Gray'})

Write-Host "`n  Specific file checks:" -ForegroundColor Yellow
$verifyResult.specificFiles.PSObject.Properties | ForEach-Object {
    $status = if($_.Value){'OK'}else{'MISSING'}
    $color = if($_.Value){'Green'}else{'Red'}
    Write-Host "    [$status] $($_.Name)" -ForegroundColor $color
}

# Save results
$transferResults = @{
    WinRM = "PASS"
    FilesTransferred = $verifyResult.totalFiles
    DirsTransferred = $verifyResult.totalDirs
    KeyDirsPresent = $verifyResult.configExists -and $verifyResult.srcExists -and $verifyResult.memoryExists -and $verifyResult.reportsExists
    TransferTimeSeconds = [math]::Round($elapsed.TotalSeconds, 1)
    FailedFiles = $failedFiles.Count
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$transferResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.transfer_results.json" -Encoding UTF8

if ($verifyResult.totalFiles -gt 100) {
    Write-Host "`n[TRANSFER SUCCESS] Files: $($verifyResult.totalFiles), Dirs: $($verifyResult.totalDirs), Time: ${elapsed.TotalSeconds.ToString("0.0")}s" -ForegroundColor Green
} else {
    Write-Host "`n[TRANSFER FAILED] Only $($verifyResult.totalFiles) files found" -ForegroundColor Red
}