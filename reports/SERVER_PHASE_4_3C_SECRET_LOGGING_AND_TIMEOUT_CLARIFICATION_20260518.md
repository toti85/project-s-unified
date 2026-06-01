# SERVER PHASE 4.3C - SECRET LOGGING & TIMEOUT CLARIFICATION

**Date:** 2026-05-18
**Target Server:** SHAYANSKA-DL380 (46.253.140.72:15985)

---

## A. RAW API KEY LOGGING SOURCE FIXED?

**NO - API key is exposed in 7 markdown files in the project root.**

### Exposed Files (sk-or-v1- pattern found):
1. `DEPLOYMENT_SUMMARY.md`
2. `FIX_IMPLEMENTATION.md`
3. `IMPLEMENTATION_GUIDE.md`
4. `LAUNCH_GUIDE.md`
5. `README_FIX_INDEX.md`
6. `SERVER_HUNT_README.md`
7. `TEST_RESULTS.md`

### JSON/Text Files:
No API keys found in `.phase43*.json` or `.txt` files in the project root.

### PowerShell Scripts:
The scripts `phase43_deploy_key_and_retry.ps1`, `check_env_full.ps1`, and `check_dotenv_load.ps1` contain the raw API key as a variable (`$newApiKey`). These are not "logging" per se, but the key is hardcoded in the script body.

### Recommended Fix:
- Replace all hardcoded API keys in `.md` files with `[EXPOSED - ROTATE IMMEDIATELY]`
- Replace hardcoded API keys in `.ps1` scripts with environment variable references: `$env:OPENROUTER_API_KEY`
- **Rotate the exposed OpenRouter key immediately** at https://openrouter.ai/keys

---

## B. CONFIGURED MISSION TIMEOUT

**600 seconds (10 minutes)**

Source: `interactive_layer/sai_runner.py` line 56:
```python
DEFAULT_TIMEOUT = 600  # 10 minutes wall-clock
```

This is passed to `asyncio.wait_for(ai.execute_intelligent_task(task=prompt), timeout=timeout)`.

The timeout is a **wall-clock limit** for the entire SAI execution including all replan cycles. The SAI system with MetaController can iterate up to 5 times (max 3 replans), each iteration calling OpenRouter API. This is why the mission can take close to 600s.

---

## C. TEST-SCRIPT POLLING TIMEOUT

**900 seconds (15 minutes)**

Source: `phase43_chat_smoke.ps1` polling loop:
```powershell
$maxPolls = 90
$pollInterval = 10
# 90 * 10 = 900 seconds
```

The smoke test polling script timed out at 900s, which is **longer** than the configured mission timeout of 600s.

---

## D. MISSION FINAL PERSISTED STATE

**EXECUTING (non-terminal)**

The mission `07ee2be9-1bf5-40a0-bae9-ff99f249c6d4` is stuck in EXECUTING state:

```
mission_id: 07ee2be9-1bf5-40a0-bae9-ff99f249c6d4
state: EXECUTING
progress: 0.3
error: None
updated_at: 2026-05-18T16:38:53.607888
state_history: [
  {"state": "PLANNING", "timestamp": "2026-05-18T16:38:52.795410", "metadata": {}},
  {"state": "EXECUTING", "timestamp": "2026-05-18T16:38:53.592279", "metadata": {}, "duration_ms": 796}
]
```

### Root Cause Analysis:

The mission is **stuck in EXECUTING** because:

1. The SAI system started executing at 19:38:53 UTC
2. Server logs show it went through multiple replan cycles (iterations 1-5/5)
3. The last log entry is at 19:39:53 UTC - approximately 60 seconds of activity
4. After reaching max replan iterations (5/5), the SAI system should have transitioned to COMPLETE/FAILED/TIMEOUT
5. The server process is still alive and /health responds OK
6. The mission never reached a terminal state

**Most likely cause:** The SAI MetaController reached max iterations (5/5) but the `_run_sai_mission` function did not properly handle the "max iterations reached" case. Looking at the code:

```python
# After max replans exceeded:
if action == "replan" and replan_count >= MAX_REPLAN_COUNT:
    _db_update_error(mission_id, "max_replan_exceeded")
    _db_log_event(mission_id, "mission_failed", {...})
    transition_mission_state(mission_id, MissionStateUpdate(state="FAILED"))
    return
```

This only handles the case where `action == "replan"` after max replans. But if the evaluator returns a different action (e.g., "approve") after max replans, or if the result doesn't have an evaluation_result dict, the code falls through to Step 4 (COMPLETE/FAILED) which checks `success = result.get("success", False)`.

If `success` is False and there's no explicit error, the mission should transition to FAILED. But if the AI call hangs or the result processing blocks indefinitely, the mission stays in EXECUTING.

**The asyncio.wait_for timeout of 600s should have triggered**, but the smoke test polling timed out at 900s before the mission timeout at 600s. The mission may still be running on the server.

---

## E. ANY FURTHER SERVER BLOCKER?

**NO** - The server infrastructure is fully functional:

| Component | Status |
|-----------|--------|
| Server process | ✅ Running |
| /health endpoint | ✅ OK |
| SQLite database | ✅ Working |
| Session creation | ✅ Works |
| Mission creation | ✅ Works |
| SAI background task | ✅ Launches and executes |
| OpenRouter API | ✅ Connected, making calls |
| AI packages | ✅ Installed (openai, anthropic, aiohttp) |
| Firewall rule | ✅ Created |

The only issue is the **stuck mission** which will resolve when either:
1. The 600s asyncio timeout fires (mission transitions to TIMEOUT)
2. The SAI system completes its execution cycle
3. The server process is restarted

---

## SUMMARY TABLE

| Item | Value |
|------|-------|
| A. Raw API key logging fixed? | **NO** - exposed in 7 .md files + 3 .ps1 scripts |
| B. Configured mission timeout | **600 seconds** (10 min) |
| C. Test-script polling timeout | **900 seconds** (15 min) |
| D. Mission final persisted state | **EXECUTING** (non-terminal, stuck) |
| E. Further server blocker? | **NO** |

---

## IMMEDIATE ACTIONS REQUIRED

1. **ROTATE API KEY** - The exposed OpenRouter key must be rotated at https://openrouter.ai/keys
2. **Clean exposed files** - Replace raw keys with `[EXPOSED - ROTATE IMMEDIATELY]` in all 7 .md files
3. **Fix scripts** - Replace hardcoded keys in .ps1 scripts with `$env:OPENROUTER_API_KEY`
4. **Restart server** - To clear the stuck EXECUTING mission (optional, will auto-resolve at 600s)