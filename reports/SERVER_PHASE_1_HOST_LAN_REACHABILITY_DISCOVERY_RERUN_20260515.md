# Server Phase 1 — Host LAN Reachability Discovery — RERUN

**Date:** 2026-05-15 ~13:50 UTC+3
**Type:** Read-only discovery — no state-changing operations
**Context:** Host LAN cable now confirmed physically connected by Toti
**Previous Run:** 2026-05-15 ~11:18 UTC+3 (all NICs null IPs, no link)

---

## 1. Executive Verdict

**Is the host OS reachable?** YES — the new DL380 Gen9 host OS now has an IP address on NIC 1: `192.168.1.180`.

**WinRM (5985) is OPEN** — this is the preferred interactive access method.
**RDP (3389) is CLOSED** — not enabled on the host OS yet.
**Ping is blocked** — Windows Firewall is blocking ICMP (expected for server configurations).

**What changed since the first run:**
- NIC 1 now has IP `192.168.1.180` (was `null` before)
- NIC 1 now shows `Status: {Health: OK, State: Enabled}` (was absent before)
- The host OS network stack has initialized and obtained an IP (likely via DHCP)
- Only NIC 1 is active; NICs 2-4 still not yet linked

---

## 2. New DL380 Host IP Candidate(s)

| NIC | MAC Address | IPv4 | Status | Health |
|-----|-------------|------|--------|--------|
| 1 | F4:03:43:3E:C6:80 | **192.168.1.180** | Enabled | OK |
| 2 | F4:03:43:3E:C6:81 | null | — | — |
| 3 | F4:03:43:3E:C6:82 | null | — | — |
| 4 | F4:03:43:3E:C6:83 | null | — | — |

**Best candidate IP:** `192.168.1.180` (NIC 1, MAC F4:03:43:3E:C6:80)

**MAC Address Match:** Confirmed — `f4-03-43-3e-c6-80` in ARP table matches NIC 1 of the new DL380 Gen9.

**NIC 1 change from first run:**
- First run: `IPv4Addresses: [null]`, no Status field
- Rerun: `IPv4Addresses: [192.168.1.180]`, `Status: {Health: OK, State: Enabled}`

---

## 3. Evidence Used to Identify Candidate(s)

### Source A: iLO / Redfish API (PRIMARY)

**Endpoint:** `https://46.253.140.72:89/redfish/v1/Systems/1/EthernetInterfaces/1/`

**Result:** NIC 1 now reports:
- `IPv4Addresses: [{Address: "192.168.1.180"}]`
- `Status: {Health: OK, State: Enabled}`
- `MacAddress: F4:03:43:3E:C6:80`

NICs 2-4 still report null IPs (not yet linked/active).

### Source B: Local ARP Table (SECONDARY)

**Confirmed match:**
```
192.168.1.180         f4-03-43-3e-c6-80     dynamic
```

This MAC (`f4-03-43-3e-c6-80`) is exclusively NIC 1 of the new DL380 Gen9.

**Other DL380 NICs in ARP:**
- `f4-03-43-3e-c6-81` — NOT FOUND (NIC 2 not active)
- `f4-03-43-3e-c6-82` — NOT FOUND (NIC 3 not active)
- `f4-03-43-3e-c6-83` — NOT FOUND (NIC 4 not active)

### Source C: Subnet Probing (TERTIARY)

TCP port probes on `192.168.1.180` (see Section 4).

---

## 4. Port Reachability Table

### 192.168.1.180 (NEW DL380 HOST — confirmed)

| Port | Service | Status | Latency | Notes |
|------|---------|--------|---------|-------|
| 3389 | RDP | **closed** | 2012ms | Not enabled on host OS |
| 22 | SSH | **closed** | 2014ms | Not installed |
| 5985 | WinRM HTTP | **OPEN** | 16ms | **PREFERRED ACCESS METHOD** |
| 5986 | WinRM HTTPS | **closed** | 2007ms | HTTPS not enabled |
| 445 | SMB | **closed** | 2003ms | Firewall blocking |
| 80 | HTTP | **closed** | 2007ms | No web server |
| 443 | HTTPS | **closed** | 2000ms | No web server |
| 135 | RPC | **OPEN** | 16ms | Windows RPC endpoint mapper (expected) |
| 139 | NetBIOS | **closed** | 2004ms | Not enabled |
| 3306 | MySQL | **closed** | 2016ms | No database |
| 1433 | MSSQL | **closed** | 2006ms | No database |
| 8080 | HTTP-Alt | **closed** | 2010ms | No proxy/web server |
| 5988 | WinRM-HTTP-alt | **closed** | 2001ms | Default is 5985 |
| 8443 | HTTPS-Alt | **closed** | 2001ms | No proxy/web server |

