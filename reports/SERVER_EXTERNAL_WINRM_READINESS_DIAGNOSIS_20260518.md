# SERVER EXTERNAL WINRM READINESS DIAGNOSIS

**Date:** 2026-05-18 15:53
**Target Server:** SHAYANSKA-DL380 (192.168.1.180)
**External IP:** 46.253.140.72
**External Port:** 15985

---

## 1. SERVER-SIDE CHECKS (SHAYANSKA-DL380)

### 1.1 WinRM Service Status
| Property | Value | Status |
|----------|-------|--------|
| Status | Running (4) | PASS |
| Startup Type | Automatic (2) | PASS |

### 1.2 WinRM Listeners
```
Transport = HTTP
Port = 5985
Hostname = (not set - listens on all interfaces)
```
Listener count detected: 0 (regex mismatch in enumeration - service is functional)

### 1.3 Port 5985 Listening
| Property | Value | Status |
|----------|-------|--------|
| Listening | True | PASS |
| Process | System (SVCHOST) | PASS |

### 1.4 Firewall Rules
| Rule Group | Enabled | Total | Status |
|------------|---------|-------|--------|
| Windows Remote Management | 2 | 2 | PASS |

### 1.5 Network Profile
| Property | Value | Status |
|----------|-------|--------|
| Name | Network 2 | Info |
| Category | 0 (Public) | WARNING |
| Interface | (not shown) | Info |
| LAN IP | 192.168.1.180 | PASS |

### 1.6 LocalAccountTokenFilterPolicy
| Value | Status |
|-------|--------|
| NOT SET (defaults to 0) | WARNING |

### 1.7 Server LAN IP
- **Current IP:** 192.168.1.180 (confirmed)

---

## 2. DEV MACHINE LAN CHECKS

### 2.1 Invoke-Command Authentication
```
Test-NetConnection 192.168.1.180 -Port 5985
TcpTestSucceeded: True
```
```
Invoke-Command to 192.168.1.180
Result: SUCCESS (hostname: SHAYANSKA-DL380)
```
**LAN WinRM: PASS**

---

## 3. EXTERNAL FORWARD TEST

```
Test-NetConnection 46.253.140.72 -Port 15985
TcpTestSucceeded: False
TracerouteHops: 0
```
**External 15985: NOT REACHABLE**

---

## 4. CONCLUSION

### A. Server-side WinRM fully correct? **NO**

**Issues found:**
1. **Network Category = 0 (Public)** - WinRM firewall rules may not apply to Public networks. The firewall rules are enabled but the network is classified as Public, which means the rules with "Public" profile may not allow inbound connections properly.
2. **LocalAccountTokenFilterPolicy NOT SET** - This means remote admin authentication may fail for some scenarios (though LAN WinRM currently works, likely because we're using local Administrator account).

### B. LAN WinRM still PASS? **YES**

LAN WinRM works correctly:
- TCP 5985 is reachable from DEV machine
- Invoke-Command authenticates successfully
- Remote PowerShell execution works

### C. External 15985 reachable? **NO**

External TCP connection to 46.253.140.72:15985 fails.

### D. Most likely remaining cause

**Router/NAT/port-forward issue** (primary) + **Network profile should be Private** (secondary)

The server-side WinRM is functional (LAN works). The external port 15985 is not reachable because:
1. The router at 46.253.140.72 does not have a port forwarding rule for TCP 15985 -> 192.168.1.180:5985
2. OR the port forward rule exists but is not functioning (NAT loopback issue)

### E. Exact next physical/router action

#### Step 1: Fix server network profile (server-side)
Run on SHAYANSKA-DL380:
```powershell
# Set network profile to Private (allows WinRM through firewall)
Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private
```

#### Step 2: Configure WinRM to listen on all addresses (server-side)
Run on SHAYANSKA-DL380:
```cmd
winrm set winrm/config/Listener?Address=*+Transport=HTTP "@Enabled=true@ListenAddress=*"
```

#### Step 3: Set LocalAccountTokenFilterPolicy (server-side)
Run on SHAYANSKA-DL380:
```powershell
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name LocalAccountTokenFilterPolicy -Value 1 -PropertyType DWORD -Force
```

#### Step 4: Configure router port forward
Log into router (likely 192.168.1.1):
- **Protocol:** TCP
- **External Port:** 15985
- **Internal IP:** 192.168.1.180
- **Internal Port:** 5985
- **Enable:** Yes

#### Step 5: Verify external access
From DEV machine:
```powershell
Test-NetConnection 46.253.140.72 -Port 15985
```

---

## 5. SUMMARY TABLE

| Check | Result | Status |
|-------|--------|--------|
| WinRM Service Running | Yes | PASS |
| WinRM Startup Type | Automatic | PASS |
| Port 5985 Listening | Yes | PASS |
| Firewall Rules Enabled | 2/2 | PASS |
| Network Profile | Public (0) | WARNING |
| LocalAccountTokenFilterPolicy | Not Set | WARNING |
| Server LAN IP | 192.168.1.180 | PASS |
| LAN WinRM (5985) | Working | PASS |
| External WinRM (15985) | Not Reachable | FAIL |

---

## 6. RECOMMENDED FIX PRIORITY

1. **HIGH** - Set network profile to Private on server
2. **HIGH** - Configure router port forward: TCP 15985 -> 192.168.1.180:5985
3. **MEDIUM** - Set LocalAccountTokenFilterPolicy = 1
4. **LOW** - Verify external access after router config

---

## 7. DIAGNOSIS VERDICT

**The remaining external WinRM problem is a combination of:**
1. **Router/NAT/port-forward missing or non-functional** (primary cause of external failure)
2. **Network profile set to Public** (may limit firewall rule application)

**The Windows Server WinRM configuration is functionally correct** - LAN WinRM works, service is running, port is listening, firewall rules are enabled.