"""
DEV DISK CLEANUP INVENTORY GENERATOR
Generates inventory + top-large + cleanup plan + quarantine script
READ-ONLY scan — no deletion.
"""
import os, json, subprocess
from pathlib import Path
from datetime import datetime

SANDBOX = Path(r"C:\ProjectS-Unified\orchestrator_runtime\sandbox")
SANDBOX.mkdir(parents=True, exist_ok=True)
DATE_TAG = "20260609"

# ── PROTECTED PATHS (never touch these) ──────────────────────────────────────
PROTECTED = {
    r"C:\ProjectS-Unified",
    r"C:\ProjectS-Unified\orchestrator_runtime",
    r"C:\Users\Admin\AppData",
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\Users\Admin\Documents",
    r"C:\Users\Admin\Pictures",
    r"C:\Users\Admin\Downloads",
    r"C:\Users\Admin\Music",
    r"C:\Users\Admin\Videos",
    r"C:\Users\Admin\Desktop",
    r"C:\inetpub",
    r"C:\Intel",
    r"C:\PerfLogs",
    r"C:\SWSetup",
    r"C:\system.sav",
    r"C:\XboxGames",
}

def is_protected(path_str):
    p = path_str.rstrip("\\").lower()
    for prot in PROTECTED:
        if p == prot.lower() or p.startswith(prot.lower() + "\\"):
            return True
    return False

# ── CANDIDATE PATHS ──────────────────────────────────────────────────────────
CANDIDATES = [
    # Direct audit/bounty/fork repos
    r"C:\audits",
    r"C:\bounties",
    r"C:\bounty-work",
    r"C:\bounty_reports",
    r"C:\firedancer",
    r"C:\watchtower_bug_poc",
    r"C:\silo-test",
    r"C:\avail-build-scripts",
    # Old project-s versions / backups
    r"C:\project-s-agent-main",
    r"C:\project-s-clean",
    r"C:\project-s-cognitive-working",
    r"C:\ProjectS",
    r"C:\project_s_agent",
    r"C:\project_s_agent0603",
    r"C:\project_s_agentbackup",
    r"C:\project_s_agent_backup_20250530_150333",
    r"C:\project_s_backups",
    r"C:\PROJECT_S_CLEAN",
    r"C:\project_s_stable",
    r"C:\ProjectS-Backups",
    r"C:\ProjectS-Snapshot-Staging",
    r"C:\ProjectS-Automation",
    r"C:\S-main",
    r"C:\S1",
    r"C:\S",
    r"C:\1",
    r"C:\backup",
    # Date-stamped old snapshots
    r"C:\0205", r"C:\0515", r"C:\0517", r"C:\0522", r"C:\0523",
    r"C:\0524", r"C:\0525", r"C:\0526", r"C:\0528", r"C:\0529",
    r"C:\0530", r"C:\0531", r"C:\0601", r"C:\0602", r"C:\0603",
    r"C:\0610", r"C:\0612", r"C:\0614", r"C:\0616",
    r"C:\0617 Mukodo", r"C:\0618 phase2",
    r"C:\0630", r"C:\0703", r"C:\0712", r"C:\0713", r"C:\0714",
    r"C:\0720", r"C:\0723", r"C:\0725", r"C:\0809", r"C:\1225",
    # Misc dev tools / experiments
    r"C:\AutoGPT",
    r"C:\Superagi",
    r"C:\Deepseek",
    r"C:\AI",
    r"C:\AI_Stable",
    r"C:\coder",
    r"C:\project",
    r"C:\v2_architecture",
    r"C:\20250426",
    r"C:\2026.03.19",
    r"C:\260101",
    r"C:\Projekt",
    r"C:\projekt1",
    r"C:\Toti",
    r"C:\mentes",
    r"C:\Mentesjoverzio",
    r"C:\OPEN",
    r"C:\osszehasonlitas",
    r"C:\temp",
    r"C:\tmp",
    r"C:\chrome-debug",
    r"C:\chrome-debug-temp",
    r"C:\ChromeDebug",
    r"C:\ChromeDebugProfile",
    r"C:\chrome_debug",
    r"C:\chrome_debug_profile",
    r"C:\RobloxGameSprint",
    # Nested audit/bounty detected earlier
    r"C:\0713\v2_architecture\calcom-bounty",
    r"C:\0713\v2_architecture\calcom-test-clone",
    r"C:\0723\v2_architecture\exo-fork",
    r"C:\0723\v2_architecture\golem-exec-bounty",
    r"C:\0725\v2_architecture\golem-exec-bounty",
    r"C:\1225\pendle_phase1_fork",
    r"C:\260101\lido-audit",
    r"C:\Users\Admin\project_s_super_core\hardhat-poc",
    r"C:\Users\Admin\project_s_super_core\bounty_audits",
]

