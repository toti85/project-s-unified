# iLO Script Recovery Search Report

**Date:** 2026-05-15
**Search Type:** Locate and identify old Project-S iLO/Redfish server-control script
**Status:** FOUND — High-confidence candidate identified

---

## 1. Executive Result

**Was the iLO script found?** YES

**Best candidate exact path:**
```
C:\ProjectS-Unified\project_s\infrastructure\ilo_controller.py
```

**Confidence level:** HIGH

**Does it include the old redirect workaround?** YES — `_handle_redirect()` method (lines 95-149) with full 192.168.x.x / private IP rewrite logic

**Does it appear usable for the new DL380 iLO?** YES — the script is parameterized (URL, username, password via constructor). The only hardcoded values are in the `__main__` test block (lines 668-672) which can be overridden. The NAT redirect workaround is built into the core `_request()` method and will work with any iLO endpoint.

---

## 2. High-Confidence Candidate(s)

### Candidate 1: `project_s/infrastructure/ilo_controller.py` (PRIMARY)

| Attribute | Value |
|-----------|-------|
| **Full path** | `C:\ProjectS-Unified\project_s\infrastructure\ilo_controller.py` |
| **Size** | 689 lines |
| **Why it matches** | Contains `ILOController` class, HPE iLO 4 Redfish API, `get_power_state`, `restart_server`, `power_on`, `power_off`, `force_power_off`, NAT redirect workaround with 192.168 rewrite |
| **Key classes/functions** | `ILOController.__init__()`, `connect()`, `get_power_state()`, `restart_server()`, `power_on()`, `power_off()`, `get_system_info()`, `get_health_summary()`, `close()`, `_handle_redirect()`, `_is_private_ip()`, `_request()` |
| **Executable or notes/docs** | **Executable** — has `if __name__ == "__main__"` test block with hardcoded endpoint `https://46.253.140.72:89` |
| **Confidence** | **HIGH** |

**Key features confirmed:**
- HPE iLO 4 Redfish API v1 interface
- Manual redirect handling (no `allow_redirects=True`) — critical for NAT scenarios
- `_handle_redirect()` detects redirects to `192.168.x.x`, `10.x.x.x`, `172.16.x.x` and rewrites back to original public endpoint
- `_is_private_ip()` checks localhost, 192.168.*, 10.*, 172.*, *.local, *.internal
- Fresh connection per request (avoids iLO 4 session closure issues)
- SSL verification disabled by default (self-signed certs)
- Timeout configurable (default 10s)
- Authentication via HTTP Basic Auth

### Candidate 2: `project_s/infrastructure/test_ilo_controller.py` (TEST)

| Attribute | Value |
|-----------|-------|
| **Full path** | `C:\ProjectS-Unified\project_s\infrastructure\test_ilo_controller.py` |
| **Size** | 88 lines |
| **Why it matches** | Live connectivity test for the ILOController, contains actual credentials |
| **Key classes/functions** | `main()` — end-to-end test: connect → get_system_info → get_power_state → get_health_summary |
| **Executable or notes/docs** | **Executable** — run via `python -m project_s.infrastructure.test_ilo_controller` |
| **Confidence** | **HIGH** (supporting test file) |

**Hardcoded credentials in test file:**
```python
ILO_URL = "https://46.253.140.72:89"
ILO_USERNAME = "Administrator"
ILO_PASSWORD = "PTSYK7BF"
```

### Candidate 3: `project_s/infrastructure/__init__.py` (MODULE)

| Attribute | Value |
|-----------|-------|
| **Full path** | `C:\ProjectS-Unified\project_s\infrastructure\__init__.py` |
| **Size** | 10 lines |
| **Why it matches** | Exports `ILOController` via `__all__` |
| **Executable or notes/docs** | Module init — not standalone executable |
| **Confidence** | **HIGH** (supporting module file) |

### Candidate 4: `project_s/infrastructure/__main__.py` (ENTRY POINT)

| Attribute | Value |
|-----------|-------|
| **Full path** | `C:\ProjectS-Unified\project_s\infrastructure\__main__.py` |
| **Size** | ~10 lines |
| **Why it matches** | Allows `python -m project_s.infrastructure` to run the test |
| **Executable or notes/docs** | Entry point wrapper |
| **Confidence** | **HIGH** (supporting entry point) |

---

## 3. Supporting Candidate Files

### Related files (not iLO scripts but server-hunt context):

| File | Relevance |
|------|-----------|
| `server_hunt_scraper.py` | Server hunting tool for HP DL380 / Dell R730 deals — search context, not iLO control |
| `server_hunt_maestro.py` | Orchestration for server hunt campaigns — search context |
| `ukraine_enterprise_server_search_v2.py` | Structured server search with HP DL380 model specs — search context |
| `ukraine_server_search.py` | Server search with scenario planning — search context |
| `meta_launcher.py` | Ukraine enterprise server search launcher — search context |
| `meta_launcher_browser.py` | Browser-based server search — search context |
| `multi_ai_ukraine_search.py` | Multi-AI server search — search context |
| `simple_ukraine_server_search.py` | Simple Playwright-based server search — search context |

These are **not** iLO control scripts. They are the **bounty/server-hunt research** scripts from the same era (2026-02-19 Ukraine enterprise server search campaign). They reference HP DL380/Dell R730 hardware specs but do NOT control servers.

---

## 4. Evidence That This Is the Old Project-S iLO Script

