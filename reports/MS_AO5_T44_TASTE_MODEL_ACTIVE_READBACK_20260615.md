# AO5_T44 — Taste Model Active Read-back
**Mission:** AO5_T44_TASTE_MODEL_ACTIVE_READBACK  
**Date:** 2026-06-15  
**Executor:** copilot (GitHub Copilot / Claude Sonnet 4.6)

---

## Files Modified

| File | Change | Lines added |
|---|---|---|
| `orchestrator_runtime/sz_prompt_generator.py` | Added `TASTE_MODEL_LOG` constant + `load_taste_model_summary()` helper + advisory injection in `render_prompt()` | +91 |

No other files were modified. No src/, no bridge_runner.py, no self_state.json, no mission_outcomes.jsonl.

---

## Changes (git diff summary)

```diff
+TASTE_MODEL_LOG = ROOT / "orchestrator_runtime" / "taste_model" / "mission_outcomes.jsonl"

+def load_taste_model_summary() -> str:
+    # reads TASTE_MODEL_LOG, returns advisory string
+    # advisory-only: NEVER raises, fallback on any error
+    # max ~6 lines of content

 def render_prompt(...):
+    taste_advisory = load_taste_model_summary()
     ...
+        "## Taste Model Advisory",
+        taste_advisory,
```

---

## Advisory Output (live smoke test)

Running `python orchestrator_runtime/sz_prompt_generator.py` produced:

```
## Taste Model Advisory
total=12  avg_value=3.67  top_model=cline-qwen-3.6-27b (avg=4.20)
recent missions:
  AO5_T40 v=3 partial_pass [copilot]
  AO5_T41 v=1 false_declaration [copilot]
  AO5_T42 v=5 completed [cline-qwen-3.6-27b]
high-value patterns (v>=5): autonomy_milestone, new_infrastructure, stdlib_only, first_autonomous_src_modification
```

Smoke test: **PASS** — generator ran, advisory section present, no errors, exit code 0.

---

## Fallback Behavior

`load_taste_model_summary()` is wrapped in a bare `except Exception` block.

If `mission_outcomes.jsonl` is missing: returns `"Taste Model unavailable; continuing."`  
If any line is malformed JSON: silently skips that line  
If any other error (permissions, encoding, etc.): returns `"Taste Model unavailable; continuing. (error: <exc>)"`

In all fallback cases the generator continues normally — advisory section shows the fallback string and prompt generation completes.

---

## Rollback Command

```powershell
git checkout HEAD -- orchestrator_runtime/sz_prompt_generator.py
```

This restores the pre-T44 generator exactly. Taste Model files are untouched.

---

## Constraint Verification

| Constraint | Status |
|---|---|
| NO src/ modifications | PASS — confirmed by git diff |
| NO bridge_runner.py modifications | PASS |
| NO self_state.json modifications | PASS |
| NO mission_outcomes.jsonl modifications | PASS |
| Taste Model advisory-only | PASS — no decision override, no blocking |
| Fallback on error | PASS — bare except, returns string |
| Max 12 lines | PASS — current output is 6 lines |
| Pure stdlib | PASS — no new imports, uses existing json + Path |