# ── SIZE HELPER ───────────────────────────────────────────────────────────────
def dir_size_bytes(p):
    total = 0
    try:
        for root, dirs, files in os.walk(p):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
    except Exception:
        pass
    return total

def has_subdir(p, name):
    try:
        for root, dirs, files in os.walk(p):
            if name in dirs:
                return True
    except Exception:
        pass
    return False

def has_file_ext(p, exts):
    try:
        for root, dirs, files in os.walk(p):
            for f in files:
                if any(f.lower().endswith(e) for e in exts):
                    return True
    except Exception:
        pass
    return False

def classify(info):
    p = info["path"]
    name = os.path.basename(p).lower()
    if is_protected(p):
        return "DO_NOT_DELETE", "Protected path."
    if not info["exists"]:
        return "SKIP", "Path does not exist."
    reasons = []
    # Strong indicators for safe-to-delete
    strong = False
    if any(x in name for x in ("bounty","audit","fork","clone","bounty-work","bounty_reports","silo-test","watchtower","firedancer","calcom","golem","pendle","lido","exo-fork")):
        strong = True
        reasons.append(f"Name matches audit/bounty/fork pattern: {name}")
    if re.match(r"^\d{4}$", name) or re.match(r"^\d{6,8}$", name):
        strong = True
        reasons.append("Date-stamped old snapshot.")
    if name in ("backup","project_s_agentbackup","project_s_agent_backup_20250530_150333","project_s_backups","projectS-backups"):
        strong = True
        reasons.append("Explicit backup folder.")
    if info["has_git"]:
        reasons.append("Contains .git (repo clone)")
    if info["has_node_modules"]:
        reasons.append("Contains node_modules (can be large, easily reinstalled)")
    if info["has_foundry"]:
        reasons.append("Contains foundry (solidity toolchain)")
    if info["has_hardhat"]:
        reasons.append("Contains hardhat config (solidity toolchain)")
    size_gb = info["size_bytes"] / 1e9
    if size_gb > 0.5:
        reasons.append(f"Large: {size_gb:.2f} GB")

    # Override: old project-s versions that are NOT the current unified
    if any(x in name for x in ("project_s_agent","project-s-agent","project-s-clean","project-s-cognitive","project_s_stable","project_s_clean","projectS-snapshot","projectS-automation","projectS-backups")):
        strong = True
        reasons.append("Old project-s version/backup.")
    # Chrome debug profiles  
    if "chrome" in name:
        strong = True
        reasons.append("Chrome debug profile (temp data).")
    if name in ("temp","tmp"):
        strong = True
        reasons.append("Temp/tmp folder.")
    if name in ("autogpt","superagi","deepseek","coder"):
        reasons.append("Third-party AI tool install (review if still needed).")
        return "REVIEW_REQUIRED", "; ".join(reasons)

    if strong:
        return "SAFE_TO_DELETE_CANDIDATE", "; ".join(reasons) if reasons else "Matches deletion criteria."
    if reasons:
        return "REVIEW_REQUIRED", "; ".join(reasons)
    return "REVIEW_REQUIRED", "No strong pattern match; manual review recommended."

import re

