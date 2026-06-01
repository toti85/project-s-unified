# CAMERA SYSTEM — LAN DISCOVERY & RECORDING STATUS AUDIT
**Date:** 2026-05-23  
**Auditor machine:** DESKTOP-VAR2T1H (192.168.1.158)  
**Scope:** Read-only passive audit — NO settings changed, NO firmware updated, NO reboots, NO password resets  
**Method:** ipconfig, arp, ping sweep, TCP port probe (raw socket), HTTP banner grab, SSL cert inspection

---

## A. LAN SUBNET SCANNED

| Parameter | Value |
|---|---|
| Active interface | Wi-Fi (Intel Wireless-AC 9560) |
| This machine IP | 192.168.1.158 |
| Subnet | 192.168.1.0/24 |
| Gateway | 192.168.1.1 (TOTOLINK router, MAC 50:c7:bf:b5:1b:a4) |
| DNS primary | 192.168.1.88 |
| DNS secondary | 8.8.8.8 |
| Ethernet adapter | Disconnected (Intel I219-LM) |
| VPN adapter | Disconnected (TAP-Windows V9) |
| Additional ARP entry | 192.168.0.1 (b0:19:21:4d:bc:28) — **not reachable**, may be stale or on unreachable subnet |

**Tools used:** PowerShell `Test-Connection`, raw `System.Net.Sockets.TcpClient`, `Invoke-WebRequest`, `System.Net.Security.SslStream`  
**nmap:** NOT installed — PowerShell TCP probes used instead

---

## B. ALL DEVICES FOUND ON LAN (ARP + PING SWEEP)

| IP Address | MAC Address | Ping | OUI Vendor (offline lookup) | Notes |
|---|---|---|---|---|
| 192.168.1.1 | 50:c7:bf:b5:1b:a4 | ✅ ALIVE | TOTOLINK/Zioncom | Gateway/Router |
| 192.168.1.62 | 4c:bd:8f:03:2d:9b | ✅ ALIVE | Uniview/HiLook | **IP Camera** |
| 192.168.1.63 | 4c:bd:8f:03:2e:62 | ✅ ALIVE | Uniview/HiLook | **IP Camera** |
| 192.168.1.65 | 4c:bd:8f:03:2e:5e | ✅ ALIVE | Uniview/HiLook | **IP Camera** |
| 192.168.1.67 | 4c:bd:8f:03:2e:56 | ✅ ALIVE | Uniview/HiLook | **IP Camera** |
| 192.168.1.68 | 4c:bd:8f:03:2c:87 | ✅ ALIVE | Uniview/HiLook | **IP Camera** |
| 192.168.1.69 | 4c:bd:8f:03:2a:d7 | ✅ ALIVE | Uniview/HiLook | **IP Camera** |
| 192.168.1.88 | e4:11:5b:e3:68:ba | ✅ ALIVE | TP-Link Technologies | Windows Server (IIS 8.5) + DNS server |
| 192.168.1.89 | f4:03:43:41:95:ca | ✅ ALIVE | Unknown | **HP iLO** server management |
| 192.168.1.154 | 90:1b:0e:19:c5:45 | ✅ ALIVE | Possible Hikvision | All TCP ports closed/filtered — **unidentifiable remotely** |
| 192.168.1.158 | d0:ab:d5:73:22:6a | — | Intel (this machine) | Audit workstation |
| 192.168.0.1 | b0:19:21:4d:bc:28 | ❌ NO PING | Unknown | Stale ARP / unreachable subnet |

> Note: MAC OUI assignments done from offline memory. Verify with https://www.wireshark.org/tools/oui-lookup.html for exact vendor.  
> Sequential MACs on cameras (03:2a:d7 → 03:2e:62) confirm they were purchased/deployed as a single batch.

---

## C. CAMERA / NVR DEVICES IDENTIFIED

### IP Cameras — 6 confirmed (192.168.1.62 / .63 / .65 / .67 / .68 / .69)

| Field | Value |
|---|---|
| Count | **6 cameras** |
| MAC OUI | 4c:bd:8f (Uniview / HiLook — same OUI block, sequential serials) |
| Open ports | **80** (HTTP web UI), **554** (RTSP stream), **8000** (Hikvision SDK) |
| Web server header | `webserver` (Hikvision/HiLook firmware signature) |
| Login page path | `/doc/page/login.asp` |
| Web framework | AngularJS (`ng-controller="loginController"`) |
| Firmware style | **Hikvision / HiLook** (100% match on web UI HTML structure) |
| ISAPI endpoint | `/ISAPI/System/deviceInfo` → HTTP 401 (auth required) |
| Device type | **IP Camera (standalone)** |
| Access method | Browser (HTTP port 80), RTSP (port 554), Hikvision SDK (port 8000) |
| Credentials | **REQUIRED — not provided — login not attempted** |

**Camera port summary:**
```
IP              : 80   554   8000   Status
192.168.1.62    : ✅   ✅    ✅     ALIVE
192.168.1.63    : ✅   ✅    ✅     ALIVE
192.168.1.65    : ✅   ✅    ✅     ALIVE
192.168.1.67    : ✅   ✅    ✅     ALIVE
192.168.1.68    : ✅   ✅    ✅     ALIVE
192.168.1.69    : ✅   ✅    ✅     ALIVE
```

---

### NVR/DVR — ⚠️ NOT CONFIRMED

**No device on this subnet was positively identified as an NVR or DVR.**

| Candidate | Status | Reason |
|---|---|---|
| 192.168.1.154 | ⚠️ UNIDENTIFIABLE | Ping-alive. All TCP ports closed or filtered (80, 443, 554, 8000, 8080, 8088, 8100-9001). Possible Hikvision device (MAC OUI 90:1b:0e) with strict ACL or all ports blocked by firewall. Cannot determine type remotely without credentials or access exception. |

**Ports scanned on 192.168.1.154 — all CLOSED:**
```
80, 81, 88, 443, 554, 8000, 8080, 8081, 8088, 8100, 8200, 8443, 8554,
8888, 9000, 9001, 6060, 7080, 7443, 8001, 8002, 8003, 37777, 5000, 8899
```

**Possible explanations for .154:**
1. Hikvision NVR with host-based firewall enabled (all services blocked from this subnet/IP)
2. Windows PC with Hikvision NIC that has its services disabled
3. ARP-cached entry of a device that was recently powered down (ARP table can linger ~20 min on Windows)
4. Device accessible only via specific client software (iVMS-4200) or VLAN

---

### Other Non-Camera Devices

| IP | Identified As | Evidence |
|---|---|---|
| 192.168.1.88 | **Windows Server (IIS 8.5)** — hosting Ukrainian website "Мінеральні води Закарпаття" (Mineral Waters of Zakarpattia); also primary DNS server for LAN; port 88 (Kerberos) open → possible AD domain controller | Server: Microsoft-IIS/8.5; port 88 open |
| 192.168.1.89 | **HP iLO** (Integrated Lights-Out) server management interface | SSL cert: `CN=ILO, O=Hewlett Packard Enterprise`; HTTP 303 → HTTPS |
| 192.168.1.1 | **TOTOLINK router** / gateway | MAC OUI TOTOLINK; default gateway |

---

## D. ACCESS METHOD FOUND

| Device | Access Method | URL / Tool | Auth Required |
|---|---|---|---|
| Cameras (.62/.63/.65/.67/.68/.69) | **Browser (HTTP)** | `http://192.168.1.6x/` → redirects to `/doc/page/login.asp` | **YES — credentials needed** |
| Cameras (.62/.63/.65/.67/.68/.69) | **RTSP stream** | `rtsp://192.168.1.6x:554/` | YES — credentials needed |
| Cameras (.62/.63/.65/.67/.68/.69) | **Hikvision SDK / iVMS-4200** | SDK port 8000 | YES — credentials needed |
| 192.168.1.154 (possible NVR) | **UNKNOWN** | No ports accessible | Unknown |
| 192.168.1.88 | Browser (HTTP) | `http://192.168.1.88/` | Public website (no auth for site) |
| 192.168.1.89 | **Browser (HTTPS)** — HP iLO web UI | `https://192.168.1.89/` | YES — iLO credentials |

---

## E. NVR/DVR IDENTIFIED?

**NO — not confirmed.**

- The 6 cameras expose ports 80/554/8000, which is typical of **standalone IP cameras**, not a connected NVR.
- An NVR would typically show port **37777** (Dahua), **8080** (Hikvision NVR web), **8000** (SDK), or similar. None found in accessible state.
- 192.168.1.154 is the only unidentified device that could be a Hikvision NVR — but all ports are blocked.
- The cameras may be:
  - Recording to internal **SD cards** (local storage, no NVR needed)
  - Connected to an NVR on a **different VLAN or subnet** not visible from this machine
  - Part of a cloud/P2P recording system (Hik-Connect, EZVIZ)

---

## F. CAMERA COUNT CONFIGURED

| Item | Count |
|---|---|
| IP cameras discovered (by ARP + port probe) | **6** |
| IP cameras confirmed reachable (ping + port 80/554/8000) | **6** |
| Cameras confirmed ONLINE | **6 / 6** |
| Cameras confirmed OFFLINE | **0** |
| Channel count on NVR | **UNKNOWN** (no NVR access) |

---

## G. CAMERA COUNT ONLINE / OFFLINE

All 6 cameras respond to ping and have TCP ports open:

| Camera IP | Ping | Port 80 | Port 554 | Port 8000 | Status |
|---|---|---|---|---|---|
| 192.168.1.62 | ✅ | ✅ | ✅ | ✅ | **ONLINE** |
| 192.168.1.63 | ✅ | ✅ | ✅ | ✅ | **ONLINE** |
| 192.168.1.65 | ✅ | ✅ | ✅ | ✅ | **ONLINE** |
| 192.168.1.67 | ✅ | ✅ | ✅ | ✅ | **ONLINE** |
| 192.168.1.68 | ✅ | ✅ | ✅ | ✅ | **ONLINE** |
| 192.168.1.69 | ✅ | ✅ | ✅ | ✅ | **ONLINE** |

> Note: "Online" here means network-reachable. Whether each camera has a connected lens, clear view, and active video signal requires login to verify.

---

## H. RECORDING STATUS PER CAMERA / CHANNEL

| Camera | Recording Active? | Schedule Recording? | Motion Recording? | Continuous? |
|---|---|---|---|---|
| 192.168.1.62 | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN |
| 192.168.1.63 | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN |
| 192.168.1.65 | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN |
| 192.168.1.67 | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN |
| 192.168.1.68 | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN |
| 192.168.1.69 | **UNKNOWN** | UNKNOWN | UNKNOWN | UNKNOWN |

**Root cause:** No NVR confirmed accessible. Camera login credentials not provided. Recording status requires one of:
- Login to each camera web UI (`http://192.168.1.6x/` → admin credentials)
- Login to NVR (if one exists) to check channel recording status
- Login to camera via iVMS-4200 or SDK with credentials

---

## I. HDD / STORAGE STATUS

| Item | Status |
|---|---|
| NVR HDD | **UNKNOWN — no NVR confirmed** |
| Camera SD cards | **UNKNOWN — login required** |
| Storage capacity | Cannot determine |
| Overwrite enabled | Cannot determine |
| Storage health | Cannot determine |

---

## J. PLAYBACK VERIFIED?

**NO.**

Playback verification requires:
1. A confirmed NVR with accessible web UI, OR
2. Camera login with SD card playback access  
Neither is available without credentials.

---

## K. PROBLEMS FOUND

| # | Severity | Problem | Detail |
|---|---|---|---|
| 1 | 🔴 CRITICAL | **No NVR/DVR confirmed** | Cannot verify recording status for any camera. Either no NVR exists, or 192.168.1.154 (possible NVR) is inaccessible due to firewall/ACL. |
| 2 | 🔴 CRITICAL | **No credentials available** | All camera web UIs require login. Cannot check recording schedule, live view, storage, or playback. |
| 3 | 🟡 HIGH | **192.168.1.154 unreachable** | Device at .154 (MAC: 90:1b:0e:19:c5:45, possible Hikvision) responds to ping but has NO open TCP ports on any standard port (80/443/554/8000+). This needs physical investigation. |
| 4 | 🟡 HIGH | **IP .64, .66 missing** | Expected sequential IPs (.62/.63/.65/.67/.68/.69 — gap at .64 and .66). Either 2 cameras are offline/unconfigured, or IP assignment skipped those numbers intentionally. |
| 5 | 🟡 MEDIUM | **No NVR found on standard ports** | Port 37777 (Dahua NVR), 8080 (Hikvision NVR web) found on no device. If an NVR exists, it may be on a different subnet or hidden behind ACL. |
| 6 | 🟡 MEDIUM | **Recording to SD only (possible)** | If no NVR exists, cameras may rely on internal SD cards. SD cards can fail silently, have limited retention, and provide no central management. |
| 7 | 🟢 LOW | **192.168.0.1 unreachable** | ARP has a stale entry for 192.168.0.1 (different subnet). Not reachable from this machine. Possibly a secondary router or old ARP artifact. |
| 8 | 🟢 INFO | **HP iLO at .89** | Server management interface found at .89. Not camera-related but should be secured — default HP iLO credentials are well-known. |

---

## L. RECOMMENDED NEXT STEPS

### Immediate (before anything else):

1. **Obtain camera credentials** from the system administrator (default admin/12345 or admin/admin for HiLook/Hikvision — do NOT guess, use known credentials only).

2. **Physically inspect 192.168.1.154** — power light on? If it's an NVR, why are all ports blocked? Check:
   - Is it powered on and booted?
   - Is there a display connected to it?
   - Is there a host firewall configured on it?
   - What model is it? Check the label on the device.

3. **Log into one camera** (e.g. `http://192.168.1.62/`) with credentials and check:
   - Date/time correct?
   - SD card present and healthy?
   - Recording enabled (continuous or scheduled)?
   - Live view working?

4. **Check for NVR on different subnet** — ask the admin if the NVR is on a VLAN, 10.x.x.x, or 172.x.x.x network.

5. **Install iVMS-4200** (Hikvision client) and attempt to add cameras by IP to verify connectivity and recording from a client perspective.

### After credentials obtained:

6. Log into each camera → Storage → SD card status → Recording schedule.
7. Check video playback for last 24h on each camera.
8. Verify NTP / time sync is correct on all cameras.
9. Check if cameras are enrolled in Hik-Connect / EZVIZ cloud (check camera Network settings).

---

## M. FIRMWARE UPDATE READINESS

| Item | Status |
|---|---|
| Current firmware version | **UNKNOWN** — login required to read firmware version |
| Model numbers | **UNKNOWN** — login required |
| Backup needed before update | **YES** — always back up NVR configuration before firmware update |
| Update risk level | **CANNOT ASSESS** — no access yet |
| **Firmware update decision** | ⛔ **DO NOT UPDATE YET** — read-only audit phase only. Update only after: (a) credentials obtained, (b) recording confirmed working, (c) full config backup taken, (d) maintenance window scheduled |

---

## RETURN ANSWERS

| Field | Answer |
|---|---|
| A. NVR/DVR found? | **NO** — not confirmed. 192.168.1.154 is the only candidate but all ports are blocked/closed. |
| B. NVR IP/address | Unknown — possible candidate: **192.168.1.154** (needs physical inspection) |
| C. Camera count | **6 IP cameras** (192.168.1.62, .63, .65, .67, .68, .69) |
| D. All cameras online? | **YES** — all 6 respond to ping and have ports 80/554/8000 open |
| E. All cameras recording? | **UNKNOWN** — no NVR access, no camera credentials to check recording status |
| F. HDD/storage healthy? | **UNKNOWN** — no NVR access |
| G. Playback verified? | **NO** — credentials required |
| H. Admin access available? | **NO** — credentials not provided |
| I. Firmware update should wait? | **YES** — do not update until audit is complete with access |
| J. Exact next action | **Get camera credentials from admin → log into `http://192.168.1.62/` → verify recording + storage → physically inspect 192.168.1.154 to determine if it is the NVR** |

---

## APPENDIX — RAW DISCOVERY DATA

### ARP Table (raw)
```
192.168.0.1     b0-19-21-4d-bc-28    dynamic  (unreachable)
192.168.1.1     50-c7-bf-b5-1b-a4    dynamic  (gateway)
192.168.1.62    4c-bd-8f-03-2d-9b    dynamic  (camera)
192.168.1.63    4c-bd-8f-03-2e-62    dynamic  (camera)
192.168.1.65    4c-bd-8f-03-2e-5e    dynamic  (camera)
192.168.1.67    4c-bd-8f-03-2e-56    dynamic  (camera)
192.168.1.68    4c-bd-8f-03-2c-87    dynamic  (camera)
192.168.1.69    4c-bd-8f-03-2a-d7    dynamic  (camera)
192.168.1.88    e4-11-5b-e3-68-ba    dynamic  (Windows IIS + DNS)
192.168.1.89    f4-03-43-41-95-ca    dynamic  (HP iLO)
192.168.1.154   90-1b-0e-19-c5-45    dynamic  (unknown, all ports closed)
```

### Port Scan Results
```
IP              Port 80  Port 88  Port 443  Port 554  Port 8000  Port 37777
192.168.1.62    OPEN     -        -         OPEN      OPEN       -
192.168.1.63    OPEN     -        -         OPEN      OPEN       -
192.168.1.65    OPEN     -        -         OPEN      OPEN       -
192.168.1.67    OPEN     -        -         OPEN      OPEN       -
192.168.1.68    OPEN     -        -         OPEN      OPEN       -
192.168.1.69    OPEN     -        -         OPEN      OPEN       -
192.168.1.88    OPEN     OPEN     -         -         -          -
192.168.1.89    303→443  -        OPEN      -         -          -
192.168.1.154   CLOSED   -        CLOSED    CLOSED    CLOSED     CLOSED
```

### HTTP Identification
```
192.168.1.62   Server: webserver    Login: /doc/page/login.asp   AngularJS loginController
192.168.1.88   Server: Microsoft-IIS/8.5   Title: Мінеральні води Закарпаття (Ukrainian mineral water company)
192.168.1.89   SSL CN=ILO, O=Hewlett Packard Enterprise   (HP iLO management interface)
```

---

*Report generated: 2026-05-23 | Audit type: READ-ONLY passive LAN scan | No device settings were changed*
