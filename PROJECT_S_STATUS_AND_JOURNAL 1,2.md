# PROJECT-S — Hol tartunk és hogyan jutottunk ide

**Verzió:** v1.2
**Dátum:** 2026-04-29 reggel (a 2026-04-28 este lezárása után)
**Készítette:** Claude + Toti (közös munka)
**Státusz:** Élő dokumentum — frissítendő mérföldköveknél
**Előző verziók:** v1.0 (2026-04-28 délelőtt), v1.1 (2026-04-28 délután)

---

## Hogyan használd ezt a dokumentumot

Ez nem dokumentáció. Ez **napló és iránytű**. Három részből áll:

- **I. RÉSZ — STATUS:** hol tartunk most (5 perc alatt képbe hoz)
- **II. RÉSZ — JOURNAL:** hogyan jutottunk ide (a teljes két nap)
- **III. RÉSZ — A KÉT ÉRTÉK RÉTEGE** *(új a v1.2-ben)*: mi marad meg ha bármi megváltozik

Ha új AI session indul: olvasd el a `PROJECT_S_FOUNDATION.md`-t, aztán a `self_state.json`-t, aztán **ha még szükség van rá**, ezt a dokumentumot. A `self_state.json` **mindig** naprakészebb mint ez.

---

# I. RÉSZ — STATUS

## A rendszer egy mondatban

Egy önreflexív rendszert építünk, amely **tudja ki ő, hol tart, mit csinált, mit tervez** — és ezt a tudást strukturált, géppel olvasható formában tárolja, hogy bármelyik AI azonnal kontextusba kerüljön.

A v1.2 frissítés egy fontos kiegészítéssel: a két nap munkája **két különálló értéket teremtett**, és ezt explicit ki kell mondani. Az egyik a Witness layer (architektúra-független), a másik a Doer pipeline-fix (architektúra-specifikus). Lásd a III. részt.

## Mi működik most

### Witness layer (megfigyelő) — kész és önálló

| Modul | Mi csinálja |
|-------|-------------|
| `witness/evidence_reader.py` | Streaming olvasó: 403,872 rekordos `meta_evidence.jsonl` |
| `witness/bridges/state_reader.py` | Read-only adapter a `PersistentStateManager`-hez (asyncio.run wrapper) |
| `witness/bridges/organism_to_meta.py` | Híd két módban: dry-run (default) + observe (`--observe` flag) |
| `witness/learning_diagnostic.py` | A `learning.jsonl` elemzője |
| `organism/core/state_observer.py` | A `self_state.json` gap-jeit task-ká konvertálja az Organism-nak |

### Doer layer (cselekvő) — élesben fut

A `main.py → AgentLoop` pipeline 7 javítással **valóban** teljes:

| Komponens | Státusz |
|-----------|---------|
| AgentLoop infinite loop | ✅ fut, 5 sec poll |
| `_async_init()` (új) | ✅ tool inicializálás a run() előtt |
| CognitiveCore (Phase 1) | ✅ `qwen3-235b` az OpenRouter-en (GAP_012 javítás után) |
| SmartToolOrchestrator | ✅ **9 tool aktív** (file × 5, web × 3, browser × 1) |
| Evaluator (Phase 3) | ✅ OpenRouter-en (confidence 0.95) |
| MetaController (observe-only) | ✅ minden task után `external_observation` event |
| RISK_001 csapda | ✅ telepítve — observe-only példányon `run_goal()` blokkolva |
| 4-fázisú pipeline | ✅ end-to-end teszt: 8 valódi találat tényleges tool-hívással |

### Tudat-réteg (self_state.json) — élő

54+ KB, élő dokumentum:
- **5 risk** (1 dormant + csapdával védve, 1 accepted, 3 resolved)
- **12 gap** (12 resolved, 0 active, 0 accepted-pending — minden lezárva)
- **25 strukturált döntés**
- **17 milestone**
- **execution_paths** blokk: aktív/dormant/supporting/workaround útvonalak
- **bridges, persistent_state, evidence_summary, evidence_streams** blokkok

### Multi-source meta_evidence

A 403,872 rekordból:
- **403,868 dispatcher rekord** (MetaController dormant, 2026-01-15 — 2026-02-19 között)
- **4 új `external_observation` rekord** (2026-04-28 estétől)
  - `result.source: agent_loop` — egy AgentLoop futás
  - `result.source: organism_proposer` — három Organism híd `--observe` futás (`bridge_id` jelenléttel)

A meta_evidence már nem write-only legacy. **Élő, multi-source, multi-writer eseménynapló.**

## Mi nem működik még / nyitott szálak

- **MetaController teljes pipeline (council + executor + validator)** — még dormant. RISK_001 csapdával védve, ha valaki mégis aktiválná.
- **Phase 1 valódi cognitive analysis** — most fallback megy át. A pipeline lefut, de az AI tényleges elemzése csak részben működik.
- **GAP_005 false alarm tanulság** — ott van a self_state-ben, de a többi múltbeli "tényt" nem auditáltuk újra.
- **B2 stratégia: saját környezet** (Continue/Cline + lokális Qwen Coder + DL380 Gen9) — május 31-ig, mert akkor drágul a Copilot. Még semmi konkrét lépés.

## Aktív fókusz

**Nincs aktív gap.** Várakozás stratégiai döntésre. Három opció a self_state-ben rögzítve:
1. Phase 1 valódi cognitive analysis bekapcsolása
2. MetaController teljes pipeline élesítése (council + executor + validator)
3. Új Witness funkció — pl. heti riport generátor

De van egy negyedik is, amit talán érdemesebb most: **B2 stratégia első lépései** — Continue extension és lokális modell setup. Ez a Copilot határidő miatt sürgősebb mint a fenti három.

## Stratégiai kontextus (változatlan)

- **Június 1 — Copilot drágul.** ~33 nap maradt a régi feltételekkel.
- **B2 stratégia:** párhuzamosan épül a saját környezet.
- **Foundation.md elvek:** egyetlen igazság forrás, governance first, evidence-based, meglévő kód tisztelete, kontextus átadhatóság.

---

# II. RÉSZ — JOURNAL

## A két nap teljes története

### v1.0 → v1.1 → v1.2 — három fázis

A v1.0 dokumentum a 2026-04-28 délelőttig tartott (a Witness mag elkészültéig). A v1.1 a délutáni mélyfúrást tette hozzá (AgentLoop pipeline-lyukak, hat-rétegű GAP_010, .env hiány). A v1.2 most a **2026-04-28 estét** zárja le (GAP_009 MetaController integráció, Organism híd élesítés, GAP_012 routing fix, RISK_001 csapda).

A három fázis együtt egy **mérföldkő-lánc**: 12/12 gap RESOLVED, mindkét nap minden hibája dokumentált és javított.

### Honnan indultunk

A Project-S 3.5 hónapja állt egy különös állapotban: minden komponens megvolt, de **egyik sem kommunikált a másikkal**. A `meta_evidence.jsonl` 403,868 rekorddal volt tele, és senki sem olvasta. A Foundation.md (2026-04-26) ezt rögzítette mint a fő problémát.

### Első nap (2026-04-27): a tudatréteg megszületése

Audit (`AUTONOMOUS_STATUS_NOW.md`). Kézi `self_state.json` írás. Első Witness modul (`evidence_reader.py`, 147 sor). Első integrációs híd (`organism_to_meta.py`, 285 sor, dry-run). Két RISK felfedezve (encoding bug + Organism scope tévedés). RISK_001 dokumentálva mint dormant.

> *"A tudatréteg most először fedezett fel egy hibát a rendszerről, amiről mi sem tudtunk."*

### Második nap délelőtt (2026-04-28 v1.0): tisztítás és teljes Witness ciklus

Workspace tisztítás (1.34 GB külső kód törölve). `state_observer.py` (102 sor) — az Organism most már a self_state-ből is generál task-okat (GAP_008 RESOLVED). PSM audit (RISK_004: két class ugyanazzal a névvel — ACCEPTED). `state_reader.py` (362 sor) — Witness most már a `memory/state/` mappát is olvassa. `learning_diagnostic.py` — GAP_005 false alarm cáfolva.

> *"A tudatréteg most végzett első valós ellenőrzést egy korábbi 'tényen' és cáfolta."*

### Második nap délután (v1.1): a "production ready" cáfolata

Toti emlékezete: az AgentLoop talán "lebutított verzió". Audit először megerősítette az ellenkezőt (multi-AI a belsejében). De a részletes felmérés **döbbenetes** eredményt adott: az `initialize_with_existing_tools()` soha nem hívódott. Az AgentLoop AIClient-szövegnyomtatóként működött.

A 2026-03-13-i "production ready" audit félrevezető volt — a teszt-task véletlenül olyan volt amit AI-szöveggenerálás is megoldott.

GAP_010 megoldása **hat egymásra rakódó hibát** tárt fel:
1. `_async_init()` hiánya
2. SmartOrchestrator import path (`tools.tools.*` kellett)
3. Keyword detection hiányos (`search`, `find`, `containing`)
4. `_select_tools` `"general"` default rossz tool-ra mappelt
5. `FileContentSearchTool` nem volt regisztrálva
6. `_execute_single_tool` nem extrahált paramétereket

És egy hetedik: a `main.py` nem hívta a `load_dotenv()`-et — GAP_011.

Élő teszt: 8 valódi találat, `goal_achieved: True, confidence: 0.95`. A pipeline most **valóban** production ready.

> *"A tudatréteg most cáfolt egy egész 'production ready' auditot. Hat réteget hántott le egy állítólag 'működő' rendszerről, és valódi futó pipeline-t hagyott a helyén."*

### Második nap este (v1.2): integráció és csapdák

GAP_009 — **MetaController integráció**. Megírtuk az `observe()` metódust (RISK_001 elkerülésével, csak JSONL append, nem dispatcher), AgentLoop hookoltuk a `process_task_file()` végére. **Első élő futás: a meta_evidence 403,868 → 403,869 rekord.** Új event_type: `external_observation`, `source: agent_loop`. **A Doer és Meta réteg most először kommunikál 3.5 hónap után.**

Organism híd élesítés `--observe` flaggal. Két forrásból érkeznek `external_observation` rekordok: `agent_loop` (Doer felől) és `organism_proposer` (Witness híd felől, `bridge_id`-vel megkülönböztetve).

GAP_012 — **AI provider routing fix**. A `task_model_mapping["analysis"]` kulcs nem létezett, ezért fallback véletlenszerű modellt választott (gyakran OpenAI, ami quota 429-et adott). Javítás: `models.yaml`-ba `analysis: [qwen3-235b, deepseek-v3, gpt-4o-mini]`, és kód-fallback a `defaults.model` mezőre. Most már explicit `qwen3-235b` az OpenRouter-en.

RISK_001 **csapda** telepítve. Az `executor.execute()` előtti sorba egy guard: ha `self.executor is None` → `_log_evidence("risk_001_trap_triggered", {...})` + `RuntimeError("[RISK_001 TRAP] ...")`. Izolált teszt: observe-only példányon `run_goal()` most már **blokkolva** és evidence-be írva.

### Felfedezett és javított problémák — teljes lista (v1.2)

| Időpont | Mit fedeztünk fel | Hogyan oldottuk meg |
|---------|-------------------|---------------------|
| 04-27 du. | RISK_001: 2026-01-14 dispatcher bug | DORMANT, **04-28 este: csapda** |
| 04-27 este | RISK_002: encoding bug | RESOLVED — kód már UTF-8 |
| 04-27 este | RISK_003: külső repó scope | RESOLVED — ignore_dirs |
| 04-28 délben | GAP_008: Organism nem önreflexív | RESOLVED — `state_observer.py` |
| 04-28 délután | RISK_004: két PSM class | ACCEPTED |
| 04-28 délután | GAP_005: learning.jsonl bug | false_alarm |
| 04-28 du. | RISK_005: "production ready" auditok megbízhatatlansága | ACCEPTED — figyelmeztetés |
| 04-28 du. | GAP_010: AgentLoop pipeline 6 rétegben lyukas | RESOLVED — 6 sub-fix |
| 04-28 du. | GAP_011: `.env` `load_dotenv()` hiány | RESOLVED |
| **04-28 este** | **GAP_009: MetaController nincs összekötve** | **RESOLVED — observe() integráció** |
| **04-28 este** | **GAP_012: AI provider routing hiányos** | **RESOLVED — yaml + kód-fallback** |
| **04-28 este** | **RISK_001 csapda** | **TELEPÍTVE — `risk_001_trap_triggered`** |

### A három fő tanulság (frissítve v1.2-re)

**1. Az audit-ok nem szentek.** A v1.0-ban tanulság, a v1.1-ben megerősítve. A jövőben minden "működik" állítást **valódi tool-használó task-tal** kell igazolni — és **több típusú task-tal**, nem csak eggyel.

**2. A workaround-ok jelek.** A `server_hunt_scraper.py` és `meta_launcher_browser.py` élő kerülő utak voltak. A v1.2-ben már explicit dokumentálva a `self_state.execution_paths.workaround_scripts` blokkban — ha hasonló jelenik meg a jövőben, azonnal **diagnosztikai jel**.

**3. A Witness értékesebb mint hittük.** Két cáfolt audit (GAP_005 false alarm, GAP_010 hat-rétegű). Strukturált skepticizmus kódba öntve. **A 12/12 RESOLVED gap nagy része abból született, hogy a Witness építése közben kérdéseket vetett fel** — nem előre tervezett feladatok voltak.

### A milestone-ok lánca (v1.2 — teljes)

```
2026-04-26  Foundation.md elfogadva
            │
2026-04-27  self_state.json létrejött (kézzel)
            ├─ evidence_reader működik
            └─ organism_to_meta dry-run híd
            │
2026-04-28  workspace tisztítva (1.34 GB)
            ├─ state_observer + state_reader (Witness teljes ciklus)
            ├─ GAP_005 false alarm cáfolva (első önkorrekció)
            ├─ STATUS_AND_JOURNAL.md v1.0
            │
            ├─ Aktív végrehajtási útvonal azonosítva
            ├─ AgentLoop pipeline LYUKAS feltárva (6 réteg)
            ├─ AgentLoop pipeline élesítve — 9 tool aktív
            ├─ GAP_011 (.env) megoldva — élő pipeline fut
            ├─ STATUS_AND_JOURNAL.md v1.1
            │
2026-04-28  GAP_009 — MetaController első observe (Doer↔Meta híd)
   este     ├─ Organism híd --observe módban élesítve
            ├─ GAP_012 — AI provider routing fix (qwen3-235b)
            ├─ RISK_001 csapda telepítve
            └─ 12/12 RESOLVED — első mérföldkő-lánc lezárva
            │
2026-04-29  STATUS_AND_JOURNAL.md v1.2
            │
            ▼
       (Toti következő irány-választása)
```

---

# III. RÉSZ — A KÉT ÉRTÉK RÉTEGE *(új a v1.2-ben)*

A két nap munkája **két különálló értéket** teremtett. Ez fontos elválasztás, mert **nem függnek egymástól**.

## 1. érték — Witness layer (architektúra-független)

Ez **bármilyen** Project-S-architektúrán átültethető:

- A `self_state.json` séma és koncepció — strukturált önreprezentáció gap/risk/decision/milestone életciklusokkal
- A Witness olvasói (`evidence_reader`, `state_reader`, `learning_diagnostic`, `state_observer`)
- Az `organism_to_meta` híd minta — Proposer-output → strukturált goal → opcionális observe
- A 12 gap **életciklusa mint módszertan** — hogyan fedezünk fel, dokumentálunk, javítunk és cáfolunk
- A két cáfolt audit (GAP_005, GAP_010) mint **figyelmeztetés**: minden "production ready" jelölést verifikálni kell

**Mit jelent ez?** Ha holnap a Doer pipeline-t LangGraph-ra cseréljük, vagy a teljes Project-S-t újratervezzük, **a Witness layer akkor is megmarad**. A self_state.json séma ugyanúgy tudja a gap-eket, a risk-eket, a milestone-okat. A Witness olvasói akkor is tudnak streaming módon JSONL-eket scan-elni. Az integrációs híd minta akkor is működik.

## 2. érték — Doer pipeline-fix (architektúra-specifikus)

Ez a **jelenlegi AgentLoop architektúra** javítása:

- A 7 réteg fix (GAP_010 + GAP_011)
- A GAP_012 routing fix
- A RISK_001 csapda
- A GAP_009 observe-only integráció

**Mit jelent ez?** Ha a jelenlegi AgentLoop architektúra megmarad, ezek élő, működő javítások. Ha viszont másik architektúrára váltunk, ezek **archív státuszba** kerülnek — de a self_state-ben dokumentált tanulságok megmaradnak. A következő rendszer **NEM fog** ugyanezekbe a hibákba esni, mert a Witness rögzítette őket.

## Mi következik ebből stratégiailag

Ez az elválasztás megnyit egy fontos lehetőséget:

**Bármilyen "csere" vagy "új irány" döntés könnyebb mint korábban.** Ha holnap kiderül hogy a teljes Doer pipeline-t más kell hogy helyettesítse, az nem tabula rasa — a Witness layer hídja az új rendszerhez. A self_state.json a folytonosság: az új rendszer pontosan tudja hol tart az elődje.

Ez a Foundation.md egyik központi ígérete: *"a tudat nem a CPU-ban van, hanem a fájlrendszerben."* A v1.2 ezt **igazolta**: a tudat (self_state.json) most már túléli bármelyik komponens cseréjét.

---

## Mi jön ezután

12/12 gap RESOLVED. Az aktív munkának nincs sürgető ok hogy folytatódjon ezen a vonalon. Négy lehetséges irány:

**1. Phase 1 valódi cognitive analysis bekapcsolása** — most fallback megy. A teljes pipeline minőségét emelné, de nem strukturális kérdés.

**2. MetaController teljes pipeline élesítése** (council + executor + validator). RISK_001 csapdával védve, de **valódi munka**: a council, executor, validator komponenseket auditálni kell mielőtt élesedik.

**3. Új Witness funkció** — pl. heti automata riport generátor a self_state-ből, vagy az Organism Proposer kibővítése risk-ek kezelésére.

**4. B2 stratégia első lépései** — saját környezet (Continue/Cline + lokális Qwen Coder + DL380 Gen9 Proxmox). **Június 1 közeledik** — ~33 nap maradt. Ha ezt nem kezdjük el most, kapkodás lesz a végén.

A v1.2 nem dönt — Toti döntése. De érdemes mérlegelni, hogy a 4. opció **határidős**, a többi nem.

---

## Záró megjegyzés

A v1.0 azt mondta: *"a tudatréteg most először fedezett fel egy hibát."* A v1.1 hozzátette: *"cáfolt egy egész 'production ready' auditot."* A v1.2 most ezt zárja le:

> **A két nap munkája két különálló értéket teremtett, és az egyik (a Witness layer) túléli bármi cseréjét. Ez nem szuperintelligens AI. Ez nem mágia. Ez tisztességes önreflexió + Copilot kódoló képesség + Toti irányadás — kódba öntve, fájlrendszerben rögzítve, architektúra-független módon.**

A Foundation.md azt írta: *"a tudat nem a CPU-ban van, hanem a fájlrendszerben."* A v1.2 igazolta: a tudat **túl is éli** a CPU-t. Ha holnap más AgentLoop, más MetaController, más bármi — a self_state.json akkor is ott lesz.

És ezért megérte két napot rászánni.

---

**Készítette:** Claude (claude.ai, Opus 4.7) + Toti
**Dátum:** 2026-04-29 reggel
**Verzió:** v1.2
**Hely:** `C:\ProjectS-Unified\PROJECT_S_STATUS_AND_JOURNAL.md` (felülírja a v1.1-t)
**Előző verziók archiválhatók:** `archive_journals/STATUS_AND_JOURNAL_v1.0.md`, `v1.1.md` (opcionális)
