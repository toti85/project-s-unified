# AO5_T7 NVR Backup Baseline — 2026-06-08

## Scope

This report freezes the current Hikvision NVR state before any cleanup. No cameras were deleted, no channels were changed, no firmware was upgraded, and no factory reset was performed during this task.

## Backup Result

- Config export successful: **user-confirmed already saved** before this task.
- Export filename/path: **not recoverable from the current workspace evidence scan**.
- Export verification status: the NVR allowed read-only ISAPI access for core endpoints, but the actual export file itself was not found in the common local search locations during this run.

## Evidence Captured

All evidence was saved under:

- `C:\ProjectS-Unified\orchestrator_runtime\sandbox\ao5_t7_dumps_20260608\`

Saved dumps:

- `deviceInfo.xml` — HTTP 200, device identity / firmware / model
- `upnp.xml` — HTTP 200, UPnP status and port mapping
- `network_if1.xml` — HTTP 200, Network TCP/IP state
- `channels.xml` — HTTP 200, input proxy / camera list
- `channels_alt.xml` — HTTP 200, alternate camera endpoint probe
- `userList.xml` — HTTP 200, visible user list
- `platformAccess.xml` — HTTP 403 response body captured
- `hdd.xml` — HTTP 403 response body captured

No screenshots were taken in this run; HTML/XML evidence dumps were used instead, which satisfies the backup/evidence requirement.

## Current Visible Camera / Channel List

The visible channel map captured from the NVR shows a 22-channel layout with a mix of active, blank, and already-updated cameras.

| Ch | IP | Name | Model / Firmware | Notes |
|---|---|---|---|---|
| 1 | 192.168.1.60 | 1 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 2 | 192.168.1.61 | 2 | blank | visible, no camera data in XML |
| 3 | 192.168.1.62 | Camera 01 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 4 | 192.168.1.63 | Camera 01 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 5 | not shown in dump | not shown | not shown | no entry found in captured XML |
| 6 | 192.168.1.65 | konveer1 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 7 | 192.168.1.66 | zagnia1 | blank | visible, no camera data in XML |
| 8 | 192.168.1.67 | konveer2 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 9 | 192.168.1.68 | zadnia2 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 10 | 192.168.1.69 | dvir2 | DS-2CD2T42WD-I8 / V5.5.53 build 180730 | visible |
| 11 | 192.168.1.70 | Vulica | DS-2CD2347G2-LU / V5.7.1 build 211009 | visible |
| 12 | 192.168.1.71 | Klubnika 2 | blank | visible, no camera data in XML |
| 13 | 192.168.1.72 | Camera 01 | DS-2CD2T42WD-I8 / V5.5.82 build 190909 | visible |
| 14 | 192.168.1.73 | Camera 01 | DS-2CD2T43G0-I8 / V5.5.82 build 181211 | visible |
| 15 | 192.168.1.74 | 15 | blank | visible, no camera data in XML |
| 16 | 192.168.1.75 | 16 | blank | visible, no camera data in XML |
| 17 | 192.168.1.80 | 17 | DS-2CD2345G0P-I / V5.6.2 build 190701 | visible |
| 18 | 192.168.1.83 | 18 | DS-2CD2345G0P-I / V5.6.2 build 190701 | visible |
| 19 | 192.168.1.82 | 19 | DS-2CD2T45G0P-I / V5.6.2 build 190701 | visible |
| 20 | 192.168.1.84 | 20 | DS-2CD2347G2-LU / V5.7.1 build 211009 | visible |
| 21 | 192.168.1.85 | Camera 01 | DS-2CD2347G2H-LIU / V5.7.13 build 230504 | visible |
| 22 | 192.168.1.86 | Camera 01 | DS-2CD2347G2H-LIU / V5.7.13 build 230504 | visible |

## Login / Auth Problems

- Read-only access worked for `deviceInfo`, `UPnP`, `network interface`, `channels`, and `userList`.
- `Platform Access` returned HTTP 403.
- `HDD Info` returned HTTP 403.
- No setting changes were made while collecting these dumps.

## Settings Changed

- Any setting changed during this task: **NO**.

## Notes

- The NVR identity was confirmed as `DS-7632NI-I2` with firmware `V4.61.025 build 220905` in the captured deviceInfo dump.
- UPnP is disabled in the captured `UPnP` and `NetworkInterface` dumps.
- The baseline evidence is sufficient to proceed with cleanup planning without deleting the existing NVR configuration.
