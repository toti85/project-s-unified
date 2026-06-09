# AO5_T6 Camera System Clean Reconfiguration Plan

**Scope:** Hikvision NVR/camera reconfiguration only. No factory reset yet. No firmware upgrade yet. No existing NVR config deletion until export and screenshots are confirmed.

## 1. Current NVR State

The documented NVR is a Hikvision DS-7632NI-I2 at `192.168.1.111:85`. The latest NVR audit records firmware `V4.61.025 Build 220905`, NTP already enabled with `216.239.35.0`, DNS write attempts blocked by firmware XML/schema limits, and UPnP NAT port-mapping in a conflict/inactive state. The web UI is reachable on port 85 with Digest auth, but the earlier live task output showed `401 Unauthorized` when credentials were not accepted or not present in the session.

The camera estate has two distinct evidence layers. The LAN audit from 2026-05-23 confirmed 6 cameras online at `192.168.1.62`, `.63`, `.65`, `.67`, `.68`, `.69`, while the AO5_T5 inventory on 2026-06-05 expanded the working set to 15 scanned addresses across `192.168.1.60-76`. That later inventory shows 7 cameras already on `V5.5.53` and 2 cameras on `V5.5.82`, with the remaining addresses either unreachable, skipped due to HTTP 401, or not yet documented in current sources.

The cleanest documented baseline is therefore:

- NVR: reachable, but remote-access hygiene still needs reconfiguration.
- Camera group A: `192.168.1.60`, `.62`, `.63`, `.65`, `.67`, `.68`, `.69` are documented as active and/or authenticated cameras.
- Camera group B: `192.168.1.72`, `.73` are already on `V5.5.82` and should be preserved.
- Camera group C: `192.168.1.61`, `.64`, `.66`, `.71`, `.74`, `.75`, `.76` are not confirmed healthy in the current source set and need one-by-one verification.
- Camera group D: `192.168.1.70` returned HTTP 401 in the AO5_T5 inventory, so it may exist but requires credentials or a different auth path.
- `192.168.1.77-79` are not documented in the current source set and remain unknown.

### Phase 2 inventory snapshot

| IP | Desired channel | Reachable | HTTP status / evidence | Model | Firmware | Serial | MAC | Auth status | NVR channel mapping | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 192.168.1.60 | ch1 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780993765 | Not documented | Authenticated in dry-run | ch1 | OK |
| 192.168.1.61 | ch2 | No current evidence | Not documented | Not documented | Not documented | Not documented | Not documented | Not documented | ch2 offline in NVR audit | OFFLINE |
| 192.168.1.62 | ch3 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780993075 | Not documented | Authenticated in dry-run | ch3 | OK |
| 192.168.1.63 | ch4 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780993274 | Not documented | Authenticated in dry-run | ch4 | OK |
| 192.168.1.64 | ch5 | No current evidence | Timeout in AO5_T5 inventory | Not documented | Not documented | Not documented | Not documented | Not documented | not mapped in source set | OFFLINE |
| 192.168.1.65 | ch6 konveer1 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780993270 | Not documented | Authenticated in dry-run | ch6 | OK |
| 192.168.1.66 | ch7 zadnia1 | No current evidence | Not documented | Not documented | Not documented | Not documented | Not documented | Not documented | ch7 offline in NVR audit | OFFLINE |
| 192.168.1.67 | ch8 konveer2 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780993262 | Not documented | Authenticated in dry-run | ch8 | OK |
| 192.168.1.68 | ch9 zadnia2 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780992799 | Not documented | Authenticated in dry-run | ch9 | OK |
| 192.168.1.69 | ch10 dvir2 | Yes | 200 in AO5_T5 prep | UNKNOWN in report | V5.5.53 | BBWR780992367 | Not documented | Authenticated in dry-run | ch10 | OK |
| 192.168.1.70 | ch11 Vulica | Yes | HTTP 401 in AO5_T5 inventory | Not documented | Not documented | Not documented | Not documented | AUTH_REQUIRED | ch11 | AUTH_REQUIRED |
| 192.168.1.71 | ch12 | No | Timeout in AO5_T5 inventory | Not documented | Not documented | Not documented | Not documented | Not documented | ch12 | OFFLINE |
| 192.168.1.72 | ch13 | Yes | 200 / up to date | UNKNOWN in report | V5.5.82 | Not documented | Not documented | Authenticated in inventory | ch13 | OK |
| 192.168.1.73 | ch14 | Yes | 200 / up to date | UNKNOWN in report | V5.5.82 | Not documented | Not documented | Authenticated in inventory | ch14 | OK |
| 192.168.1.74 | ch15 | No | Timeout in AO5_T5 inventory | Not documented | Not documented | Not documented | Not documented | Not documented | ch15 | OFFLINE |
| 192.168.1.75 | ch16 | No | Timeout in AO5_T5 inventory | Not documented | Not documented | Not documented | Not documented | Not documented | ch16 | OFFLINE |
| 192.168.1.76 | ch17 | No | Timeout in AO5_T5 inventory | Not documented | Not documented | Not documented | Not documented | Not documented | ch17 | OFFLINE |
| 192.168.1.77 | not documented | Unknown | No current match in source set | Not documented | Not documented | Not documented | Not documented | Not documented | Unknown | UNKNOWN |
| 192.168.1.78 | not documented | Unknown | No current match in source set | Not documented | Not documented | Not documented | Not documented | Not documented | Unknown | UNKNOWN |
| 192.168.1.79 | not documented | Unknown | No current match in source set | Not documented | Not documented | Not documented | Not documented | Not documented | Unknown | UNKNOWN |

