# AO5_T11_5 — CWI Import Diagnostic

**Date:** 2026-06-10
**Status:** DIAGNOSTIC — READ ONLY, no modifications

## Root Cause

**bridge_runner.py sys.path does NOT include `src/` directory.**

### Evidence

1. **bridge_runner.py line 35:**
   ```python
   sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
   ```
   This adds `C:\ProjectS-Unified` (project root) to sys.path.

2. **CWI module location:**
   `src/core/cognitive_workflow_integration.py`

3. **CWI import statement (line 31):**
   ```python
   from core.cognitive import (
       cognitive_registry,
       ...
   )
   ```
   This requires `src/` to be in sys.path so that `core` is importable.

4. **Result:** When bridge_runner tries to import `core.cognitive_workflow_integration`, Python searches in `C:\ProjectS-Unified` but `core/` is in `C:\ProjectS-Unified\src/core/`. The module is not found.

## Fix

**TRIVIAL (1 line)**

Add `src/` to sys.path in bridge_runner.py, line 35:

```python
# Current:
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Fix:
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
```

Or add both:

```python
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
```

## Verification

After fix, the import chain works:
1. `from core.cognitive_workflow_integration import get_cognitive_workflow_integration` — finds `src/core/cognitive_workflow_integration.py`
2. CWI's own imports (`from core.cognitive import ...`) — finds `src/core/cognitive/__init__.py`
3. All 4 dependencies resolve correctly

## Should T11 be re-run after fix?

**Yes** — to verify CWI advisory executes successfully (not just IMPORT_FAILED).

## Files Modified

**NO** — this is diagnostic only.