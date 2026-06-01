# Server Phase 1 — Host LAN Reachability Discovery

**Date:** 2026-05-15
**Type:** Read-only discovery — no state-changing operations
**Command Used:** iLO Redfish API queries + TCP port probes + ARP table inspection

---

## 1. Executive Verdict

**Is the host OS reachable?** NO — the new DL380 Gen9 host OS has no IP address configured on any of its 4 Ethernet interfaces.

**Why:** The iLO Redfish API reports all 4 host NICs with `IPv4Addresses: [null]` and `IPv6Addresses: [null]`. The host LAN cable was just connected by Toti, but the Windows Server OS has not obtained or been assigned an IP address.

**What this means:** The server is physically powered on (iLO confirmed), but the host OS network stack is not yet configured. The next step is to use iLO remote console or local console to inspect the Windows Server network configuration and either enable DHCP or assign a static IP.

---

## 2. New DL380 Host IP Candidate(s)

**No candidate IPs identified.** The new DL380 host OS has no IP address.

### Evidence from iLO Redfish API

The iLO reports 4 host Ethernet interfaces, all with null IP addresses:

| NIC | MAC Address | IPv4 | IPv6 | FullDuplex | Speed |
|-----|-------------|------|------|------------|-------|
| 1 | F4:03:43:3E:C6:80 | null | null | false | null |
| 2 | F4:03:43:3E:C6:81 | null | null | false | null |
| 3 | F4:03:43:3E:C6:82 | null | null | false | null |
| 4 | F4:03:43:3E:C6:83 | null | null | false | null |

**Key observation:** All 4 NICs show `FullDuplex: false` and `SpeedMbps: null` — this typically means the network cable is either not connected to those specific ports, or the host OS is not negotiating link. Since Toti just connected the LAN cable, it's possible the cable is connected to a different port than the one the OS is configured to use, or the OS network stack hasn't initialized yet.

### MAC Address Vendor Clue

The MAC prefix `F4:03:43` is an HPE/OCP (Oracle) registered OUI, consistent with the Broadcom NetXtreme-B adapters found in the DL380 Gen9.

---

## 3. Evidence Used to Identify Candidates

### Source A: iLO / Redfish API (PRIMARY)

**Endpoint:** `https://46.253.140.72:89/redfish/v1/Systems/1/EthernetInterfaces/`

**Result:** 4 host NICs found, all with null IPv4/IPv6 addresses.

**Endpoints tried:**
- `/redfish/v1/Systems/1/EthernetInterfaces/` — 200 OK, 4 members
- `/redfish/v1/Systems/1/NetworkInterfaces/` — 404
- `/redfish/v1/Managers/1/NetworkInterfaces/` — 404

### Source B: Local ARP Table (SECONDARY)

The dev machine's ARP table was inspected for the new DL380's MAC range (`F4:03:43:3E:C6:xx`). **No matches found.**

The only MAC in the `F4:03:43` range in the ARP table is `192.168.1.89` with MAC `f4-03-43-41-95-ca` — this is the **iLO management processor**, not the host OS.

### Source C: Subnet Probing (TERTIARY)

A TCP port scan of `192.168.1.80-100` for RDP (3389) found one open port:
- `192.168.1.88` — RDP OPEN

However, the MAC for `192.168.1.88` is `e4-11-5b-e3-68-ba`, which does NOT match any of the new DL380's NIC MACs. This is a different machine on the network (likely the old Windows Server 2012 R2 production machine or another device).

---

## 4. Port Reachability Table

### 192.168.1.88 (NOT the new DL380 — different MAC)

| Port | Service | Status | Notes |
|------|---------|--------|-------|
| 3389 | RDP | OPEN | Different machine |
| 22 | SSH | closed | |
| 5985 | WinRM | OPEN | Different machine |
| 5986 | WinRM-HTTPS | closed | |
| 445 | SMB | OPEN | Different machine |
| 80 | HTTP | OPEN | Different machine |
| 443 | HTTPS | closed | |

### 192.168.1.89 (iLO management processor — NOT host OS)

| Port | Service | Status | Notes |
|------|---------|--------|-------|
| 3389 | RDP | closed | iLO, not host |
| 22 | SSH | OPEN | iLO has SSH (expected) |
| 5985 | WinRM | closed | iLO, not host |
| 5986 | WinRM-HTTPS | closed | iLO, not host |
| 445 | SMB | closed | iLO, not host |