## 2. Identified Issues

1. The NVR remote-access path is not cleanly configured yet. The NVR has documented UPnP conflict/inactive behavior, and the router audit was still incomplete because another admin session blocked full verification.
2. The camera inventory is inconsistent across time slices. Some channels are confirmed online, some are offline, one returns HTTP 401, and `192.168.1.77-79` are not documented in the current source set.
3. Camera firmware is mixed. Seven cameras are documented on `V5.5.53`, while two are already on `V5.5.82`; this means any reconfiguration must preserve the already-updated units and avoid accidental downgrade.
4. NVR-side DNS cannot be changed reliably via the tested ISAPI path on the current firmware, so manual UI verification is required before any network reconfiguration is considered complete.
5. The NVR is still on an older firmware branch, but this task explicitly forbids firmware installation. The correct operational stance is HOLD, not upgrade.
6. The current source set does not contain NVR-specific entries in `self_state.json`, so there is no central gap tracker to coordinate this work.

## 3. Action Items

### Phase 1 — Backup first, then freeze the baseline

- What: Export the NVR configuration and capture screenshots or HTML dumps of IP Camera list, Recording Schedule, HDD Info, Network TCP/IP, NAT/UPnP, Platform Access, and User list.
- Why: The plan must be recoverable. No channel cleanup should happen until the current state is archived.
- How: Log into `http://192.168.1.111:85/`, export the configuration, and save the requested UI pages or HTML dumps with timestamps before touching any camera entry.
- Estimated effort: 30-45 minutes.

### Phase 2 — Re-scan the full 192.168.1.60-79 range one camera at a time

- What: Verify each IP in the requested range, record reachability, HTTP status, model, firmware, serial, MAC if available, auth status, and NVR mapping.
- Why: The current evidence shows partial coverage; reconfiguration must use a clean inventory rather than stale assumptions.
- How: Check each IP individually, record whether it is OK, AUTH_REQUIRED, OFFLINE, DUPLICATE, or UNKNOWN, and compare the result against the desired channel table below.
- Estimated effort: 45-90 minutes depending on credential and network response behavior.

### Phase 3 — Normalize the channel map without deleting config yet

- What: Prepare the desired channel layout and compare it against the live NVR mapping before removing stale entries.
- Why: This prevents accidental loss of a working camera during cleanup.
- How: Use the desired table from this task as the target, then mark mismatches, duplicate addresses, and offline placeholders.
- Estimated effort: 20-30 minutes.

### Phase 4 — Clean reconfiguration, one channel at a time

- What: Remove stale/offline duplicate camera entries, re-add each camera manually, set names, and confirm per-channel settings.
- Why: A one-channel-at-a-time workflow reduces risk and makes failures obvious.
- How: For each channel, first remove or disable only the stale entry, then re-add the intended camera, then verify live view and recording before moving to the next channel.
- Estimated effort: 15-25 minutes per channel pair.

### Phase 5 — Lock in recording and retention behavior

- What: Rebuild recording schedules and verify circular recording on the HDDs.
- Why: The plan must preserve long-term storage behavior and avoid accidental gaps after cleanup.
- How: Set schedule templates, verify playback for at least one representative camera, and confirm HDD quota/circular overwrite remains active.
- Estimated effort: 30-45 minutes.

### Phase 6 — Network hardening after channel cleanup

- What: Disable NVR UPnP and use manual router forwarding only if remote access is genuinely required.
- Why: The documented UPnP state is conflict-prone and does not produce clean remote access.
- How: Confirm the NVR UPnP status is off, then on the router keep only explicitly needed forwards for HTTP 85, RTSP 554, and TLS 8443.
- Estimated effort: 20-30 minutes.

### Phase 7 — Firmware decision gate

- What: Check official firmware availability, but do not install anything.
- Why: This task is explicitly a clean reconfiguration plan, not a firmware operation.
- How: If the exact model/region firmware package is not confirmed for the deployment, keep the upgrade decision at HOLD. The plan should proceed only with reconfiguration and inventory work.
- Estimated effort: 10-15 minutes.

## 4. Quick Wins

1. Export the NVR config before making any channel changes. This is the single most important safety step.
2. Capture the NVR UI pages listed in Phase 1 so the baseline is frozen before cleanup.
3. Confirm `192.168.1.72` and `192.168.1.73` stay untouched because they are already on `V5.5.82`.
4. Mark `192.168.1.70` as AUTH_REQUIRED instead of treating it as offline; the current inventory shows HTTP 401 rather than timeout.
5. Mark `192.168.1.77-79` as UNKNOWN, not as failures, because they are not documented in the current source set.

## 5. Verification Steps

1. Backup verification: confirm the NVR export file exists and that screenshots or HTML dumps are saved with timestamps.
2. Inventory verification: re-check `192.168.1.60-79` and confirm every address has one of the defined statuses with no ambiguous blanks.
3. Channel-map verification: confirm the live NVR mapping matches the desired ch1-ch11 table before removing any stale entry.
4. Recording verification: open live view and playback on at least one representative camera after every small group of changes.
5. HDD verification: confirm circular overwrite / quota mode is still active and that the HDDs remain healthy after reconfiguration.
6. Network verification: confirm UPnP is disabled on the NVR and that only the minimum necessary router forwards remain.
7. Firmware verification: confirm the firmware decision remains HOLD unless exact model/region package confirmation is obtained and a separate upgrade task is authorized.
