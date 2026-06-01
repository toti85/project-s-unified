# SERVER PHASE 0: ACCESS & CONTROL DISCOVERY
**Mission:** Non-destructive audit of HP DL380 Gen9 remote access capabilities  
**Date:** 2026-05-15  
**Status:** COMPLETE — iLO confirmed reachable; OS IP unknown (not on 192.168.1.0/24)  
**Executed by:** GitHub Copilot + Toti  

---

## EXECUTIVE VERDICT

| Channel | Status | Detail |
|---------|--------|--------|
| iLO Redfish API (external NAT) | ✅ REACHABLE | `https://46.253.140.72:89` — full read/write |
| iLO Redfish API (internal LAN) | ✅ REACHABLE | `https://192.168.1.89:443` — TCP OPEN, 2ms RTT |
| iLO Web UI / KVM console | ✅ ACCESSIBLE | Login at `https://192.168.1.89` from dev machine |
| RDP (3389) on any LAN host | ❌ NOT FOUND | No open RDP on any 192.168.1.x alive host |
| SSH (22) | ❌ NOT PROBED | OS IP unknown; unreachable without IP |
| WinRM (5985/5986) | ❌ NOT PROBED | OS IP unknown; unreachable without IP |
| Server OS on 192.168.1.0/24 | ❌ ABSENT | OS host MACs not in ARP table anywhere |

**Recommended next access path:** iLO Web UI → HTML5 KVM Console → Windows desktop → `ipconfig` → discover OS IP.

---

## 1. LOCATED iLO SCRIPTS

All iLO tooling is present and operational:

| File | Purpose |
|------|---------|
| `C:\Users\Admin\ilo_extra.py` | **Read-only probe** — EthernetInterfaces, Host NICs, System Summary |
| `C:\Users\Admin\ilo_poweron.py` | Power control — checks state, sends power_on if Off |
| `C:\ProjectS-Unified\project_s\infrastructure\ilo_controller.py` | ILOController class — Redfish API, NAT redirect rewriting, all methods |

`ILOController` handles iLO's redirect from `192.168.1.89` back to the public NAT endpoint automatically. No credentials are stored in this report; refer to the scripts above for authentication details.

---

## 2. iLO CONNECTIVITY & SERVER STATE (Live Query — `ilo_extra.py`)

**iLO endpoint:** `https://46.253.140.72:89` (external) → rewrites to same after iLO redirect  
**iLO LAN endpoint:** `https://192.168.1.89` (internal, directly reachable from dev machine)

### iLO Management NICs
| NIC | Name | IPv4 | Origin |
|-----|------|------|--------|
| 1 | Manager Dedicated Network Interface | `192.168.1.89 / 255.255.255.0` | Static |
| 2 | Manager Shared Network Interface | `0.0.0.0 / 255.255.255.255` | DHCP (unassigned) |

### Server Hardware Summary
| Field | Value |
|-------|-------|
| HostName | `WIN-DG0NK5UH3L5` |
| Power | **On** |
| PostState | **FinishedPost** ← OS has fully booted |
| RAM | 128 GiB |
| CPUs | 2 × Intel Xeon E5-2699 v3 @ 2.30GHz |
| Host NIC MACs | `f4:03:43:3e:c6:80`, `:81`, `:82`, `:83` |
| OS-reported IP (HostCorrelation) | `['', '', '', '']` — iLO has no IP data from OS |

**Interpretation:** Windows Server is running (`FinishedPost` = OS boot complete). The iLO HostCorrelation endpoint returns empty IPs — Windows is not pushing IP data to iLO (requires HP Insight Management Agents / iLO Management Controller Driver to be running on the OS for this to populate).

---

## 3. LAN REACHABILITY PROBE RESULTS

**Dev machine:** `192.168.1.161/24` (Wi-Fi) — same /24 subnet as iLO  

### Subnet Sweep — 192.168.1.1–254 (ICMP, 200ms timeout)

22 alive hosts found. None with MAC prefix `f4:03:43:3e:c6` (server OS NICs):

```
.1    50-c7-bf-b5-1b-a4   (router)
.60   4c-bd-8f-03-30-4d
.62   4c-bd-8f-03-2d-9b
.63   4c-bd-8f-03-2e-62
.65   4c-bd-8f-03-2e-5e
.67   4c-bd-8f-03-2e-56
.68   4c-bd-8f-03-2c-87
.69   4c-bd-8f-03-2a-d7
.70   ac-b9-2f-8a-89-56
.72   4c-bd-8f-03-2e-a0
.73   94-e1-ac-da-15-ff
.74   94-e1-ac-da-18-03
.80   c0-51-7e-ec-42-d7
.82   ec-c8-9c-5b-70-ac
.83   c0-51-7e-ec-42-ce
.84   ac-b9-2f-8a-8b-69
.85   08-54-11-8a-ce-02
.86   08-54-11-8a-cd-c3
.88   e4-11-5b-e3-68-ba   (DNS server — see below)
.89   f4-03-43-41-95-ca   ← iLO Dedicated NIC (confirmed HPE prefix)
.111  18-68-cb-92-56-11
.161  (dev machine)
.177  aa-03-91-8d-fd-91
```

