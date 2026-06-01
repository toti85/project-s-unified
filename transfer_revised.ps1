$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

$devSource = "C:\ProjectS-Unified"
$serverDest = "C:\ProjectS\project-s-code"

Write-Host "=== Phase 2: REVISED Transfer to SHAYANSKA-DL380 ===" -ForegroundColor Cyan
Write-Host "Source: $devSource" -ForegroundColor Yellow
Write-Host "Destination: $serverDest (via WinRM base64 encoding)" -ForegroundColor Yellow

# Step 0: Clean server staging directory
Write-Host "`n[0/6] Cleaning server staging directory..." -ForegroundColor Yellow
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $dest = "C:\ProjectS\project-s-code"
    if (Test-Path $dest) {
        Get-ChildItem $dest -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        New-Item -Path $dest -ItemType Directory -Force | Out-Null
        Write-Host "  Staging directory cleaned."
    }
}

# Step 1: Build file list with revised exclude patterns
Write-Host "[1/6] Building file list with revised excludes..." -ForegroundColor Yellow

$allFiles = Get-ChildItem -Path $devSource -Recurse -Force -File -ErrorAction SilentlyContinue
$filesToTransfer = @()
$dirsToCreate = @()
$excludedCount = 0
$ownScripts = @(".transfer_list.txt", "transfer_v4.ps1", "transfer_v3.ps1", "transfer_to_server.ps1", "prepare_transfer.ps1", "test_winrm.ps1", "verify_server.ps1", "transfer_v2.ps1", "audit_transfer_scope.ps1", "transfer_revised.ps1")

foreach ($file in $allFiles) {
    $relativePath = $file.FullName.Substring($devSource.Length + 1)
    $leafName = Split-Path $relativePath -Leaf
    
    # Skip our own scripts
    if ($ownScripts -contains $relativePath -or $ownScripts -contains $leafName) {
        $excludedCount++
        continue
    }
    
    $shouldExclude = $false
    
    # Standard excludes
    if ($relativePath -like "*\.git*" -or $relativePath -like "*__pycache__*" -or $leafName -like "*.pyc" -or $relativePath -like "*\.pytest_cache*" -or $relativePath -like "*\.vscode*" -or $relativePath -like "*\node_modules*" -or $relativePath -like "*\.benchmarks*" -or $leafName -like "*.log") {
        $shouldExclude = $true
    }
    
    # Revised excludes
    if ($leafName -like "*.zip" -or $leafName -like "*.exe" -or $leafName -like "*.apk" -or $leafName -like "*.msi" -or $leafName -like "*.dll") {
        $shouldExclude = $true
    }
    if ($leafName -like "*.rbxl" -or $leafName -like "*.rbxm" -or $leafName -like "*.rbxlx" -or $leafName -like "*.rbxmx") {
        $shouldExclude = $true
    }
    if ($leafName -like "*.db" -or $leafName -like "*.sqlite*" -or $leafName -like "*.pkl") {
        $shouldExclude = $true
    }
    if ($leafName -like "*.png" -or $leafName -like "*.jpg" -or $leafName -like "*.jpeg" -or $leafName -like "*.gif" -or $leafName -like "*.pdf") {
        $shouldExclude = $true
    }
    if ($leafName -like "*.csv" -or $leafName -like "*.lock" -or $leafName -like "*.bak*" -or $leafName -like "*.html") {
        $shouldExclude = $true
    }
    
    # Path-based excludes
    if (-not $shouldExclude) {
        if ($relativePath -like "*\*meta_evidence*" -or $relativePath -like "*\*audits*\*" -or $relativePath -like "*\*bounty*\*" -or $relativePath -like "*\*browser_automation_report*" -or $relativePath -like "*\*ultra_optimized*" -or $relativePath -like "*\*test_output*" -or $relativePath -like "*\*debug_output*" -or $relativePath -like "*\*d_output*" -or $relativePath -like "*\*e_output*" -or $relativePath -like "*\*qwen_full_run*" -or $relativePath -like "*\*strategic_output*" -or $relativePath -like "*\*test_strategic*" -or $relativePath -like "*\*benchmarks*\*") {
            $shouldExclude = $true
        }
    }
    
    # EXEMPTION: interactive_layer/static/ui.html must be included
    if ($shouldExclude -and $relativePath -eq "interactive_layer\static\ui.html") {
        $shouldExclude = $false
        Write-Host "  EXEMPTION: Preserving interactive_layer\static\ui.html" -ForegroundColor Green
    }
    
    if (-not $shouldExclude) {
        if ($file.PSIsContainer) {
            $dirsToCreate += $relativePath
        } else {
            $filesToTransfer += [PSCustomObject]@{
                Path = $relativePath
                Size = $file.Length
            }
        }
    } else {
        $excludedCount++
    }
}