print(f"Scanning {len(CANDIDATES)} candidates ...")
records = []
for idx, p in enumerate(CANDIDATES):
    print(f"  [{idx+1}/{len(CANDIDATES)}] {p} ...", end="", flush=True)
    exists = os.path.isdir(p)
    if exists and not is_protected(p):
        size_b = dir_size_bytes(p)
        has_git = os.path.isdir(os.path.join(p, ".git"))
        has_nm = has_subdir(p, "node_modules")
        has_foundry = has_subdir(p, "foundry") or has_subdir(p, ".foundry")
        has_hh = has_file_ext(p, (".hardhat.config.js", ".hardhat.config.ts")) or \
                 os.path.exists(os.path.join(p, "hardhat.config.js")) or \
                 os.path.exists(os.path.join(p, "hardhat.config.ts"))
        has_sol = has_file_ext(p, (".sol",))
        try:
            last_write = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            last_write = "unknown"
    else:
        size_b = 0
        has_git = has_nm = has_foundry = has_hh = has_sol = False
        last_write = "n/a"
    info = {
        "path": p,
        "exists": exists,
        "size_bytes": size_b,
        "size_mb": round(size_b / 1e6, 1),
        "size_gb": round(size_b / 1e9, 3),
        "last_write": last_write,
        "has_git": has_git,
        "has_node_modules": has_nm,
        "has_foundry": has_foundry,
        "has_hardhat": has_hh,
        "has_solidity": has_sol,
        "protected": is_protected(p),
    }
    rec_class, rec_reason = classify(info)
    info["recommendation"] = rec_class
    info["reason"] = rec_reason
    records.append(info)
    size_str = f"{info['size_gb']:.2f}GB" if info['size_gb'] >= 0.1 else f"{info['size_mb']:.0f}MB"
    print(f" {size_str} -> {rec_class}")

# Filter only existing
existing = [r for r in records if r["exists"]]
safe = [r for r in existing if r["recommendation"] == "SAFE_TO_DELETE_CANDIDATE"]
review = [r for r in existing if r["recommendation"] == "REVIEW_REQUIRED"]
skip = [r for r in records if not r["exists"]]

total_safe_bytes = sum(r["size_bytes"] for r in safe)
total_review_bytes = sum(r["size_bytes"] for r in review)

# ── WRITE JSON ────────────────────────────────────────────────────────────────
json_path = SANDBOX / f"dev_disk_cleanup_audit_forks_inventory_{DATE_TAG}.json"
with json_path.open("w", encoding="utf-8") as f:
    json.dump({
        "generated": datetime.now().isoformat(),
        "total_candidates": len(records),
        "existing": len(existing),
        "safe_to_delete_candidates": len(safe),
        "review_required": len(review),
        "not_found": len(skip),
        "total_reclaimable_safe_gb": round(total_safe_bytes / 1e9, 2),
        "total_review_gb": round(total_review_bytes / 1e9, 2),
        "records": existing,
    }, f, indent=2, default=str)
print(f"\nJSON written: {json_path}")

# ── WRITE INVENTORY MD ───────────────────────────────────────────────────────
md_path = SANDBOX / f"dev_disk_cleanup_audit_forks_inventory_{DATE_TAG}.md"
lines = []
lines.append("# DEV DISK CLEANUP — AUDIT FORKS INVENTORY")
lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append("")
lines.append("## SUMMARY")
lines.append(f"- Candidates scanned: {len(records)}")
lines.append(f"- Existing folders: {len(existing)}")
lines.append(f"- SAFE_TO_DELETE_CANDIDATE: **{len(safe)}** folders, "
             f"**{total_safe_bytes/1e9:.2f} GB** total")
lines.append(f"- REVIEW_REQUIRED: **{len(review)}** folders, "
             f"**{total_review_bytes/1e9:.2f} GB** total")
lines.append(f"- Not found / already deleted: {len(skip)}")
lines.append("")
lines.append("---")

for section, title in [(safe, "SAFE_TO_DELETE_CANDIDATE"), (review, "REVIEW_REQUIRED")]:
    lines.append(f"\n## {title}")
    lines.append("| Path | Size | LastWrite | .git | node_modules | foundry | Reason |")
    lines.append("|---|---:|---|:---:|:---:|:---:|---|")
    for r in sorted(section, key=lambda x: x["size_bytes"], reverse=True):
        sz = f"{r['size_gb']:.2f} GB" if r['size_gb'] >= 0.1 else f"{r['size_mb']:.0f} MB"
        lines.append(
            f"| {r['path']} | {sz} | {r['last_write']} | "
            f"{'✓' if r['has_git'] else ''} | "
            f"{'✓' if r['has_node_modules'] else ''} | "
            f"{'✓' if r['has_foundry'] else ''} | "
            f"{r['reason'][:120]} |"
        )

lines.append("\n## NOT FOUND (paths do not exist)")
for r in skip:
    lines.append(f"- {r['path']}")

md_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Inventory MD written: {md_path}")