### New DL380 Host OS

**No IP assigned — no ports to probe.**

---

## 5. Preferred Next Access Method

**iLO Remote Console first.**

Since the host OS has no IP configured, the only way to interact with the Windows Server network configuration is through the iLO remote console (HTML5 or KVM over IP).

**Steps:**
1. Open iLO web interface at `https://46.253.140.72:89` (credentials: Administrator / PTSYK7BF)
2. Launch Remote Console (KVM)
3. Inspect Windows Server network configuration
4. Either:
   - Enable DHCP (if a DHCP server exists on the network)
   - Assign a static IP (e.g., `192.168.1.90` with gateway `192.168.1.1`)
   - Enable the network adapter if it's disabled

**After IP is configured:**
- RDP (3389) is the preferred interactive access method (Windows Server)
- WinRM (5985) is also open on the network, could be enabled for PowerShell remoting
- SSH (22) is not standard on Windows Server but can be enabled via OpenSSH

---

## 6. What Is Confirmed

| Item | Status |
|------|--------|
| New server model | HP ProLiant DL380 Gen9 |
| Serial | CZ3733LABY |
| BIOS | P89 v3.40 (08/29/2024) |
| Power state | ON |
| Health | OK |
| iLO access | Working via `https://46.253.140.72:89` |
| Host NICs detected | 4 (MACs F4:03:43:3E:C6:80-83) |
| Host NIC link status | FullDuplex=false, Speed=null (no link negotiation) |
| Host IP configuration | All IPv4/IPv6 addresses are null |
| Host LAN cable | Just connected by Toti |
| Host OS | Expected Windows Server 2019 (unverified) |
| iLO redirect workaround | Working (192.168.1.89 → public endpoint) |

---

## 7. What Remains Unknown

| Item | Status |
|------|--------|
| Host OS IP address | Unknown (no IP configured) |
| Host OS identity | Expected Windows Server 2019, unverified |
| Host OS running state | Unknown (could be booted, could be at login screen, could be in BIOS) |
| Which NIC port the LAN cable is plugged into | Unknown (4 NICs, only 1 cable) |
| Whether DHCP server exists on network | Unknown |
| Whether the Tesla M60 is recognized by host OS | Unknown |
| Whether NVMe drives are initialized | Unknown |
| Whether the old Windows Server 2012 R2 is still installed or replaced | Unknown |

---

## 8. Exact Next Action for Toti

**Option A — iLO Remote Console (recommended, no physical access needed):**
1. Open `https://46.253.140.72:89` in browser (credentials: Administrator / PTSYK7BF)
2. Launch Remote Console (KVM over IP)
3. Check if Windows Server is visible at the login screen
4. If visible: check network adapter status in Windows
5. Either enable DHCP or assign a static IP
6. Once IP is assigned, report it back for RDP access

**Option B — Physical console (if Toti is near the server):**
1. Connect a monitor and keyboard to the DL380 Gen9
2. Check if Windows Server is booting
3. Check network adapter status in Windows Network Settings
4. Either enable DHCP or assign a static IP
5. Report the IP back

**Option C — iLO Virtual Media / DHCP configuration:**
1. In iLO, check if there's a DHCP configuration option for the host
2. Some iLO versions allow setting host NIC to DHCP mode remotely
3. If available, enable DHCP and wait for lease

**After Toti obtains an IP:**
- The next step will be RDP into the server
- Then proceed with Phase 1 deployment (NVIDIA drivers, Python, llama.cpp)

---

## Appendix A: iLO Redfish NIC Data (Raw)

```json
{
  "Members": [
    {"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/1/"},
    {"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/2/"},
    {"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/3/"},
    {"@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/4/"}
  ],
  "Total": 4
}
```

**NIC 1:** MAC=F4:03:43:3E:C6:80, IPv4=null, IPv6=null, FullDuplex=false, Speed=null
**NIC 2:** MAC=F4:03:43:3E:C6:81, IPv4=null, IPv6=null, FullDuplex=false, Speed=null
**NIC 3:** MAC=F4:03:43:3E:C6:82, IPv4=null, IPv6=null, FullDuplex=false, Speed=null
**NIC 4:** MAC=F4:03:43:3E:C6:83, IPv4=null, IPv6=null, FullDuplex=false, Speed=null

---

**Készítette:** Cline
**Dátum:** 2026-05-15
**Verzió:** v1.0