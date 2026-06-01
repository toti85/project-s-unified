# SERVER PHASE 2: Project-S Migration to SHAYANSKA-DL380

**Date:** 2026-05-18
**Target:** SHAYANSKA-DL380 (192.168.1.180)
**Phase 1 Status:** PASS (Git 2.47.1, Python 3.12.9, pip 24.3.1 verified, directories created)

---

## CRITICAL MIGRATION CONSTRAINTS — READ FIRST

### Authoritative Operating Rules

1. **STAGING ONLY, NOT PRODUCTION**
   - The DL380 server is a STAGING environment
   - The DEV machine at C:\ProjectS-Unified remains the MASTER Project-S workspace
   - Do NOT treat the server copy as production/main Project-S instance

2. **COPY, NEVER MOVE**
   - Migration is COPY only
   - The DEV workspace must NOT be modified, deleted, relocated, or "cleaned up"
   - The server receives a SNAPSHOT COPY at a specific point in time

3. **NO PERSISTENT SERVICES**
   - Do NOT start any persistent service on the server in this phase
   - Do NOT use the server for real Project-S work yet
   - Goal: prove the code can be transferred and run import/smoke checks

4. **PARALLEL WORK PROTECTION**
   - A separate DEV Cline thread works on Interactive Layer / GAP_029
   - The server migration snapshot may become slightly behind the DEV master
   - This is acceptable; final server sync happens later after DEV master stabilizes

5. **SCOPE ISOLATION**
   - Server Cline scope: C:\ProjectS on SHAYANSKA-DL380
   - DEV Cline scope: C:\ProjectS-Unified on DEV machine
   - These must NOT interleave or modify each other's files
   - Reports go to different paths: reports/SERVER_* vs reports/GAP_029_*

---

## PRE-MIGRATION SNAPSHOT (ALREADY COMPLETED)

**Backup Location:** `C:\ProjectS-Backups\2026-05-18-1504-pre-server-migration`

**Files Backed Up:**
- self_state.json
- PROJECT_S_OVERVIEW.md
- PROJECT_S_STATUS_AND_JOURNAL.md
- memory/intelligence/meta_evidence.jsonl
- interactive_layer_data/interactive.db

**Git Status:** Not a git repository (skip commit/tag)

---

## PHASE 1 SUMMARY (ALREADY COMPLETED)

| Item | Status |
|------|--------|
| WinRM LAN connection | VERIFIED (192.168.1.180:5985, Administrator/Qwe123) |
| Hostname | Confirmed: SHAYANSKA-DL380 |
| Git | 2.47.1.windows.1 (pre-existing) |
| Python | 3.12.9 (pre-existing) |
| pip | 24.3.1 (pre-existing) |
| Project-S directories | All 4 created (C:\ProjectS, bootstrap, logs, reports) |
| Reboot needed | NO |
| winget/chocolatey | NOT available on this server |

---

## PHASE 2 GOALS

1. **Transfer Project-S code from DEV to server**
   - Copy C:\ProjectS-Unified to C:\ProjectS\project-s-code on server
   - Exclude: .git, __pycache__, *.pyc, .pytest_cache, .vscode, *.exe, *.apk, *.rbxm, *.rbxl, node_modules, .benchmarks, *.log
   - Use WinRM or network share for transfer

2. **Verify transfer integrity**
   - Count files/directories transferred
   - Verify key directories exist: config/, src/core/, interactive_layer/

3. **Run Python import smoke test**
   - Verify Python 3.12.9 can import the transferred code
   - Check that core modules load without errors
   - Report any missing dependencies

4. **Generate Phase 2 report**
   - Document transfer results
   - List any errors or missing dependencies
   - Recommend next steps

---

## PHASE 2 TASKS

### Task 2.1: Verify WinRM Connectivity

From DEV machine, verify WinRM is still working:

```powershell
$targetIP = "192.168.1.180"
$targetPassword = "Qwe123"
$securePass = ConvertTo-SecureString $targetPassword -AsPlainText -Force
$targetCred = New-Object System.Management.Automation.PSCredential("$targetIP\Administrator", $securePass)

# Test hostname
$hostname = Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock { hostname }
Write-Host "Server hostname: $hostname"
```

Expected: `SHAYANSKA-DL380`

### Task 2.2: Prepare Transfer List

On DEV machine, create a list of files to transfer:

```powershell
$devSource = "C:\ProjectS-Unified"
$excludePatterns = @(".git", "__pycache__", "*.pyc", ".pytest_cache", ".vscode", "*.exe", "*.apk", "*.rbxm", "*.rbxl", "node_modules", ".benchmarks", "*.log")

$transferList = @()
$allItems = Get-ChildItem -Path $devSource -Recurse -Force
foreach ($item in $allItems) {
    $relativePath = $item.FullName.Substring($devSource.Length + 1)
    $shouldExclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    if (-not $shouldExclude) {
        $transferList += $relativePath
    }
}

Write-Host "Files to transfer: $($transferList.Count)"
$transferList | Out-File -FilePath "C:\ProjectS-Unified\.transfer_list.txt" -Encoding UTF8
```

### Task 2.3: Transfer Files to Server

Create directory structure on server first:

```powershell
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    New-Item -Path "C:\ProjectS\project-s-code" -ItemType Directory -Force | Out-Null
}
```

Then copy files. The most reliable method for large transfers is robocopy to a network share:

```powershell
# Option A: If network share is accessible
robocopy "C:\ProjectS-Unified" "\\192.168.1.180\C$\ProjectS\project-s-code" /E /XF *.exe *.apk *.rbxm *.rbxl *.log /XD .git node_modules .benchmarks .pytest_cache .vscode

# Option B: If network share not accessible, use PowerShell remoting
# (This is slower but more reliable for WinRM-only connections)
```

### Task 2.4: Verify Transfer

On server, verify the transfer:

```powershell
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $projectSDir = "C:\ProjectS\project-s-code"
    $fileCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -File | Measure-Object).Count
    $dirCount = (Get-ChildItem -Path $projectSDir -Recurse -Force -Directory | Measure-Object).Count

    Write-Host "Files transferred: $fileCount"
    Write-Host "Directories transferred: $dirCount"
    Write-Host "project-s-code/ exists: $(Test-Path $projectSDir)"
    Write-Host "config/ exists: $(Test-Path '$projectSDir\config')"
    Write-Host "src/core/ exists: $(Test-Path '$projectSDir\src\core')"
    Write-Host "interactive_layer/ exists: $(Test-Path '$projectSDir\interactive_layer')"
}
```

### Task 2.5: Python Import Smoke Test

On server, test that Python can import the transferred code:

```powershell
Invoke-Command -ComputerName $targetIP -Credential $targetCred -ScriptBlock {
    $env:PATH = "C:\Program Files\Python312;C:\Program Files\Python312\Scripts;" + $env:PATH
    $env:PYTHONPATH = "C:\ProjectS\project-s-code"

    Write-Host "Python version: $(python --version 2>&1)"

    # Test basic imports
    try {
        python -c "import sys; print('Python path:', sys.path)" 2>&1
    } catch {
        Write-Host "FAIL: Python import failed: $_"
    }

    # Test if key directories are accessible
    Write-Host "ProjectS dir exists: $(Test-Path 'C:\ProjectS\project-s-code')"
}
```

### Task 2.6: Generate Phase 2 Report

Create report at:
`reports\SERVER_PHASE_2_MIGRATION_YYYYMMDD.md`

---

## REPORT STRUCTURE

```markdown
# SERVER PHASE 2 MIGRATION REPORT

**Date:** YYYY-MM-DD
**Target:** SHAYANSKA-DL380 (192.168.1.180)
**Phase:** 2 - Project-S Code Transfer (STAGING)

## Executive Verdict: PASS / PARTIAL / FAIL

## Constraints Applied
- STAGING only, NOT production
- Migration is COPY, never MOVE
- DEV machine remains MASTER
- No persistent services started

## Pre-Migration Snapshot
- Backup Location: C:\ProjectS-Backups\2026-05-18-1504-pre-server-migration
- Files Backed Up: 5
- Git Status: Not a git repository

## Transfer Results
| Check | Result |
|-------|--------|
| WinRM Connectivity | PASS/FAIL |
| Python on Server | 3.12.9 |
| Files Transferred | COUNT |
| Directories Transferred | COUNT |
| Key Directories Present | YES/NO |
| Import Smoke Test | PASS/FAIL |

## Errors or Manual Action Required
[None or list errors]

## Next Recommended Step
Phase 3: Install Python dependencies, run full import test
```

---

## WHAT NOT TO DO

- DO NOT modify C:\ProjectS-Unified on DEV machine
- DO NOT delete any files from DEV
- DO NOT start any service on the server
- DO NOT install Python packages yet (Phase 3)
- DO NOT attempt to run the full Project-S application
- DO NOT change network configuration
- DO NOT install NVIDIA drivers (separate phase)
- DO NOT migrate Project-S data files (databases, configs) yet

---

## SUCCESS CRITERIA

Phase 2 is considered SUCCESS when:
1. [ ] WinRM connectivity verified
2. [ ] Project-S code transferred to C:\ProjectS\project-s-code on server
3. [ ] File count and directory count reported
4. [ ] Key directories verified (config/, src/core/, interactive_layer/)
5. [ ] Python import smoke test runs without errors
6. [ ] Phase 2 report generated

---

## NEXT PHASE (PHASE 3) - PENDING

After Phase 2 completes successfully:
1. Install Python dependencies on server
2. Run full import test
3. Test interactive layer functionality
4. Document any compatibility issues