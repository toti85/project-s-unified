# SERVER PHASE 2 - TRANSFER SCOPE AUDIT AND RETRY PLAN

**Date:** 2026-05-18
**Target:** SHAYANSKA-DL380 (192.168.1.180)
**Audit Type:** Transfer Scope Analysis + Revised Plan

---

## 1. WHY WAS THE FIRST TRANSFER 520 MB?

The original transfer included 1062 files totaling 520.55 MB because it used broad exclude patterns that missed several large categories:

| Category | Size | Files | Included? |
|----------|------|-------|-----------|
| ZIP archives (LunX.zip, Delta-Android-*.zip) | 238.66 MB | 8 | YES (not excluded) |
| meta_evidence.jsonl (4 files) | 104.97 MB | 4 | YES (not excluded) |
| Bounty/audit directories | 2.76 MB | 124 | YES (not excluded) |
| SQLite/DB files | 0.27 MB | 2 | YES (not excluded) |
| Browser caches | 0.74 MB | 16 | YES (not excluded) |
| Code + docs (Python, MD, JSON, etc.) | ~173 MB | ~708 | YES (needed) |
| **TOTAL** | **520.55 MB** | **1062** | |

**Root cause:** The exclude patterns only covered `.git`, `__pycache__`, `*.pyc`, `.pytest_cache`, `.vscode`, `*.exe`, `*.apk`, `*.rbxm`, `*.rbxl`, `node_modules`, `.benchmarks`, `*.log`. Large ZIP archives, JSONL evidence files, and audit directories were not excluded.

---

## 2. WERE BOUNTY/AUDIT MATERIALS INCLUDED?

**YES** - 124 files, 2.76 MB found in bounty/audit directories:
- `memory/bounty_audits/` - Contains audit PDFs, analysis files
- `audits/` - Contains audit reports

---

## 3. WERE meta_evidence.jsonl OR LARGE REPORTS INCLUDED?

**YES** - meta_evidence.jsonl: 4 files, 104.97 MB in `memory/intelligence/`
- `meta_evidence.jsonl` is the largest single category

**YES** - Large reports in `reports/` directory: 81 files included

---

## 4. RECOMMENDED REVISED TRANSFER SIZE AND FILE COUNT

| Metric | Original | Revised (Minimal) | Reduction |
|--------|----------|-------------------|-----------|
| Files | 1062 | 789 | 26% |
| Size | 520.55 MB | 172.03 MB | 67% |

---

## 5. SHOULD PARTIAL SERVER FOLDER BE DELETED BEFORE RETRY?

**YES** - The current `C:\ProjectS\project-s-code` on the server contains only 1 empty directory (API/). It should be cleaned before retry to avoid confusion.

---

## 6. EXACT REVISED INCLUDE/EXCLUDE RULES

### INCLUDE:
- `src/` - Core source code
- `tools/` - Utility tools
- `interactive_layer/` - Interactive layer code
- `project_s/` - Project S code (if imported)
- `config/` - Configuration files
- `scripts/` - Bootstrap scripts
- `tests/` - Test files
- `tests_invariant_violation_poc.rs` - Test code
- `requirements*.txt` - Python dependencies
- `foundry.toml` - Foundry config
- `self_state.json` - Runtime state
- `PROJECT_S_OVERVIEW.md` - Project overview
- `PROJECT_S_STATUS_AND_JOURNAL.md` - Status journal
- `DECISIONS.md` - Key decisions
- `COMPONENT_INVENTORY.md` - Architecture docs
- `CI_GATE_CONFIG.md` - CI config
- `README.md` - Documentation
- `*.py`, `*.ps1`, `*.sol`, `*.ts`, `*.js`, `*.lua`, `*.yaml`, `*.yml`, `*.json`, `*.toml` - Source files
- `memory/telemetry/` - Runtime telemetry
- `memory/intelligence/strategic_decisions.md` - Strategic decisions
- `logs/` - Server logs
- `reports/` - Migration reports

### EXCLUDE:
- `*.zip` - ZIP archives (238.66 MB savings)
- `*meta_evidence*` - JSONL evidence files (104.97 MB savings)
- `*audits*` directories - Audit materials (2.76 MB)
- `*bounty*` directories - Bounty materials
- `*.db`, `*.sqlite`, `*.sqlite3` - Database files
- `*.png`, `*.jpg`, `*.jpeg`, `*.gif` - Image files
- `*.exe`, `*.apk`, `*.msi` - Installers
- `*.rbxl`, `*.rbxm`, `*.rbxlx` - Roblox assets
- `*.csv` - CSV data files
- `*.lock` - Lock files
- `*.bak`, `*.bak_cleanup` - Backup files
- `*.html` - HTML files (except key ones)
- `*.pdf` - PDF files
- `*.pkl` - Pickle files
- `*browser_automation_report*` - Old browser reports
- `*ultra_optimized*` - Old optimization reports
- `*test_output*`, `*debug_output*`, `*d_output*`, `*e_output*` - Test outputs
- `*qwen_full_run*`, `*strategic_output*`, `*test_strategic*` - Run outputs
- `*benchmarks*` - Benchmark directories
- `.git`, `__pycache__`, `*.pyc`, `.pytest_cache`, `.vscode`, `node_modules` - Standard excludes

---

## 7. READY TO RETRY TRANSFER?

**YES** - After cleaning the server staging directory and applying the revised exclude rules.

---

## 8. TRANSFER MANIFEST

See: `reports/SERVER_PHASE_2_REVISED_TRANSFER_MANIFEST_20260518.txt`

---

## ANSWERS TO REQUIRED QUESTIONS

| Question | Answer |
|----------|--------|
| A. Why was the first transfer 520 MB? | ZIP archives (238 MB) + meta_evidence.jsonl (105 MB) + bounty/audit dirs (3 MB) + code (174 MB) |
| B. Were bounty/audit materials included? | YES - 124 files, 2.76 MB |
| C. Were meta_evidence.jsonl or large reports included? | YES - 4 files, 104.97 MB |
| D. Recommended revised transfer size and file count | 172 MB, 789 files |
| E. Should partial server folder be deleted before retry? | YES |
| F. Exact revised include/exclude rules | See Section 6 above |
| G. Ready to retry transfer? | YES |