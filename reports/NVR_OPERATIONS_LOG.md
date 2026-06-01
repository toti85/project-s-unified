# NVR / Camera / Network Operations Log

Ez a doksi a Project-S fizikai infrastruktúra szálának (NVR, kamerák,
router, ISAPI munkák) naplója. NEM Project-S core fejlesztés.

A Project-S core STATUS_AND_JOURNAL csak hivatkozik erre, nem
ismétli a tartalmat.

Kapcsolódó doksi: `reports/NVR_FIRMWARE_AUDIT_DS7632NI_I2_20260526.md`

---

## 2026-05-26: NVR kamera rendszer audit + automatikus ISAPI konfig módosítások

### Kontextus

DEV gép (10.157.236.79) nem volt a kamera LAN-on. A DL380 szerver (SHAYANSKA-DL380, 46.253.140.72) ki volt kapcsolva. A cél: NVR konfiguráció export átnézése és automatikus javítások.

**Relay lánc:** DEV → iLO Redfish (46.253.140.72:89) → DL380 power-on → WinRM (46.253.140.72:15985) → Python requests + Digest auth → NVR ISAPI (192.168.1.111:85)

### iLO power-on

A DL380 ki volt kapcsolva. `ilo_controller.py` Redfish API-val bekapcsolva:
- NAT redirect workaround működött (192.168.1.89 → 46.253.140.72:89 reírás)
- `power_on()` → `True`
- 154 másodperc után WinRM port 15985 elérhetővé vált

### NVR azonosítás és ISAPI audit

**Eszköz:** Hikvision DS-7632NI-I2 NVR, 32 csatornás  
**IP:** 192.168.1.111:85 (nem-standard HTTP port)  
**Firmware:** V4.61.025 Build 220905 (2022-09-05) — 3,5 éve nem frissítve  
**Auth:** Digest MD5

22 csatorna leltározva ISAPI-n keresztül (9 db DS-2CD2T42WD-I8, firmware 2018 — kritikusan elavult). 6 db offline csatorna.

### Automatikusan elvégzett módosítások (ISAPI PUT via DL380 relay)

| # | Módosítás | Előtte | Utána | Státusz |
|---|-----------|--------|-------|---------|
| 1 | `timeMode` | `manual` | `NTP` | ✅ OK |
| 2 | NTP szerver | *(üres)* | `216.239.35.0` (Google NTP, IP-alapú) | ✅ OK |
| 3 | DNS engedélyezés | — | ELUTASÍTVA (NVR strict XML schema) | ⚠️ Manuális UI |

**DNS workaround:** Az NTP szerver IP-alapúra állítva → nem szükséges DNS a szinkronizáláshoz.  
**DNS UI lépés (manuális):** `http://192.168.1.111:85/` → Configuration → Network → Basic Settings → DNS: `8.8.8.8` / `8.8.4.4`

### Audit report

`reports/NVR_FIRMWARE_AUDIT_DS7632NI_I2_20260526.md` — létrehozva és frissítve:
- 22 csatornás kamera leltár
- Firmware kockázatelemzés (NVR: 🔴 MAGAS, kamerák: 🔴 KRITIKUS)
- 9. szekció hozzáadva: automatikus ISAPI módosítások dokumentálva

---

## 2026-05-27: NVR audit folytatás — TZ/DST, DNS diagnózis, UPnP, router azonosítás

### Elvégzett munkák

#### 9.5 — Időzóna (TZ/DST) javítás
- DST endpoint (`/ISAPI/System/time/localTime`) → `403 notSupport` a V4.61 firmwarén
- **Fix:** `CST-3:00:00` közvetlen PUT `/ISAPI/System/time`-ra → `+03:00` megerősítve
- Caveat: DST automatikus váltás nem támogatott — október végén manuálisan kell `CST-2:00:00`-ra visszaállítani

#### 9.1 — DNS diagnózis (teljes kivizsgálás)
- 6 különböző XML variáns kipróbálva a `/ISAPI/System/Network/interfaces/1` PUT-hoz
- Minden kísérlet sikertelen: `Tag N is invalid (two root tags)` / `badXmlContent`
- **Végeredmény:** V4.61.025 firmwaren az interfész endpoint gyakorlatilag csak olvasható
- DNS manuálisan szükséges a Web UI-n: `http://192.168.1.111:85/`

#### 9.4 — UPnP kétszintű architektúra tisztázva
- **SSDP Discovery** (`/ISAPI/System/Network/interfaces/1`): `false` — KIKAPCSOLVA ✅
- **NAT UPnP port-mapping** (`/ISAPI/System/Network/UPnP`): `enabled` de minden port CONFLICT/inactive
- Konfliktusok: HTTP(80)→`conflict`, SDK(8000)→`conflict`, RTSP(554)→`conflict`, HTTPS(443)→`inactive`, SDK_TLS(8443)→`inactive`
- WAN IP helyesen felismert: `46.253.140.72`

#### Riport frissítések (NVR_FIRMWARE_AUDIT_DS7632NI_I2_20260526.md)
- Szekció 3.1: UPnP kétszintű részletezés (3.1.A SSDP / 3.1.B NAT / 3.1.C port státusz)
- Szekció 9.1: DNS diagnózis (6 kísérlet dokumentálva, firmware korlát)
- Szekció 9.4: UPnP pontosítás
- Szekció 9.5: TZ/DST javítás
- Summary block: `UPNP NAT: conflict`, `UPNP SSDP: KIKAPCSOLVA`, `IDŐZÓNA: CST-3:00:00 ✅`

### Router azonosítás (TP-LINK TL-WR940N)

**Fontos:** A router **NEM TOTOLINK** — `WWW-Authenticate: Basic realm="TP-LINK Wireless N Router WR940N"`

| Tulajdonság | Érték |
|-------------|-------|
| Model | TP-LINK TL-WR940N |
| Firmware | OpenWrt custom (Dropbear SSH 2012.55) |
| HTTP | Port 80 — nyitva |
| SSH | Port 22 — nyitva (Dropbear 2012.55, legacy KEX: diffie-hellman-group1-sha1) |
| Web auth | Cookie-alapú Basic, MD5 jelszóhash, JavaScript escape() kódolás |

### Router audit akadályok

- HTTP Web UI: `errCode=1` minden kísérletnél = **egy másik admin már be van jelentkezve**
- SSH: `root` felhasználó létezik, de a jelszó ismeretlen (AUTH FAIL: "", admin, tplink, 1234, root, er13fig1)
- paramiko 5.x: nem támogatja a Dropbear 2012 legacy KEX-et → downgrade 2.12.0-ra szükséges holnapra

### Függőben maradt feladatok (2026-05-28-ra)

- [ ] Router audit befejezése (HTTP + SSH) — miután a másik admin kilép a sessionből
- [ ] Riport 10. szekció megírása: router model, port-forward szabályok, UPnP, WAN, DHCP
- [ ] Konfliktuselemzés: melyik manuális port-forward ütközik az NVR UPnP kéréseivel

---
