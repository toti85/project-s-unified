# QUARANTINE SCRIPT — OLD AUDIT FORKS (FIXED v2)
# Generated: 2026-06-10 — VERIFIED SAFE
# Uses ONLY Move-Item. NO Remove-Item. NO permanent deletion.
# Quarantine target: C:\_cleanup_quarantine\audit_forks_20260609\
# Only SAFE_TO_DELETE_CANDIDATE folders from JSON inventory.
# All REVIEW_REQUIRED folders are EXCLUDED.
# Script continues on error (no throw — logs and continues).

$ErrorActionPreference = "Continue"
$quarantine = "C:\_cleanup_quarantine\audit_forks_20260609"
$log        = "C:\_cleanup_quarantine\quarantine_log_20260609.txt"

New-Item -ItemType Directory -Path $quarantine -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path $log) -Force | Out-Null

$moved   = 0
$skipped = 0
$errors  = 0

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content $log $line -ErrorAction SilentlyContinue
}

# PROTECTED PATHS — never touch these
$protected = @(
    "C:\Intel",
    "C:\PerfLogs",
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\ProjectS-Unified",
    "C:\SWSetup",
    "C:\Users\Admin\AppData",
    "C:\Users\Admin\Desktop",
    "C:\Users\Admin\Documents",
    "C:\Users\Admin\Downloads",
    "C:\Users\Admin\Music",
    "C:\Users\Admin\Pictures",
    "C:\Users\Admin\Videos",
    "C:\Windows",
    "C:\XboxGames",
    "C:\inetpub",
    "C:\system.sav",
    "C:\Toti",
    "C:\AutoGPT",
    "C:\S",
    "C:\S-main",
    "C:\S1",
    "C:\0617 Mukodo",
    "C:\0618 phase2",
    "C:\ProjectS-Backups"
)

function Move-ToQuarantine($src) {
    # Protected check
    foreach ($p in $protected) {
        if ($src.ToLower() -eq $p.ToLower() -or $src.ToLower().StartsWith($p.ToLower() + '\')) {
            Write-Log "SKIP (protected): $src"
            $script:skipped++
            return
        }
    }
    # ProjectS-Unified extra safety
    if ($src.ToLower().StartsWith("c:\projectS-unified\".ToLower())) {
        Write-Log "SKIP (protected ProjectS-Unified): $src"
        $script:skipped++
        return
    }
    # Not found
    if (-not (Test-Path $src)) {
        Write-Log "SKIP (not found — parent already moved or never existed): $src"
        $script:skipped++
        return
    }
    # Destination conflict check
    $destName = [IO.Path]::GetFileName($src.TrimEnd('\'))
    $dest = Join-Path $quarantine $destName
    if (Test-Path $dest) {
        Write-Log "SKIP (dest already exists — rename needed): $src -> $dest"
        $script:skipped++
        return
    }
    # Move
    Write-Log "MOVING: $src -> $dest"
    try {
        Move-Item -Path $src -Destination $dest -ErrorAction Stop
        Write-Log "OK: $src"
        $script:moved++
    } catch {
        Write-Log "ERROR moving $src : $_"
        $script:errors++
    }
}

Write-Log "=== QUARANTINE RUN START ==="
Write-Log "Quarantine target: $quarantine"

# ── SAFE_TO_DELETE_CANDIDATE — TOP-LEVEL FOLDERS ONLY ──────────────────────
# (Nested sub-paths whose parents are already included are intentionally omitted;
#  they will be moved as part of their parent directory.)

# Largest first
Move-ToQuarantine "C:\260101"
Move-ToQuarantine "C:\tmp"
Move-ToQuarantine "C:\1225"
Move-ToQuarantine "C:\20250426"
Move-ToQuarantine "C:\project_s_agent0603"
Move-ToQuarantine "C:\0602"
Move-ToQuarantine "C:\audits"
Move-ToQuarantine "C:\0725"
Move-ToQuarantine "C:\bounty-work"
Move-ToQuarantine "C:\0703"
Move-ToQuarantine "C:\0720"
Move-ToQuarantine "C:\0723"
Move-ToQuarantine "C:\project_s_agent"
Move-ToQuarantine "C:\0612"
Move-ToQuarantine "C:\0616"
Move-ToQuarantine "C:\chrome_debug"
Move-ToQuarantine "C:\chrome-debug"
Move-ToQuarantine "C:\0809"
Move-ToQuarantine "C:\0610"
Move-ToQuarantine "C:\0531"
Move-ToQuarantine "C:\0614"
Move-ToQuarantine "C:\0601"
Move-ToQuarantine "C:\project_s_agentbackup"
Move-ToQuarantine "C:\0603"
Move-ToQuarantine "C:\0530"
Move-ToQuarantine "C:\0529"
Move-ToQuarantine "C:\0528"
Move-ToQuarantine "C:\project_s_agent_backup_20250530_150333"
Move-ToQuarantine "C:\ChromeDebugProfile"
Move-ToQuarantine "C:\0522"
Move-ToQuarantine "C:\temp"
Move-ToQuarantine "C:\ChromeDebug"
Move-ToQuarantine "C:\firedancer"
Move-ToQuarantine "C:\0714"
Move-ToQuarantine "C:\chrome_debug_profile"
Move-ToQuarantine "C:\watchtower_bug_poc"
Move-ToQuarantine "C:\chrome-debug-temp"
Move-ToQuarantine "C:\0523"
Move-ToQuarantine "C:\0526"
Move-ToQuarantine "C:\0525"
Move-ToQuarantine "C:\0524"
Move-ToQuarantine "C:\0713"
Move-ToQuarantine "C:\project-s-agent-main"
Move-ToQuarantine "C:\0712"
Move-ToQuarantine "C:\0205"
Move-ToQuarantine "C:\PROJECT_S_CLEAN"
Move-ToQuarantine "C:\0517"
Move-ToQuarantine "C:\0515"
Move-ToQuarantine "C:\0630"
Move-ToQuarantine "C:\project_s_backups"
Move-ToQuarantine "C:\project-s-clean"
Move-ToQuarantine "C:\project-s-cognitive-working"
Move-ToQuarantine "C:\project_s_stable"
Move-ToQuarantine "C:\backup"
Move-ToQuarantine "C:\bounty_reports"
Move-ToQuarantine "C:\silo-test"

Write-Log "=== QUARANTINE RUN COMPLETE ==="
Write-Log "Moved:   $moved"
Write-Log "Skipped: $skipped"
Write-Log "Errors:  $errors"

$freeGB = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
Write-Log "C:\ free after: $freeGB GB"

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Moved:   $moved" -ForegroundColor Green
Write-Host "Skipped: $skipped" -ForegroundColor Yellow
Write-Host "Errors:  $errors" -ForegroundColor $(if($errors -gt 0){"Red"}else{"Green"})
Write-Host "Free:    $freeGB GB"
Write-Host "Log:     $log"
