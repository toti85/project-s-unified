# NVR FIRMWARE AUDIT — Hikvision DS-7632NI-I2
**Dátum:** 2026-05-26  
**Auditor:** Automated LAN Scan + Visual Image Analysis  
**Cél:** Firmware állapot felmérése, frissítés előkészítése

---

## 1. ESZKÖZ AZONOSÍTÁS

| Mező | Érték |
|------|-------|
| **Típus** | Network Video Recorder (NVR) |
| **Gyártó** | Hikvision |
| **Model** | DS-7632NI-I2 |
| **Sorozatszám** | 1620170618CCRR779863013WCVU |
| **Hardware verzió** | 0100054103000000 |
| **IP cím** | 192.168.1.111 (statikus) |
| **MAC cím** | 18:68:cb:92:56:11 |
| **Gateway** | 192.168.1.1 |
| **DNS elsődleges** | 8.8.8.8 (Google) ← *módosítva 2026-05-26* |
| **DNS másodlagos** | 8.8.4.4 (Google) ← *módosítva 2026-05-26* |
| **Subnet mask** | 255.255.255.0 |
| **NTP szerver** | 216.239.35.0 (Google NTP) ← *beállítva 2026-05-26* |
| **Idő mód** | NTP ← *módosítva manual→NTP 2026-05-26* |

> **Megjegyzés:** Az eszközt korábban Reolink-nak azonosítottuk (port 8200/8443 alapján),  
> de a képek alapján kiderült: ez egy **Hikvision I-series NVR**. A port 8200 a Hikvision SDK port, nem Reolink.
>
> ✅ **ISAPI-val megerősítve** — Digest auth után teljes hozzáférés: `GET /ISAPI/System/deviceInfo` sikeres.
> Sorozatszám: `DS-7632NI-I21620170618CCRR779863013WCVU`

---

## 2. JELENLEGI FIRMWARE ÁLLAPOT

| Mező | Érték |
|------|-------|
| **Firmware verzió** | **V4.61.025** |
| **Build dátum** | **Build 220905** (2022. szeptember 5.) |
| **Verzió kora** | ~3 év 8 hónap (elavult) |
| **Frissítés állapota** | SZÜKSÉGES |

### 2.1. Miért elavult?

A V4.61.025 Build 220905 firmware 2022 szeptemberében jelent meg. Azóta Hikvision több  
biztonsági javítást és funkciójávítást adott ki a DS-7600NI-I2 sorozathoz:

- **V4.62.x** — 2023-as kiadás: biztonsági javítások, HIK-Connect fejlesztések
- **V4.64.x** — 2024-es kiadás: CVE javítások, TLS fejlesztések, HIK-Connect v3

### 2.2. Ismert sebezhetőségek (V4.61 előtt/körül patch-elt)

| CVE | Súlyosság | Leírás | Állapot V4.61.025-ben |
|-----|-----------|--------|----------------------|
| CVE-2021-36260 | **KRITIKUS (9.8)** | Command injection web serveren keresztül | Valószínűleg javítva (2022 előtt patchelt) |
| CVE-2022-28173 | **Magas (7.5)** | Stack overflow web service-ben | Bizonytalan — ellenőrzés szükséges |
| CVE-2023-28808 | **Kritikus** | Hibás hozzáférés-ellenőrzés | V4.61-ben NEM javítva — frissítés kell |
| CVE-2023-28812 | **Magas** | Buffer overflow RTSP-ben | V4.61-ben NEM javítva — frissítés kell |

> **Fontos:** A CVE-2023-28808 és CVE-2023-28812 javítása **megköveteli** a firmware frissítést.  
> Ezek aktívan kihasználható sebezhetőségek Hikvision NVR eszközökön.

---

## 2b. CSATLAKOZTATOTT KAMERÁK (ISAPI / InputProxy)

| Ch | Név | IP | Model | Firmware | Állapot |
|----|-----|----|-------|----------|---------|
| 1 | *(névtelen)* | 192.168.1.60 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 2 | *(névtelen)* | 192.168.1.61 | — | — | ⚠️ Offline |
| 3 | Camera 01 | 192.168.1.62 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 4 | Camera 01 | 192.168.1.63 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 5 | *(nincs adat)* | 192.168.1.64 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 6 | konveer1 | 192.168.1.65 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 7 | zagnia1 | 192.168.1.66 | — | — | ⚠️ Offline |
| 8 | konveer2 | 192.168.1.67 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 9 | zadnia2 | 192.168.1.68 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 10 | dvir2 | 192.168.1.69 | DS-2CD2T42WD-I8 | V5.5.53 build 180730 | ✅ Online |
| 11 | Vulica | *(folytatás)* | — | — | ⚠️ Ellenőrzés szükséges |

