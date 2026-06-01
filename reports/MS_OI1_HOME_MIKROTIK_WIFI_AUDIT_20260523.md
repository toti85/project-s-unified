# HOME MIKROTIK + DEV WIFI STABILITY AUDIT REPORT
**Date:** 2026-05-24  
**Auditor:** Project-S Autonomous Agent  
**Target:** Home MikroTik Router + DEV Machine (DESKTOP-VAR2T1H)  
**Status:** DIAGNOSIS COMPLETE — CHANGES NOT APPLIED (awaiting approval)

---

## A. NETWORK CONTEXT CONFIRMED

**Verdict: REAL_HOME_MIKROTIK ✓**

| Parameter | Value |
|-----------|-------|
| Hostname | DESKTOP-VAR2T1H |
| Adapter | Intel(R) Wireless-AC 9560 160MHz |
| Connection | Wi-Fi (802.11n / 2.4 GHz) |
| SSID | MikroTik-BE3983 |
| AP BSSID | d4:ca:6d:be:39:83 |
| DEV IP | 192.168.88.17/24 |
| Gateway | 192.168.88.1 |
| DHCP Server | 192.168.88.1 |
| DNS Primary | 192.168.88.1 (router.lan) |
| DNS Secondary | 8.8.8.8 |
| DHCP Lease | ~35 minutes (obtained 05:41, expires 06:16) |
| Authentication | **OPEN — NO ENCRYPTION** ⚠️🚨 |

---

## B. GATEWAY PING RESULT (192.168.88.1)

| Metric | Value | Assessment |
|--------|-------|------------|
| Packets Sent | 100 | — |
| Packets Received | 100 | — |
| **Packet Loss** | **0%** | ✅ Excellent |
| Minimum Latency | 1ms | ✅ Excellent |
| Average Latency | 14ms | ✅ Good |
| Maximum Latency | **452ms** | ⚠️ Spike detected |

**Assessment:** Local network to gateway is stable with zero packet loss. The 452ms maximum spike suggests occasional WiFi contention or router CPU burst, but overall local connectivity is healthy.

---

## C. INTERNET PING RESULT

### Cloudflare 1.1.1.1

| Metric | Value | Assessment |
|--------|-------|------------|
| Packets Sent | 100 | — |
| Packets Received | 99 | — |
| **Packet Loss** | **1%** | ⚠️ Minor loss |
| Minimum Latency | 16ms | ✅ Good |
| Average Latency | 26ms | ✅ Good |
| Maximum Latency | **208ms** | ⚠️ Spike detected |

### Google DNS 8.8.8.8

| Metric | Value | Assessment |
|--------|-------|------------|
| Packet Loss | ~1-2% (timed out packets observed) | ⚠️ Minor loss |
| Latency Range | 29ms - **1086ms** | 🔴 SEVERE SPIKES |
| Notable Spikes | 1086ms, 1084ms, 1023ms, 499ms, 498ms, 488ms, 418ms | 🔴 |

**Assessment:** Internet connectivity shows **intermittent severe latency spikes** (up to 1086ms) and minor packet loss (1-2%). This pattern is characteristic of:
1. **WiFi interference** (2.4 GHz band congestion)
2. **Router NAT/DPI processing delays**
3. **ISP-side congestion** during peak hours
4. **Open WiFi network** allowing unauthorized airtime consumption

---

## D. DNS RESULT

| Test | Result |
|------|--------|
| nslookup google.com | ✅ RESOLVED (142.251.38.206) via router.lan |
| nslookup cloudflare.com | ✅ RESOLVED (104.16.133.229) via router.lan |
| DNS Server | router.lan (192.168.88.1) |

**Assessment:** DNS resolution works correctly. Router is acting as DNS proxy forwarder. No DNS failures detected.

---

## E. MIKROTIK REACHABLE — WHICH PORTS?

| Service | Port | Status |
|---------|------|--------|
| WebFig (HTTP) | 80 | ✅ **OPEN** |
| WebFig (HTTPS) | 443 | ❌ Closed |
| WinBox | 8291 | ✅ **OPEN** |
| SSH | 22 | ⚠️ Testing (may be open) |
| API | 8728 | Not tested |
| API SSL | 8729 | Not tested |

**Assessment:** MikroTik is accessible via:
- **WebFig:** http://192.168.88.1
- **WinBox:** 192.168.88.1:8291 (MAC or IP)

---

## F. WIFI STABILITY ISSUES FOUND

### 🔴 CRITICAL ISSUES

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | **OPEN NETWORK — NO ENCRYPTION** | 🔴 CRITICAL | Anyone can connect, consume bandwidth, use network maliciously |
| 2 | **Weak signal: -77 dBm / 41%** | 🔴 CRITICAL | Below acceptable threshold (-70 dBm). Causes retransmissions, low throughput, disconnections |
| 3 | **Only 802.11n on 2.4 GHz** | 🔴 CRITICAL | Adapter supports AC/160MHz but locked to N. Massive speed penalty |
| 4 | **Very low data rates: 13 Mbps RX / 5.5 Mbps TX** | 🔴 CRITICAL | 5.5 Mbps TX is bare minimum 802.11b rate. Explains instability |
| 5 | **Severe internet latency spikes: up to 1086ms** | 🔴 CRITICAL | Makes real-time work (RDP, VoIP, video) unusable during spikes |

### ⚠️ SIGNIFICANT ISSUES

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 6 | **Co-channel interference** | ⚠️ HIGH | Neighbor AP (AP_2710187423) at 82% signal on same Channel 1 |
| 7 | **Short DHCP lease: 35 minutes** | ⚠️ HIGH | Excessive DHCP churn, renewal overhead, risk of lease gaps |
| 8 | **No 5 GHz WiFi detected** | ⚠️ HIGH | Router may have 5 GHz capability but not configured |
| 9 | **Channel 1 congestion** | ⚠️ MEDIUM | Both visible networks on Channel 1 = contention |

---

## G. RECOMMENDED FIRST SAFE CHANGES

### CATEGORY 1: SAFE TO APPLY NOW (low risk, high impact)

#### 1. Enable WPA2/WPA3 Encryption on WiFi
**Risk:** Low (may disconnect clients temporarily until they re-authenticate)  
**Impact:** CRITICAL — prevents unauthorized access, improves airtime efficiency  
**Action in Router:**
```
/interface wireless set [find default-name=wlan1] security-profile=wpa2-psk
/interface wireless security-profiles set [find default] wpa-psk-sentence="your-strong-password"
```
OR for WiFi Queuing (if WiFiQ package):
```
/interface wifi add name=wifi1 band=2gng-n comment="2.4GHz"
/interface wifi security-profiles add authentication-types=wpa2-psk password="your-password"
```

#### 2. Extend DHCP Lease Time
**Risk:** None  
**Impact:** High — reduces DHCP churn  
**Action:** Change from 35min to 24h (or at least 4h):
```
/ip dhcp-server network set [find] lease-time=24h
```

#### 3. Set Static IP or Static DHCP Lease for DEV
**Risk:** None  
**Impact:** Medium — ensures consistent IP for DEV  
**Action:**
```
/ip dhcp-server lease add address=192.168.88.17 interface=bridge1 mac-address=D0:AB:D5:73:22:6A server=dhcp1
```

### CATEGORY 2: APPLY AFTER CONFIRMATION (medium risk)

#### 4. Enable/Configure 5 GHz WiFi
**Risk:** Medium (requires physical router access to verify radio capabilities)  
**Impact:** HIGH — AC9560 can do 433+ Mbps on 5GHz vs current 5.5 Mbps TX on 2.4GHz  
**Action:** Verify router has 5GHz radio, enable separate SSID:
```
/interface wireless print detail  [check for wlan5 or similar]
```

#### 5. Change 2.4 GHz Channel or Channel Width
**Risk:** Low  
**Impact:** Medium — reduces interference  
**Action:** Since neighbor is on Channel 1, try Channel 6 or 11:
```
/interface wireless set [find default-name=wlan1] band=2GHz-n-20 channel=6
```

#### 6. Set Channel Width to 20 MHz on 2.4 GHz
**Risk:** Low  
**Impact:** Medium — more stable in congested environments  
**Action:**
```
/interface wireless set [find default-name=wlan1] channel-width=20/20
```

### CATEGORY 3: DO NOT APPLY WITHOUT MANUAL REVIEW

#### 7. RouterOS Upgrade
**Risk:** High if done incorrectly  
**Impact:** Medium — security patches, bug fixes  
**Action:** Manual check required: `/system package update check`