### Direct evidence:

1. **Class name matches historical clue:** `ILOController` — exact match
2. **API matches historical clue:** HPE iLO 4 Redfish API — exact match
3. **Methods match historical clue:** `get_power_state`, `restart_server`, `power_on`, `power_off` — all present
4. **NAT redirect workaround present:** `_handle_redirect()` method (lines 95-149) explicitly handles the `192.168.x.x` internal redirect issue described in the task
5. **Connection reuse pattern:** `_request()` creates fresh connections per call, avoids iLO 4 session closure — matches "connection reuse / error handling logic" clue
6. **DL380 context:** The Ukraine server search scripts reference DL380 Gen9 as the target hardware — this iLO script was likely intended for the same DL380 Gen9 server being migrated
7. **Date alignment:** The `project_s/` directory structure matches the pre-2026-04-26 workspace layout (before the unified `src/` structure was adopted)

### Redirect workaround details:

The `_handle_redirect()` method (lines 95-149) does the following:
1. Intercepts HTTP 301/302/303/307/308 redirects
2. Parses the `Location` header
3. Checks if the redirect target is a private IP via `_is_private_ip()`
4. If private IP detected, rewrites the URL to use the **original public endpoint** while preserving the redirected path and query string
5. Retries the request against the rewritten URL

This is **exactly** the workaround described in the task: "the iLO/Redfish endpoint redirected internally to 192.168.x.x, and the client was adjusted to rewrite/handle that redirect so remote public endpoint access still worked."

---

## 5. What the Script Appears Able to Do

### Power Management:
- `get_power_state()` — Read current power state (On/Off)
- `power_on()` — Send ForceOn reset command via Redfish
- `power_off()` — Send ForceOff reset command via Redfish
- `restart_server()` — Send ForceRestart reset command via Redfish

### System Information:
- `get_system_info()` — Full Redfish system info (Model, Manufacturer, SerialNumber, BIOS, etc.)
- `get_health_summary()` — Compact health summary (model, manufacturer, power_state, serial, bios_version, health)

### Connectivity:
- `connect()` — Test Redfish API v1 connectivity
- `close()` — Cleanup (no-op in current implementation since each request uses fresh connection)

### NAT/Redirect Handling:
- `_handle_redirect()` — Rewrite internal 192.168.x.x redirects to public endpoint
- `_is_private_ip()` — Detect private IPs (10.*, 172.16-31.*, 192.168.*, localhost, *.local, *.internal)

### Authentication:
- HTTP Basic Auth via constructor credentials
- SSL verification disabled by default (self-signed certs)

---

## 6. What Is Still Unknown

1. **Current iLO credentials:** The test file contains credentials for `46.253.140.72:89` (the old Windows Server 2012 R2 machine's iLO). The **new** DL380 Gen9 has different iLO credentials that need to be obtained from Toti.

2. **New DL380 iLO endpoint:** The new server's iLO IP/URL is not yet known. Only the iLO network cable is connected; the host OS LAN is not connected.

3. **iLO 4 vs iLO 5:** The script targets iLO 4 Redfish API. The new DL380 Gen9 typically ships with iLO 4 (not iLO 5, which came with Gen10). This should be compatible, but needs verification.

4. **Network reachability:** The new DL380 Gen9's iLO is only reachable via direct iLO cable. It's unclear if the DEV machine can currently reach the new server's iLO IP.

5. **Power state of new server:** The new DL380 Gen9 may be powered off or in an unknown state. The script's `power_on()` method would be needed to boot it.

---

## 7. Recommended Next Step

### Option A: Inspect Only (Recommended First Step)
The script is **ready to use** with minimal changes. Next steps:
1. Obtain new DL380 Gen9 iLO IP/URL and credentials from Toti
2. Update the test file credentials (or pass via environment variable)
3. Run `python -m project_s.infrastructure.test_ilo_controller` to verify connectivity
4. If successful, use `ILOController` methods for power management

### Option B: Recover Into Current Unified Workspace
The script lives in `project_s/infrastructure/` which is the **old** pre-unification layout. Consider:
1. Copy `ilo_controller.py` and `test_ilo_controller.py` to `src/core/infrastructure/` or `tools/tools/implementations/`
2. Update imports to match current `src/` package structure
3. Add to `__all__` exports
4. Create a new test file with placeholder credentials for the new DL380

### Option C: Recreate From Scratch
**Not recommended.** The script is found, well-written, and includes the critical NAT redirect workaround. There is no need to recreate it.

### Recommended Action: **Option A first, then Option B after verification**

1. Get new DL380 iLO credentials from Toti
2. Update `test_ilo_controller.py` with new credentials
3. Run connectivity test
4. If successful, recover into current workspace structure
5. Document the iLO control capability in `self_state.json` and `PROJECT_S_OVERVIEW.md`

---

## 8. File Inventory

| File | Path | Size | Role |
|------|------|------|------|
| `ilo_controller.py` | `project_s/infrastructure/ilo_controller.py` | 689 lines | Main implementation |
| `test_ilo_controller.py` | `project_s/infrastructure/test_ilo_controller.py` | 88 lines | Live connectivity test |
| `__init__.py` | `project_s/infrastructure/__init__.py` | 10 lines | Module export |
| `__main__.py` | `project_s/infrastructure/__main__.py` | ~10 lines | Entry point |

---

**Készítette:** Cline
**Dátum:** 2026-05-15
**Verzió:** v1.0