# ── TOP LARGE FOLDERS REPORT ──────────────────────────────────────────────────
top_path = SANDBOX / f"dev_disk_cleanup_top_large_folders_{DATE_TAG}.md"
top_lines = []
top_lines.append("# DEV DISK CLEANUP — TOP LARGE FOLDERS")
top_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
top_lines.append("")
top_lines.append("## Top 30 Largest Candidate Folders (sorted by size)")
top_lines.append("| Rank | Path | Size | LastWrite | Recommendation |")
top_lines.append("|---:|---|---:|---|---|")
for i, r in enumerate(sorted(existing, key=lambda x: x["size_bytes"], reverse=True)[:30], 1):
    sz = f"{r['size_gb']:.2f} GB" if r['size_gb'] >= 0.1 else f"{r['size_mb']:.0f} MB"
    top_lines.append(f"| {i} | {r['path']} | {sz} | {r['last_write']} | {r['recommendation']} |")

top_path.write_text("\n".join(top_lines), encoding="utf-8")
print(f"Top large folders MD written: {top_path}")

# ── CLEANUP PLAN ──────────────────────────────────────────────────────────────
plan_path = SANDBOX / f"dev_disk_cleanup_plan_{DATE_TAG}.md"
plan_lines = []
plan_lines.append("# DEV DISK CLEANUP PLAN")
plan_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
plan_lines.append("")
plan_lines.append("> **⚠️ NO DELETIONS PERFORMED.** This is a plan only. Human approval required.")
plan_lines.append("")
plan_lines.append("## Estimated Reclaimable Space")
plan_lines.append(f"- SAFE_TO_DELETE total: **{total_safe_bytes/1e9:.2f} GB**")
plan_lines.append(f"- REVIEW_REQUIRED total: **{total_review_bytes/1e9:.2f} GB**")
plan_lines.append(f"- Maximum possible reclaim: **{(total_safe_bytes+total_review_bytes)/1e9:.2f} GB**")
plan_lines.append("")
plan_lines.append("## Protected Folders (NEVER TOUCH)")
for p in sorted(PROTECTED):
    plan_lines.append(f"- {p}")
plan_lines.append("")
plan_lines.append("## Folders Recommended for Deletion (SAFE_TO_DELETE_CANDIDATE)")
plan_lines.append("")
for r in sorted(safe, key=lambda x: x["size_bytes"], reverse=True):
    sz = f"{r['size_gb']:.2f} GB" if r['size_gb'] >= 0.1 else f"{r['size_mb']:.0f} MB"
    plan_lines.append(f"### {r['path']}")
    plan_lines.append(f"- Size: {sz}")
    plan_lines.append(f"- Last modified: {r['last_write']}")
    plan_lines.append(f"- Reason: {r['reason']}")
    plan_lines.append(f"- Delete command: `Remove-Item -Recurse -Force \"{r['path']}\"`")
    plan_lines.append("")
plan_lines.append("## Folders Requiring Human Review")
plan_lines.append("")
for r in sorted(review, key=lambda x: x["size_bytes"], reverse=True):
    sz = f"{r['size_gb']:.2f} GB" if r['size_gb'] >= 0.1 else f"{r['size_mb']:.0f} MB"
    plan_lines.append(f"- **{r['path']}** | {sz} | {r['reason'][:100]}")
plan_lines.append("")
plan_lines.append("## PowerShell Batch Delete Commands (SAFE_TO_DELETE_CANDIDATE only)")
plan_lines.append("```powershell")
plan_lines.append("# Run ONLY after confirming inventory above")
plan_lines.append("# Recommended: quarantine first, then delete")
for r in sorted(safe, key=lambda x: x["size_bytes"], reverse=True):
    plan_lines.append(f"Remove-Item -Recurse -Force \"{r['path']}\"")
plan_lines.append("```")
plan_lines.append("")
plan_lines.append("## ⚠️ ROLLBACK WARNING")
plan_lines.append("- `Remove-Item` is **permanent**. There is no Recycle Bin for recursive folder deletes from PowerShell.")
plan_lines.append("- **Recommended approach**: Move to quarantine folder first (see quarantine script), verify, then delete.")
plan_lines.append("- Quarantine location: `C:\\_cleanup_quarantine\\audit_forks_20260609\\`")

plan_path.write_text("\n".join(plan_lines), encoding="utf-8")
print(f"Cleanup plan MD written: {plan_path}")

