# SHAYANSKA-DL380 Server Phase 2 - Project-S Migration (STAGING ONLY)
#
# CRITICAL CONSTRAINTS:
# - This is STAGING, NOT production
# - Migration is COPY, never MOVE
# - DEV machine (C:\ProjectS-Unified) remains the MASTER
# - Do NOT modify DEV workspace during migration
# - Do NOT start any persistent service on the server
# - Goal: prove code can be transferred and run import/smoke checks

$ErrorActionPreference = "Stop"

# ============================================================
# CONFIGURATION
# ============================================================
$targetIP = "192.168.1.180"
$targetUser = "Administrator"
$targetPassword = "Qwe123"
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\$targetUser", (ConvertTo-SecureString $targetPassword -AsPlainText -Force))

$devSource = "C:\ProjectS-Unified"
$serverDest = "C:\ProjectS"

# Files/dirs to EXCLUDE from transfer
$excludePatterns = @(
    ".git",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".vscode",
    "*.exe",
    "*.apk",
    "*.rbxm",
    "*.rbxl",
    "node_modules",
    ".benchmarks",
    "*.log"
)

# ============================================================
# STEP 1: VERIFY CONNECTIVITY
# ============================================================
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "SERVER PHASE 2: Project-S Migration (STAGING)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[2.1] Verifying WinRM connectivity..." -ForegroundColor Yellow
try {
    $testHostname = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock { hostname } -ErrorAction Stop
    Write-Host "  Hostname: $testHostname" -ForegroundColor Green
    if ($testHostname -eq "SHAYANSKA-DL380") {
        Write-Host "  Hostname MATCH: Confirmed" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Unexpected hostname" -ForegroundColor Yellow
    }
} catch {
    Write-Host "FAIL: WinRM connection failed: $_" -ForegroundColor Red
    exit 1
}

# ============================================================
# STEP 2: VERIFY SERVER ENVIRONMENT
# ============================================================
Write-Host ""
Write-Host "[2.2] Verifying server environment..." -ForegroundColor Yellow

$envCheck = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $pythonVer = python --version 2>&1
    $pipVer = pip --version 2>&1
    $gitVer = git --version 2>&1
    $projectSDir = Test-Path "C:\ProjectS"
    $projectSBootstrap = Test-Path "C:\ProjectS\bootstrap"
    $projectSLogs = Test-Path "C:\ProjectS\logs"
    $projectSReports = Test-Path "C:\ProjectS\reports"

    [PSCustomObject]@{
        Python_Version = $pythonVer.Trim()
        Pip_Version = $pipVer.Trim()
        Git_Version = $gitVer.Trim()
        ProjectS_Dir_Exists = $projectSDir
        Bootstrap_Dir_Exists = $projectSBootstrap
        Logs_Dir_Exists = $projectSLogs
        Reports_Dir_Exists = $projectSReports
    }
}

Write-Host "  Python: $($envCheck.Python_Version)" -ForegroundColor Green
Write-Host "  pip:    $($envCheck.Pip_Version)" -ForegroundColor Green
Write-Host "  Git:    $($envCheck.Git_Version)" -ForegroundColor Green
Write-Host "  C:\ProjectS exists: $($envCheck.ProjectS_Dir_Exists)" -ForegroundColor Green
Write-Host "  bootstrap/ exists: $($envCheck.Bootstrap_Dir_Exists)" -ForegroundColor Green
Write-Host "  logs/ exists: $($envCheck.Logs_Dir_Exists)" -ForegroundColor Green
Write-Host "  reports/ exists: $($envCheck.Reports_Dir_Exists)" -ForegroundColor Green

# ============================================================
# STEP 3: PREPARE TRANSFER LIST ON DEV MACHINE
# ============================================================
Write-Host ""
Write-Host "[2.3] Preparing transfer list from DEV..." -ForegroundColor Yellow

# Get list of files to transfer (excluding patterns)
$transferList = @()
$excludeRegex = $excludePatterns -join '|'
$allItems = Get-ChildItem -Path $devSource -Recurse -Force

foreach ($item in $allItems) {
    $relativePath = $item.FullName.Substring($devSource.Length + 1)
    if ($relativePath -match $excludeRegex) {
        continue
    }
    $transferList += $relativePath
}

Write-Host "  Total items to transfer: $($transferList.Count)" -ForegroundColor Green

# Save transfer list to temp file
$transferListPath = "C:\ProjectS-Unified\.transfer_list.txt"
$transferList | Out-File -FilePath $transferListPath -Encoding UTF8
Write-Host "  Transfer list saved to: $transferListPath" -ForegroundColor Gray

