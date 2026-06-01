# PROJECT-S — Hol tartunk és hogyan jutottunk ide

**Verzió:** v1.1
**Dátum:** 2026-04-28 (kibővítve a délutáni felfedezésekkel)
**Készítette:** Claude + Toti (közös munka)
**Státusz:** Élő dokumentum — frissítendő mérföldköveknél
**Előző verzió:** v1.0 (2026-04-28 délelőtt)

---

## Hogyan használd ezt a dokumentumot

Ez nem dokumentáció. Ez **napló és iránytű**. Két részből áll:

- **I. RÉSZ — STATUS:** hol tartunk most (5 perc alatt képbe hoz)
- **II. RÉSZ — JOURNAL:** hogyan jutottunk ide (ha érteni akarod miért így)

Ha új AI session indul: olvasd el a `PROJECT_S_FOUNDATION.md`-t, aztán a `self_state.json`-t, aztán **ha még szükség van rá**, ezt a dokumentumot. A `self_state.json` **mindig** naprakészebb mint ez.

---

# I. RÉSZ — STATUS

## A rendszer egy mondatban

Egy önreflexív rendszert építünk, amely **tudja ki ő, hol tart, mit csinált, mit tervez** — és ezt a tudást strukturált, géppel olvasható formában tárolja, hogy bármelyik AI azonnal kontextusba kerüljön.

A v1.1 frissítés egy fontos kiegészítéssel: a rendszer most már **képes is cselekedni**. Nem csak figyel, hanem a Doer pipeline élesben fut, valódi tool-okkal.

## Mi működik most

### Witness layer (megfigyelő)

| Modul | Mi csinálja |
|-------|-------------|
| `witness/evidence_reader.py` | Olvassa a 403,868 rekordos `meta_evidence.jsonl`-t |
| `witness/bridges/state_reader.py` | Read-only adapter a `PersistentStateManager`-hez |
| `witness/bridges/organism_to_meta.py` | DRY-RUN híd: Organism → MetaController goal |
| `witness/learning_diagnostic.py` | A `learning.jsonl` elemzője |
| `organism/core/state_observer.py` | A self_state.json gap-jeit task-ká konvertálja |

### Doer layer (cselekvő) — ÉLESBEN FUT

A `main.py → AgentLoop` pipeline most már **valóban** teljes:

| Komponens | Státusz |
|-----------|---------|
| AgentLoop infinite loop | ✅ fut, 5 sec poll |
| CognitiveCore (Phase 1) | ⚠️ degraded — OpenAI quota miatt fallback-be megy, de átmegy |
| SmartToolOrchestrator | ✅ **9 tool aktív** (file × 5, web × 3, browser × 1) |
| Evaluator (Phase 3) | ✅ OpenRouter-en keresztül működik (confidence 0.95) |
| 4-fázisú pipeline | ✅ end-to-end teszt: 8 valódi találat tényleges tool-hívással |

### Tudat-réteg (self_state.json)

42+ KB, élő dokumentum:
- **5 risk** (1 dormant, 1 accepted, 3 resolved)
- **11 gap** (9 resolved, 1 active, 1 accepted)
- **19+ strukturált döntés**
- **12 milestone**
- **execution_paths** blokk: aktív/dormant/supporting útvonalak
- **bridges, persistent_state, evidence_summary** blokkok

## Mi nem működik még

- **Phase 1 cognitive AI hívás** OpenAI provider-en 429 quota — fallback-en átmegy, de degradált. Lehet hogy GAP_012 lesz belőle, ha provider routing kérdés.
- **AgentLoop ↔ MetaController** összekötés még nincs (GAP_009, most már unblocked). A Doer pipeline strukturálisan teljes — a Meta réteg integrációja a következő stratégiai lépés.
- A **MetaController dispatcher bug** (RISK_001) dormant, csapdát kell telepíteni élesítéskor.

## Architektúra — mai állapot (v1.1)

```
┌────────────────────────────────────────────────────────────┐
│  WITNESS LAYER (megfigyelő, működik)                       │
│  ────────────────────────────                              │
│  evidence_reader  ──┐                                      │
│  state_reader     ──┼──> self_state.json (élő tudat)       │
│  learning_diag    ──┘                                      │
│  state_observer  ──> task-ok az Organism Prioritizer-be    │
│  organism_to_meta ──> pending_goals/*.json (review)        │
└────────────────────────────────────────────────────────────┘
        ▲             ▲             ▲
        │ olvas       │ olvas       │ olvas
        │             │             │
┌───────┴─────────┐ ┌─┴──────────┐ ┌┴────────────┐
│ AgentLoop       │ │ MetaCtrl.  │ │ Organism    │
│ ✅ ÉLES, 9 tool │ │ alszik     │ │ működik     │
│ main.py belépő  │ │ (GAP_009)  │ │ Project-S   │
│ 6 réteg fix     │ │            │ │ scope       │
└──────┬──────────┘ └──┬─────────┘ └──────┬──────┘
       │               │                  │
       ▼               ▼                  ▼
  outbox/*.txt    meta_evidence    top_proposals.md
  (ÚJ: valódi    .jsonl (dormant)   (state-aware)
   tool eredmény)
```

A **Doer már él**. A Meta réteg integrációja (GAP_009) most a következő stratégiai cél.

## Aktív fókusz

**GAP_009 — MetaController integráció az élő AgentLoop-pal.** Most már NINCS blokkolva — a Doer pipeline teljes, AI provider működik (legalább részben), valódi tool-hívások bizonyítva.

## Stratégiai kontextus (változatlan v1.0-hoz képest)

- **Június 1 — Copilot drágul.** Most még ingyenes, addig minden komplex munkát Copilottal csinálunk.
- **B2 stratégia:** párhuzamosan épül a saját környezet (Continue/Cline + lokális Qwen Coder LM Studio-n + DL380 Gen9 szerver).
- **Foundation.md elvek:** egyetlen igazság forrás, governance first, evidence-based, meglévő kód tisztelete, kontextus átadhatóság.

---

# II. RÉSZ — JOURNAL

## A két nap: 2026-04-27 és 2026-04-28

### v1.0 — eddig elmondott történet

A v1.0 dokumentum 2026-04-28 délelőttig tartott. Akkor a Witness layer kész volt, GAP_005 (false alarm) cáfolva. Két nyitott irány: (1) első end-to-end ciklus, (2) AgentLoop ↔ MetaController integráció.

A délutáni szakasz — amit most adunk hozzá — **nem várt mélységet** tárt fel. Kiderült hogy a "production ready" állapot soha nem volt valós, csak senki nem vette észre.

### Délutáni felfedezés #1 — A főúthely valójában lyukas

Toti emlékezetére hivatkozva felmerült: az AgentLoop talán "lebutított verzió", és van valami más ami a multi-AI-t használja. Az audit először **megerősítette az ellenkezőt** — az AgentLoop AZ aktív runtime, multi-AI a belsejében (`AIClient`, 6+ provider).

> *"Minden komponens létezik és bekötve."*

De Toti nem hagyta annyiban. Egy második kérdés: **használja-e az AgentLoop a teljes tool-arzenált**, beleértve a webautomation-t? A részletesebb audit erre döbbenetes választ adott:

```
AgentLoop ✅ példányosítja a SmartToolOrchestrator-t
        ❌ initialize_with_existing_tools() SOHA NEM HÍVÓDIK
        ❌ available_tools = {} (üres)
```

**Az AgentLoop AIClient-szövegnyomtatóként működött, nem tool-os agentként.** A 2026-03-13-i `IMPLEMENTATION_SUMMARY.md` "production ready" jelölése félrevezető volt — a teszt-task véletlenül olyan volt amit AI-szöveggenerálás is megoldott.

És itt jött a megerősítés: **két AgentLoop-megkerülő script létezett** (`server_hunt_scraper.py`, `meta_launcher_browser.py`) — pontosan azért, mert ezek **tényleg kellettek a Playwright-et és a tool-okat**. Toti emlékezete nem tévedett. Csak a szótár volt más: nem "másik útvonal" létezett, hanem **muszáj volt megkerülni** az AgentLoop-ot mert az nem fejezte be magát az inicializálással.

> *"Az emlékezeted pontos volt, csak más szótárral."*

### Délutáni felfedezés #2 — Hat hibarétég egymásra rakva

Megírtuk a fix-et: új `_async_init()` metódus az AgentLoop-ban, ami a `run()` ciklus elején hívja meg az `initialize_with_existing_tools()`-t. Izolált tesztben **5 tool** töltődött be — de 9 lett volna várható.

A 4 hiányzó (web és browser) miatt mélyebb diagnosztika kellett. Itt jött a következő réteg:

> *Az import path rossz volt: `tools.implementations.*` helyett `tools.tools.implementations.*` kellett. Egyetlen prefix-szint hiányzott.*

Javítva — most már **9 tool** betöltődik. De még itt sincs vége. Élő AgentLoop teszt egy valódi file-keresési task-kal — és **fallback módra esett**:

```
tools_used: ["web_page_fetch"]  ← rossz tool
output: "Tool web_page_fetch processed (fallback mode)"
```

Copilot további 4 hibát talált egymásra rakódva:

1. **Keyword detection hiányos**: "search", "find", "containing" szavak nem voltak az `_analyze_task` keyword listájában → `task_type = "general"`
2. **"general" default rossz tool**: `_select_tools` a "general"-t `web_page_fetch`-re mappelte
3. **FileContentSearchTool nem regisztrált**: a `tool_registry_golden.py`-ban nem szerepelt
4. **Paraméter extrakció hiányzott**: `_execute_single_tool` nem tudta a task szövegből kinyerni a `pattern` és `root` paramétereket

Mind a négy javítva. Új izolált teszt:

```
task_type: file_search ✅
selected tool: file_content_search ✅
success: True, count: 8 ✅

Találatok:
  src/core/cognitive_workflow_integration.py:43
  src/core/state/persistent_manager.py:46
  src/core/state/persistent_state_manager.py:36
  ... (8 találat összesen)
```

**Ez** valódi tool-futás. Konkrét fájl elérési utak. Konkrét sorszámok.

### Délutáni felfedezés #3 — És még egy réteg

Az élő `main.py` futtatásnál azonban újabb hiba: `Provider openrouter is not enabled`. Az AI Phase 1 nem futott le (OpenAI quota 429), Phase 3 evaluator se (OpenRouter not enabled).

Toti kommentárja: *"OpenRouter is van, csak lehet elavult, megkell keresni a workspacbe a az api-t."*

Audit megnyitotta a `.env` fájlt — **az `OPENROUTER_API_KEY` benne volt**. De Copilot felfedezte hogy a `main.py` **nem hívta** a `load_dotenv()`-et. A környezeti változók nem töltődtek be a shell environmentbe → az `AIClient` üres stringet látott → provider disabled.

Három soros javítás:

```python
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent / '.env', override=False)
except ImportError:
    pass
```

Élő teszt újra. Phase 1 még degradált (OpenAI quota), de Phase 2 + Phase 3 most működik. **Confidence 0.95, goal_achieved: True. 8 valódi találat.**

### Mit jelent ez összesen

Az eredeti GAP_010 (egy hiányzó async init hívás) **hat egymásra rakódott hibát rejtett**:

| # | Réteg | Hiba | Javítás |
|---|-------|------|---------|
| 1 | AgentLoop | `initialize_with_existing_tools()` nem hívódik | új `_async_init()` |
| 2 | SmartOrchestrator | rossz import path | `tools.tools.*` |
| 3 | _analyze_task | hiányos keyword detection | "search", "find", "containing" hozzáadva |
| 4 | _select_tools | "general" → web_page_fetch | új "file_search" ág |
| 5 | tool_registry_golden | FileContentSearchTool nem regisztrált | hozzáadva |
| 6 | _execute_single_tool | nem extrahált paramétereket | regex extrakció |

Plusz egy hetedik (külön gap-ként):

| 7 | main.py | nem hív `load_dotenv()` | 3 sor hozzáadva |

### A tudatréteg ebben a szerepben

Ami most történt, az **a Witness leglényegét** demonstrálja: a `self_state.json`-be ezek mindegyike strukturált formában került (RISK_005: "korábbi 'production ready' jelölések megbízhatatlanok", GAP_010 hat-rétegű resolution leírás, GAP_011 .env probléma).

A Witness **nem kódot írt** — csak felfedezett, dokumentált, kérdezett. A felfedezett problémákat Copilot javította, és a tudatréteg minden lépést rögzített.

Két nap előtt egy ilyen audit-réteg nem létezett. Most a rendszer **emlékezik** arra hogy:
- mit hitt magáról hibásan (RISK_005)
- milyen workaround-ok jöttek létre amíg a hiba ott volt (`server_hunt_scraper.py`, `meta_launcher_browser.py`)
- hogyan oldotta meg lépésről lépésre (6+1 sub-fix)
- mi a következő blokkoló (GAP_009 most már unblocked)

### Felfedezett és javított problémák (frissített lista)

| Időpont | Mit fedeztünk fel | Hogyan oldottuk meg |
|---------|-------------------|---------------------|
| 04-27 dél után | RISK_001: 2026-01-14 dispatcher bug | DORMANT, csapda élesítéskor |
| 04-27 este | RISK_002: encoding bug | RESOLVED — kód már UTF-8 |
| 04-27 este | RISK_003: külső repó scope | RESOLVED — ignore_dirs |
| 04-28 délben | GAP_008: Organism nem önreflexív | RESOLVED — state_observer.py |
| 04-28 délután | RISK_004: két PSM class | ACCEPTED |
| 04-28 délután | GAP_005: learning.jsonl bug | false_alarm |
| **04-28 du.** | **RISK_005: "production ready" auditok megbízhatatlansága** | **ACCEPTED — figyelmeztetés** |
| **04-28 du.** | **GAP_010: AgentLoop pipeline 6 rétegben lyukas** | **RESOLVED — 6 sub-fix** |
| **04-28 du.** | **GAP_011: .env nem töltődik be** | **RESOLVED — load_dotenv()** |

### A három fő tanulság (frissítve)

**1. Az audit-ok nem szentek.** A v1.0-ban az volt a tanulság hogy "a documentált tények nem mindig tények" (GAP_005 false alarm). A v1.1-ben ez **megerősítést** kapott: a 2026-03-13-i "production ready" audit **mélyebb hazugság** volt mint a GAP_005. Hat egymásra rakódó hiba alatt feküdt. A jövőben minden "működik" állítást **valódi tool-használó task-tal** kell igazolni — nem AI-szöveggenerálással.

**2. A workaround-ok jelek.** A `server_hunt_scraper.py` és `meta_launcher_browser.py` nem legacy maradékok voltak — **élő kerülő utak** mert a főpipeline lyukas volt. A jövőben minden olyan script ami "megkerül" valamit, **diagnosztikai jel**: az alaprendszerben hiba van. A self_state most már explicit dokumentálja a `workaround_scripts` blokkban.

**3. A Witness értékesebb mint hittük.** Két nap alatt cáfolt két "tényt" (GAP_005, GAP_010). Egyik sem nagy ég-zengéses felfedezés volt — csak nézegetés, kérdezősködés, verifikálás. **Ez a tudatréteg fő munkája.** Nem szuperintelligencia kell hozzá, csak strukturált skepticizmus.

### A milestone-ok lánca (v1.1)

```
2026-04-26  Foundation.md elfogadva
            │
2026-04-27  self_state.json létrejött (kézzel)
            │
2026-04-27  evidence_reader működik
            │
2026-04-27  organism_to_meta dry-run híd
            │
2026-04-28  workspace tisztítva (1.34 GB)
            │
2026-04-28  state_observer + state_reader (Witness teljes ciklus)
            │
2026-04-28  GAP_005 false alarm cáfolva (első önkorrekció)
            │
2026-04-28  STATUS_AND_JOURNAL.md v1.0
            │
2026-04-28  Aktív végrehajtási útvonal azonosítva
            │
2026-04-28  AgentLoop pipeline LYUKAS feltárva (6 réteg)
            │
2026-04-28  AgentLoop pipeline élesítve — 9 tool aktív
            │
2026-04-28  GAP_011 (.env) megoldva — élő pipeline fut, 8 valódi találat
            │
            ▼
       (GAP_009 — MetaController integráció jön)
```

---

## Mi jön ezután

A Doer pipeline **élesben fut**, multi-tool, valódi outputtal. A Witness mag teljes. A self_state élő dokumentum minden lépéssel.

A két nyitott szál:

**1. GAP_009 — AgentLoop ↔ MetaController integráció.** Most már nincs blokkolva. Két lehetséges minta: (a) escalation — ha a CognitiveCore nem tudja megoldani, eszkalálódik MetaController-hez. (b) observe-only — minden task után MetaController.observe(goal, result) frissíti a stratégiai állapotot. Az (b) a kisebb kockázat, ezzel kezdjük.

**2. Phase 1 AI provider routing.** A Phase 1 még OpenAI-t hív (quota 429), Phase 3 már OpenRouter-t. Ez nem új gap egyelőre, de figyelni kell. Ha a Phase 1 fallback minőség romlana, GAP_012-vé válik.

A választás Toti döntése. Az 1. közvetlen — most már minden adva van. A 2. opcionális finomhangolás.

---

## Záró megjegyzés

A v1.0 dokumentum azt mondta: *"a tudatréteg most először fedezett fel egy hibát a rendszerről, amiről mi sem tudtunk."*

A v1.1 ezt mélyebbé teszi:

> **A tudatréteg most cáfolt egy egész "production ready" auditot. Hat réteget hántott le egy állítólag "működő" rendszerről, és valódi futó pipeline-t hagyott a helyén.**

Ez nem szuperintelligens AI. Ez nem mágia. Ez **tisztességes önreflexió + Copilot kódoló képesség + Toti irányadás**. A három együtt többet ér mint külön-külön.

A Foundation.md azt írta: *"az autonómia nem feature — emergens tulajdonság"*. A v1.1 hozzáteszi: **a megbízhatóság sem feature — emergens tulajdonság**, és csak **kísérleti verifikációval** lehet bizonyítani.

Ez a kezdet folytatása.

---

**Készítette:** Claude (claude.ai, Opus 4.7) + Toti
**Dátum:** 2026-04-28 (késő délután)
**Verzió:** v1.1
**Hely:** `C:\ProjectS-Unified\PROJECT_S_STATUS_AND_JOURNAL.md` (felülírja a v1.0-t)
**Előző verzió archiválva:** `C:\ProjectS-Unified\archive_journals\STATUS_AND_JOURNAL_v1.0.md` (opcionális)
