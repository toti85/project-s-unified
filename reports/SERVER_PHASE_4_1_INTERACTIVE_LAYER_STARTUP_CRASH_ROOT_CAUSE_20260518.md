# SERVER PHASE 4.1 - INTERACTIVE LAYER STARTUP CRASH ROOT CAUSE

**Date:** 2026-05-18
**Target Server:** SHAYANSKA-DL380 (192.168.1.180)
**Project Path:** C:\ProjectS\project-s-code

---

## EXECUTIVE SUMMARY

Root cause identified: **uvicorn not installed** on server. After installing uvicorn 0.47.0, the Interactive Layer server starts successfully, health check passes locally, and port 8000 is listening. Port 8000 is NOT reachable from DEV machine due to Windows Firewall (needs inbound rule).

---

## A. EXACT CRASH TRACEBACK SUMMARY

**Root crash output:**
```
Importing uvicorn...
uvicorn import FAILED: No module named 'uvicorn'
```

**File:** `interactive_layer/start_server.py`, line 31
**Line:** `import uvicorn`
**Exception:** `ModuleNotFoundError: No module named 'uvicorn'`

The server process started (PID 9428, PID 9348) but exited immediately because `start_server.py` line 31 attempts `import uvicorn`, which was never installed on the server.

---

## B. ROOT CAUSE CATEGORY

**Category: A - Missing Dependency**

The `start_server.py` script imports `uvicorn` at line 31:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("interactive_layer.main:app", host="0.0.0.0", port=8000, reload=False)
```

uvicorn was not installed via pip on the server. It was not in the Phase 3 dependency list because the initial smoke tests used `importlib.util` to load the module (which doesn't execute `if __name__ == "__main__"` blocks), so the crash was not detected until the actual server launch.

---

## C. FILES CHANGED / PACKAGES INSTALLED

| Package | Version | Purpose |
|---------|---------|---------|
| uvicorn | 0.47.0 | ASGI server for FastAPI |
| click | 8.4.0 | CLI utilities (uvicorn dependency) |
| colorama | 0.4.6 | Cross-platform colored terminal (click dependency) |

**Command:** `pip install uvicorn`

---

## D. SERVER NOW STAYS RUNNING

**Result: YES**

- Process running: True
- Port 8000 listening: True
- Health check: `{"status":"ok"}` (HTTP 200)

---

## E. /HEALTH LOCAL PASS

**Result: YES**

```
GET http://localhost:8000/health
Response: {"status":"ok"}
Status: 200 OK
```

---

## F. PORT 8000 REACHABLE FROM DEV

**Result: NO**

- Test-NetConnection 192.168.1.180 -Port 8000: False
- **Cause:** Windows Firewall blocking inbound TCP 8000
- **Fix needed:** Add inbound firewall rule for TCP 8000 on Private profile only

---

## G. READY FOR SMOKE MISSION

**Result: YES (locally)**

The server is running and healthy. A smoke mission can be launched via the API:

```powershell
# From DEV machine (after firewall fix):
$body = @{ prompt = "Test message" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://192.168.1.180:8000/api/missions" -Method Post -Body $body -ContentType "application/json"
```

---

## H. NEXT RECOMMENDED SERVER STEP

**1. Add Windows Firewall rule for TCP 8000 (Private profile only):**

```powershell
# On SHAYANSKA-DL380
New-NetFirewallRule -DisplayName "Project-S Interactive Layer" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

**2. Verify from DEV machine:**

```powershell
Test-NetConnection 192.168.1.180 -Port 8000
```

**3. Run smoke mission:**

```powershell
# From DEV machine
$body = @{ prompt = "Írj 3 rövid mondatot arról, hogy miért fontos a pontos dokumentáció." } | ConvertTo-Json
Invoke-RestMethod -Uri "http://192.168.1.180:8000/api/missions" -Method Post -Body $body -ContentType "application/json"
```

**NOT YET:** Full browser automation, NVIDIA drivers, permanent services.

---

## SUMMARY TABLE

| Check | Result |
|-------|--------|
| A. Exact crash traceback | ✅ Captured (uvicorn import failed) |
| B. Root cause category | ✅ A - Missing dependency |
| C. Files changed/packages installed | ✅ uvicorn 0.47.0, click 8.4.0, colorama 0.4.6 |
| D. Server now stays running | ✅ YES |
| E. /health local PASS | ✅ YES (`{"status":"ok"}`) |
| F. Port 8000 reachable from DEV | ❌ NO (Windows Firewall) |
| G. Ready for smoke mission | ✅ YES (after firewall fix) |

---

## FILES CREATED DURING PHASE 4.1

1. `reports/SERVER_PHASE_4_1_INTERACTIVE_LAYER_STARTUP_CRASH_ROOT_CAUSE_20260518.md` - This report
2. `phase41_crash_capture.ps1` - Crash capture script
3. `phase41_direct_run.ps1` - Direct server run script
4. `phase41_install_uvicorn.ps1` - uvicorn install + server start script