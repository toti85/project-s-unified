# MS-AO5 AO5_T4 NVR Remote Access Fix — PREP Report — 2026-06-05

## Deliverables Checklist

| Item | Answer |
|------|--------|
| A. ao5_t4_nvr_fix.py created? | **YES** |
| B. script covers all 4 tasks? | **YES** |
| C. next_prompt.md created? | **YES** |
| D. did you execute or simulate? | **NO** |

---

## Script: ao5_t4_nvr_fix.py

**Path:** `orchestrator_runtime/sandbox/ao5_t4_nvr_fix.py`

**4 Tasks Covered:**

| Task | Function | Description |
|------|----------|-------------|
| 1 | `task1_disable_upnp()` | NVR UPnP disable via ISAPI (GET current → PUT disable → GET verify) |
| 2 | `task2_nvr_state()` | NVR current state check (deviceInfo + network interface) |
| 3 | `task3_router_portforward()` | Router port-forward rules (HTTP:85, RTSP:554, TLS:8443) |
| 4 | `task4_verification()` | Verification summary (remote access URLs, next steps) |

**Safety:**
- Passwords input at runtime via `input()` — NEVER hardcoded
- Digest auth for NVR (HTTPDigestAuth)
- MD5 cookie auth for router (TP-LINK TL-WR940N)
- All requests have 10s timeout
- Graceful error handling (try/except on all tasks)

---

## Handoff Files

### next_prompt.md
- **Path:** `orchestrator_runtime/cline_inbox/next_prompt.md`
- **Content:** AO5_T4 — NVR Remote Access Fix execution instructions
- **Script:** `orchestrator_runtime/sandbox/ao5_t4_nvr_fix.py`

### prompt_ready.json
- **Path:** `orchestrator_runtime/cline_inbox/prompt_ready.json`
- **Checksum:** 6c7c5b5c1b5d9419 (SHA-256 first 16 chars of next_prompt.md)
- **Protocol:** FA1_HANDOFF_V1
- **Run ID:** AO5_T4
- **Risk:** MEDIUM (network configuration changes)

---

## Safety

- PREP ONLY: **YES**
- No execution or simulation: **YES**
- No output_ready.json written: **YES**
- No src/ modifications: **YES**
- No self_state.json modifications: **YES**
- Passwords never hardcoded: **YES**