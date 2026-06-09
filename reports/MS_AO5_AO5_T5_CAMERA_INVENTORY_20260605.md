# MS-AO5 AO5_T5 Camera Firmware Inventory — 2026-06-05

## Summary

| Metric | Count |
|--------|-------|
| Total cameras scanned | 15 |
| UP_TO_DATE (V5.5.82) | 2 |
| NEEDS_UPDATE (V5.5.53) | 7 |
| UNREACHABLE (timeout) | 6 |

## Full Inventory Table

| Channel | IP | Firmware | Status |
|---------|----|----------|--------|
| ch1 | 192.168.1.60 | V5.5.53 | NEEDS_UPDATE |
| ch3 | 192.168.1.62 | V5.5.53 | NEEDS_UPDATE |
| ch4 | 192.168.1.63 | V5.5.53 | NEEDS_UPDATE |
| ch5 | 192.168.1.64 | — | UNREACHABLE (timeout) |
| ch6 (konveer1) | 192.168.1.65 | V5.5.53 | NEEDS_UPDATE |
| ch8 (konveer2) | 192.168.1.67 | V5.5.53 | NEEDS_UPDATE |
| ch9 (zadnia2) | 192.168.1.68 | V5.5.53 | NEEDS_UPDATE |
| ch10 (dvir2) | 192.168.1.69 | V5.5.53 | NEEDS_UPDATE |
| ch11 | 192.168.1.70 | — | SKIP (HTTP 401) |
| ch12 | 192.168.1.71 | — | UNREACHABLE (timeout) |
| ch13 | 192.168.1.72 | V5.5.82 | UP_TO_DATE |
| ch14 | 192.168.1.73 | V5.5.82 | UP_TO_DATE |
| ch15 | 192.168.1.74 | — | UNREACHABLE (timeout) |
| ch16 | 192.168.1.75 | — | UNREACHABLE (timeout) |
| ch17 | 192.168.1.76 | — | UNREACHABLE (timeout) |

## Findings

- **7 cameras** on V5.5.53 need upgrade to V5.5.82
- **2 cameras** already on V5.5.82 (ch13, ch14)
- **6 cameras** unreachable (5 timeout + 1 HTTP 401 at .70 — different credentials)
- Model field returned UNKNOWN — ISAPI deviceModel field may use different XML tag name

## Scripts

| Script | Path |
|--------|------|
| Inventory script | `orchestrator_runtime/sandbox/ao5_t5_camera_fw_check.py` |
| DL380 runner | `orchestrator_runtime/sandbox/ao5_t5_dl380_runner.ps1` |

## Safety

- Inventory only — NO firmware upgrades performed
- No src/ modifications
- No self_state.json modifications
- Credentials only in sandbox script, never in reports