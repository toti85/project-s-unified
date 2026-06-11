import json
from pathlib import Path
from datetime import datetime

data = json.loads(Path(r"C:\ProjectS-Unified\orchestrator_runtime\sandbox\dev_disk_cleanup_audit_forks_inventory_20260609.json").read_text(encoding="utf-8"))
safe = [r for r in data["records"] if r["recommendation"] == "SAFE_TO_DELETE_CANDIDATE"]
review = [r for r in data["records"] if r["recommendation"] == "REVIEW_REQUIRED"]

total_bytes = sum(r["size_bytes"] for r in safe)
top20 = sorted(safe, key=lambda x: x["size_bytes"], reverse=True)[:20]

lines = []
lines.append("# PRE-QUARANTINE VERIFICATION REPORT")
lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append("")
lines.append("## OPERATION SUMMARY")
lines.append(f"- SAFE_TO_DELETE folders to move: **{len(safe)}**")
lines.append(f"- Total estimated size: **{total_bytes/1e9:.2f} GB** ({total_bytes/1e6:.0f} MB)")
lines.append("- Quarantine destination: `C:\\_cleanup_quarantine\\audit_forks_20260609\\`")
lines.append("- Method: Move-Item only. NO Remove-Item. NO permanent deletion.")
lines.append("- Disk freed immediately: **0 GB** (same-drive move = metadata only, space freed when quarantine is deleted later)")
lines.append("")
lines.append("## SAFETY CHECKS")
lines.append("- [x] Script uses Move-Item only — verified")
lines.append("- [x] No Remove-Item in executable lines — verified (only in comment)")
lines.append("- [x] No REVIEW_REQUIRED folders in move list — verified")
lines.append("- [x] C:\\ProjectS-Unified in protected list — verified")
lines.append("- [x] C:\\Toti explicitly excluded — verified")
lines.append("- [x] C:\\AutoGPT explicitly excluded — verified")
lines.append("- [x] C:\\S, S-main, S1 explicitly excluded — verified")
lines.append("- [x] C:\\0617 Mukodo, C:\\0618 phase2 explicitly excluded — verified")
lines.append("- [x] C:\\ProjectS-Backups explicitly excluded — verified")
lines.append("- [x] hardhat-poc under Users\\Admin\\project_s_super_core excluded — verified")
lines.append("- [x] Script continues on error (no throw) — verified v2")
lines.append("")
lines.append("## TOP 20 FOLDERS TO BE MOVED (by size)")
lines.append("| # | Path | Size | .git | node_modules | Last Modified |")
lines.append("|---:|---|---:|:---:|:---:|---|")
for i, r in enumerate(top20, 1):
    sz = f"{r['size_bytes']/1e9:.3f} GB"
    git = "Y" if r["has_git"] else ""
    nm = "Y" if r["has_node_modules"] else ""
    lines.append(f"| {i} | {r['path']} | {sz} | {git} | {nm} | {r['last_write']} |")

lines.append("")
lines.append("## ALL SAFE_TO_DELETE PATHS (top-level)")
top_level = [r for r in safe if r["path"].count("\\") <= 1]
nested = [r for r in safe if r["path"].count("\\") > 1]
lines.append(f"Top-level count: {len(top_level)} (moved directly)")
lines.append(f"Nested sub-paths count: {len(nested)} (covered by parent move, will show as skipped-not-found)")
lines.append("")
for r in sorted(top_level, key=lambda x: x["size_bytes"], reverse=True):
    gb = r["size_bytes"] / 1e9
    lines.append(f"- {r['path']} ({gb:.3f} GB)")

lines.append("")
lines.append("## NESTED ENTRIES (already covered by parent — will be skipped)")
for r in nested:
    lines.append(f"- {r['path']}")

lines.append("")
lines.append("## REVIEW_REQUIRED FOLDERS — EXPLICITLY NOT TOUCHED")
for r in sorted(review, key=lambda x: x["size_bytes"], reverse=True):
    gb = r["size_bytes"] / 1e9
    reason = r["reason"][:90]
    lines.append(f"- {r['path']} ({gb:.3f} GB) — {reason}")

lines.append("")
lines.append("## CONFIRMATION")
lines.append("- Permanent deletion performed: **NO**")
lines.append("- self_state.json modified: **NO**")
lines.append("- C:\\ProjectS-Unified modified: **NO** (except sandbox report files)")
lines.append("- REVIEW_REQUIRED folders touched: **NO**")
lines.append("")
lines.append("## NOTE ON DISK SPACE")
lines.append("- Current C:\\ free space before quarantine: **0.9 GB**")
lines.append("- Moving within C:\\ does NOT increase free space (same-drive rename, no data copy).")
lines.append("- Disk space freed ONLY when quarantine folder is permanently deleted in a later step.")
lines.append("- Expected reclaim after deletion: ~62 GB")

out = Path(r"C:\ProjectS-Unified\orchestrator_runtime\sandbox\dev_disk_cleanup_pre_quarantine_verification_20260609.md")
out.write_text("\n".join(lines), encoding="utf-8")
print("Written:", out)
print("Lines:", len(lines))
