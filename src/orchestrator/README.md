# src.orchestrator — MS-FA1 Internal Orchestrator

**Version:** 0.1.0 (Scaffold)  
**Status:** Skeleton only — no deep logic yet

---

## Overview

This package implements the internal Project-S orchestrator layer for
filesystem-based task automation between Project-S and Cline.

## Modules

| Module | Responsibility |
|--------|----------------|
| `filesystem_orchestrator.py` | Goal/prompt lifecycle management |
| `state_machine.py` | Run state transitions and tracking |
| `verdict_schema.py` | Verdict creation, validation, and storage |
| `cline_bridge.py` | Prompt drafting and output parsing for Cline |
| `run_archive.py` | Run folder creation, archiving, and retrieval |

## Runtime Data

All runtime filesystem data lives in:
```
C:\ProjectS-Unified\orchestrator_runtime\
```

## Design Document

See: `reports/MS_FA1_FILESYSTEM_AUTOMATION_PIPELINE_DESIGN_20260524.md`

## Current Status

- [x] Package scaffold created
- [x] Module stubs with docstrings
- [ ] Filesystem orchestrator logic
- [ ] State machine implementation
- [ ] Verdict validation
- [ ] Cline bridge
- [ ] Run archiving

## Next Step

FA1.1: Manual filesystem loop with sandbox task execution.