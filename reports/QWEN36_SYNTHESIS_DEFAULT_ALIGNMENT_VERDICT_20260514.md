# Qwen3.6 Synthesis Default Alignment — Verdict Report
**Date:** 2026-05-14  
**Mission type:** Runtime model-policy alignment fix + live verification  
**Status: VERIFIED COMPLETE**

---

## 1. Problem Statement

Post-positioning reconciliation (2026-05-14) identified a **model-policy drift**:
- `self_state.json` and all documentation stated `qwen/qwen3.6-35b-a3b` as synthesis default
- `smart_orchestrator.py` line 1397 hard-coded `"openai/gpt-4o-mini"` as the actual runtime fallback
- Result: standard launchers that did not set `_synthesis_model_override` silently used gpt-4o-mini

---

## 2. Code Fix

**File:** `tools/tools/registry/smart_orchestrator.py`

| Location | Before | After |
|----------|--------|-------|
| Comment (line ~1311) | `"If None, falls back to default \"openai/gpt-4o-mini\" via OpenRouter."` | `"If None, falls back to default \"qwen/qwen3.6-35b-a3b\" via OpenRouter."` |
| Fallback value (line ~1397) | `or "openai/gpt-4o-mini"` | `or "qwen/qwen3.6-35b-a3b"` |

Override behavior **unchanged**: `_synthesis_model_override` still wins when explicitly set. Explicit override remains supported in `run_qwen_full.py`, `run_opportunity_scan.py`, and any future launcher.

---

## 3. Test Results — 14/14 PASS

**File:** `tests/test_gap_019_synthesis.py`

Three new tests added in class `TestSynthesisModelSelection`:

| Test | Result |
|------|--------|
| `test_no_override_uses_qwen36_default` | **PASS** — `_synthesis_model_override=None` → `qwen/qwen3.6-35b-a3b` selected |
| `test_explicit_override_wins` | **PASS** — override `openai/gpt-4o-mini` beats default |
| `test_override_reset_restores_default` | **PASS** — resetting override to `None` restores `qwen/qwen3.6-35b-a3b` |

**Full suite (14/14):**
```
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_triggers_for_web_search_plus_report_keyword PASSED
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_triggers_for_write_keyword PASSED
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_triggers_for_recommendation_keyword PASSED
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_no_trigger_without_web_markers PASSED
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_no_trigger_for_plain_write_task PASSED
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_no_trigger_keyword_but_no_web_data PASSED
tests/test_gap_019_synthesis.py::TestIsSynthesisTask::test_no_trigger_web_data_but_no_report_keyword PASSED
tests/test_gap_019_synthesis.py::TestSynthesisPassedToFileWriter::test_synthesized_markdown_is_written PASSED
tests/test_gap_019_synthesis.py::TestNoSynthesisForPlainTasks::test_plain_write_skips_synthesis PASSED
tests/test_gap_019_synthesis.py::TestSynthesisFailureFallback::test_failure_writes_partial_fallback PASSED
tests/test_gap_019_synthesis.py::TestSynthesisFailureFallback::test_failure_does_not_silently_pass_raw_dump_as_synthesized PASSED
tests/test_gap_019_synthesis.py::TestSynthesisModelSelection::test_no_override_uses_qwen36_default PASSED
tests/test_gap_019_synthesis.py::TestSynthesisModelSelection::test_explicit_override_wins PASSED
tests/test_gap_019_synthesis.py::TestSynthesisModelSelection::test_override_reset_restores_default PASSED

14 passed in 12.04s
```

---

## 4. Live Smoke Verification — PASS

**Launcher:** `run_smoke_qwen36_default.py`  
**`_synthesis_model_override`:** `None` (not set — relying solely on code default)

### Run result

| Field | Value |
|-------|-------|
| SAI success | True |
| Elapsed | 42.7s |
| Iterations | 1 |
| Tool sequence | `[web_search, file_writer]` |
| Output file | `reports/QWEN_DEFAULT_SYNTHESIS_SMOKE_20260514.md` (3480 bytes) |
| Section score | **5/5** |
| Final verdict | **PASS** |
| Evaluator event | `evaluation.success` |

### Critical log lines (confirmed from run output)

```
INFO [tools.tools.registry.smart_orchestrator] GAP_019: Web research report detected — running synthesis step
INFO [tools.tools.registry.smart_orchestrator] GAP_019: Synthesis model → qwen/qwen3.6-35b-a3b
INFO [tools.tools.registry.smart_orchestrator] ✅ GAP_019: Synthesis complete — 3457 chars
INFO [core.infrastructure.event_bus] Publishing event: evaluation.success
```

### Section check results

| Section | Result |
|---------|--------|
| `## Executive Summary` | PASS |
| `## Key Findings` | PASS |
| `## Recommendation` | PASS |
| `## Sources` | PASS |
| Non-empty content (>300 chars) | PASS |

---

## 5. Summary

**A. Files changed:**
- `tools/tools/registry/smart_orchestrator.py` — synthesis fallback changed (comment + value)
- `tests/test_gap_019_synthesis.py` — 3 new model-selection tests added (14 total, all pass)
- `reports/QWEN_DEFAULT_SYNTHESIS_SMOKE_20260514.md` — live smoke output (3480 bytes, created by the pipeline itself)
- `self_state.json` — model_policy updated, what_i_am corrected, last_updated set
- `PROJECT_S_OVERVIEW.md` — model policy corrected
- `PROJECT_S_STATUS_AND_JOURNAL.md` — synthesis table row corrected

**B. Test results:** 14/14 PASS (including 3 new model-selection tests)

**C. Exact code diff:**
```
File: tools/tools/registry/smart_orchestrator.py
Line ~1311 (comment):
-  # If None, falls back to default "openai/gpt-4o-mini" via OpenRouter.
+  # If None, falls back to default "qwen/qwen3.6-35b-a3b" via OpenRouter.

Line ~1397 (synthesis_model fallback):
-  or "openai/gpt-4o-mini"
+  or "qwen/qwen3.6-35b-a3b"
```

**D. Live smoke verification:** PASS — `GAP_019: Synthesis model → qwen/qwen3.6-35b-a3b` confirmed in log. 5/5 sections, 3480 bytes, 42.7s, 1 iteration.

**E. Is Qwen3.6 now truly the runtime default?** **YES** — confirmed by unit tests (AIClient mock captures model string) and live mission log (GAP_019 line). Any launcher that does not set `_synthesis_model_override` will now use `qwen/qwen3.6-35b-a3b`.

**F. Docs/self_state updated?** YES — see files changed list above.
