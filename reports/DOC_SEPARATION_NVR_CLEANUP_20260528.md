# DOC SEPARATION — NVR Cleanup Report

**Dátum:** 2026-05-28  
**Feladat:** NVR / fizikai infrastruktúra tartalom kiemelése a PROJECT_S_STATUS_AND_JOURNAL.md-ből

---

## 1. Executive Summary

A `PROJECT_S_STATUS_AND_JOURNAL.md` véletlenül megkapta a 2026-05-26 és 2026-05-27 NVR/kamera/router naplózási tartalmát (~95 sor). Ez ellentétes a stratégiai döntéssel: a STATUS_AND_JOURNAL CSAK a Project-S core (szoftver, AI, orchestration) szálát követi.

**Művelet:** A teljes NVR tartalom áthelyezve egy dedikált `reports/NVR_OPERATIONS_LOG.md` fájlba. A STATUS_AND_JOURNAL-ban rövid hivatkozás maradt. Doksi-szeparáció szabály beillesztve a dokumentum elejére.

**Verdict: CLEAN** ✅

---

## 2. NVR_OPERATIONS_LOG.md létrehozva

| Paraméter | Érték |
|-----------|-------|
| Fájl | `reports/NVR_OPERATIONS_LOG.md` |
| Sorok száma | 109 sor |
| Áthelyezett szekciók | 2 db |

**Áthelyezett szekciók:**
- `## 2026-05-26: NVR kamera rendszer audit + automatikus ISAPI konfig módosítások`
- `## 2026-05-27: NVR audit folytatás — TZ/DST, DNS diagnózis, UPnP, router azonosítás`

Tartalom változatlanul (szó szerint) áthelyezve.

---

## 3. STATUS_AND_JOURNAL.md előtte/utána

| Metrika | Előtte | Utána | Különbség |
|---------|--------|-------|-----------|
| Sorok száma | 838 | 764 | -74 (nettó) |
| NVR részletes tartalom | ~95 sor | 0 sor | eltávolítva |
| Szeparációs szabály | nincs | 13 sor (line 13-27) | hozzáadva |
| Rövid NVR hivatkozás | nincs | 7 sor (line 757-764) | hozzáadva |
| Backup | — | `.bak_pre_nvr_separation_20260528` | 50671 bytes |

---

## 4. Doksi-szeparáció szabály beillesztve

**Helye:** `PROJECT_S_STATUS_AND_JOURNAL.md` — 13. sor, a bevezető `---` után, `# I. RÉSZ — STATUS` előtt

**Tartalom:**
```
## Doksi-szeparáció szabály (2026-05-27)

A STATUS_AND_JOURNAL CSAK a Project-S core (szoftver, AI,
orchestration, milestone) fejlesztését tartalmazza.

Külön dokumentumok kezelik:
- `reports/NVR_OPERATIONS_LOG.md` — NVR, kamerák, ISAPI munkák
- (későbbi) `reports/NETWORK_OPERATIONS_LOG.md` — router, VPN, port forward
- (későbbi) `reports/SERVER_OPERATIONS_LOG.md` — DL380 fizikai szerver, iLO
```

---

## 5. self_state.json érintettség

**Érintett volt-e: NEM** ✅

Keresés eredménye: NVR / Hikvision / ISAPI / kamera / 192.168.1.111 tartalom **nem található** a `self_state.json`-ban. Csak Project-S core tartalom (AI provider, OpenRouter, gap-ek, modellek). **Módosítás nem szükséges.**

---

## 6. PROJECT_S_OVERVIEW.md érintettség

**Érintett volt-e: NEM** ✅

A fájl tartalmaz DL380 hivatkozásokat, de KIZÁRÓLAG a Project-S staging proof kontextusában (a rendszer futtathatóságának bizonyítékaként). NVR / Hikvision / ISAPI / router / kamera tartalom **nem található**. **Módosítás nem szükséges.**

---

## 7. Backupok listája

| Fájl | Méret |
|------|-------|
| `PROJECT_S_STATUS_AND_JOURNAL.md.bak_pre_nvr_separation_20260528` | 50671 bytes |

(Korábban létező backupok érintetlenek: `.bak_before_msfa1_sync_20260524`)

---

## 8. Ellenőrzőlista

| # | Teszt | Eredmény |
|---|-------|----------|
| A | `NVR_OPERATIONS_LOG.md` létrehozva | ✅ Y (109 sor) |
| B | 2026-05-26 szakasz áthelyezve | ✅ Y |
| C | 2026-05-27 szakasz áthelyezve | ✅ Y |
| D | STATUS_AND_JOURNAL-ban rövid hivatkozás maradt | ✅ Y |
| E | Doksi-szeparáció szabály beillesztve | ✅ Y (line 13) |
| F | self_state.json NVR-érintett volt | ✅ N (nem volt) |
| G | PROJECT_S_OVERVIEW.md NVR-érintett volt | ✅ N (nem volt) |
| H | Backup elkészült | ✅ Y |
| I | Kód-szintű módosítás történt | ✅ N (csak markdown) |
| J | **Verdict** | ✅ **CLEAN** |
| K | STATUS_AND_JOURNAL most csak Project-S core-t tartalmaz | ✅ Y |
