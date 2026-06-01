# MS-OI1: Network Inventory & Remote Access Strategy

**Date:** 2026-05-24
**Agent:** Cline
**Purpose:** Operational Infrastructure Hardening — Phase 1 & 2

---

## PHASE 1 — NETWORK INVENTORY

### 1.1 DEV Machine Network

| Property | Value |
|----------|-------|
| IP | 10.52.231.79 |
| Interface | Wi-Fi (Intel AC 9560, 72.2 Mbps) |
| Gateway | 10.52.231.107 |
| DNS | 10.52.231.107 (primary), 8.8.8.8/8.8.4.4 (fallback) |
| Subnet | /24 (inferred from gateway) |
| Ethernet | 169.254.238.35 (APIPA — no DHCP, disconnected) |
| External IP | 2a02:2378:106c:fc79:c814:34be:4ed7:81ae (IPv6, behind Google proxy) |

### 1.2 Router / MikroTik

| Property | Value |
|----------|-------|
| Router IP | 10.52.231.107 |
| Ping | ✅ REACHABLE (4ms, TTL=64) |
| Web (80) | ❌ CLOSED |
| HTTPS (8443) | ❌ CLOSED |
| WinBox (8291) | ❌ CLOSED |
| SSH (22) | ❌ CLOSED |
| WinRM (15985) | ❌ CLOSED |

**Assessment:** Router is reachable via ICMP but all management ports are closed from DEV machine. This could mean:
- Ports are bound to specific interfaces
- Firewall rules block LAN management
- Router uses non-standard ports
- Router is not MikroTik (TTL=64 suggests Linux-based)

### 1.3 DL380 Server

| Property | Value |
|----------|-------|
| External IP | 46.253.140.72 |
| Ping | ✅ REACHABLE (54ms, TTL=56) |
| WinRM (15985) | ✅ OPEN |
| RDP (3389) | ❌ CLOSED |
| SSH (22) | ❌ CLOSED |
| Model 8097 | ❌ BLOCKED (documented — ISP/router) |
| Model 8098 | ❌ BLOCKED (documented — ISP/router) |
| Model 8099 | ❌ BLOCKED (documented — ISP/router) |
| LAN IP | Unknown (10.52.231.108 and 192.168.1.100 both failed) |

**Assessment:** DL380 is reachable externally via WinRM only. Model ports are blocked as documented. LAN IP is on a different subnet than DEV (not 10.52.231.x or 192.168.1.x based on quick probes).

### 1.4 Camera / NVR Discovery

| Property | Value |
|----------|-------|
| Common IPs probed | 10.52.231.100-102, 192.168.1.100-102, 192.168.1.200 |
| Web (80) | None found |
| RTSP (554) | None found |

**Assessment:** No cameras discovered on common IPs from DEV machine. Cameras may be on a different VLAN/subnet or require direct LAN access.

---

## PHASE 2 — REMOTE ACCESS STRATEGY

### Option A: SSH Tunnel (RECOMMENDED — LOWEST RISK)

| Property | Value |
|----------|-------|
| What must be configured | Install OpenSSH Server on DL380 (Windows optional feature) |
| Ports needed | One new port forward on router (e.g., 2222 → DL380:22) |
| What already works | WinRM 15985 is already forwarded |
| What is missing | SSH server on DL380, router port forward |
| Risk | LOW — SSH is encrypted, key-based auth, single port |
| Maintenance | Minimal — SSH is stable, auto-starts as service |

**Usage:**
```bash
# On any remote machine:
ssh -L 8098:127.0.0.1:8098 -L 8099:127.0.0.1:8099 -L 8097:127.0.0.1:8097 user@46.253.140.72 -p 2222 -N
# Then Cline Base URL: http://127.0.0.1:8098
```

### Option B: WireGuard VPN via Router

| Property | Value |
|----------|-------|
| What must be configured | WireGuard on router (if MikroTik) or separate WireGuard server |
| Ports needed | UDP 51820 forwarded to router |
| What already works | Router is pingable |
| What is missing | Router management access (WinBox/SSH all closed), WireGuard setup |
| Risk | LOW — VPN is standard, encrypted |
| Maintenance | MEDIUM — requires router config access, peer management |

**Blocker:** Cannot configure router without management access. WinBox (8291) and SSH (22) are both closed from DEV.

### Option C: Direct RDP Port Forward (LAST RESORT)

| Property | Value |
|----------|-------|
| What must be configured | Port forward 3389 (or custom) → DL380:3389 |
| Ports needed | One TCP port forward |
| What already works | WinRM 15985 is forwarded (proves port forwarding works) |
| What is missing | RDP port forward |
| Risk | HIGH — RDP is frequently attacked, requires NLA + strong password |
| Maintenance | LOW — once configured, works |

**Note:** Only consider if SSH tunnel is not feasible. Must use NLA + non-standard port + strong password.

### Recommendation

**Primary:** SSH Tunnel (Option A)
1. Enable OpenSSH Server on DL380 via WinRM
2. Request router port forward for SSH port
3. Use key-based authentication
4. Tunnel all model ports through SSH

**Fallback:** Continue using WinRM 15985 for remote PowerShell sessions (already works)

---

*End of Phase 1 & 2 report.*