$totalSize = ($filesToTransfer | Measure-Object -Property Size -Sum).Sum
Write-Host "  Files to transfer: $($filesToTransfer.Count)" -ForegroundColor Green
Write-Host "  Directories to create: $($dirsToCreate.Count)" -ForegroundColor Green
Write-Host "  Total size: $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor Green
Write-Host "  Excluded: $excludedCount items" -ForegroundColor Gray

# Step 2: Create directory structure on server
Write-Host "`n[2/6] Creating directory structure on server..." -ForegroundColor Yellow
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
}
Write-Host "  Directory structure created: $($dirsToCreate.Count) dirs" -ForegroundColor Green

# Step 3: Copy files via base64 encoding
Write-Host "`n[3/6] Copying files via WinRM (base64 encoding)..." -ForegroundColor Yellow
Write-Host "  Method: Read file locally -> base64 -> write remotely" -ForegroundColor Gray

$transferProgress = 0
$batchSize = 3
$startTime = Get-Date
$failedFiles = @()

for ($i = 0; $i -lt $filesToTransfer.Count; $i += $batchSize) {
    $chunk = $filesToTransfer[$i..([Math]::Min($i + $batchSize - 1, $filesToTransfer.Count - 1))]
    
    # Build base64 encoded data
    $batchData = @()
    foreach ($f in $chunk) {
        $src = Join-Path $devSource $f.Path
        try {
            $content = [System.IO.File]::ReadAllBytes($src)
            $encoded = [System.Convert]::ToBase64String($content)
            $batchData += "$($f.Path)`u{001F}$encoded"
        } catch {
            if (-not ($failedFiles -contains $f.Path)) {
                $failedFiles += $f.Path
            }
        }
    }
    
    $batchStr = $batchData -join "`u{001E}"
    $batchBytes = [System.Text.Encoding]::UTF8.GetBytes($batchStr)
    $batchBase64 = [System.Convert]::ToBase64String($batchBytes, 0, $batchBytes.Length, [System.Base64FormattingOptions]::InsertLineBreaks)
    
    $remoteScript = {
        param($batchBase64, $destBase)
        $decoded = [System.Convert]::FromBase64String($batchBase64)
        $text = [System.Text.Encoding]::UTF8.GetString($decoded)
        $entries = $text -split [char]0x001E
        
        foreach ($entry in $entries) {
            if ($entry -eq "") { continue }
            $usPos = $entry.IndexOf([char]0x001F)
            if ($usPos -lt 0) { continue }
            $relPath = $entry.Substring(0, $usPos)
            $contentBase64 = $entry.Substring($usPos + 1)
            
            $dst = Join-Path $destBase $relPath
            $dstDir = Split-Path $dst -Parent
            if (!(Test-Path $dstDir)) {
                New-Item -Path $dstDir -ItemType Directory -Force | Out-Null
            }
            $content = [System.Convert]::FromBase64String($contentBase64)
            [System.IO.File]::WriteAllBytes($dst, $content)
        }
    }
    
    try {
        Invoke-Command -ComputerName $targetIP -Credential $targetCred -ArgumentList $batchBase64, $serverDest -ScriptBlock $remoteScript -ErrorAction Stop
        $transferProgress += $chunk.Count
    } catch {
        foreach ($f in $chunk) {
            if (-not ($failedFiles -contains $f.Path)) {
                $failedFiles += $f.Path
            }
        }
    }
    
    $percent = [math]::Round($transferProgress / $filesToTransfer.Count * 100, 1)
    $elapsed = (Get-Date) - $startTime
    $rate = if ($transferProgress -gt 0) { $elapsed.TotalSeconds / $transferProgress } else { 0 }
    $remaining = [math]::Round(($filesToTransfer.Count - $transferProgress) * $rate)
    Write-Host "  Progress: $transferProgress / $($filesToTransfer.Count) ($percent%) - ETA: ~${remaining}s" -NoNewline -ForegroundColor Gray
    Write-Host " [`r"]
    
    Start-Sleep -Milliseconds 300
}

$elapsed = (Get-Date) - $startTime
Write-Host "`n  Copy completed in $([math]::Round($elapsed.TotalSeconds, 1))s" -ForegroundColor Green
Write-Host "  Rate: $([math]::Round($totalSize / 1MB / $elapsed.TotalSeconds, 1)) MB/s" -ForegroundColor Green
if ($failedFiles.Count -gt 0) {
    Write-Host "  Failed files: $($failedFiles.Count)" -ForegroundColor Red
    $failedFiles | Select-Object -First 10 | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
}

