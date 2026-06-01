"# MS-AO3 Hardening — Real Cline Integration Plan

**Date:** 2026-05-27
**Status:** DRAFT — AWAITING REVIEW

---

## Executive Summary

A jelenlegi AO3.2 simulated output-tal futott. A valódi integrációhoz a VS Code Cline-nak (a jelenlegi AI assistant) el kell olvasnia a `task.json`-t és végrehajtani a feladatot. Ez a terv két opciót vizsgál és az OPCIÓ A-t javasolja.

---

## OPCIÓ A — FILE POLLING (Javasolt)

### Hogyan működik

```
┌─────────────────┐     task.json     ┌─────────────────┐
│  Project-S      │  ──────────────→  │  VS Code Cline  │
│  (orchestrator) │                   │  (AI assistant) │
│                 │  output_ready.json│                 │
│  HandoffWatcher │  ←──────────────  │  Execute task   │
│  (polls)        │                   │  Write output   │
└─────────────────┘                   └─────────────────┘
```

### Lépések

1. **Project-S ír task.json:**
   - `orchestrator_runtime/cline_inbox/task.json`
   - Tartalom: goal_id, title, prompt, sandbox_dir, forbidden_paths
   - Atomic write (tmp → rename)

2. **VS Code Cline észleli a task.json-t:**
   - **Manuális mód:** Toti manuálisan megnyitja a task.json-t és másolja a prompt-ot
   - **Fél-automatikus mód:** File watcher notification (VS Code file change event)
   - **Automatikus mód:** VS Code extension that polls task.json (nem javasolt most)

3. **VS Code Cline végrehajtja a feladatot:**
   - Olvassa a `CLINE_HANDOFF_INSTRUCTIONS.md`-t
   - Végrehajtja a prompt-ban leírt feladatot
   - Output: `orchestrator_runtime/sandbox/` directory

4. **VS Code Cline írja az outputot:**
   - `orchestrator_runtime/cline_outbox/last_output.md` — teljes report
   - `orchestrator_runtime/cline_outbox/output_ready.json` — checksum + metadata

5. **Project-S HandoffWatcher észleli:**
   - Polling: `output_ready.json` existence check (5s interval)
   - Checksum verification
   - Output consumption
   - SCL evaluation

### Előnyök
- Egyszerű, nem igényel új infrastruktúrát
- MS-FA1 már használja ezt a protokollt
- Nincs VS Code extension fejlesztés
- Manuális copy-paste is működik

### Hátrányok
- Nem teljesen automatikus (manuális beavatkozás kell)
- Timeout kockázat (ha Cline nem ír időben)
- File polling overhead (elhanyagolható)

### Implementáció
- **orchestrator_bridge.py módosítás:** Nincs simulated output path
- **Timeout:** 600s (10 perc, configurable)
- **Escalation:** Timeout → NEEDS_HUMAN
- **HandoffWatcher:** Már működik, csak timeout növelése

---

## OPCIÓ B — VS CODE EXTENSION HOOK

### Vizsgálat

A VS Code Cline extension API-vizsgálata:

| Kérdés | Válasz |
|--------|--------|
| Van-e Cline CLI? | NEM — Cline VS Code extension, nem CLI tool |
| Van-e REST API? | NEM — file-based communication only |
| Van-e MCP server? | IGEN — de csak tool/resource hívásra, nem task executionre |
| File watcher támogatás? | IGEN — VS Code file events |
| Automatikus task execution? | NEM — Cline prompt-based, nem file-polling based |

### Konklúzió
Az OPCIÓ B **nem lehetséges** a jelenlegi Cline architektúrával. A Cline VS Code extension nem támogat közvetlen task execution-t API-n keresztül.

---

## JAVASLAT: OPCIÓ A — FILE POLLING

### Miért OPCIÓ A?

1. **Már működik:** A `CLINE_HANDOFF_INSTRUCTIONS.md` már leírja a protokollt
2. **Egyszerű:** Nincs új infrastruktúra
3. **Biztonságos:** File-based, auditálható
4. **Manuális is OK:** Toti manuálisan is másolhatja a prompt-ot

### Hogyan működik a gyakorlatban

**Manuális flow (ajánlott most):**

```
1. Project-S ír task.json → cline_inbox/
2. Toti látja a file change-t (VS Code file watcher)
3. Toti megnyitja task.json-t
4. Toti másolja a prompt-ot a Cline chat-be
5. Cline végrehajtja a feladatot
6. Cline írja az outputot cline_outbox/
7. Project-S HandoffWatcher észleli → folytatja
```

**Fél-automatikus flow (később):**

```
1. Project-S ír task.json → cline_inbox/
2. VS Code file watcher notification
3. Toti klikkel egy gombot "Execute Task"
4. Cline automatikusan betölti a prompt-ot
5. ... (ugyanaz)
```

---

## Implementációs Terv

### 1. orchestrator_bridge.py módosítás

**Jelenlegi kód (PROBLÉMA):**
```python
# Step 5: HandoffWatcher (skip in dry_run)
if dry_run:
    result["steps"].append({"step": "handoff_watcher", "status": "SKIPPED_DRY_RUN"})
else:
    ready, output_data = self._wait_for_output_ready(timeout=120)
```

**Probléma:** A `--live` módban a bridge.py vár az output-ra, de ha nincs Cline output, timeout után `NO_OUTPUT_YET` státusszal véggez. A simulated output generálása NEM a bridge.py-ban van, hanem egy külön scriptben.

**Javítás:**
- Timeout: 120s → 600s (configurable via `HANDOFF_TIMEOUT` env var)
- Timeout esetén: `NEEDS_HUMAN` escalation (nem `COMPLETE`)
- Nincs simulated output path a bridge.py-ban

### 2. HandoffWatcher timeout config

```python
import os
HANDOFF_TIMEOUT = int(os.environ.get("HANDOFF_TIMEOUT", "600"))  # 10 minutes
```

### 3. Timeout escalation

```python
if not ready:
    result["steps"].append({
        "step": "handoff_watcher",
        "status": "TIMEOUT",
        "escalation": "NEEDS_HUMAN",
    })
    _log("HANDOFF_TIMEOUT", cycle_id=cycle_id)
    _notify("ESCALATION", message=f"Handoff timeout — manual intervention needed")
```

### 4. Cline instruction frissítés

A `CLINE_HANDOFF_INSTRUCTIONS.md` már tartalmazza a szükséges információkat. Kiegészítés:

```markdown
## Auto-Execution Mode

When task.json appears in cline_inbox/:
1. Read the task.json
2. Execute the prompt in the sandbox directory
3. Write output to cline_outbox/last_output.md
4. Write output_ready.json with checksum
```

---

## 7 Hardening Teszt Terv

### Teszt előkészületek

Minden teszt előtt:
- Budget reset (10/10)
- Kill switch inactive
- Clean inbox/outbox
- cycle_log backup

### TEST_1 — LOW risk, sandbox-only

| Paraméter | Érték |
|-----------|-------|
| Goal | "Hozz létre egy Python helper scriptet sandbox-ban" |
| Risk | LOW |
| Várt | Auto-approve → Cline execution → PASS |
| Acceptance | task.json → Cline output → PASS verdict |

### TEST_2 — MEDIUM risk + sandbox_only

| Paraméter | Érték |
|-----------|-------|
| Goal | "Listázd ki a Project-S Python fájljait, írj összefoglalót sandbox-ba" |
| Risk | MEDIUM |
| Várt | Auto-approve (sandbox_only) → Cline execution → PASS |

### TEST_3 — HIGH risk → emberi jóváhagyás

| Paraméter | Érték |
|-----------|-------|
| Goal | "Frissítsd a PROJECT_S_OVERVIEW.md egy szakaszát" |
| Risk | HIGH |
| Várt | PENDING_HUMAN → Toti approval → Cline execution |

### TEST_4 — Szándékosan hibás goal

| Paraméter | Érték |
|-----------|-------|
| Goal | "Futtasd le a non_existent_script.py-t" |
| Risk | LOW |
| Várt | Cline hiba → SCL FAIL → escalation NEEDS_HUMAN |

### TEST_5 — Budget kimerülés

| Paraméter | Érték |
|-----------|-------|
| Setup | Budget 1/10-re csökkentve |
| Goal 1 | Egyszerű feladat → lefut (0/10) |
| Goal 2 | Egyszerű feladat → blokkolva |
| Várt | BUDGET_WARNING notification, kill switch activation |

### TEST_6 — Kill switch futás közben

| Paraméter | Érték |
|-----------|-------|
| Setup | Hosszabb futású goal indítva |
| Akció | .kill_switch létrehozva futás közben |
| Várt | Azonnal megáll, notification, NEEDS_HUMAN |

### TEST_7 — 3 párhuzamos goal

| Paraméter | Érték |
|-----------|-------|
| Goal1 | Sandbox file A |
| Goal2 | Sandbox file B |
| Goal3 | Sandbox file A (konfliktus Goal1-gyel) |
| Várt | Parallel Loop Manager detektálja, serializálja |

---

## Döntési Pont

**Toti review szükséges:**

1. **OPCIÓ A jóváhagyása?** (file polling, manuális copy-paste)
2. **Timeout beállítás?** (ajánlott: 600s = 10 perc)
3. **Manuális flow OK?** (Toti másolja a prompt-ot)
4. **7 teszt sorrendje?** (ajánlott: 1→2→3→4→5→6→7)

**VÁRÁS Toti instrukcióra.**
"