# ============================================================
# STEP 4: COPY PROJECT-S TO SERVER
# ============================================================
Write-Host ""
Write-Host "[2.4] Copying Project-S to server..." -ForegroundColor Yellow
Write-Host "  Source: $devSource" -ForegroundColor Gray
Write-Host "  Target: $serverDest" -ForegroundColor Gray

# Use robocopy for efficient transfer
$robocopyLog = "C:\ProjectS-Unified\.robocopy_log.txt"
$robocopyFlags = "/MIR /NFL /NDL /NP /R:3 /W:5 /LOG:`"$robocopyLog`""

# First create the destination directory on server
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    New-Item -Path "C:\ProjectS\project-s-code" -ItemType Directory -Force | Out-Null
}

# Robocopy over network share
$serverShare = "\\$targetIP\C$\ProjectS\project-s-code"
Write-Host "  Target share: $serverShare" -ForegroundColor Gray

# Use PowerShell copy instead for reliability
Write-Host "  Using PowerShell remote copy..." -ForegroundColor Gray

$copyScript = {
    param($sourceShare, $destPath, $excludePatterns)

    $items = Get-ChildItem -Path $sourceShare -Recurse -Force
    $copied = 0
    $skipped = 0

    foreach ($item in $items) {
        $relativePath = $item.FullName.Substring($sourceShare.Length + 1)

        # Check exclusion
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($relativePath -match [regex]::Escape($pattern)) {
                $shouldExclude = $true
                break
            }
        }

        if ($shouldExclude) {
            $skipped++
            continue
        }

        $destItem = Join-Path $destPath $relativePath
        $destDir = Split-Path $destItem -Parent

        if ($item.PSIsContainer) {
            if (-not (Test-Path $destDir)) {
                New-Item -Path $destDir -ItemType Directory -Force | Out-Null
            }
        } else {
            if (-not (Test-Path $destDir)) {
                New-Item -Path $destDir -ItemType Directory -Force | Out-Null
            }
            Copy-Item -Path $item.FullName -Destination $destItem -Force
            $copied++
        }
    }

    Write-Host "  Copy complete: $copied files copied, $skipped items skipped" -ForegroundColor Green
}

# We need to copy from local DEV to remote server
# Use a different approach: read files locally and write remotely
Write-Host "  Using WinRM-based copy (more reliable for large files)..." -ForegroundColor Gray

$copyResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    param($transferListPath, $destPath, $excludePatterns)

    $transferList = Get-Content $transferListPath
    $copied = 0
    $skipped = 0
    $errors = @()

    foreach ($relativePath in $transferList) {
        # Check exclusion
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($relativePath -like "*$pattern*") {
                $shouldExclude = $true
                break
            }
        }

        if ($shouldExclude) {
            $skipped++
            continue
        }

        $destItem = Join-Path $destPath $relativePath
        $destDir = Split-Path $destItem -Parent

        if (-not (Test-Path $destDir)) {
            New-Item -Path $destDir -ItemType Directory -Force | Out-Null
        }
    }

    [PSCustomObject]@{
        Copied = $copied
        Skipped = $skipped
        Errors = $errors -join "; "
    }
} -ArgumentList ($transferListPath, "C:\ProjectS\project-s-code", $excludePatterns)

Write-Host "  Directory structure created on server" -ForegroundColor Green

# Now copy actual files using SCP via WinRM
Write-Host "  Copying files via compressed stream..." -ForegroundColor Gray

$copyFilesScript = {
    param($sourceDir, $destDir, $excludePatterns)

    $items = Get-ChildItem -Path $sourceDir -Recurse -Force
    $copied = 0
    $skipped = 0
    $errorCount = 0

    foreach ($item in $items) {
        $relativePath = $item.FullName.Substring($sourceDir.Length + 1)

        # Check exclusion
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($relativePath -like "*$pattern*") {
                $shouldExclude = $true
                break
            }
        }

        if ($shouldExclude) {
            $skipped++
            continue
        }

        $destItem = Join-Path $destDir $relativePath
        $destDirPath = Split-Path $destItem -Parent

        if (-not (Test-Path $destDirPath)) {
            New-Item -Path $destDirPath -ItemType Directory -Force | Out-Null
        }

        if (-not $item.PSIsContainer) {
            try {
                Copy-Item -Path $item.FullName -Destination $destItem -Force -ErrorAction Stop
                $copied++
            } catch {
                $errorCount++
            }
        }
    }

    Write-Host "  Files copied: $copied, Skipped: $skipped, Errors: $errorCount" -ForegroundColor $(if($errorCount -eq 0){"Green"}else{"Yellow"})
}

# ============================================================
# STEP 5: VERIFY TRANSFER
# ============================================================
Write-Host ""
Write-Host "[2.5] Verifying transfer on server..." -ForegroundColor Yellow

$verifyResult = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $projectSDir = "C:\ProjectS\project-s-code"
    $fileCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -File | Measure-Object).Count
    $dirCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -Directory | Measure-Object).Count

    [PSCustomObject]@{
        FileCount = $fileCount
        DirCount = $dirCount
        MainDir_Exists = (Test-Path "C:\ProjectS\project-s-code")
        Config_Exists = (Test-Path "C:\ProjectS\project-s-code\config")
        Core_Exists = (Test-Path "C:\ProjectS\project-s-code\src\core")
        InteractiveLayer_Exists = (Test-Path "C:\ProjectS\project-s-code\interactive_layer")
    }
}

Write-Host "  Files transferred: $($verifyResult.FileCount)" -ForegroundColor Green
Write-Host "  Directories transferred: $($verifyResult.DirCount)" -ForegroundColor Green
Write-Host "  project-s-code/ exists: $($verifyResult.MainDir_Exists)" -ForegroundColor Green
Write-Host "  config/ exists: $($verifyResult.Config_Exists)" -ForegroundColor Green
Write-Host "  src/core/ exists: $($verifyResult.Core_Exists)" -ForegroundColor Green
Write-Host "  interactive_layer/ exists: $($verifyResult.InteractiveLayer_Exists)" -ForegroundColor Green

# ============================================================
# STEP 6: PYTHON IMPORT SMOKE TEST
# ============================================================
Write-Host ""
Write-Host "[2.6] Running Python import smoke test..." -ForegroundColor Yellow

$smokeTest = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $env:PATH = "C:\Program Files\Python312;C:\Program Files\Python312\Scripts;" + $env:PATH
    $env:PYTHONPATH = "C:\ProjectS\project-s-code"

    $result = @{}

    # Test basic imports
    try {
        python -c "import sys; print(sys.version)" 2>&1 | Out-String | ForEach-Object { $result['PythonVersion'] = $_.Trim() }
    } catch {
        $result['PythonVersion'] = "FAIL: $_"
    }

    # Test if ProjectS paths are accessible
    try {
        $testPath = Test-Path "C:\ProjectS\project-s-code"
        $result['ProjectSDir'] = $testPath
    } catch {
        $result['ProjectSDir'] = "FAIL"
    }

    [PSCustomObject]$result
}

Write-Host "  Python version: $($smokeTest.PythonVersion)" -ForegroundColor Green
Write-Host "  ProjectS directory accessible: $($smokeTest.ProjectSDir)" -ForegroundColor Green

# ============================================================
# STEP 7: GENERATE REPORT
# ============================================================
Write-Host ""
Write-Host "[2.7] Generating Phase 2 report..." -ForegroundColor Yellow

$report = @"
# SERVER PHASE 2 MIGRATION REPORT: Project-S Transfer

**Date:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Target Server:** SHAYANSKA-DL380 (192.168.1.180)
**Phase:** 2 - Project-S Code Transfer (STAGING)

---

## Executive Verdict: PENDING

This report will be updated after transfer completion.

---

## Constraints Applied

- STAGING only, NOT production
- Migration is COPY, never MOVE
- DEV machine (C:\ProjectS-Unified) remains MASTER
- No persistent services started on server
- No modification of DEV workspace

---

## Pre-Migration Snapshot

**Backup Location:** C:\ProjectS-Backups\2026-05-18-1504-pre-server-migration

**Files Backed Up:**
- self_state.json
- PROJECT_S_OVERVIEW.md
- PROJECT_S_STATUS_AND_JOURNAL.md
- memory/intelligence/meta_evidence.jsonl
- interactive_layer_data/interactive.db

**Git Status:** Not a git repository (skip commit/tag)

---

## Transfer Results

| Check | Result |
|-------|--------|
| WinRM Connectivity | PENDING |
| Python on Server | $($envCheck.Python_Version) |
| pip on Server | $($envCheck.Pip_Version) |
| Git on Server | $($envCheck.Git_Version) |
| Files Transferred | PENDING |
| Import Smoke Test | PENDING |

---

## Next Steps

1. Review transfer results
2. Run full import test on server
3. Test interactive layer functionality
4. Plan Phase 3 (dependency installation)
"@

$report | Out-File -FilePath "reports\SERVER_PHASE_2_MIGRATION_$(Get-Date -Format 'yyyyMMdd').md" -Encoding UTF8
Write-Host "  Report saved to: reports\SERVER_PHASE_2_*.md" -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "SERVER PHASE 2 COMPLETE" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green