# AO5_T3 NVR Remediation Action Plan

## 1. Current NVR State

The currently documented NVR is a Hikvision DS-7632NI-I2 at `192.168.1.111:85`, confirmed via ISAPI and web access records. The NVR firmware is `V4.61.025 Build 220905`, which the audit describes as outdated and still requiring upgrade for later Hikvision security fixes. The unit has 22 inventoried channels, with 6 channels offline according to the NVR operations log, while the earlier passive LAN audit from 2026-05-23 had only confirmed 6 reachable cameras and could not positively identify the NVR at that time. Two ~5.46 TB HDDs are present and full in quota/circular overwrite mode, which is documented as normal rather than a fault.

Time configuration was partially remediated already: `timeMode` was changed from manual to NTP, the NTP server was set to `216.239.35.0`, and timezone was corrected to `CST-3:00:00` on 2026-05-27. DNS write attempts through ISAPI failed repeatedly because the firmware rejects the relevant XML PUT path, so DNS must be set manually through the web UI if needed. UPnP NAT mapping is enabled on the NVR, but the documented status is conflict/inactive across relevant ports, so remote access is not functioning as intended.

The camera estate is mixed across reports. The firmware audit documents multiple DS-2CD2T42WD-I8 cameras with `V5.5.53 build 180730`, which is described as critically outdated. The passive LAN audit also shows that some earlier device assumptions were incomplete or inconsistent, so the current action plan should rely on the later NVR/ISAPI-based inventory where possible and treat earlier discovery-only observations as lower-confidence baseline evidence.

## 2. Identified Issues

1. High severity: NVR firmware is outdated and the audit explicitly flags missing fixes associated with later Hikvision releases.
2. High severity: Camera firmware is much older than the NVR firmware and is marked as critically outdated for the documented DS-2CD2T42WD-I8 units.
3. High severity: Remote access is not operational because UPnP NAT requests are conflicting at the router layer.
4. High severity: Multiple channels are offline; the operations log records 6 offline channels and the older LAN audit also showed addressing gaps that support a device availability problem.
5. Medium severity: DNS cannot be updated through the tested ISAPI path on the current firmware, so web UI/manual intervention is required.
6. Medium severity: DST automatic switching is not supported through the audited firmware path, so seasonal timezone rollback needs manual handling.
7. Medium severity: Router audit remained incomplete because another admin session was active and SSH compatibility/tooling was blocked by legacy KEX constraints.
8. Low severity: HTTP is on non-standard port `85` and HTTPS is not actively serving on the expected port, which is not the main failure but reduces cleanliness and security posture.
9. Information gap: The doc separation report states there are no NVR-specific known_gaps in `self_state.json`, so NVR follow-up currently depends on report-based tracking rather than centralized self-state tracking.

## 3. Action Items

### Action 1 — Export NVR configuration before any firmware change

- What: Perform full config export and capture screenshots of recording schedule, camera management, and HDD info.
- Why: The firmware audit marks config backup as mandatory before upgrade, and current state must be recoverable if the upgrade fails or resets settings.
- How: Log into `http://192.168.1.111:85/` with authorized admin credentials, then use Maintenance -> Import/Export for config export; capture Recording Schedule, Camera Management, and HDD Info screens.
- Estimated effort: 20-30 minutes.

### Action 2 — Verify current operational baseline on the NVR itself

- What: Confirm live view, offline channel list, channel-to-IP mapping, storage state, and exact current firmware on the NVR UI.
- Why: The reports combine passive network observations and later ISAPI-based findings; before remediation, one authoritative baseline is needed.
- How: In the NVR web UI or local display, record the exact online/offline channels, verify whether the offline count is still 6, confirm HDD health, and save the current firmware/build number.
- Estimated effort: 20-30 minutes.

### Action 3 — Manually set/verify DNS in the NVR web UI

- What: Ensure DNS is configured manually in the UI to `8.8.8.8` and `8.8.4.4` if remote name resolution or online upgrade workflows require it.
- Why: ISAPI-based DNS remediation failed repeatedly due to firmware schema limitations; this remains an unresolved manual step.
- How: Open `http://192.168.1.111:85/` -> Configuration -> Network -> Basic Settings -> DNS, then verify or set the values documented in the reports.
- Estimated effort: 5-10 minutes.

### Action 4 — Resolve router-side port mapping conflicts

- What: Complete the router audit and identify which manual forwards conflict with the NVR's UPnP requests.
- Why: Remote access is currently broken because HTTP/SDK/RTSP mappings are reported as `conflict`, not active.
- How: Access the TP-LINK TL-WR940N after the other admin session ends, inspect existing port forwards, compare them with the NVR's desired mappings (`85`, `554`, `8000`, `8443` behavior from the reports), and either clean up conflicts or replace UPnP reliance with explicit manual forwards.
- Estimated effort: 30-60 minutes.

### Action 5 — Decide and execute NVR firmware upgrade path

- What: Upgrade the DS-7632NI-I2 from `V4.61.025 Build 220905` to an appropriate later Hikvision release for the model family.
- Why: The firmware audit explicitly states later fixes are needed and highlights unresolved security exposure on the current version.
- How: Download the correct `DS-7600NI-I2` family firmware from the official Hikvision source, validate model compatibility, ensure stable power/UPS, then perform local or web-based upgrade exactly as documented in the firmware audit.
- Estimated effort: 45-90 minutes including prep and reboot validation.

### Action 6 — Re-test time, NTP, timezone, and remote access after upgrade

- What: Confirm that the previously remediated time settings persist and re-check whether network-management endpoints behave differently after firmware upgrade.
- Why: Firmware change can reset or alter time/network behavior, and it may also remove some of the current ISAPI limitations.
- How: Re-run checks for `timeMode`, NTP server, timezone, UPnP status, and DNS behavior; document whether DST support or network interface writes improved.
- Estimated effort: 15-25 minutes.

### Action 7 — Triage offline channels one by one

- What: Investigate each offline camera/channel physically and logically.
- Why: Offline channels represent direct coverage gaps; firmware and remote-access cleanup will not solve missing power, cabling, PoE, switch, or per-camera failures by itself.
- How: For each offline channel, identify expected IP/device, verify power, link lights, switch/PoE path, ping reachability, web login, and camera firmware/version if reachable.
- Estimated effort: 15-30 minutes per channel, depending on site access.

### Action 8 — Plan phased camera firmware updates after NVR stabilization

- What: Prepare a camera-by-camera upgrade plan for the documented DS-2CD2T42WD-I8 fleet.
- Why: The audit marks the camera firmware as critically outdated, older than the NVR, and likely the largest residual technical risk after the NVR itself.
- How: Build an inventory table with channel, IP, model, current firmware, target firmware, upgrade order, rollback notes, and operational window; update only after recording and playback are verified stable on the upgraded NVR.
- Estimated effort: 60-120 minutes planning, then separate execution windows.

## 4. Quick Wins

1. Verify that the NVR still shows `NTP` mode and `216.239.35.0` as the NTP server. Estimated effort: 5 minutes.
2. Manually confirm DNS settings in the web UI, because ISAPI cannot set them reliably on current firmware. Estimated effort: 5-10 minutes.
3. Export configuration and take screenshots before any other change. Estimated effort: 20 minutes.
4. Confirm whether the documented offline channels are still the same today; if not, note the delta before deeper remediation. Estimated effort: 10-15 minutes.
5. Schedule router-access time with the other admin so the incomplete TP-LINK audit can resume without guesswork. Estimated effort: 5 minutes coordination.

## 5. Verification Steps

1. Configuration backup verification: confirm the export file exists and can be stored safely alongside dated screenshots.
2. NVR baseline verification: after login, confirm model, firmware, channel count, offline list, HDD state, and live view match or intentionally supersede the reports.
3. DNS/NTP verification: in the UI or via follow-up read-only checks, confirm DNS values, `timeMode=NTP`, timezone `CST-3:00:00`, and successful time sync status.
4. Router/remoting verification: after port-forward cleanup, confirm expected external mappings no longer show `conflict` and test remote reachability in a controlled way.
5. Firmware verification: after NVR upgrade, confirm the new firmware/build number and re-check login, recording, live view, HDD visibility, and network settings.
6. Offline camera verification: each previously offline channel should either return online with image/stream available or be documented with a specific hardware/network root cause.
7. Playback verification: review recent footage on at least one representative online channel after remediation to prove recording continuity.
8. Final acceptance check: record a short before/after summary covering firmware version, remote-access status, offline-channel count, and any remaining manual tasks such as seasonal DST rollback.