### iLO LAN Connectivity
| Probe | Result |
|-------|--------|
| Ping 192.168.1.89 | ✅ Reply, 1–4ms RTT |
| TCP 192.168.1.89:443 | ✅ `TcpTestSucceeded = True` |
| Ping WIN-DG0NK5UH3L5 (NetBIOS/DNS) | ❌ Host not found |
| nslookup WIN-DG0NK5UH3L5 | ❌ `Server failed` (DNS at .88 cannot resolve) |

### RDP Sweep on All Alive Hosts
All alive hosts probed on port 3389 — **no RDP found open on any host**.  
Samples: `.85:3389 TcpTestSucceeded=False`, `.86:3389 TcpTestSucceeded=False`

---

## 4. ANALYSIS — WHY THE OS IP IS UNKNOWN

The server has 4 host OS NICs (`f4:03:43:3e:c6:80–83`). None of these MACs appear in the ARP cache for the 192.168.1.0/24 subnet after a full ICMP sweep. This means one of:

1. **OS NICs are on a different subnet** — the server may have been configured with static IPs on a different range (10.x.x.x, 172.16.x.x, or a second 192.168.x.x segment), or connected to a separate switch/VLAN
2. **OS NICs are not connected** — the 4 NIC ports (RJ45 on the back of the DL380) may not be physically connected to the same switch as the iLO Dedicated NIC
3. **DHCP not responding / static IP out of 192.168.1.0/24 range** — if the server was moved from another environment it may retain a static IP from a different subnet

The iLO Dedicated NIC (Embedded port) is confirmed connected to the 192.168.1.0/24 network. The 4 data NICs may use a different physical NIC module or switch port.

---

## 5. WHAT WE CAN DO REMOTELY RIGHT NOW

✅ **iLO Redfish API** — full system information read (power, hardware, NIC MACs, temperatures, fans)  
✅ **iLO power control** — power on, power off, cold/warm reboot (via `ilo_poweron.py` or `ILOController`)  
✅ **iLO Web UI** — accessible at `https://192.168.1.89` from dev machine  
✅ **iLO Virtual Console (KVM-over-IP)** — login to iLO Web UI → Remote Console → launch HTML5 console → full keyboard+video+mouse access to Windows desktop  
✅ **iLO Virtual Media** — mount ISO remotely (install OS, run tools, etc.)  

---

## 6. WHAT REQUIRES HUMAN ACTION OR CONFIRMATION

❗ **Physical NIC check** — verify which NIC ports on the back of the DL380 are physically connected to which switch. The OS data NICs may need a cable to the same switch as iLO.  
❗ **iLO KVM session** — requires iLO Advanced license. If iLO is Standard edition, HTML5 console may be limited. Check license tier in iLO Web UI (`https://192.168.1.89` → Administration → Licensing).  
❗ **Windows login credentials** — if accessing Windows via KVM console, local admin credentials are needed. These are not stored in any script.  

---

## 7. RECOMMENDED NEXT ACTION (PHASE 1)

### Step 1: iLO Web UI → System Overview (2 min)
Open from dev machine: `https://192.168.1.89`  
Confirm iLO license tier (Standard vs Advanced). Check iLO Event Log and System Health.

### Step 2: Launch iLO KVM Console
`Remote Console` → `HTML5-based integrated remote console`  
This gives full Windows desktop access without knowing the OS IP.

### Step 3: From Windows Desktop → Find OS IP
Open `cmd.exe` → `ipconfig /all`  
This reveals all NIC IPs, including which subnet the OS is on.  
Then enable RDP if not already on: `sysdm.cpl` → Remote tab → Allow Remote Desktop.

### Step 4: Open RDP From Dev Machine
Once OS IP is known: `mstsc /v:192.168.x.x` from dev machine.

### Step 5: (Optional) Install iLO Management Controller Driver
Installs HP Insight Management drivers on Windows → iLO HostCorrelation.IPAddress populates automatically in future.

---

## 8. RISKS / DO NOT TOUCH

| Constraint | Reason |
|-----------|--------|
| ❌ Do NOT use `ilo_poweron.py` unless server is confirmed Off | Script unconditionally power-on if Off; harmless but unnecessary when server is already On |
| ❌ Do NOT reboot the new server (WIN-DG0NK5UH3L5) | Any running services/state would be lost |
| ❌ Do NOT install anything on new server yet | Phase 0 is discovery only |
| ❌ Do NOT touch old Windows Server 2012 R2 | Separate machine; any changes could affect production |
| ❌ Do NOT run RDP brute-force or port sweeps | Network hygiene; unnecessary noise |

---

## 9. GAPS REMAINING

| Gap | Status | Required Action |
|-----|--------|----------------|
| Server OS IP address | ❌ Unknown | iLO KVM → ipconfig |
| iLO license tier | ❌ Unknown | iLO Web UI → Administration → Licensing |
| OS RDP/SSH/WinRM enabled | ❌ Unknown | KVM → check Windows settings |
| Physical NIC cable mapping | ❌ Unknown | Visual inspection or KVM → Device Manager |
| Windows local admin password | ❌ Unknown (not in any script) | Required for KVM login |

---

*Report auto-generated from live probe data. No credentials included. All probes were read-only and non-destructive.*