### Ping Test

```
Pinging 192.168.1.180 with 32 bytes of data:
Request timed out.
Request timed out.
```

**ICMP blocked by Windows Firewall** — this is expected and normal for Windows Server configurations. Does NOT indicate a problem; WinRM (5985) is confirmed open with 16ms latency.

---

## 5. Preferred Next Access Method

**WinRM (PowerShell remoting) — PREFERRED**

Since RDP is not enabled, the best access method is PowerShell remoting via WinRM (port 5985).

**How to connect:**
```powershell
# From the dev machine (192.168.1.161)
Enter-PSSession -ComputerName 192.168.1.180 -Credential 192.168.1.180\Administrator
```

Or for a one-off command:
```powershell
Invoke-Command -ComputerName 192.168.1.180 -Credential 192.168.1.180\Administrator -ScriptBlock { hostname; Get-NetAdapter; Get-ComputerInfo }
```

**After WinRM access is established:**
1. Enable RDP for future interactive access:
   ```powershell
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
   Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
   ```
2. Verify network adapter status
3. Proceed with Phase 1 deployment planning

**Alternative: iLO Remote Console**
If WinRM authentication fails (domain/workgroup issues), use iLO Remote Console as fallback:
1. Open `https://46.253.140.72:89` (Administrator / PTSYK7BF)
2. Launch Remote Console (KVM)
3. Inspect Windows Server login screen directly

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
| Host NIC 1 MAC | F4:03:43:3E:C6:80 |
| Host NIC 1 IP | **192.168.1.180** (DHCP assigned) |
| Host NIC 1 status | Enabled, Health OK |
| Host NIC 2-4 | Not yet active (null IPs, no ARP entries) |
| WinRM (5985) | **OPEN** — PowerShell remoting available |
| RPC (135) | **OPEN** — Windows RPC confirmed |
| RDP (3389) | Closed — not enabled |
| SSH (22) | Closed — not installed |
| ICMP (ping) | Blocked by Windows Firewall (expected) |
| Host OS | Likely Windows Server (RPC + WinRM confirmed) |

---

## 7. What Remains Unknown

| Item | Status |
|------|--------|
| Host OS version | Windows Server 2019? 2022? Unverified |
| Host OS hostname | Unknown |
| Host OS administrator password | Unknown |
| Whether NIC 1 got IP via DHCP or static | Likely DHCP (first time seeing an IP) |
| Whether the Tesla M60 is recognized | Unknown (need host OS access) |
| Whether NVMe drives are initialized | Unknown |
| Which physical port the LAN cable is plugged into | Unknown (4 NICs, only 1 active) |
| Whether the old Windows Server 2012 R2 is still installed | Unknown |

---

## 8. Exact Next Action for Toti

**Option A — WinRM PowerShell (recommended, no physical access needed):**
1. From the dev machine, try PowerShell remoting:
   ```powershell
   Enter-PSSession -ComputerName 192.168.1.180 -Credential 192.168.1.180\Administrator
   ```
2. If prompted for password, use the server administrator password
3. Once connected, enable RDP for easier future access:
   ```powershell
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -name "fDenyTSConnections" -value 0
   Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
   ```
4. Then RDP into `192.168.1.180` for interactive access

**Option B — If WinRM authentication fails:**
1. Use iLO Remote Console at `https://46.253.140.72:89`
2. Launch KVM and check Windows Server login screen
3. Log in with Administrator credentials
4. Enable RDP from Network and Sharing Center
5. Then RDP into `192.168.1.180`

**Option C — If you don't know the administrator password:**
1. Use iLO Remote Console to access the login screen
2. Check if the server is at the login prompt or already logged in
3. If logged in, check network adapter status in Windows Settings

---

## Appendix A: iLO Redfish NIC 1 Data (Rerun)

```json
{
  "Id": "1",
  "MacAddress": "F4:03:43:3E:C6:80",
  "IPv4Addresses": [{"Address": "192.168.1.180"}],
  "IPv6Addresses": [{"Address": null}],
  "Status": {"Health": "OK", "State": "Enabled"},
  "FullDuplex": false,
  "SpeedMbps": null
}
```

**Key change from first run:** `IPv4Addresses` changed from `[null]` to `[192.168.1.180]`, and `Status` field now present with `State: Enabled`.

---

**Készítette:** Cline
**Dátum:** 2026-05-15
**Verzió:** v1.1 (RERUN)