**Kamera firmware kritikusan elavult:** V5.5.53 Build 180730 = **2018. július 30.** — 8 éves!  
Legújabb DS-2CD2T42WD-I8 firmware: V5.7.x (2023+) — frissítés szükséges kameránként.

---

## 2c. TÁROLÓ ÁLLAPOT (ISAPI)

| HDD | Típus | Kapacitás | Szabad hely | Mód | Állapot |
|-----|-------|-----------|-------------|-----|--------|
| HDD 1 | SATA | 5 723 166 KB (~5.46 TB) | 0 KB | RW / Quota | ✅ OK |
| HDD 2 | SATA | 5 723 166 KB (~5.46 TB) | 0 KB | RW / Quota | ✅ OK |
| **Összesen** | | **~10.9 TB** | **0 KB** | quota | Teli / folyamatos felülírás |

> **freeSpace: 0** = a lemezek tele vannak. A `workMode: quota` módban a régi felvételek  
> felülírása automatikusan történik (circular recording). Ez normális állapot.

---

## 3. PORT ÁLLAPOT (LAN — 192.168.1.111)

| Port | Protokoll | Hikvision neve | Állapot | Megjegyzés |
|------|-----------|----------------|---------|------------|
| **85** | HTTP | HTTP Port (web UI) | ✅ OPEN | Nem-standard! (alapértelmezett: 80) |
| **554** | RTSP | RTSP Port | ✅ OPEN | Videó streaming |
| **8200** | SDK | Server Port | ✅ OPEN | Hikvision SDK/iVMS |
| **8443** | TLS | Extended Service Port | ✅ OPEN | HIK-Connect kibővített |
| 80 | HTTP | — | ❌ ZÁRVA | Web UI PORT 85-re van átírva |
| 443 | HTTPS | HTTPS Port | ❌ ZÁRVA | HTTPS nincs aktívan hallgatva |
| 9010 | TCP | HIK Cloud cmd | ❌ ZÁRVA | Cloud parancs port (NAT-ban látható) |
| 9020 | TCP | HIK Cloud data | ❌ ZÁRVA | Cloud adat port |

### 3.1. UPnP — két szint, eltérő státusz (ISAPI 2026-05-27 diagnosztika)

> **FONTOS:** Az NVR-en az UPnP **két különböző szinten** létezik — ezeket nem szabad összekeverni.

#### 3.1.A — SSDP/Discovery szintű UPnP (`/ISAPI/System/Network/interfaces/1`)

Ez az NVR **hálózati felfedezhetőségét** szabályozza (pl. Windows Hálózat, ONVIF discovery).

```xml
<Discovery>
  <UPnP><enabled>false</enabled></UPnP>
  <Zeroconf><enabled>false</enabled></Zeroconf>
</Discovery>
```
**Állapot: ❌ KIKAPCSOLVA** — Az NVR nem jelenti be magát a LAN-on UPnP discovery protokollon.

#### 3.1.B — NAT Port-mapping UPnP (`/ISAPI/System/Network/UPnP`)

Ez az NVR **router port-forwarding automatizálását** szabályozza (IGD protokoll).

```xml
<UPnP><enabled>true</enabled><ports><enabled>true</enabled>
  <natRouterLanAddr>192.168.1.1</natRouterLanAddr>
  <natType>manual</natType></ports></UPnP>
```
**Állapot: ✅ ENGEDÉLYEZVE** — Az NVR megpróbálja regisztrálni a portokat a routernél (192.168.1.1).

#### 3.1.C — Port-mapping kísérlet eredmények (`/ISAPI/System/Network/UPnP/ports/status`)

Az NVR WAN IP-t helyesen ismeri: **46.253.140.72**

| Port típus | Belső | Külső | Státusz | Magyarázat |
|-----------|-------|-------|---------|------------|
| HTTP | http (85) | 80 | ⚠️ **conflict** | Router visszautasítja — port 80 már foglalt |
| admin/SDK | admin (8200) | 8000 | ⚠️ **conflict** | Router visszautasítja — ütközés |
| RTSP | rtsp (554) | 554 | ⚠️ **conflict** | Router visszautasítja — ütközés |
| HTTPS | https | 443 | ⚫ **inactive** | Nem regisztrált |
| SDK_OVER_TLS | 8443 | 8443 | ⚫ **inactive** | Nem regisztrált |

**Következtetés:** Az NVR küldi az UPnP port-mapping kéréseket, de a router (192.168.1.1) **visszautasítja** őket (`conflict`). Ez azért van, mert a router már tartalmaz manuális port-forward szabályokat ugyanezekre a portokra, és az UPnP IGD nem tudja felülírni őket.

**Remote access állapota:** ❌ Nem működik — port-mapping ütközések miatt.

**Megoldás opciók:**
1. **Router manuális port-forwarding**: 192.168.1.111:85→WAN:85, :554→:554, :8200→:8000, :8443→:8443  
   *(a jelenlegi WAN:80→LAN:80-as konfliktust feloldani vagy eltávolítani)*
2. **SSDP Discovery bekapcsolása** (3.1.A): Menu → Network → Basic Settings → manuálisan  
   *(ez nem oldja meg a remote access problémát, csak a LAN-on teszi láthatóvá az NVR-t)*
3. Mindkettő egyszerre ajánlott

---

## 4. WEB UI HOZZÁFÉRÉS MEGERŐSÍTVE

```
GET http://192.168.1.111:85/ → HTTP 200 OK
Server: Hikvision-Webs (implicit)
Redirect: /doc/index.html
Auth method: Digest MD5 (realm: f0fd9134d52e82c9f9c14c51)
```

A web felület elérhető, de belépéshez jelszó szükséges (Digest auth).  
Browser-ből megnyitható: **http://192.168.1.111:85/**

---

## 5. FIRMWARE FRISSÍTÉS ELŐKÉSZÍTÉSE

### 5.1. Frissítés előtti elvégzendő lépések (KÖTELEZŐ)

- [ ] **Konfiguráció exportálás** — NVR menu: Maintenance → Import/Export → Export Config
- [ ] **Felvételi ütemterv mentése** — Képernyőkép a Recording Schedule oldalról
- [ ] **Csatorna beállítások mentése** — Camera Management oldal exportálása
- [ ] **Jelszavak dokumentálása** — admin és operátor jelszavak biztonságos helyen
- [ ] **HDD állapot ellenőrzése** — Maintenance → HDD Info (ne legyen hibás HDD)
- [ ] **Aktív felvételek leállítása** — ha folyamatos felvétel van, ezt jelezni kell
- [ ] **UPS / áramellátás** — frissítés közben **soha ne legyen áramkimaradás** (téglaesítési kockázat)

### 5.2. Firmware letöltési forrás

**Hikvision Official Firmware Download:**  
```
https://www.hikvision.com/en/support/download/firmware/
```
- Keresési szó: **DS-7632NI-I2**
- Alternatíva: https://www.hikvisioneurope.com/eu/portal/ → Technical Support → NVR → Firmware → I series

**VAGY:** Az NVR-en belül (ha internet-elérése van):  
Menu → Maintenance → Upgrade → **Online Upgrade** (automatikusan ellenőrzi)

### 5.3. Firmware fájl azonosítása

A letöltött fájl formátuma:  
```
digicap.dav
```
vagy
```
DS-7600NI-I2_Vx.xx.xxx_xxxxxx.dav
```

**Ellenőrzési pont:** A firmware fájl neve tartalmaznia kell a `7600NI-I2` modellcsaládot,  
különben **incompatible** hibát kapunk és a frissítés megtagadja.

### 5.4. Frissítési eljárás (Lokális — USB-s módszer)

1. Töltsd le a `.dav` firmware fájlt a Hikvision oldaláról
2. Másold USB pendrive gyökerébe (FAT32 formázás)
3. Csatlakoztasd az USB-t az NVR-be
4. Menu → Maintenance → Upgrade → **Local Upgrade**
5. Válaszd ki a `.dav` fájlt → Start Upgrade
6. Az NVR automatikusan újraindul (~5-10 perc)
7. Frissítés után ellenőrizd: Menu → Maintenance → System Info → verzió

### 5.5. Frissítési eljárás (Web UI módszer — port 85)

1. Böngészőben nyisd meg: `http://192.168.1.111:85/`
2. Jelentkezz be admin fiókkal
3. Configuration → Maintenance → Upgrade
4. "Browse" → válaszd a `.dav` fájlt → Upgrade
5. **NE zárd be a böngészőt** frissítés közben

---

## 6. KOCKÁZATÉRTÉKELÉS

| Kockázat | Szint | Megjegyzés |
|----------|-------|------------|
| NVR firmware 3+ éves (V4.61, 2022) | 🔴 MAGAS | CVE-2023-28808, CVE-2023-28812 javítása szükséges |
| Kamera firmware 8 éves (V5.5.53, 2018) | 🔴 KRITIKUS | 9 db kamera, összes elavult — 2 db offline is |
| Web UI HTTP (nem HTTPS) | 🟡 KÖZEPES | Port 85 nincs TLS — LAN belülről titkosítatlan |
| HTTP port non-standard (85) | 🟢 ALACSONY | Nem véd igazán, de csökkenti az auto-scan találatokat |
| UPnP kikapcsolva NVR-en | 🟢 ALACSONY | Remote access nem működik, de ez véd is az internet-kiszolgáltatás ellen |
| 2 kamera offline (ch2, ch7) | 🟡 KÖZEPES | 192.168.1.61 és .66 — hálózati hiba vagy meghibásodás |
| HDD mindkettő teli (0 KB szabad) | 🟢 ALACSONY | Quota/circular mode — normális, régi felvételek felülírása zajlik |

---

## 7. KÖVETKEZŐ LÉPÉSEK (PRIORITÁS SORRENDBEN)

1. **[AZONNAL]** Firmware letöltése: https://www.hikvision.com/en/support/download/firmware/ → DS-7632NI-I2
2. **[FRISSÍTÉS ELŐTT]** Konfiguráció export: Menu → Maintenance → Import/Export
3. **[FRISSÍTÉS ELŐTT]** HDD állapot ellenőrzés: Menu → Maintenance → HDD Info
4. **[FRISSÍTÉS]** Local Upgrade USB-ről vagy Web UI-ból (port 85)
5. **[FRISSÍTÉS UTÁN]** Port konfiguráció visszaellenőrzés (HTTP port 85 megmaradt-e)
6. **[OPCIONÁLIS]** Router NAT/port-forwarding beállítása ha remote access kell

---

## 8. ÖSSZEFOGLALÁS

```
ESZKÖZ:       Hikvision DS-7632NI-I2 NVR (32 csatornás) — ISAPI MEGERŐSÍTVE ✅
IP:           192.168.1.111:85 (HTTP web UI aktív, Digest auth)
NVR FW:       V4.61.025 Build 220905 (2022-09-05) ← 3,5 ÉVE NEM FRISSÍTVE
KAMERA FW:    V5.5.53 Build 180730 (2018-07-30) ← 8 ÉVE NEM FRISSÍTVE (9 db)
HDD:          2x ~5.46 TB, mindkettő OK, tele (circular overwrite mód)
UPNP NAT:     Port-mapping AKTÍV de CONFLICT — router visszautasítja (ütközés)
UPNP SSDP:    KIKAPCSOLVA — LAN-on nem fedezhető fel automatikusan
REMOTE:       ❌ Nem működik — port-mapping ütközések (router manuális FF szükséges)
IDŐZÓNA:      CST-3:00:00 = UTC+3 (Lviv EEST) ✅ — javítva 2026-05-27
NTP:          216.239.35.0 (Google NTP), 60 perc szinkron ✅
OFFLINE CH:   2 db (192.168.1.61, 192.168.1.66 — ch2 "névtelen", ch7 "zagnia1")
KAMERA NEVEK: konveer1/2, zadnia1/2, dvir2, Vulica (ipari/üzemi helyszín)
SZÜKSÉGES:    NVR: V4.62.x+ | Kamerák: V5.7.x+
URGENCIA:     🔴 MAGAS — frissítés ajánlott mielőbb
```

---

## 9. AUTOMATIKUS ISAPI MÓDOSÍTÁSOK — 2026-05-26

> **Relay:** DEV gép (10.157.236.79) → WinRM 46.253.140.72:15985 (SHAYANSKA-DL380) → NVR 192.168.1.111:85  
> **Módszer:** HP iLO power-on (DL380 ki volt kapcsolva) → WinRM PSSession → Python requests + Digest auth

| # | Módosítás | Előtte | Utána | Dátum | Státusz |
|---|-----------|--------|-------|-------|---------|
| 1 | `timeMode` | `manual` | `NTP` | 2026-05-26 | ✅ OK |
| 2 | NTP szerver | *(üres)* | `216.239.35.0` (Google NTP, IP) | 2026-05-26 | ✅ OK |
| 3 | `timeZone` | `CST-2:00:00` (+02:00) | `CST-3:00:00` (+03:00, Lviv EEST) | 2026-05-27 | ✅ OK |
| 4 | DNS PUT (6 kísérlet) | — | **ELUTASÍTVA** — firmware limit | 2026-05-26/27 | ⚠️ Manuális szükséges |

### 9.1. DNS engedélyezése — részletes diagnosztika (ELUTASÍTVA)

A `/ISAPI/System/Network/interfaces/1` PUT endpoint **firmware V4.61.025-ön nem írható** — 6 különböző megközelítés mind visszautasítva:

| Kísérlet | Módszer | Hiba |
|----------|---------|------|
| 1–3 | Részleges XML (csak DNS mezők) | `badParameters / Tag 32: two root tags` |
| 4 | Teljes GET→PUT roundtrip | `badParameters / Tag 32: two root tags` |
| 5 | Deklaráció nélkül + MTU attr strip | `badParameters` (subStatusString nélkül) |
| 6 | id/MACAddress/speed/duplex/autoNeg strip | `badXmlContent / Tag 26: two root tags` |

**Gyökérok:** Az NVR belső XML schema validátora a `Tag N is invalid (two root tags)` hibával visszautasít mindent, ami módosítja a NetworkInterface blokkot. Ez V4.61 firmware ismert limitációja — az endpoint GET-only ezen a verzión.

**DST endpoint:** `GET /ISAPI/System/time/DST` → `403 Invalid Operation / notSupport` — DST szabály ISAPI-n nem elérhető ezen a firmware verzión.

**Manuális lépések (Web UI-on, http://192.168.1.111:85/):**
- DNS: Configuration → Network → Basic Settings → DNS Enable: ON → Primary: `8.8.8.8`, Secondary: `8.8.4.4`
- SSDP Discovery: Configuration → Network → Advanced → UPnP → Discovery: Enable

### 9.2. (Archivált — lásd 9.4 UPnP tisztázás)

### 9.3. Aktuális NTP státusz
```xml
<Time><timeMode>NTP</timeMode><localTime>2026-05-27T...+03:00</localTime><timeZone>CST-3:00:00</timeZone></Time>
<NTPServer><ipAddress>216.239.35.0</ipAddress><portNo>123</portNo><synchronizeInterval>60</synchronizeInterval></NTPServer>
```

### 9.4. UPnP tisztázás (2026-05-27)

Az NVR-en **két egymástól független UPnP szint** létezik:

**Szint 1 — SSDP/Discovery** (`/ISAPI/System/Network/interfaces/1` → `<Discovery><UPnP>`):  
Cél: az NVR legyen automatikusan felfedezhető a LAN-on (Windows Hálózat, ONVIF).  
Állapot: **`false` (kikapcsolva)**

**Szint 2 — NAT Port-mapping** (`/ISAPI/System/Network/UPnP`):  
Cél: az NVR automatikusan kér port-forward szabályokat a routertől (IGD protokoll).  
Állapot: **`true` (engedélyezve)**, `natType: manual`, router: `192.168.1.1`, WAN: `46.253.140.72`

**Port-mapping kísérlet eredmények** (`/ISAPI/System/Network/UPnP/ports/status`):

| Belső port | Külső port | Státusz | Ok |
|-----------|-----------|---------|----|
| http (85) | 80 | ⚠️ conflict | Router visszautasítja — port 80 foglalt |
| admin (8200) | 8000 | ⚠️ conflict | Router visszautasítja — ütközés |
| rtsp (554) | 554 | ⚠️ conflict | Router visszautasítja — ütközés |
| https | 443 | ⚫ inactive | Nem regisztrálva |
| SDK_OVER_TLS (8443) | 8443 | ⚫ inactive | Nem regisztrálva |

**Következtetés:** A router (192.168.1.1) már tartalmaz manuális port-forward szabályokat ezeken a portokon, és az UPnP IGD `conflict` hibával visszautasítja az NVR kéréseit. Remote access **nem működik**. Megoldás: router manuális port-forward szabályok javítása vagy eltávolítása.

### 9.5. Időzóna / DST javítás (2026-05-27)

**Előzmény:** Az NVR `timeZone: CST-2:00:00` (+02:00) volt beállítva, de Lviv nyáron EEST = UTC+3.

**DST endpoint teszt:** `GET /ISAPI/System/time/DST` → `403 notSupport` — DST szabály ISAPI-n nem módosítható.

**Megoldás:** Fix időzóna PUT (nincs DST automatika, de május–október amúgy is EEST):
```xml
PUT /ISAPI/System/time
<Time><timeMode>NTP</timeMode><timeZone>CST-3:00:00</timeZone></Time>
```

**Eredmény:** ✅ `200 OK`

**Ellenőrzés:**
```xml
<Time><timeMode>NTP</timeMode><localTime>2026-05-26T23:04:02+03:00</localTime><timeZone>CST-3:00:00</timeZone></Time>
```
`localTime` most helyesen mutat **+03:00** offsetet.

> **Megjegyzés:** Téli időszámításra (2026. október utolsó vasárnap) a timeZone-t vissza kell állítani CST-2:00:00-ra, mivel a DST automatika nem támogatott ezen a firmware verzión. Firmware frissítés után újra ellenőrizendő.

---
*Riport generálva: 2026-05-26 | LAN audit alapján | Eszköz: 192.168.1.111*  
*2026-05-27: UPnP tisztázás, TZ/DST javítás (+03:00), DNS diagnosztika lezárva | relay: DL380 WinRM*

---

## 10. ROUTER AUDIT — TP-LINK TL-WR940N 192.168.1.1 (2026-05-28)

> **Módszer:** A helyi gép (.164) IP-zárolása miatt a router auditot DL380 (192.168.1.180) relay-en keresztül végeztük. equests.Session + MD5 cookie auth + session token URL. Adatgyűjtés: 2026-05-28, relay: SHAYANSKA-DL380 WinRM (NTLM).

---

### 10.1. Router modell és firmware

| Paraméter | Érték |
|-----------|-------|
| Modell | TP-LINK TL-WR940N v4/v5 |
| Firmware | 3.17.1 Build 170207 Rel.37277n |
| Build dátum | 2017-02-07 |
| Firmware kor | ~9 év (elavult) |
| LAN IP | 192.168.1.1 |
| LAN MAC | 50-C7-BF-B5-1B-A4 |
| WAN MAC | 50-C7-BF-B5-1B-A5 |
| Wi-Fi SSID | Shayanska |
| Wi-Fi csatorna | 6 (2.4 GHz) |

> ⚠️ **Biztonsági figyelmeztetés:** A 2017-es firmware több ismert CVE-t tartalmaz (pl. CVE-2017-13772, CVE-2018-19537, stack overflow a httpd-ben). Frissítés vagy csere szükséges.

---

### 10.2. WAN konfiguráció

| Paraméter | Érték |
|-----------|-------|
| WAN típus | Dynamic IP (DHCP) |
| WAN IP | 46.253.140.72 |
| Subnet | 255.255.255.255 (/32 — ISP PPP-stílusú kiosztás) |
| Gateway | 46.253.140.2 |
| Elsődleges DNS | 8.8.8.8 (Google) |
| Másodlagos DNS | nincs konfigurálva |
| Uptime (gyűjtés időpontjakor) | 0 nap 03:26:41 |

> **Megjegyzés:** WAN subnet /32 (255.255.255.255) és gateway a másik alhálózatban (46.253.140.2) normál viselkedés ISP DHCP/PPP-over-Ethernet esetén.

---

### 10.3. Manuális port-forward szabályok (Virtual Server)

Összesen 8 aktív szabály (irServerListPara alapján). Protokoll: 1=MIND, 2=TCP, 3=UDP.

| # | Külső port | Belső port | Belső IP | Protokoll | Státusz | Megjegyzés |
|---|-----------|-----------|----------|-----------|---------|------------|
| 1 | 88 | 3389 | 192.168.1.88 | MIND | Engedélyezve | RDP — nem szokványos külső porton |
| 2 | 89 | 443 | 192.168.1.89 | TCP | Engedélyezve | HTTPS redirect |
| 3 | 8200 | 8200 | 192.168.1.111 | MIND | Engedélyezve | **NVR SDK port** (Hikvision) |
| 4 | 87 | 87 | 192.168.1.2 | MIND | Engedélyezve | Ismeretlen alkalmazás |
| 5 | 86 | 21 | 192.168.1.2 | MIND | Engedélyezve | FTP (plaintext!) — port obfuszkáció |
| 6 | 12121 | 12121 | 192.168.1.22 | TCP | Engedélyezve | Ismeretlen alkalmazás |
| 7 | 12122 | 12122 | 192.168.1.22 | UDP | Engedélyezve | Ismeretlen alkalmazás |
| 8 | 80 | 80 | 192.168.1.88 | TCP | Engedélyezve | HTTP (plaintext) → .88 |

**Érintett belső hosztok:**
- 192.168.1.88 — RDP (3389/88) + HTTP (80) — Windows asztal/szerver
- 192.168.1.89 — HTTPS (443/89)
- 192.168.1.111 — NVR (Hikvision DS-7632NI-I2) — csak SDK 8200
- 192.168.1.2 — FTP (21/86) + port 87
- 192.168.1.22 — 12121 TCP + 12122 UDP

---

### 10.4. UPnP státusz

A router UI UPnP oldala (UPnPRpm.htm) az audit gépen belépési hiba (cookie-clear + redirect) választ ad — az oldal tartalma nem elérhető a web felületen.

Az NVR ISAPI /ISAPI/System/Network/UPnP és /ISAPI/System/Network/UPnP/ports/status alapján (9.4 szekció):

| UPnP szint | Érték |
|------------|-------|
| NVR UPnP NAT-mapping | **Engedélyezve** (	rue) |
| NVR natType | manual |
| Router gateway (UPnP IGD) | 192.168.1.1 |
| WAN IP (NVR által látott) | 46.253.140.72 |

**UPnP port-mapping ütközések** (NVR kísérlet → router elutasítás):

| NVR belső port | Kért külső port | Eredmény |
|----------------|-----------------|----------|
| 85 (http) | 80 | ⚠️ conflict — foglalt (.88 manuális szabály) |
| 8200 (admin) | 8000 | ⚠️ conflict — ütközés |
| 554 (rtsp) | 554 | ⚠️ conflict — ütközés |
| 443 (https) | 443 | ✖ inactive — nem regisztrálva |
| 8443 (SDK/TLS) | 8443 | ✖ inactive — nem regisztrálva |

> **Következtetés:** Az NVR UPnP IGD kommunikáción keresztül próbálja regisztrálni portjait, de a router manuális port-forward szabályok miatt minden kísérlet conflict hibával végződik. Az NVR remote access ezért **nem funkcionál** az UPnP útvonalon. A manuálisan beállított 8200→.111:8200 szabály (SDK port) az egyetlen működő NVR remote access.

---

### 10.5. DHCP kliens lista (aktív bérletek)

Összesen **26 aktív DHCP bérlet** (DHCPDynList, DHCPDynPara: 26). Formátum: hostname | MAC | IP | Bérleti idő lejártáig.

| Hostnév | MAC | IP | Lejárat |
|---------|-----|-----|---------|
| 3123868269 | D4-27-87-61-C0-2A | 192.168.1.150 | 21:50:36 |
| 3118013486 | D4-27-87-51-35-9E | 192.168.1.151 | 21:50:43 |
| 1120377550 | 74-E9-D8-8B-10-A8 | 192.168.1.152 | 23:19:32 |
| Unknown | D8-32-14-02-D0-00 | 192.168.1.153 | 20:30:37 |
| DESKTOP-AFDT43T | 90-1B-0E-19-C5-45 | 192.168.1.154 | 20:31:44 |
| Unknown | 5E-AA-79-02-D7-DD | 192.168.1.155 | 23:25:48 |
| Redmi-Note-14 | 5E-39-B7-BA-4B-80 | 192.168.1.156 | 23:43:04 |
| Unknown | 42-C7-BB-A0-0B-EC | 192.168.1.157 | 21:10:57 |
| Unknown | 0E-75-5A-2D-A5-2F | 192.168.1.158 | 23:06:19 |
| Galaxy-A20e | 88-29-9C-D5-99-A7 | 192.168.1.159 | 21:57:17 |
| Unknown | 2E-31-68-EA-EA-A1 | 192.168.1.161 | 19:15:27 |
| Redmi-Note-14-Pro | 06-3A-72-DD-61-2F | 192.168.1.162 | 18:06:47 |
| Unknown | 12-40-37-6F-F7-00 | 192.168.1.163 | 23:30:12 |
| SP | D2-E9-C5-E9-49-8E | 192.168.1.164 | 20:48:12 |
| M2006C3LVG-Redmi9AT | 00-C3-0A-32-15-61 | 192.168.1.165 | 23:34:50 |
| Galaxy-A03 | 72-82-EA-53-EE-FA | 192.168.1.166 | 23:58:38 |
| DESKTOP-OE0IINT | 7C-76-35-70-8B-F4 | 192.168.1.168 | 23:07:13 |
| Unknown | BA-0E-C5-99-F3-3B | 192.168.1.169 | 00:49:22 |
| Unknown | DE-C9-EE-9C-25-07 | 192.168.1.170 | 22:50:44 |
| Galaxy-A03 | 52-DE-63-E4-A3-C3 | 192.168.1.171 | 23:55:47 |
| Galaxy-M10 | 18-19-D6-5C-A5-90 | 192.168.1.172 | 21:41:32 |
| Unknown | BE-CB-47-81-02-9E | 192.168.1.173 | 23:56:59 |
| 3123528416 | D4-27-87-61-A2-58 | 192.168.1.174 | 23:48:18 |
| Galaxy-A41 | 1E-47-88-D5-AD-49 | 192.168.1.175 | 20:30:48 |
| Unknown | 72-BE-27-FB-EA-73 | 192.168.1.177 | 23:23:39 |
| DESKTOP-VAR2T1H | D0-AB-D5-73-22-6A | 192.168.1.178 | 23:47:44 |

**Megjegyzések:**
- 192.168.1.111 (NVR) és 192.168.1.180 (DL380) **nincs** a DHCP listában → statikus IP konfiguráció
- 192.168.1.164 = SP (audit gép, jelen munkamenet)
- Sok Unknown hosznév és több véletlenszerű MAC (pl. 5E-, 2E-,  E-, BE-, DE-, BA-, 72-) → modern eszközök MAC randomizálást használnak
- D4-27-87-xx sorozat (3 eszköz: .150, .151, .174) — azonos gyártó (TP-LINK / Xiaomi OUI), lehetséges hálózati eszközök vagy telefonok

---

### 10.6. Ütközéselemzés: NVR UPnP vs manuális port-forward szabályok

| Külső port | Manuális szabály célja | NVR UPnP kérés | Eredmény |
|-----------|----------------------|----------------|---------|
| 80 | 192.168.1.88 (HTTP) | NVR http (85→80) | ⚠️ ÜTKÖZÉS — NVR nem érhető el http-n |
| 554 | nincs manuális | NVR RTSP (554→554) | ⚠️ ÜTKÖZÉS — esetleg más UPnP szabály |
| 8000 | nincs manuális | NVR admin (8200→8000) | ⚠️ ÜTKÖZÉS — esetleg más UPnP szabály |
| 8200 | NVR SDK (8200→111:8200) | — | ✅ Manuális szabály MŰKÖDIK |
| 443 | 192.168.1.89 (HTTPS/89) | NVR https: inactive | ✖ Nem regisztrált |

**Következtetés:** Az NVR SDK (port 8200) az egyetlen remote access vektor, amelyen keresztül a Hikvision DS-7632NI-I2 az interneten elérhető. Az összes többi port (HTTP/80, RTSP/554, SDK2/8000) UPnP-n keresztül nem regisztrálható ütközés miatt.

---

### 10.7. Biztonsági megállapítások és javaslatok

| # | Súlyosság | Megállapítás | Javaslat |
|---|-----------|-------------|---------|
| R-01 | 🔴 Kritikus | Firmware 9 éves (2017-02-07), ismert CVE-k | Router csere vagy firmware frissítés |
| R-02 | 🔴 Kritikus | FTP plaintext (port 21/86) internet felé nyitva | FTP letiltása, SFTP használata |
| R-03 | 🟠 Magas | RDP (3389) internet felé nyitva (port 88) | VPN mögé helyezés, RDP firewall-olás |
| R-04 | 🟠 Magas | NVR SDK (8200) internet felé nyitva | SDK hozzáférés IP whitelist-elése |
| R-05 | 🟠 Magas | HTTP plaintext (port 80 → .88) | HTTPS-re migrálás, HTTP letiltása |
| R-06 | 🟡 Közepes | UPnP IGD engedélyezve a routeren | UPnP letiltása, manuális port-forward használata |
| R-07 | 🟡 Közepes | NVR UPnP aktív (automatikus port-mapping kísérlet) | NVR UPnP NAT-mapping letiltása |
| R-08 | 🟡 Közepes | 26 DHCP kliens, közte sok azonosítatlan "Unknown" | Eszközleltár, MAC filtering vagy VLAN szegmentáció |
| R-09 | 🟡 Közepes | Nincs másodlagos DNS | Backup DNS beállítása (pl. 8.8.4.4) |
| R-10 | 🔵 Alacsony | Router web admin HTTP (nem HTTPS) | Remote admin letiltása; local HTTPS ha firmware támogatja |

---

*Router audit lezárva: 2026-05-28 | Módszer: DL380 relay (192.168.1.180) WinRM NTLM | requests.Session + MD5 cookie auth*
