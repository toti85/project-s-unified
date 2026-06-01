# GAP_030 — Interactive Mission Wall-Clock Timeout Does Not Reliably Transition EXECUTING to TIMEOUT

**Date:** 2026-05-18
**Severity:** HIGH
**Component:** `interactive_layer/sai_runner.py`
**Related Mission:** `07ee2be9-1bf5-40a0-bae9-ff99f249c6d4`

---

## EXECUTIVE SUMMARY

The SAI mission `07ee2be9-1bf5-40a0-bae9-ff99f249c6d4` was persisted in state `EXECUTING` with `progress: 0.3` after the configured 600-second wall-clock timeout should have fired. The mission never reached a terminal state (COMPLETE/FAILED/TIMEOUT). This is a confirmed timeout failure.

---

## A. DID THE 600S TIMEOUT FAIL IN REALITY?

**YES**

### Evidence:

1. **Mission created at:** 2026-05-18T16:38:52.795410 (PLANNING state)
2. **Mission entered EXECUTING at:** 2026-05-18T16:38:53.592279
3. **Configured timeout:** 600 seconds (DEFAULT_TIMEOUT = 600)
4. **Expected TIMEOUT transition at:** ~2026-05-18T16:48:53
5. **Last server log entry:** 2026-05-18T19:39:53 (approximately 60 seconds of SAI activity)
6. **Final persisted state:** EXECUTING, progress 0.3, error: None

The server logs show SAI activity for approximately 60 seconds (19:38:53 to 19:39:53), then the logs stop. The mission was stuck in EXECUTING. The asyncio.wait_for timeout of 600s should have fired well before the smoke test polling timeout of 900s.

---

## B. EXACT ROOT CAUSE

### Root Cause: `asyncio.wait_for` timeout wraps `ai.execute_intelligent_task()`, but the SAI MetaController's internal replan loop does NOT respect the outer timeout boundary.

### Detailed Analysis:

Looking at `sai_runner.py` lines 97-107:

```python
# Execute with wall-clock timeout
try:
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(task=prompt),
        timeout=timeout,  # 600 seconds
    )
except asyncio.TimeoutError:
    _db_update_error(mission_id, f"SAI mission timed out after {timeout}s")
    _db_log_event(mission_id, "mission_timeout", {"timeout_seconds": timeout})
    transition_mission_state(mission_id, MissionStateUpdate(state="TIMEOUT"))
    return
```

The timeout IS correctly wrapped around `ai.execute_intelligent_task()`. The TimeoutError IS caught. The TIMEOUT transition IS called.

**However, the server logs reveal the actual problem:**

The SAI system went through multiple replan cycles:
```
[19:38:57] Starting execution of core.evaluator.evaluate_execution_result
[19:39:06] Handled evaluation result with action: replan (original: replan)
[19:39:09] Starting execution of core.evaluator.evaluate_execution_result
[19:39:18] Handled evaluation result with action: replan (original: replan)
[19:39:21] Starting execution of core.evaluator.evaluate_execution_result
[19:39:37] Handled evaluation result with action: replan (original: replan)
[19:39:41] Starting execution of core.evaluator.evaluate_execution_result
[19:39:49] Handled evaluation result with action: replan (original: replan)
[19:39:52] Strategic plan created using Qwen3 235B with 0.9 confidence
```

The replan loop in `sai_runner.py` lines 138-150 has a **SECOND** `asyncio.wait_for` call:

```python
try:
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(task=prompt),
        timeout=timeout,  # SAME 600s timeout!
    )
```

**CRITICAL BUG:** The replan retry uses the SAME `timeout=600` parameter. This means:
- First execution: 0-600s timeout window
- First replan retry: ANOTHER 0-600s timeout window (resets!)
- Second replan retry: ANOTHER 0-600s timeout window (resets again!)
- Third replan retry: ANOTHER 0-600s timeout window (resets again!)

The effective timeout is **600s PER REPLAN ITERATION**, not 600s for the entire mission. With 5 replan iterations, the SAI system could run for up to 5 * 600 = 3000 seconds (50 minutes).

