# GAP_022 — Evaluator JSON Serialization Fix Verdict

**Date:** 2026-05-14
**GAP ID:** GAP_022
**Title:** Evaluator cannot serialize browser_use AgentHistoryList — TypeError in evaluate_execution_result
**Status:** RESOLVED

---

## 1. Root Cause

### Exact Failure Path

During the browser external mission rerun, the `browser_use` library returned an `AgentHistoryList` object as part of the execution result. The evaluator's `_build_evaluation_prompt()` method called `json.dumps(execution_result, indent=2)` to embed the result in the evaluation prompt. Since `AgentHistoryList` is not JSON-serializable, this raised:

```
TypeError: Object of type AgentHistoryList is not JSON serializable
```

### Where AgentHistoryList Enters the Payload

The `browser_automation` tool (via `browser_use`) returns execution results that include `AgentHistoryList` objects containing the browser session history. These objects are passed through the SmartToolOrchestrator to the evaluator's `evaluate_execution_result()` method, which calls `_build_evaluation_prompt()` with the raw execution result.

### Scope

The issue is not limited to `browser_use.AgentHistoryList`. Any tool that returns a non-JSON-serializable object (custom classes, dataclasses without `asdict()`, etc.) would trigger the same failure. The fix is general-purpose.

---

## 2. Implementation Approach

### Files Changed

| File | Change |
|------|--------|
| `src/core/evaluator.py` | Added `_sanitize_for_json()` helper method (12 lines) |
| `src/core/evaluator.py` | Added `_safe_json_serialize()` helper method (8 lines) |
| `src/core/evaluator.py` | Modified `_build_evaluation_prompt()` to sanitize execution_result and context before `json.dumps` |
| `tests/test_gap_022_json_serialize.py` | New test file with 16 focused tests |

### Implementation Details

**`_sanitize_for_json(obj)`** — Recursively walks dicts and lists, testing each leaf value for JSON serializability. If a value cannot be serialized (detected via `json.dumps(obj)` try), it is converted to a string in the format:

```
[non-serializable: TypeName] actual_string_representation[:500]
```

This preserves:
- All serializable data unchanged
- Type information of the non-serializable object
- Up to 500 characters of the object's string representation

**`_safe_json_serialize(obj, default=str)`** — Alternative one-shot serializer that catches TypeError/ValueError and falls back to `str(obj)`. Used as a secondary utility.

**Integration point:** In `_build_evaluation_prompt()`, both `execution_result` and `context` are sanitized before being passed to `json.dumps()`:

```python
safe_execution_result = self._sanitize_for_json(execution_result)
safe_context = self._sanitize_for_json(context or {})
```

---

## 3. Tests Added and Results

**File:** `tests/test_gap_022_json_serialize.py`
**Total tests:** 16
**Result:** 16/16 PASSED

### Test Categories

| Category | Tests | Purpose |
|----------|-------|---------|
| `TestSanitizeForJson` | 9 | Core sanitization: non-serializable leaves, nested dicts, normal data unchanged, truncation |
| `TestBuildEvaluationPromptWithSanitization` | 3 | Full prompt building with AgentHistoryList in execution_result and context |
| `TestSafeJsonSerialize` | 3 | One-shot serialization helper |
| `TestEndToEndEvaluationPath` | 1 | End-to-end: sanitize → build prompt → json.dumps succeeds |

### Key Test Cases

1. **test_dict_with_non_serializable_leaf** — AgentHistoryList inside dict → converted to string
2. **test_list_with_non_serializable_item** — AgentHistoryList inside list → converted to string
3. **test_nested_dict_with_non_serializable** — Deep nesting handled correctly
4. **test_normal_dict_unchanged** — Normal JSON data passes through unmodified
5. **test_normal_list_unchanged** — Normal JSON list passes through unmodified
6. **test_string_value_preserved** — String values unchanged
7. **test_number_values_preserved** — Numeric values unchanged
8. **test_bool_and_none_preserved** — Boolean and None unchanged
9. **test_truncation_of_long_repr** — Long reprs truncated to 500 chars
10. **test_prompt_builds_with_agent_history_list** — Full prompt builds without TypeError
11. **test_prompt_builds_with_normal_result** — Normal results still work
12. **test_prompt_builds_with_context_containing_non_serializable** — Context sanitized too
13. **test_evaluation_path_no_typeerror_with_agent_history** — End-to-end path completes

---

## 4. Verification

### Unit Test Verification
- **16/16 tests PASS** in `tests/test_gap_022_json_serialize.py`
- Execution time: 0.73s

### Integration Verification
The fix was verified through the unit test `test_prompt_builds_with_agent_history_list` which simulates the exact scenario that was failing:
- execution_result contains `AgentHistoryList` (mimicking browser_use output)
- `_build_evaluation_prompt()` is called
- `json.dumps()` is invoked on the sanitized result
- No TypeError is raised
- The sanitized AgentHistoryList appears in the prompt as `[non-serializable: AgentHistoryList] AgentHistoryList(2 items)`

### No Regression on Existing Functionality
- Normal JSON-native execution results (dicts, lists, strings, numbers, booleans, None) pass through unchanged
- The `_truncate_for_prompt()` helper (GAP_016) continues to work independently
- The truthfulness fixes from GAP_020 are not affected (they operate at a different layer)

---

## 5. Impact Assessment

### What This Fix Does NOT Change
- Web search outputs — unaffected
- Synthesis outputs — unaffected
- Truthfulness `success/partial/failure` logic — unaffected
- Existing report generation — unaffected
- Browser automation tool behavior — unchanged

### What This Fix Does Change
- The evaluator's `_build_evaluation_prompt()` now sanitizes execution results before JSON serialization
- Non-serializable objects are converted to descriptive strings
- The evaluator's AI assessment step will no longer be skipped due to TypeError

---

## 6. Verdict

**GAP_022: RESOLVED**

The evaluator JSON serialization issue is fully resolved. The fix is:
- **Surgical:** 20 lines of new code in one file
- **Test-backed:** 16 focused tests, all passing
- **Non-breaking:** Normal JSON data passes through unchanged
- **General-purpose:** Handles any non-serializable object, not just AgentHistoryList

---

## 7. Documentation Updates Required

The following documents should be updated to reflect GAP_022 as RESOLVED:
- `self_state.json` — gaps_summary: resolved=21, active=0
- `PROJECT_S_OVERVIEW.md` — gap counts updated
- `PROJECT_S_STATUS_AND_JOURNAL.md` — brief mention of GAP_022 closure
- `PROJECT_S_20260514_EXTERNAL_MISSION_MILESTONE.md` — final gap state

---

**Készítette:** Cline
**Dátum:** 2026-05-14
**Verzió:** v1.0