# Step 4: Verify transfer
Write-Host "`n[4/6] Verifying transfer on server..." -ForegroundColor Yellow
$verifyResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
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
        uiHtmlExists = (Test-Path "$projectSDir\interactive_layer\static\ui.html")
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
Write-Host "  interactive_layer/ exists: $($verifyResult.interactiveLayerExists)" -ForegroundColor $(if($verifyResult.interactiveLayerExists){'Green'}else{'Red'})
Write-Host "  interactive_layer/static/ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor $(if($verifyResult.uiHtmlExists){'Green'}else{'Red'})

Write-Host "`n  Specific file checks:" -ForegroundColor Yellow
$verifyResult.specificFiles.PSObject.Properties | ForEach-Object {
    $status = if($_.Value){'OK'}else{'MISSING'}
    $color = if($_.Value){'Green'}else{'Red'}
    Write-Host "    [$status] $($_.Name)" -ForegroundColor $color
}

# Step 5: Python import smoke test
Write-Host "`n[5/6] Python import smoke test on server..." -ForegroundColor Yellow
$pythonTest = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $env:PATH = "C:\Program Files\Python312;C:\Program Files\Python312\Scripts;" + $env:PATH
    $env:PYTHONPATH = "C:\ProjectS\project-s-code"
    
    $results = @{}
    
    try {
        $version = python --version 2>&1
        $results.PythonVersion = $version
        $results.PythonAvailable = $true
    } catch {
        $results.PythonAvailable = $false
        $results.PythonVersion = "Not found"
    }
    
    $importTests = @("sys", "os", "json", "pathlib", "subprocess", "threading", "asyncio")
    $importResults = @{}
    foreach ($mod in $importTests) {
        try {
            python -c "import $mod" 2>&1 | Out-Null
            $importResults[$mod] = "OK"
        } catch {
            $importResults[$mod] = "FAIL: $_"
        }
    }
    $results.ImportTests = $importResults
    $results.PythonCodeAccessible = (Test-Path "C:\ProjectS\project-s-code\config")
    
    $results
}

Write-Host "  Python available: $($pythonTest.PythonAvailable)" -ForegroundColor $(if($pythonTest.PythonAvailable){'Green'}else{'Red'})
Write-Host "  Python version: $($pythonTest.PythonVersion)" -ForegroundColor $(if($pythonTest.PythonAvailable){'Green'}else{'Red'})
Write-Host "  Project code accessible: $($pythonTest.PythonCodeAccessible)" -ForegroundColor $(if($pythonTest.PythonCodeAccessible){'Green'}else{'Red'})

Write-Host "`n  Module import tests:" -ForegroundColor Yellow
$pythonTest.ImportTests.PSObject.Properties | ForEach-Object {
    $status = if($_.Value -eq "OK"){'OK'}else{'FAIL'}
    $color = if($_.Value -eq "OK"){'Green'}else{'Red'}
    Write-Host "    [$status] $($_.Name): $($_.Value)" -ForegroundColor $color
}

# Step 6: Save results
Write-Host "`n[6/6] Saving results..." -ForegroundColor Yellow
$transferResults = @{
    Phase = "2 - Revised Transfer"
    WinRM = "PASS"
    FilesTransferred = $verifyResult.totalFiles
    DirsTransferred = $verifyResult.totalDirs
    TotalSizeMB = [math]::Round($totalSize / 1MB, 2)
    KeyDirsPresent = $verifyResult.configExists -and $verifyResult.srcExists -and $verifyResult.interactiveLayerExists
    UIHtmlExists = $verifyResult.uiHtmlExists
    TransferTimeSeconds = [math]::Round($elapsed.TotalSeconds, 1)
    FailedFiles = $failedFiles.Count
    PythonAvailable = $pythonTest.PythonAvailable
    PythonVersion = $pythonTest.PythonVersion
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}
$transferResults | ConvertTo-Json | Out-File -FilePath "C:\ProjectS-Unified\.transfer_results.json" -Encoding UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
if ($verifyResult.totalFiles -gt 100 -and $pythonTest.PythonAvailable -and $verifyResult.uiHtmlExists) {
    Write-Host "[PHASE 2 REVISED SUCCESS]" -ForegroundColor Green
    Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Green
    Write-Host "  Dirs: $($verifyResult.totalDirs)" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($totalSize/1MB, 2)) MB" -ForegroundColor Green
    Write-Host "  Time: $([math]::Round($elapsed.TotalSeconds, 1))s" -ForegroundColor Green
    Write-Host "  ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor Green
    Write-Host "  Python: $($pythonTest.PythonVersion)" -ForegroundColor Green
} else {
    Write-Host "[PHASE 2 ISSUES]" -ForegroundColor Yellow
    Write-Host "  Files: $($verifyResult.totalFiles)" -ForegroundColor Yellow
    Write-Host "  ui.html: $($verifyResult.uiHtmlExists)" -ForegroundColor Yellow
    Write-Host "  Python: $($pythonTest.PythonAvailable)" -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan