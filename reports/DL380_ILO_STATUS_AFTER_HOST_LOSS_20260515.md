# DL380 iLO Status Report — After Host OS Network Loss

**Date:** 2026-05-17 ~00:03 UTC+3
**Type:** Read-only iLO status investigation
**Target:** 192.168.1.180 (new HP ProLiant DL380 Gen9)
**iLO Endpoint:** `https://46.253.140.72:89` (external NAT) → rewrites to `https://192.168.1.89` (internal)

---

## 1. Executive Summary

The DL380 Gen9 server is **physically powered ON** and **iLO is fully operational**. However, the **host OS network stack reports no IP addresses on any of its 4 NICs**. The server was reachable via LAN earlier today (2026-05-15 ~14:56 UTC+3) but is now completely unreachable from the LAN.

---

## 2. iLO Connectivity

| Check | Result |
|-------|--------|
| **iLO reachable via public endpoint** | **YES** — `https://46.253.140.72:89` responded |
| **iLO redirect workaround** | Working — 302 redirect to `192.168.1.89` rewritten back to public endpoint |
| **iLO Firmware** | iLO 4 v2.82 |
| **Authentication** | Success (Administrator / credentials valid) |
| **Redfish API** | v1 responsive |

**A. iLO reachable?** YES

---

## 3. Server Power State

| Check | Result |
|-------|--------|
| **PowerState** | **On** |
| **System State** | Enabled |
| **HostOSBoot** | Not directly exposed via Redfish (requires HP Insight Agents) |

The server is receiving power and the iLO management processor is active.

**B. Power state:** ON

---

## 4. Health Summary

| Item | Value |
|------|-------|
| **Model** | ProLiant DL380 Gen9 |
| **Manufacturer** | HPE |
| **Serial Number** | CZ3733LABY |
| **BIOS Version** | P89 v3.40 (08/29/2024) |
| **System Type** | Physical |
| **Overall Health** | **OK** |
| **Status State** | Enabled |

No hardware faults, thermal issues, or power supply problems detected at the iLO level.

**C. Health summary:** OK — no faults detected

---

## 5. Host OS Network / NIC State

### 5.1 Host EthernetInterfaces (4 ports)

iLO reports **4 host Ethernet interfaces**, all with **null IP addresses**:

| Interface | State | LinkStatus | IPv4 | IPv6 | MAC | Speed |
|-----------|-------|------------|------|------|-----|-------|
| **NIC 1** | Enabled, Health OK | N/A | None | None | N/A | None |
| **NIC 2** | N/A | N/A | None | None | N/A | None |
| **NIC 3** | N/A | N/A | None | None | N/A | None |
| **NIC 4** | N/A | N/A | None | None | N/A | None |

**Key finding:** All 4 host NICs report `IPv4Addresses: [{'Address': None}]` and `IPv6Addresses: [{'Address': None}]`. No MAC addresses, no link status, no speed reported.

### 5.2 iLO Management NIC

| Item | Value |
|------|-------|
| **IPv4 Address** | `192.168.1.89` (Static) |
| **Gateway** | `192.168.1.1` |
| **Subnet Mask** | `255.255.255.0` |
| **IPv6 Address** | `FE80::F603:43FF:FE41:95CA` (SLAAC) |
| **Permanent MAC** | `F4:03:43:41:95:CA` |
| **Speed** | 100 Mbps |
| **Status** | Enabled, Health OK |

### 5.3 Interpretation

The host OS 4 NICs (which should be on the rear panel of the DL380) are reporting **no link, no IP, no MAC, no speed** to iLO. This means:

1. **The host OS may be crashed/hung** — Windows Server is not responding to iLO's HostCorrelation queries
2. **The NICs may be physically disconnected** — cables unplugged from the rear panel
3. **The NICs may be in a PCIe adapter card** that iLO cannot enumerate (requires HP Insight Management Agents installed in the OS for full PCIe NIC discovery)
4. **The host OS may have lost network configuration** — NIC drivers loaded but no IP assigned

**D. Host NIC/IP state:** All 4 NICs report NO IP, NO link, NO MAC. Host OS network stack is non-responsive or NICs are physically disconnected.

---

## 6. Event Logs

| Log Service | Available? | Result |
|-------------|------------|--------|
| **Log1** (Event Log) | NO | 404 — endpoint not found |
| **SystemLog** | NO | 404 — endpoint not found |

The iLO 4 v2.82 firmware on this server does not expose Log1 or SystemLog via the Redfish API. This may be a firmware limitation or the log services may need to be enabled in iLO configuration.

**E. Errors/events found:** No event logs accessible via Redfish API. No hardware fault indicators in health summary.

---

## 7. Additional Sensor Data (from Chassis)

The sensor endpoint was not queried in this session. Based on the health summary showing OK, no critical sensor alerts are active.

---

## 8. Timeline of Events

| Time | Event |
|------|-------|
| **2026-05-15 ~14:56 UTC+3** | WinRM remote inventory completed successfully via LAN (192.168.1.180:5985) |
| **2026-05-15 ~14:56 UTC+3** | RDP enablement completed successfully via LAN |
| **2026-05-15 ~14:56 UTC+3** | RDP port 3389 confirmed OPEN on LAN |
| **2026-05-15 evening** | Server was last confirmed reachable via LAN |
| **2026-05-16 ~00:48 UTC+3** | External WinRM verification attempt — server unreachable (both LAN and external) |
| **2026-05-17 ~00:03 UTC+3** | iLO check — server ON, health OK, but all 4 host NICs report null |

The server went from fully operational (WinRM/RDP working on LAN) to completely unreachable over approximately 10 hours.

---

## 9. Root Cause Assessment

The most likely explanation is one of:

1. **Windows Server crashed/hung** — The OS stopped responding but the hardware remained powered on (iLO continues to function independently of the host OS)
2. **Network cables were disconnected** — Someone physically unplugged the LAN cables from the rear panel
3. **Power cycle during outage** — If there was a power interruption, the server may have auto-booted but the OS failed to initialize NICs properly
4. **NIC adapter failure** — The PCIe NIC card (if present) failed or lost connection

**iLO confirms the hardware is fine** — power OK, health OK, management processor running. The issue is at the **host OS / NIC level**.

---

## 10. Recommended Next Steps

### Step 1: Check physical cabling (PRIORITY)
- Verify LAN cables are plugged into the correct rear panel ports of the DL380
- The 4 data NIC ports are separate from the iLO Dedicated NIC port
- Confirm cables are connected to the same switch as the iLO

### Step 2: Use iLO Remote Console to inspect host OS
- Open `https://46.253.140.72:89` in browser
- Login: `Administrator` / `PTSYK7BF`
- Launch HTML5 Remote Console (KVM)
- Check if Windows Server is displaying:
  - A login screen
  - A desktop (OS is running but no network)
  - A BSOD / crash screen
  - BIOS/UEFI setup

### Step 3: If OS is hung/crashed
- Use iLO to perform a **soft reset** (not power off):
  - Redfish: `POST /redfish/v1/Systems/1/Actions/ComputerSystem.Reset` with `ResetType: GracefulRestart`
  - Or via iLO Web UI: Remote Console → Actions → Reset Server → Graceful Restart

### Step 4: After OS comes back up
- Run `ipconfig /all` from an elevated command prompt
- Check if NICs have DHCP-assigned or static IPs
- Re-enable WinRM: `winrm quickconfig`
- Verify LAN connectivity from the dev machine

### Step 5: Re-attempt external WinRM verification
- Once LAN connectivity is restored, re-test:
  - `Test-NetConnection 192.168.1.180 -Port 5985`
  - `Test-NetConnection 46.253.140.72 -Port 15985`

---

## 11. Summary Table

| Check | Result |
|-------|--------|
| **A. iLO reachable?** | **YES** — `https://46.253.140.72:89` responded successfully |
| **B. Power state** | **ON** |
| **C. Health summary** | **OK** — no hardware faults |
| **D. Host NIC/IP state** | **ALL 4 NICs report NULL** — no IP, no link, no MAC |
| **E. Errors/events** | **None accessible** — Log1 and SystemLog endpoints return 404 |
| **F. Recommended next step** | **Use iLO KVM console** to inspect host OS screen; check physical LAN cable connection |

---

## 12. Credentials Reference

| Item | Value |
|------|-------|
| iLO URL (external) | `https://46.253.140.72:89` |
| iLO URL (internal) | `https://192.168.1.89` |
| iLO Username | `Administrator` |
| iLO Password | `PTSYK7BF` |
| iLO Firmware | iLO 4 v2.82 |
| Server Model | HP ProLiant DL380 Gen9 |
| Serial Number | CZ3733LABY |
| BIOS | P89 v3.40 (08/29/2024) |

---

**Report generated:** 2026-05-17 ~00:03 UTC+3
**Report type:** READ-ONLY — no state-changing operations performed
**Status:** Server hardware OK, host OS network non-responsive