# Snapshot transfer to DL380 - using proven pattern from robocopy_phase2_v2.ps1
$zipSource = "C:\ProjectS-Unified\ProjectS-Snapshot-20260601.zip"
$destUNC = "\\192.168.1.180\C$\ProjectS-Snapshot-20260601"
$userName = "192.168.1.180\Administrator"
$password = "Qwe123"
$cred = New-Object System.Management.Automation.PSCredential("$userName", (ConvertTo-SecureString $password -AsPlainText -Force))

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SNAPSHOT TRANSFER: DEV -> DL380" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Step 1: Verify ZIP exists
Write-Host ""
Write-Host "[1/5] Verifying source ZIP..." -ForegroundColor Yellow
if (-not (Test-Path $zipSource)) {
    Write-Host "ERROR: ZIP not found at $zipSource" -ForegroundColor Red
    exit 1
}
$zipSize = (Get-Item $zipSource).Length
Write-Host "  ZIP exists: $([math]::Round($zipSize/1MB, 2)) MB" -ForegroundColor Green

# Step 2: Create target directory on DL380 via WinRM
Write-Host ""
Write-Host "[2/5] Creating target directory on DL380..." -ForegroundColor Yellow
try {
    Invoke-Command -ComputerName "192.168.1.180" -Credential $cred -ScriptBlock {
        $target = "C:\ProjectS-Snapshot-20260601"
        if (-not (Test-Path $target)) {
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            Write-Output "Created: $target"
        } else {
            Write-Output "Directory exists: $target"
        }
    } | Out-Null
    Write-Host "  Target directory ready" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 3: Map network drive and copy ZIP via SMB
Write-Host ""
Write-Host "[3/5] Copying ZIP to DL380 via SMB..." -ForegroundColor Yellow
net use $destUNC $password /user:$userName /persistent:no 2>$null
Start-Sleep -Seconds 2

$uncTest = Test-Path $destUNC
Write-Host "  UNC reachable: $uncTest" -ForegroundColor $(if($uncTest){"Green"}else{"Red"})

if ($uncTest) {
    Copy-Item -Path $zipSource -Destination "$destUNC\ProjectS-Snapshot-20260601.zip" -Force
    Write-Host "  ZIP copied" -ForegroundColor Green
    
    # Verify
    $remoteZip = "$destUNC\ProjectS-Snapshot-20260601.zip"
    if (Test-Path $remoteZip) {
        $remoteSize = (Get-Item $remoteZip).Length
        Write-Host "  Remote ZIP size: $([math]::Round($remoteSize/1MB, 2)) MB" -ForegroundColor Green
        if ($remoteSize -eq $zipSize) {
            Write-Host "  Size match: OK" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Size mismatch!" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ERROR: Cannot reach UNC path" -ForegroundColor Red
    exit 1
}

# Cleanup network mapping
net use $destUNC /delete /y 2>$null

# Step 4: Extract ZIP on DL380 via WinRM
Write-Host ""
Write-Host "[4/5] Extracting ZIP on DL380..." -ForegroundColor Yellow
try {
    $extractResult = Invoke-Command -ComputerName "192.168.1.180" -Credential $cred -ScriptBlock {
        $zip = "C:\ProjectS-Snapshot-20260601\ProjectS-Snapshot-20260601.zip"
        $dest = "C:\ProjectS-Snapshot-20260601"
        
        if (-not (Test-Path $zip)) {
            Write-Error "ZIP not found on server"
            return @{success=$false}
        }
        
        Expand-Archive -Path $zip -DestinationPath $dest -Force
        
        # Count files
        $fileCount = (Get-ChildItem $dest -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
        
        # List directories
        $dirs = (Get-ChildItem $dest -Directory | Select-Object -ExpandProperty Name) -join ", "
        
        # Check no .env files
        $envFiles = Get-ChildItem $dest -Recurse -Include ".env", ".env.local" -ErrorAction SilentlyContinue
        
        # Check self_state.json
        $ssPath = Join-Path $dest "self_state.json"
        $ssValid = $false
        if (Test-Path $ssPath) {
            try {
                $content = Get-Content $ssPath -Raw
                $null = ConvertFrom-Json $content
                $ssValid = $true
            } catch {
                $ssValid = $false
            }
        }
        
        @{
            success = $true
            fileCount = $fileCount
            directories = $dirs
            envFilesFound = if($envFiles) { $envFiles.Count } else { 0 }
            selfStateValid = $ssValid
        }
    }
    
    Write-Host "  Files extracted: $($extractResult.fileCount)" -ForegroundColor Green
    Write-Host "  Directories: $($extractResult.directories)" -ForegroundColor Green
    Write-Host "  Credential files found: $($extractResult.envFilesFound) (should be 0)" -ForegroundColor $(if($extractResult.envFilesFound -eq 0){"Green"}else{"Red"})
    Write-Host "  self_state.json valid: $($extractResult.selfStateValid)" -ForegroundColor $(if($extractResult.selfStateValid){"Green"}else{"Red"})
} catch {
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 5: Final verification
Write-Host ""
Write-Host "[5/5] Final verification..." -ForegroundColor Yellow
try {
    $finalCheck = Invoke-Command -ComputerName "192.168.1.180" -Credential $cred -ScriptBlock {
        $base = "C:\ProjectS-Snapshot-20260601"
        @{
            srcExists = (Test-Path "$base\src")
            orchestratorExists = (Test-Path "$base\orchestrator_runtime")
            interactiveExists = (Test-Path "$base\interactive_layer")
            reportsExists = (Test-Path "$base\reports")
            scriptsExists = (Test-Path "$base\scripts")
            selfStateExists = (Test-Path "$base\self_state.json")
            gitignoreExists = (Test-Path "$base\.gitignore")
            noDotGit = -not (Test-Path "$base\.git")
            noEnvLocal = -not (Test-Path "$base\.env.local")
        }
    }
    
    Write-Host "  src/: $($finalCheck.srcExists)" -ForegroundColor $(if($finalCheck.srcExists){"Green"}else{"Red"})
    Write-Host "  orchestrator_runtime/: $($finalCheck.orchestratorExists)" -ForegroundColor $(if($finalCheck.orchestratorExists){"Green"}else{"Red"})
    Write-Host "  interactive_layer/: $($finalCheck.interactiveExists)" -ForegroundColor $(if($finalCheck.interactiveExists){"Green"}else{"Red"})
    Write-Host "  reports/: $($finalCheck.reportsExists)" -ForegroundColor $(if($finalCheck.reportsExists){"Green"}else{"Red"})
    Write-Host "  scripts/: $($finalCheck.scriptsExists)" -ForegroundColor $(if($finalCheck.scriptsExists){"Green"}else{"Red"})
    Write-Host "  self_state.json: $($finalCheck.selfStateExists)" -ForegroundColor $(if($finalCheck.selfStateExists){"Green"}else{"Red"})
    Write-Host "  .gitignore: $($finalCheck.gitignoreExists)" -ForegroundColor $(if($finalCheck.gitignoreExists){"Green"}else{"Red"})
    Write-Host "  .git/ absent: $($finalCheck.noDotGit)" -ForegroundColor $(if($finalCheck.noDotGit){"Green"}else{"Red"})
    Write-Host "  .env.local absent: $($finalCheck.noEnvLocal)" -ForegroundColor $(if($finalCheck.noEnvLocal){"Green"}else{"Red"})
} catch {
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  TRANSFER COMPLETE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan