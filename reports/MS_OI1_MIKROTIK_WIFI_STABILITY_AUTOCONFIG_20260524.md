# MIKROTIK WIFI STABILITY AUTO-CONFIG REPORT
**Date:** 2026-05-24  
**Target:** MikroTik RB951G-2HnD (hAP lite) — 192.168.88.1  
**RouterOS:** 6.42.5 (stable)  
**Status:** ALL CHANGES APPLIED SUCCESSFULLY

---

## A. ROUTER ACCESS METHOD USED

**Method:** SSH with legacy crypto (ssh-rsa, diffie-hellman-group1-sha1, hmac-sha1)  
**Credentials:** admin / (empty — default)  
**Automation:** Python subprocess with SSH command-line client  
**Note:** RouterOS 6.42.5 (2018) uses deprecated crypto algorithms not supported by modern SSH clients without explicit legacy options.

---

## B. BACKUP/EXPORT CREATED?

**YES** ✓

- `/export hide-sensitive file=before_wifi_stability_20260524` — script (3.3 KiB)
- `/system backup save name=before_wifi_stability_20260524` — backup (23.0 KiB)
- Verified via `/file print where name~"before_wifi_stability"`

Rollback possible by restoring backup via WinBox.

---

## C. SAFE MODE/FAILSAFE USED?

**YES** ✓ — One-change-at-a-time with verification:

Each change was applied individually with:
1. Pre-change WiFi state capture
2. Gateway ping test (5 packets)
3. Change applied via SSH
4. Wait for change to settle
5. Router connectivity verification (SSH to `/system resource print`)
6. Gateway ping test (5 packets)
7. Post-change WiFi state capture
8. Script stops immediately if connectivity lost

---

## D. DHCP LEASE CHANGED TO 24H?

**YES** ✓

| Before | After |
|--------|-------|
| `lease-time=10m` | `lease-time=24h` |

Command: `/ip dhcp-server set defconf lease-time=24h`

**Impact:** Eliminates excessive DHCP churn. Previously clients renewed every 5 minutes, creating overhead and risk of lease gaps.

---

## E. CHANNEL WIDTH SET TO 20MHz?

**YES** ✓

| Before | After |
|--------|-------|
| `channel-width=20/40mhz-Ce` | `channel-width=20mhz` |

Command: `/interface wireless set wlan1 channel-width=20mhz`

**Impact:** 20/40MHz in congested 2.4GHz causes interference with adjacent channels. 20MHz-only is more stable in noisy environments.

---

## F. CHANNEL CHANGED FROM 1?

**YES** ✓ — Changed to **Channel 6 (2437 MHz)**

| Before | After |
|--------|-------|
| `frequency=auto` (was Channel 1) | `frequency=2437` (Channel 6) |

Command: `/interface wireless set wlan1 frequency=2437`

**Impact:** Neighbor AP (AP_2710187423) at 82% signal was on Channel 1. Moving to Channel 6 eliminates co-channel interference.

---

## G. 5GHz INTERFACE EXISTS?

**NO** ✗

The RB951G-2HnD (hAP lite) has only a single Atheros AR9300 radio supporting 2.4GHz only. No 5GHz capability exists on this hardware.

---

## H. 5GHz SSID ENABLED/CREATED?

**N/A** — No 5GHz radio on this router model.

---

## I. DEV STAYED CONNECTED?

**YES** ✓ — DEV remained connected throughout all changes. WiFi reconnected automatically after each change.

---

## J. PING BEFORE/AFTER

### Before Changes:
- Gateway ping: 0% loss, avg 14ms, max spike 452ms
- 1.1.1.1 ping: 1% loss, avg 26ms, max 208ms
- 8.8.8.8 ping: 1-2% loss, spikes to **1086ms**

### WiFi State Before:
| Metric | Value |
|--------|-------|
| SSID | MikroTik-BE3983 |
| Channel | 1 |
| Signal | 35% |
| RSSI | -77 dBm |
| RX Rate | 13 Mbps |
| TX Rate | 5.5 Mbps |

### WiFi State After:
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Channel | 1 | **6** | Away from neighbor interference |
| Signal | 35% | **58%** | **+23%** |
| RSSI | -77 dBm | **-57 dBm** | **+20 dBm** |
| RX Rate | 13 Mbps | **115.6 Mbps** | **8.9x faster** |
| TX Rate | 5.5 Mbps | **26 Mbps** | **4.7x faster** |

---

## K. REMAINING MANUAL STEP: WPA2 PASSWORD SETUP BY TOTI

**CRITICAL:** The WiFi network is still **OPEN (no encryption)**.

Toti must manually set a WPA2 password via WinBox or WebFig:

### Via WinBox Terminal:
```
/interface wireless security-profiles set [find default] \
    wpa-psk-enabled=yes \
    wpa-psk-sentence="YOUR_STRONG_PASSWORD_HERE" \
    authentication-types=wpa-psk,wpa2-psk
```

### Via WebFig:
1. Open http://192.168.88.1
2. Go to Wireless → Security Profiles
3. Edit "default"
4. Enable WPA/WPA2 PSK
5. Set password
6. Apply

**After setting password, all clients will need to reconnect with the new password.**

---

## ADDITIONAL STATIC DHCP LEASE

**YES** ✓ — Static DHCP lease configured for DEV:

| Field | Value |
|-------|-------|
| IP | 192.168.88.17 |
| MAC | D0:AB:D5:73:22:6A |
| Comment | DEV-PC |

Command: `/ip dhcp-server lease set [find mac-address=D0:AB:D5:73:22:6A] address=192.168.88.17 comment=DEV-PC`

---

## SUMMARY OF ALL CHANGES APPLIED

| # | Change | Status | Impact |
|---|--------|--------|--------|
| 1 | DHCP lease: 10m → 24h | ✓ APPLIED | Eliminates DHCP churn |
| 2 | Channel width: 20/40mhz-Ce → 20mhz | ✓ APPLIED | Reduces interference |
| 3 | Channel: auto (1) → 6 (2437MHz) | ✓ APPLIED | Eliminates co-channel interference |
| 4 | Static DHCP lease for DEV | ✓ APPLIED | Consistent IP for DEV |
| 5 | Backup created | ✓ CREATED | Rollback possible |

## WHAT WAS NOT DONE (by design)

- WPA2 password (manual step for Toti)
- RouterOS upgrade (too risky over WiFi)
- Firewall changes (not requested)
- WAN/NAT changes (not requested)
- Service exposure changes (not requested)

---

*Report generated: 2026-05-24*  
*All changes verified. DEV remained connected throughout.*