# ── QUARANTINE SCRIPT ─────────────────────────────────────────────────────────
qs_path = SANDBOX / f"quarantine_old_audit_forks_{DATE_TAG}.ps1"
qs_lines = []
qs_lines.append("# QUARANTINE SCRIPT — OLD AUDIT FORKS")
qs_lines.append("# Generated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
qs_lines.append("# DO NOT RUN without explicit approval from Toti.")
qs_lines.append("# This script MOVES folders to quarantine — does NOT delete.")
qs_lines.append("")
qs_lines.append('$ErrorActionPreference = "Stop"')
qs_lines.append('$quarantine = "C:\\_cleanup_quarantine\\audit_forks_20260609"')
qs_lines.append('$log = "C:\\_cleanup_quarantine\\quarantine_log_20260609.txt"')
qs_lines.append('New-Item -ItemType Directory -Path $quarantine -Force | Out-Null')
qs_lines.append('Add-Content $log "--- Quarantine run: $(Get-Date) ---"')
qs_lines.append("")
qs_lines.append("# PROTECTED PATHS — skip these always")
qs_lines.append("$protected = @(")
for p in sorted(PROTECTED):
    qs_lines.append(f'  "{p}",')
qs_lines.append("  'SENTINEL'")
qs_lines.append(")")
qs_lines.append("")
qs_lines.append("function Move-ToQuarantine($src) {")
qs_lines.append("  foreach ($p in $protected) {")
qs_lines.append("    if ($src.ToLower() -eq $p.ToLower() -or $src.ToLower().StartsWith($p.ToLower() + '\\')) {")
qs_lines.append('      Write-Host "SKIP (protected): $src" -ForegroundColor Yellow')
qs_lines.append('      Add-Content $log "SKIP (protected): $src"')
qs_lines.append("      return")
qs_lines.append("    }")
qs_lines.append("  }")
qs_lines.append("  if (-not (Test-Path $src)) {")
qs_lines.append('    Write-Host "SKIP (not found): $src" -ForegroundColor DarkGray')
qs_lines.append("    return")
qs_lines.append("  }")
qs_lines.append("  $dest = Join-Path $quarantine ([IO.Path]::GetFileName($src))")
qs_lines.append("  Write-Host \"Moving: $src -> $dest\"")
qs_lines.append("  try {")
qs_lines.append("    Move-Item -Path $src -Destination $dest -ErrorAction Stop")
qs_lines.append('    Add-Content $log "MOVED: $src -> $dest"')
qs_lines.append('    Write-Host "OK: $src" -ForegroundColor Green')
qs_lines.append("  } catch {")
qs_lines.append('    Write-Host "ERROR moving $src : $_" -ForegroundColor Red')
qs_lines.append('    Add-Content $log "ERROR: $src : $_"')
qs_lines.append("    throw")
qs_lines.append("  }")
qs_lines.append("}")
qs_lines.append("")
qs_lines.append("# SAFE_TO_DELETE_CANDIDATE folders to quarantine:")
for r in sorted(safe, key=lambda x: x["size_bytes"], reverse=True):
    qs_lines.append(f'Move-ToQuarantine "{r["path"]}"')
qs_lines.append("")
qs_lines.append('Add-Content $log "--- Quarantine run complete: $(Get-Date) ---"')
qs_lines.append('Write-Host "Quarantine complete. Log: $log" -ForegroundColor Cyan')

qs_path.write_text("\n".join(qs_lines), encoding="utf-8")
print(f"Quarantine script written: {qs_path}")

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"Safe-to-delete candidates: {len(safe)}")
print(f"Reclaimable (safe):        {total_safe_bytes/1e9:.2f} GB")
print(f"Review required:           {len(review)}")
print(f"Max reclaimable:           {(total_safe_bytes+total_review_bytes)/1e9:.2f} GB")
print("\nTop 10 by size:")
for i, r in enumerate(sorted(safe+review, key=lambda x: x["size_bytes"], reverse=True)[:10], 1):
    sz = f"{r['size_gb']:.3f} GB"
    print(f"  {i:2}. {r['path']:60s} {sz:>10}  [{r['recommendation']}]")
print(f"\nOutput files:")
print(f"  {json_path}")
print(f"  {md_path}")
print(f"  {top_path}")
print(f"  {plan_path}")
print(f"  {qs_path}")
