# Interactive Layer Timeout Root Cause Analysis

**Date:** 2026-05-20 01:48 UTC+3  
**Type:** DIAGNOSIS — Stale GAP_030 Validation Patch  
**Trigger:** 7/8 missions TIMEOUT after ~30s in 120s observation window rerun

---

## A. Did the 7 missions really TIMEOUT after ~25–30s?

**YES.** All 7 TIMEOUT missions show:
- Elapsed time from `created_at` to `updated_at`: **30.0–31.6 seconds**
- Error string: `"SAI mission timed out after 30s remaining (replan=0/3)"`
- `timeout_seconds` stored in SQLite: **600** (correct)

---

## B. What exact `timeout_seconds` value was stored in SQLite?

**600** for all 7 missions. The database column is correct.

---

## C. What exact timeout value did the running server use?

**30 seconds.** The server log confirms:
```
SAI mission 695a294c-d285-4b5e-9200-096cecdf44bb: global deadline established (timeout=30s)
SAI mission 695a294c-d285-4b5e-9200-096cecdf44bb: execution timed out (remaining=29.9s, replan=0/3)
```

The global deadline was established with `timeout=30s`, not `600s`.

---

## D. Did live_ui_test_20260518.py pass a timeout override?

**NO.** The test harness does NOT send any `timeout_seconds` override. It uses the browser UI at `http://localhost:8000/ui`, which calls `POST /api/chat`, which creates a `MissionCreate` with default `timeout_seconds=600` (from the Pydantic model).

---

## E. Exact root cause of the 25–30s TIMEOUTs

**`restart_and_validate.ps1` patched `DEFAULT_TIMEOUT` from 600 to 30 on disk, and the running server process was started with the patched code.**

### Evidence chain:

1. **`restart_and_validate.ps1` line 16:**
   ```powershell
   $content = $content -replace 'DEFAULT_TIMEOUT = 600', 'DEFAULT_TIMEOUT = 30'
   Set-Content $saiRunnerPath $content -NoNewline
   ```
   This script patches `sai_runner.py` on disk from `DEFAULT_TIMEOUT = 600` to `DEFAULT_TIMEOUT = 30`.

2. **Running server process:**
   ```
   PID 55124: python interactive_layer/start_server.py
   Python 3.11 (C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe)
   ```
   The server was started AFTER the patch was applied, so it imported `DEFAULT_TIMEOUT = 30`.

3. **Server log confirms:**
   ```
   SAI mission 695a294c-d285-4b5e-9200-096cecdf44bb: global deadline established (timeout=30s)
   ```

4. **The patch was never restored.** The script `restart_and_validate.ps1` patches on disk but does NOT restore the original value after validation.

### Why the "server restart changed execution paths" explanation was wrong:

The server restart did NOT change execution paths. The server was running with `DEFAULT_TIMEOUT = 30` because `restart_and_validate.ps1` had patched the file on disk. The server process simply imported the patched value.

---

## F. Was the previous "server restart changed execution paths" explanation correct?

**NO.** The previous explanation was incorrect. The server was not restarted between the original test and the rerun — it was the SAME server process (PID 55124) that had been patched by `restart_and_validate.ps1` earlier. The 30s timeout was not caused by a server restart; it was caused by a stale file patch.

---

## G. Is a real new system GAP present?

**NO.** This is a test infrastructure issue, not a system defect. The `DEFAULT_TIMEOUT = 30` was intentionally set by a GAP_030 DEV validation script for testing purposes, and was never restored. The correct value is `DEFAULT_TIMEOUT = 600`.

---

## H. Is the 8/8 matrix rerun valid or must it be discarded?

**The rerun is INVALID.** The 7 TIMEOUT results are artifacts of the stale `DEFAULT_TIMEOUT = 30` patch, not a reflection of the system's actual behavior. The rerun must be discarded and re-executed after:

1. Restoring `DEFAULT_TIMEOUT = 600` in `sai_runner.py` (DONE)
2. Restarting the server process to load the restored value
3. Re-running the 8/8 test matrix

---

## Fix Applied

`interactive_layer/sai_runner.py` line 56:
```python
# DEFAULT_TIMEOUT was patched to 30 by restart_and_validate.ps1 for GAP_030 DEV validation.
# Restoring to 600 (10 minutes) — this is the correct production value.
DEFAULT_TIMEOUT = 600  # 10 minutes wall-clock (GLOBAL deadline)
```

---

## Next Steps

1. **Restart the server process** (PID 55124) to load the restored `DEFAULT_TIMEOUT = 600`
2. **Re-run the 8/8 test matrix** with the 120s observation window
3. **Clean up stale GAP_030 validation scripts** that patch `DEFAULT_TIMEOUT` on disk:
   - `restart_and_validate.ps1` — patches on disk, never restores
   - `final_validate.ps1` — patches in-memory, restores after
   - `full_gap030_validation.py` — patches in-memory, restores after
   - `validate_gap030.py` — patches in-memory, restores after
   - `run_gap030_live_validation.ps1` — patches in-memory, restores after
   - `run_gap030_live.py` — patches on disk, may not restore
   - `patch_and_wait.ps1` — patches running server, restores after

---

## Summary

| Question | Answer |
|----------|--------|
| A. Did missions TIMEOUT after ~30s? | YES |
| B. `timeout_seconds` in SQLite? | 600 (correct) |
| C. Timeout value used by server? | 30 (stale patch) |
| D. Test harness passed timeout override? | NO |
| E. Exact root cause | `restart_and_validate.ps1` patched `DEFAULT_TIMEOUT = 30` on disk, server imported patched value |
| F. Previous explanation correct? | NO |
| G. Real new system GAP? | NO |
| H. Rerun valid? | NO — must be discarded and re-executed |