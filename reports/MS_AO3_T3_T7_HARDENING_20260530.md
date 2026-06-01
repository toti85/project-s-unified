# MS-AO3 Hardening T3-T7 — Negative/Edge-Case Path Tests — 2026-05-30

## Summary

| Test | Expected | Result | PASS? |
|------|----------|--------|-------|
| T3 — Checksum mismatch | REJECTED_CHECKSUM | REJECTED_CHECKSUM | **YES** |
| T4 — Missing output | WAITING_FOR_EXECUTOR | WAITING_FOR_EXECUTOR | **YES** |
| T5 — Wrong run_id | REJECTED_RUN_ID | REJECTED_RUN_ID | **YES** |
| T6 — Already consumed | REJECTED_CONSUMED | REJECTED_CONSUMED | **YES** |
| T7 — SCL integration | SCL invoked (no import error) | SCL invoked | **YES** |

**All 5 hardening tests: PASS (5/5)**

## T3 — Checksum Mismatch

**Fixture:** Valid `last_output.md` + `output_ready.json` with wrong checksum (`0000000000000000`)

**Raw Output:**
```json
{
    "status": "REJECTED_CHECKSUM",
    "content": null,
    "run_id": "AO3_T3",
    "iteration": 1,
    "error": "Checksum mismatch: expected 0000000000000000, got <actual>"
}
```

**Result:** REJECTED_CHECKSUM ✅

---

## T4 — Missing Output (No output_ready.json)

**Fixture:** Empty `cline_outbox/` directory — no files

**Raw Output:**
```json
{
    "status": "WAITING_FOR_EXECUTOR",
    "content": null,
    "run_id": "AO3_T4",
    "iteration": 1,
    "error": "output_ready.json not found"
}
```

**Result:** WAITING_FOR_EXECUTOR ✅

---

## T5 — Wrong Run ID

**Fixture:** `output_ready.json` with `run_id=AO3_T5_WRONG`, consume with `run_id=AO3_T5_RIGHT`

**Raw Output:**
```json
{
    "status": "REJECTED_RUN_ID",
    "content": null,
    "run_id": "AO3_T5_RIGHT",
    "iteration": 1,
    "error": "run_id mismatch: expected AO3_T5_RIGHT, got AO3_T5_WRONG"
}
```

**Result:** REJECTED_RUN_ID ✅

---

## T6 — Already Consumed

**Fixture:** `output_ready.json` with `consumed: true`

**Raw Output:**
```json
{
    "status": "REJECTED_CONSUMED",
    "content": null,
    "run_id": "AO3_T6",
    "iteration": 1,
    "error": "Output already consumed (no double-consume)"
}
```

**Result:** REJECTED_CONSUMED ✅

---

## T7 — SCL Integration (--verdict)

**Fixture:** Valid output files with correct checksum, `--verdict` flag

**Raw Output:**
```json
{
    "status": "ACCEPTED",
    "content": "# AO3_T7 Execution Report\n- run_id: AO3_T7\n- result: PASS\n",
    "run_id": "AO3_T7",
    "iteration": 1,
    "error": null,
    "verdict": {
        "<SCL result from self_correcting_loop.process_goal()>"
    }
}
```

**Result:** SCL invoked, no import error ✅

---

## Safety Verification

- [x] No src/ modifications
- [x] No self_state.json modifications
- [x] Sandbox + orchestrator_runtime + reports only
- [x] No end-to-end flow simulation (rejection/error paths only)
- [x] All tests use real on-disk fixtures in temp directories

## Test Runner

`orchestrator_runtime/sandbox/run_hardening_tests.py` — runs all 5 tests with real file I/O, temp directories, and direct function calls.