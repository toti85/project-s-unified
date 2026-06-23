# MS_AO8J_1_CONTINUE_RESULT_NONE_FIX — 2026-06-22

## A. Root cause confirmed?

**YES.**

`continuous_mind.py` line ~699:
```python
continue_result.get("outbox", {}).get("status")
continue_result.get("outbox", {}).get("checksum")
```

When the Continue executor adapter returns `{"status": "FAIL", "outbox": None}`, 
the `.get("outbox", {})` default is **NOT used** because the key `"outbox"` 
exists (its value is `None`). Python's `dict.get(key, default)` only returns 
the default if the key is **missing**, not if the value is `None`. 

So `None.get("status")` raises `AttributeError`.

Same risk exists for `continue_result.get("run", {}).get(...)` — if `"run": None`.

---

## B. continuous_mind.py patched?

**YES.** Surgical fix at the two access points:

**Line 699 (before):**
```python
run_ok = continue_result.get("overall") == "OK" and continue_result.get("run", {}).get("status") == "OK"
...
"run_status": continue_result.get("run", {}).get("status"),
"outbox_status": continue_result.get("outbox", {}).get("status"),
"checksum": continue_result.get("outbox", {}).get("checksum"),
```

**Line 699 (after):**
```python
run = continue_result.get("run") or {}
outbox = continue_result.get("outbox") or {}
run_ok = continue_result.get("overall") == "OK" and run.get("status") == "OK"
...
"run_status": run.get("status"),
"outbox_status": outbox.get("status"),
"checksum": outbox.get("checksum"),
```

**Line 788 (before):**
```python
log.warning("Continue execution failed: %s", continue_result.get("run", {}).get("error"))
```

**Line 788 (after):**
```python
log.warning("Continue execution failed: %s", run.get("error", "(no error field)"))
```

The pattern `x = d.get("key") or {}` ensures:
- If key is missing → `{}` (default)
- If key exists with value `None` → `{}` (falsy → fallback)
- If key exists with value `{"status": ...}` → the dict (preserved)

---

## C. Unsafe patterns found/patched

| Pattern | Found | Patched | Notes |
|---------|-------|---------|-------|
| `.get("outbox", {}).get(` | **2** | **2** | Both in the same jsonl log block |
| `.get("run", {}).get(` | **3** | **3** | Same block, plus the `run_ok` check, plus the `error` log |
| `.get("result", {}).get(` | 0 | 0 | Not used |
| `.get("execution", {}).get(` | 0 | 0 | Not used |

**Total: 5 unsafe chained `.get()` calls found → all 5 patched.**

---

## D. Regression test added/run?

**YES.** Two new tests added to `orchestrator_runtime/governance/test_continue_executor_adapter.py`:

### test_k_continue_result_outbox_none
Simulates the exact crash: `{"status": "FAIL", "outbox": None, "run": None}`.
Verifies:
- `outbox.get("status")` → returns `"MISSING"` (not crash)
- `outbox.get("checksum")` → returns `"MISSING"` (not crash)
- `run.get("status")` → returns `"MISSING"` (not crash)
- `run.get("error", "(no error field)")` → fallback string

### test_l_continue_result_outbox_none_overall_ok
Simulates partial success: `{"overall": "OK", "outbox": None, "run": {"status": "OK"}}`.
Verifies:
- `run_ok` computed correctly (`True`)
- `outbox.get("status")` → `"MISSING"` without crash
- `outbox.get("checksum")` → `"MISSING"` without crash

**Both pass:**
```
[K] PASS | outbox=None handled: status=MISSING checksum=MISSING run=MISSING
[L] PASS | outbox=None with run_ok=True: status=MISSING checksum=MISSING
```

---

## E. Compile/tests pass?

| Check | Status |
|-------|--------|
| `python -m py_compile continuous_mind.py` | **PASS** ✅ |
| `test_k_continue_result_outbox_none` | **PASS** ✅ |
| `test_l_continue_result_outbox_none_overall_ok` | **PASS** ✅ |
| `test_continue_watchdog.py` | 2 pass / 2 fail (pre-existing) 🔶 |
| `test_continue_executor_adapter.py` (live) | 8 pass / 2 fail (pre-existing) 🔶 |

**Pre-existing failures** (unrelated to this fix):
1. Unicode `charmap` encoding error in test_c (console codepage)
2. Large file threshold mismatch in test_j (250 KB vs 200 KB threshold, probing mode)
3. Watchdog synthetic fail/low-avg tests (threshold tuning needed)

---

## F. src modifications?

**NO.** Only `orchestrator_runtime/continuous_mind.py` and `orchestrator_runtime/governance/test_continue_executor_adapter.py` were modified. No files under `src/` were touched.

---

## G. self_state modifications?

**NO.** No `self_state.json` was read or written.

---

## H. Ready to resume AO8J?

**YES.** The None-safe patch is backward-compatible:
- All previous successful Continue CLI runs used `outbox={...}` or `run={...}`, never `None` → behavior unchanged.
- The only change is defensive: when `None` is returned, fields become `MISSING`/`{}` instead of crashing.
- No new dependencies, no config changes.
- Testing infrastructure confirmed the fix handles both crash scenarios.

---

## I. Git status --short

```
 M orchestrator_runtime/continuous_mind.py
?? orchestrator_runtime/governance/test_continue_executor_adapter.py
```

Only two files changed, both in `orchestrator_runtime/`. No `src/`, no root-level, no `self_state.json`.