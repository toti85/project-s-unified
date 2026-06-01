# MS-FA1 CLI Entrypoint Fix

**Date:** 2026-05-26
**Version:** FA1-CLI-Fix
**Status:** COMPLETE
**Verdict:** PASS

---

## Problem

`python -m orchestrator.cli` failed with `No module named orchestrator.cli` because `cli.py` did not exist.

## Solution

Created `src/orchestrator/cli.py` and `src/orchestrator/__main__.py`.

---

## Created Files

### src/orchestrator/cli.py

CLI entrypoint with 3 commands:

| Command | Description |
|---------|-------------|
| `--help` | Show help |
| `list-runs` | List all runs |
| `status` | Show latest run status + verdict |
| `run-loop --auto --max-iterations N --timeout S` | Execute a run loop |

**Reuses existing modules:**
- `FilesystemOrchestrator` — goal reading, run creation, prompt drafting, output evaluation, verdict issuance, archiving
- `HandoffWatcher` — handoff signal preparation
- `run_archive` — run listing, status
- `verdict_schema` — verdict loading

**Safety:**
- No automatic Cline invocation
- No UI automation
- Stops safely if Cline output not available (prints WAITING_FOR_CLINE)
- Prints clear operator instructions

### src/orchestrator/__main__.py

Module runner for `python -m orchestrator.cli`.

---

## Validation Results

### --help
```
usage: orchestrator.cli [-h] {list-runs,status,run-loop} ...
MS-FA1 Filesystem Orchestration Pipeline CLI
```
**Result:** PASS

### list-runs
```
Run ID       Status          Goal (truncated)
----------------------------------------------------------------------
FA1_001      unknown
FA1_002      unknown
FA1_003      unknown
FA1_004      unknown
Total: 4 run(s)
```
**Result:** PASS

### status
```
Latest run: FA1_005
Status: ARCHIVED
Verdict: PASS
Confidence: 1.0
Summary: Heuristic evaluation: PASS (confidence 1.00)
```
**Result:** PASS

### run-loop --auto --max-iterations 2 --timeout 5
```
============================================================
MS-FA1 Run Loop
============================================================

Goal: CLI test goal: verify run-loop works...
Acceptance criteria: 2
Constraints: 0

Run ID: FA1_005

Drafting prompt...
Prompt drafted (739 chars)
  -> C:\ProjectS-Unified\orchestrator_runtime\cline_inbox\next_prompt.md

Preparing handoff signal...
  -> C:\ProjectS-Unified\orchestrator_runtime\cline_inbox\prompt_ready.json

Waiting for Cline output (timeout: 5s)...

INSTRUCTIONS FOR OPERATOR:
  1. Copy the prompt from: ...
  2. Paste it into Cline
  3. Cline should write output to: ...
  4. Cline should also create: ...

Cline output received!
  Length: 693 chars

Evaluating output...
  Verdict: PASS
  Confidence: 1.00
  Summary: Heuristic evaluation: PASS (confidence 1.00)

Run archived.
```
**Result:** PASS

---

## Generated Files

| File | Generated | Size |
|------|-----------|------|
| `orchestrator_runtime/cline_inbox/next_prompt.md` | YES | 769 bytes |
| `orchestrator_runtime/cline_inbox/prompt_ready.json` | YES | 174 bytes |
| `orchestrator_runtime/runs/FA1_005/` | YES | Full run folder |

---

## Fallback Behavior

When `OPENROUTER_API_KEY` is not set:
- AI prompt drafting → falls back to deterministic template ✓
- AI evaluation → falls back to heuristic evaluator ✓
- Both fallbacks work correctly ✓

---

## Report Answers

| Question | Answer |
|----------|--------|
| A. cli.py created? | **YES** |
| B. --help works? | **YES** |
| C. list-runs works? | **YES** |
| D. run-loop starts? | **YES** |
| E. next_prompt.md generated? | **YES** (769 bytes) |
| F. prompt_ready.json generated? | **YES** (174 bytes) |
| G. current state after run-loop | **ARCHIVED** (FA1_005, PASS verdict) |
| H. report created? | **YES** |

---

**Document End**