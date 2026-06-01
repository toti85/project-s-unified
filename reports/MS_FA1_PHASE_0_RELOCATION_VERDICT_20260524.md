# MS-FA1 Phase 0 Relocation Verdict

**Date:** 2026-05-24  
**Version:** FA1.0-Relocation  
**Status:** Complete  
**Model Policy:** Quality-First (OpenRouter Qwen3.6 baseline)

---

## 1. Why MS-FA1 is Internal Project-S Layer

MS-FA1 is the filesystem automation pipeline that enables Project-S to draft tasks
and Cline to execute them in a controlled manual loop. It is an internal Project-S
layer because:

- It operates on Project-S goals and uses Project-S evaluation
- The orchestrator package (`src/orchestrator/`) is a first-class Project-S module
- Runtime data lives inside the Project-S workspace (`orchestrator_runtime/`)
- It is not a standalone external automation system

This architectural decision keeps the pipeline close to the codebase it serves,
enabling future integration with SAI and the interactive layer without cross-directory
boundaries.

---

## 2. Files Moved/Copied

| Source | Destination | Status |
|--------|-------------|--------|
| `C:\ProjectS-Automation\*` | `C:\ProjectS-Unified\orchestrator_runtime\` | Copied |
| `C:\ProjectS-Automation\README.md` | (deprecated marker) | Updated with relocation notice |

Old `C:\ProjectS-Automation\` preserved with deprecation marker.

---

## 3. New Folder Structure

### Runtime Data (`orchestrator_runtime/`)

```
C:\ProjectS-Unified\orchestrator_runtime\
├── README.md
├── verdict_schema.json
├── cline_inbox\
│   └── next_prompt.md
├── cline_outbox\
│   └── last_output.md
├── inbox\
│   └── goal.md
├── logs\
├── reports\
├── runs\
└── sandbox\
    └── SANDBOX_TASK_001.md
```

### Orchestrator Package (`src/orchestrator/`)

```
C:\ProjectS-Unified\src\orchestrator\
├── __init__.py
├── README.md
├── filesystem_orchestrator.py
├── state_machine.py
├── verdict_schema.py
├── cline_bridge.py
└── run_archive.py
```

---

## 4. New src/orchestrator Scaffold

| Module | Purpose | Status |
|--------|---------|--------|
| `__init__.py` | Package init, version 0.1.0 | Scaffold |
| `filesystem_orchestrator.py` | Goal/prompt lifecycle | Stubs with docstrings |
| `state_machine.py` | Run state transitions | Stubs + RunState enum + VALID_TRANSITIONS |
| `verdict_schema.py` | Verdict creation/validation | Stubs + VerdictStatus enum |
| `cline_bridge.py` | Prompt drafting/output parsing | Stubs with docstrings |
| `run_archive.py` | Run folder management | Stubs with docstrings |
| `README.md` | Package documentation | Complete |

**Python import smoke test:** PASS
```
Import OK: 0.1.0 scaffold
```

---

## 5. Path References Updated

| File | Old Path | New Path |
|------|----------|----------|
| `orchestrator_runtime/README.md` | `C:\ProjectS-Automation\` | `C:\ProjectS-Unified\orchestrator_runtime\` |
| `orchestrator_runtime/cline_inbox/next_prompt.md` | `C:\ProjectS-Automation\sandbox\` | `C:\ProjectS-Unified\orchestrator_runtime\sandbox\` |
| `orchestrator_runtime/sandbox/SANDBOX_TASK_001.md` | `C:\ProjectS-Automation\` | `C:\ProjectS-Unified\orchestrator_runtime\` |
| `src/orchestrator/*.py` | N/A (new files) | `RUNTIME_ROOT` points to `orchestrator_runtime/` |

---

## 6. Safety Check

| Check | Result |
|-------|--------|
| No production files modified (only docs/scaffold) | PASS |
| `src/core/` unchanged | PASS |
| `super_intelligent_ai.py` unchanged | PASS |
| No router/server config touched | PASS |
| No automation loop started | PASS |
| Python import smoke test | PASS |
| Git diff | N/A (not a git repo) |

---

## 7. Next Step: FA1.1 Manual Filesystem Loop

1. Human reviews `orchestrator_runtime/cline_inbox/next_prompt.md`
2. Human copies prompt to Cline
3. Cline executes SANDBOX_TASK_001 (works only in `orchestrator_runtime/sandbox/`)
4. Cline writes results to `orchestrator_runtime/cline_outbox/last_output.md`
5. Project-S evaluates, issues verdict
6. Run archived in `orchestrator_runtime/runs/FA1_001/`

---

## Phase 5 Report

| Item | Status |
|------|--------|
| **A. Runtime moved/copied?** | YES |
| **B. Old C:\ProjectS-Automation preserved/marked?** | YES (deprecation marker) |
| **C. src/orchestrator scaffold created?** | YES (7 files, import smoke PASS) |
| **D. Path references updated?** | YES (all docs point to new paths) |
| **E. SAI / interactive_layer unchanged?** | YES (no modifications to src/core/) |
| **F. Ready for FA1.1?** | YES |

---

**Document End**