**But the logs show only ~60 seconds of activity**, which means the SAI system didn't actually timeout - it likely **blocked on a synchronous operation** inside `ai.execute_intelligent_task()` that prevented `asyncio.wait_for` from cancelling the coroutine.

### Most Likely Actual Cause: **Blocking synchronous work inside `execute_intelligent_task()`**

The `asyncio.wait_for()` mechanism can only cancel **async** coroutines. If `execute_intelligent_task()` contains any blocking synchronous code (e.g., `requests.get()`, `time.sleep()`, file I/O, or a synchronous HTTP client), the asyncio event loop cannot interrupt it, and the timeout will never fire.

The server logs show the last activity was at 19:39:53, and the mission has been stuck in EXECUTING since then. The server process is still alive. This is consistent with a blocking call that will eventually complete, but the mission state will never be updated to terminal.

---

## C. GAP_030 SHOULD OPEN?

**YES**

This is a confirmed runtime integrity issue where:
1. The timeout mechanism exists in code
2. The timeout did NOT transition the mission to a terminal state
3. The mission is stuck in EXECUTING indefinitely
4. The server process is alive but the background task is blocked

---

## D. BEST MINIMAL FIX RECOMMENDATION

### Fix 1: Track elapsed time across replan iterations

Replace the per-iteration timeout with a shared elapsed-time tracker:

```python
# In _run_sai_mission:
start_time = datetime.utcnow()
max_duration = 600  # 10 minutes total

# In replan retry:
elapsed = (datetime.utcnow() - start_time).total_seconds()
remaining = max(0, int(max_duration - elapsed))
if remaining <= 0:
    # Already exceeded total timeout
    transition_mission_state(mission_id, MissionStateUpdate(state="TIMEOUT"))
    return
result = await asyncio.wait_for(
    ai.execute_intelligent_task(task=prompt),
    timeout=remaining,
)
```

### Fix 2: Add a watchdog timer (defensive)

Add a separate asyncio task that monitors mission state and forces terminal transition if EXECUTING state persists too long:

```python
# After launching background task in main.py:
task = asyncio.create_task(_run_sai_mission(...))
watchdog = asyncio.create_task(_mission_watchdog(mission_id, task, timeout=720))
```

### Fix 3: Use async-compatible HTTP client

Ensure `SuperIntelligentAI.execute_intelligent_task()` uses `aiohttp` or `httpx.AsyncClient` for all HTTP calls, never blocking `requests` library.

---

## E. IS ANY MISSION CURRENTLY STUCK EXECUTING?

**YES**

Mission `07ee2be9-1bf5-40a0-bae9-ff99f249c6d4` is stuck in EXECUTING state with progress 0.3.

### Manual Repair:

```sql
-- Option 1: Mark as FAILED (safer)
UPDATE missions SET state = 'FAILED', error = 'GAP_030: timeout did not fire, manual repair', updated_at = datetime('now') WHERE mission_id = '07ee2be9-1bf5-40a0-bae9-ff99f249c6d4';

-- Option 2: Mark as TIMEOUT
UPDATE missions SET state = 'TIMEOUT', error = 'GAP_030: timeout did not fire, manual repair', updated_at = datetime('now') WHERE mission_id = '07ee2be9-1bf5-40a0-bae9-ff99f249c6d4';
```

Also check mission `6bab48af-acfc-48ec-8542-8f38dc11af2c` which was stuck in QUEUED state from an earlier test.

---

## SUMMARY TABLE

| Item | Value |
|------|-------|
| A. Did 600s timeout fail? | **YES** |
| B. Exact root cause | **Per-iteration timeout resets on replan + possible blocking sync code preventing asyncio cancellation** |
| C. GAP_030 should open? | **YES** |
| D. Best minimal fix | **Track elapsed time across replan iterations + ensure all HTTP calls are async** |
| E. Mission currently stuck? | **YES - 07ee2be9-1bf5-40a0-bae9-ff99f249c6d4 in EXECUTING** |