#### 8. Firewall Rule Changes
**Risk:** High — can lock out access  
**Impact:** Medium — security hardening  
**Action:** Requires full firewall audit first

---

## H. WHAT NEEDS MANUAL ROUTER LOGIN?

The following requires Toti to log into the MikroTik router manually (WinBox or WebFig):

### Immediate Priority (login required):
1. **Enable WiFi encryption** — open network is a severe security risk
2. **Check 5 GHz radio existence** — `/interface wireless print` or `/interface wifi print`
3. **Check RouterOS version** — `/system resource print`
4. **Check CPU/RAM load** — `/system resource print`
5. **Review DHCP lease time** — `/ip dhcp-server network print`
6. **Review existing firewall rules** — `/ip firewall filter print`
7. **Review NAT/port forwards** — `/ip firewall nat print`
8. **Check for unauthorized clients** — `/ip dhcp-server lease print`
9. **Review wireless clients** — `/interface wireless registration-table print`

### Router Access Methods:
- **WinBox:** Connect to 192.168.88.1 (port 8291)
- **WebFig:** http://192.168.88.1 (port 80)
- **SSH:** 192.168.88.1:22 (if enabled)

---

## I. SUMMARY AND ROOT CAUSE ANALYSIS

### Primary Root Causes of WiFi/Internet Instability:

1. **OPEN UNENCRYPTED WiFi NETWORK** — Anyone nearby can connect and consume airtime/bandwidth, causing latency spikes and disconnections for legitimate clients.

2. **WEAK SIGNAL (-77 dBm)** — DEV is at the edge of acceptable range. This causes:
   - Low data rates (5.5 Mbps TX)
   - Excessive retransmissions
   - Frequent disconnections/reassociations
   - High sensitivity to interference

3. **2.4 GHz ONLY + CO-CHANNEL INTERFERENCE** — Both visible networks on Channel 1 creates contention. The neighbor AP at 82% signal is a major source of interference.

4. **NO 5 GHz WiFi AVAILABLE** — The DEV's Intel AC9560 adapter is capable of 5 GHz AC (433+ Mbps), but the router either doesn't have 5 GHz enabled or it's not broadcasting.

### Recommended Immediate Actions (in order):

| Priority | Action | Expected Improvement |
|----------|--------|---------------------|
| 1 | **Enable WPA2 encryption** | Blocks unauthorized clients, stabilizes airtime |
| 2 | **Connect DEV via Ethernet LAN cable** | Eliminates WiFi issues entirely for serious work |
| 3 | **Enable 5 GHz WiFi if router supports it** | 10-20x speed improvement for DEV |
| 4 | **Extend DHCP lease to 24h** | Reduces DHCP overhead |
| 5 | **Change 2.4 GHz to Channel 6 or 11** | Reduces co-channel interference |
| 6 | **Move DEV closer to router or add repeater** | Improves signal from -77 to better than -65 dBm |

### For Serious Project-S Work:
**Cable DEV via Ethernet.** The WiFi signal at -77 dBm with 5.5 Mbps TX rate is fundamentally unstable for RDP, file transfers, or real-time work. A LAN cable to the MikroTik (or a switch connected to it) would provide:
- 1 Gbps symmetric speeds
- Zero packet loss
- Sub-1ms latency
- No interference

The Ethernet port on DEV shows a TOTOLINK DNS suffix, suggesting it was previously connected to a different network. If the MikroTik has available LAN ports, connect the Ethernet cable.

---

## J. CONFIGURATION SNAPSHOT RECOMMENDATION

Before any changes, Toti should create a backup:
```
/export hide-sensitive file=before_audit_20260524
/system backup save name=before_audit_20260524
```

---

## K. NEXT STEPS

1. **Toti reviews this report**
2. **Toti logs into MikroTik via WinBox (192.168.88.1)**
3. **Toti enables WiFi encryption (WPA2 minimum)**
4. **Toti checks for 5 GHz radio capability**
5. **Toti extends DHCP lease time**
6. **Toti considers Ethernet cable for DEV**
7. **Optional: Second audit after changes to verify improvements**

---

*Report generated: 2026-05-24 06:34 UTC+3*  
*No router changes were applied during this audit.*