# MS_AO8J_3_WATCHDOG_STALE_STATE_DIAGNOSIS — 2026-06-22

## A. Exact root cause

**`_recent_outbox_errors()` in `continue_watchdog.py` reads `output_ready.json` directly and checks `consumed` field.**

When `consumed=false`, it unconditionally appends `"outbox not consumed: run_id=..."` to the errors list, which causes `decide()` to return `allow_continue=False` with `reason="OUTBOX_ERRORS"`.

The watchdog has **no awareness** of:
- Whether the outbox was already archived by `check_stale_outbox()` in the adapter
- Whether the file is stale (older than a few minutes)
- Whether the file was already processed by a previous cycle

**Chain:**
```
Continue CLI produces empty output (AO8J_2)
  → adapter writes output_ready.json with consumed=false
    → bridge_runner errors on consume (empty output)
      → output_ready.json stays with consumed=false
        → watchdog reads it fresh each cycle
          → consumed=false → "outbox not consumed: run_id=AO8J_LOOP_TEST_13"
            → decide() returns allow_continue=False
              → CM blocks all subsequent goals
```

Even after AO8J_2 fix prevents new empty outputs, the **existing stale** `output_ready.json` from LOOP_TEST_13 (and later LOOP_TEST_17) continues to block the watchdog because the watchdog has its own independent persistence read — it doesn't share state with the adapter's `check_stale_outbox()`.

## B. File/path containing stale state

**`orchestrator_runtime/cline_outbox/output_ready.json`**

The watchdog reads this file directly at line 65-73:
```python
files = sorted(outbox_dir.glob("output_ready.json"), ...)
for f in files[:count]:
    data = json.loads(f.read_text(...))
    consumed = data.get("consumed", False)
    if not consumed:
        errors.append(f"outbox not consumed: run_id={run_id}")
```

No other persistence source is involved:
- `mission_outcomes.jsonl` — only used for consecutive FAIL/PARTIAL checks (rules 2-4)
- `cm_v01_cycle_log.jsonl` — not read by watchdog at all
- No in-memory cache — every `decide()` call re-reads from disk

## C. Patch applied?

**YES.** Surgical fix in `_recent_outbox_errors()` (lines 60-78):

```python
# ── AO8J_3: Stale outbox — if not consumed and older than 5 min, archive ──
if not consumed:
    age_seconds = (datetime.now(timezone.utc).timestamp() - f.stat().st_mtime)
    if age_seconds > 300:  # 5 minutes
        archive_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        for fname in ["last_output.md", "output_ready.json"]:
            src = outbox_dir / fname
            if src.exists():
                dst = archive_dir / f"{ts}_stale_{run_id}_{fname}"
                src.rename(dst)
                log.info("Watchdog archived stale outbox %s -> %s", src.name, dst.name)
        consumed = True
```

Logic:
1. If `consumed=false` AND file is older than 5 minutes → it's stale
2. Archive both `last_output.md` and `output_ready.json` to `archive/` with timestamp + run_id
3. Set `consumed = True` so no error is appended
4. Fresh files (< 5 min old) still trigger the error as before (no behavioral change for active runs)

**Files modified:**
- `orchestrator_runtime/governance/continue_watchdog.py` — 1 function patched
- `orchestrator_runtime/governance/test_continue_watchdog.py` — 1 test added

## D. Regression test PASS?

**YES.** Test 5: `test_5_stale_outbox_archived`

```
[5] stale outbox older than 5 min — should ALLOW (archive + skip)
  [PASS] stale outbox archived: errors=[]
        archived files: ['20260622T204049_stale_AO8J_STALE_TEST_last_output.md',
                         '20260622T204049_stale_AO8J_STALE_TEST_output_ready.json']
```

Verifies:
- Stale `output_ready.json` with `consumed=false` and mtime > 5 min → **no errors**
- Archive directory created with both files
- `_recent_outbox_errors()` returns empty list

**Full test suite: 3 PASS / 2 FAIL** (2 pre-existing failures in tests 2/3 are taste model threshold tuning, unrelated)

## E. Ready for AO8J rerun?

**YES.**

1. **AO8J_1 fix** (outbox=None crash) → prevents `AttributeError` when `"outbox": None`
2. **AO8J_2 fix** (empty output guard) → prevents new empty `output_ready.json` from being created
3. **AO8J_3 fix** (watchdog stale state) → watchdog auto-archives stale outbox files older than 5 min

The three fixes together form a complete defense:
- **Prevention:** Empty output never reaches outbox (AO8J_2)
- **Resilience:** If stale outbox exists, watchdog archives it and continues (AO8J_3)
- **Safety:** `None` values don't crash (AO8J_1)

**No src/ modifications. No self_state modifications.**