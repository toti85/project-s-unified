# SAI REAL OUTPUT FIX REPORT
**Date:** 2026-04-30  
**Session:** SAI output delivery fix  
**Baseline:** SAI_REAL_OUTPUT_VALIDATION_20260430.md (Verdict: PARTIAL)  
**Final Verdict: PASS — 7/7 ground truth match**

---

## Executive Summary

The SAI pipeline previously returned `Status: True` but produced only a generic
wrapper string instead of actual execution results. Two root causes were
identified and four targeted code patches were applied. The live re-validation
confirmed **all 7 ground truth files returned in the output.**

---

## Before / After

| Metric | Before | After |
|--------|--------|-------|
| Status: True | ✅ | ✅ |
| Tool selected | `web_page_fetch` (wrong) | `directory_lister` (correct) |
| Output content | generic wrapper only | real file list |
| Ground truth match | 0/7 | **7/7** |
| Verdict | PARTIAL | **PASS** |

---

## Root Causes & Fixes

### Bug 1: Task classification — "list/recursively" not in file_search keywords
**File:** `tools/tools/registry/smart_orchestrator.py`  
**Function:** `_analyze_task()` ~L1047

**Problem:** Keywords `"list"`, `"recursively"`, `"recursive"`, `"*.py"`,
`"relative paths"`, `"directory"`, `"folder"` were absent from the `file_search`
keyword list. The task `"List all Python files...recursively..."` fell through to
`task_type = "general"` → `web_page_fetch` selected.

**Fix (Phase 1):** Added the keywords to the `file_search` branch.  
**Fix (Phase 2 — refinement):** Split into two separate task types:
- `"directory_listing"` — list/recursive/folder/directory keywords → `directory_lister` tool
- `"file_search"` — search/grep/containing keywords → `file_content_search` tool

This separation is semantically correct: listing ≠ content search.

---

### Bug 2: MetaController success return missing `"output"` field
**File:** `src/core/meta/meta_controller.py`  
**Function:** `run_goal()` success return ~L300

**Problem:** The `return` dict on success path had `"final_result"` but no
`"output"` field. The executor's file list was present but unlabeled.

**Fix:**
```python
# Added to success return dict:
"output": execution_result.get("output") or execution_result.get("result") or "",
"execution_result": execution_result,
```

---

### Bug 3: SAI MetaController branch discarded executor output
**File:** `src/core/super_intelligent_ai.py`  
**Function:** `execute_intelligent_task()` MetaController branch ~L387

**Problem:** The branch replaced real output with a hardcoded string:
```python
"output": f"[OK] MetaController completed goal in {meta_result.get('iterations', 1)} iterations"
```

**Fix:** Added fallback chain:
```python
output = (
    meta_result.get("output")
    or (meta_result.get("execution_result") or {}).get("output")
    or (meta_result.get("final_result") or {}).get("output")
    or f"[OK] MetaController completed goal in {meta_result.get('iterations', 1)} iterations"
)
```

---

### Bug 4: SAI strategic execution wrapper discarded tool output
**File:** `src/core/super_intelligent_ai.py`  
**Function:** `execute_intelligent_task()` strategic branch ~L524

**Problem:** The `execution_output` f-string only included `orchestration_result["final_output"]["summary"]`
(a one-liner) — actual tool results in `detailed_results` were ignored.

**Fix:** After building the strategic summary, extract real tool output from
`orchestration_result.final_output.detailed_results[].result.output` and use it
as the final output if non-empty.

---

### Bug 5: `directory_lister` not registered in `tool_registry_golden.py`
**File:** `tools/tools/registry/smart_orchestrator.py`  
**Function:** `_execute_single_tool()` not-found fallback

**Problem:** `DirectoryListerTool` exists in `tools/tools/file_tools.py` but
was never added to `tool_registry_golden.py`. The orchestrator's "not found"
branch discarded the request entirely.

**Fix:** Added direct-instantiation fallback specifically for `directory_lister`:
when the golden registry does not contain it, the tool is imported and executed
directly from `tools.tools.file_tools`.

---

## Files Modified

| File | Change |
|------|--------|
| `tools/tools/registry/smart_orchestrator.py` | ① keyword split (directory_listing), ② directory_lister in _select_tools, ③ directory_lister execution handler, ④ direct-instantiation fallback |
| `src/core/meta/meta_controller.py` | `"output"` + `"execution_result"` fields in success return |
| `src/core/super_intelligent_ai.py` | MetaController branch fallback chain + strategic branch real-output extraction |

---

## Tests Created

### `tests/test_sai_tool_selection_file_list.py` — 7/7 PASS
- `test_list_recursively_classified_as_file_search` — exact live task → `directory_listing`
- `test_list_keyword_triggers_file_search` — list/List/LIST → `directory_listing`
- `test_recursively_keyword_triggers_file_search` — recursively/recursive → `directory_listing`
- `test_py_glob_triggers_file_search` — `*.py` → `directory_listing`
- `test_directory_folder_keywords_trigger_file_search` — directory/folder → `directory_listing`
- `test_file_search_does_not_select_web_page_fetch` — web_page_fetch NOT selected; directory_lister IS selected
- `test_existing_keywords_still_work` — search/grep → `file_search` (no regression)

### `tests/test_sai_output_propagation.py` — 6/6 PASS (pure logic)
- `test_direct_output_field_propagated` — meta_result["output"] propagated
- `test_execution_result_output_propagated` — execution_result.output fallback
- `test_final_result_output_propagated` — final_result.output fallback
- `test_fallback_wrapper_when_no_output` — generic wrapper as last resort
- `test_output_priority_direct_over_execution_result` — priority ordering
- `test_failed_status_not_propagated` — failed status → success=False

---

## Live Validation Run

**Script:** `sai_valid2_run.py`  
**Log:** `sai_valid2d.log`  
**Task:** `"List all Python files in C:\ProjectS-Unified\witness recursively and return exact relative paths."`

### Output (actual):
```
witness\bridges\organism_to_meta.py
witness\bridges\state_reader.py
witness\bridges\__init__.py
witness\evidence_diagnostic.py
witness\evidence_reader.py
witness\learning_diagnostic.py
witness\__init__.py
```

### Match:
```
[FOUND]  witness\evidence_diagnostic.py
[FOUND]  witness\evidence_reader.py
[FOUND]  witness\learning_diagnostic.py
[FOUND]  witness\__init__.py
[FOUND]  witness\bridges\organism_to_meta.py
[FOUND]  witness\bridges\state_reader.py
[FOUND]  witness\bridges\__init__.py

GROUND TRUTH MATCH: 7/7
VERDICT: PASS — all 7 files found in output
```

---

## Design Notes

- All fixes are **minimal patches** — no refactoring, no architecture change
- The `directory_lister` direct fallback is intentionally scoped (only fires for that tool name)
- The `directory_listing` task type is additive (does not remove `file_search`)
- Output priority chain in SAI MetaController branch is deterministic (direct > execution_result > final_result > generic)
- The golden registry still does not contain `directory_lister` — the fallback is the correct minimal fix until a proper registration is added

---

## Status

| Item | Status |
|------|--------|
| Tool selection fix | ✅ DONE |
| Output propagation fix | ✅ DONE |
| Regression tests | ✅ 13/13 PASS |
| Live validation | ✅ 7/7 PASS |
| Report | ✅ THIS DOCUMENT |
