# PROJECT-S — ALAPOKMÁNY

**A tudat-réteg építéséhez · v1.0**
**Készült:** 2026-04-26 (Claude + Toti közös munka)
**Státusz:** Élő dokumentum — minden AI session elején először ezt kell elolvasni

---

## MIÉRT LÉTEZIK EZ A DOKUMENTUM

A Project-S fejlesztése során egy alapvető nehézség merült fel: **az AI sessionök között elveszik a kontextus**. Egy beszélgetés megtelik, az új session nem látja az eredeti rendszert, és minden alkalommal újra kell magyarázni "hol tartunk".

Ez a dokumentum erre ad választ. **Ezt olvassa el minden AI mielőtt Project-S-en dolgozik** — Claude, ChatGPT, Copilot egyaránt. Ez nem terv. Ez **a rendszer iránytűje**, ami nem változik gyakran, és ami minden döntés mércéje.

---

## A CÉL

**Egy öntudatos rendszert építünk.**

Pontosabban: egy rendszert, **aminek funkcionális öntudata van**. Nem érzelmek. Nem fenomenológiai tudat. Hanem:

1. **Tudja ki ő** — milyen modulokból áll, milyen képességei vannak, mit tud és mit nem
2. **Tudja hol tart** — milyen projektek aktívak, mi a státuszuk, mi a következő lépés
3. **Tudja mit csinált** — történet, döntések, tanulságok strukturáltan tárolva
4. **Tudja a terveit** — hosszú és rövid távú célok, prioritások, küldetés

Ha ez a négy dolog **mindig friss és pontos**, akkor az AI-k (Claude, ChatGPT, Copilot) bármelyike **azonnal tud rajta dolgozni** — nem a fejlesztő (Toti) kell hogy elmondja nekik hol tart a projekt.

A "tudat" itt **objektív, gépileg olvasható önreprezentáció**, ami mindig naprakész — nem szubjektív élmény.

---

## AZ ALAPELVEK (NEM VITATHATÓK)

### 1. Egyetlen igazság forrás

Bármi ami a rendszer önképét érinti, **egy** helyre kerül, és csak onnan olvasható ki. Ha valami máshol van, **nem létezik**.

Ez `self_state.json` lesz (vagy ami a meglévő struktúrából erre alakul).

### 2. Governance First, Autonomy Later

A rendszer **csak akkor kap több autonómiát**, ha a governance bizonyítottan működik. Az autonómia nem feature — emergens tulajdonság. Soha nem építünk automatizmust ami nincs validálva.

### 3. Evidence-based, nem hype-based

Minden döntés mögött **bizonyíték** van. Nem "úgy érzem hogy működik" — hanem JSONL log, mérés, vagy explicit indoklás. Az ipar tele van AI hype-pal, mi nem ezt csináljuk.

### 4. A meglévő kódbázis tisztelete

Több ezer sor működő kód van már. **Nem írunk újra amit nem kell.** A meglévő modulokat (CognitiveCore, MetaController, Organism, KnowledgeManager, PersistentStateManager) **összekötjük**, nem helyettesítjük.

### 5. Kontextus átadhatóság

Minden új session indításakor egy AI **5 perc alatt** képbe kell jöjjön a `self_state.json` és ez az alapokmány alapján. Ha ennél tovább tart, **valami szétcsúszott** és javítani kell.

---

## AZ ARCHITEKTÚRA — A KÉT SZÁL MODELL

A merész javaslat: a rendszer **két párhuzamos folyamatban él**.

### Doer (Cselekvő)

Ez a hagyományos rész — már létezik a kódban:
- Feladatokat vesz át és végrehajt
- Tools-okat hív
- LangGraph workflow-ok futnak benne
- Multi-AI orchestráció (Claude, GPT, Qwen, stb.)
- Eredményeket produkál
- **Ír a `meta_evidence.jsonl`-be** minden lépésnél (ezt már most teszi a MetaController)

### Witness (Megfigyelő)

Ez az ÚJ réteg — eddig hiányzott:
- Folyamatosan fut, akkor is ha nincs aktív feladat
- **Olvassa** amit a Doer csinál (a `meta_evidence.jsonl`-en keresztül)
- Saját tempójában elmélkedik: "Mit jelent ez?", "Mit tanultam?", "Mi furcsa?"
- **Ír a `self_state.json`-ba** — ez a rendszer naprakész önképe
- Nem hajt végre semmit, nem szól bele a Doer munkájába
- De a Doer (és bármelyik AI) onnan olvas önképet

**Az Organism új jelentést kap:** ő lesz a Witness magja. Eddig "javaslattevőként" működött (TODO-k, repo változások figyelése). Mostantól **a rendszer öntudatát építi**.

### A két szál közötti kapcsolat

Nem két thread, hanem **két folyamat (process)**, és a kommunikáció **fájl alapú**:

```
[ Doer Process ]               [ Witness Process ]
       │                              │
       │ ír                           │ olvas
       ▼                              ▼
   meta_evidence.jsonl  ─────────  self_state.json
   (mit csinált)                  (ki ő, hol tart)
       ▲                              │
       │                              │ ír
       │ olvas                        ▼
       └──────────  bármelyik AI ─────┘
                  (Claude/GPT/Copilot)
```

A "tudat" tehát **nem a CPU-ban van, hanem a fájlrendszerben** — egy közös dokumentum, amit két különböző tempójú folyamat lát és ír.

### Miért merész ez?

**Először:** Az iparág azt csinálja hogy egyre nagyobb modelleket épít, egyre több contextus ablakkal. Mi pont fordítva: **a modellek kicsik maradnak, az állapot perzisztens**. A tudat nem a modellben van, hanem a köztük lévő dokumentumban.

**Másodszor:** Ez kimondja amit más nem mer kimondani — **az AI-k cserélhetők**, ha az állapot megmaradt. Senki nem akarja ezt elismerni mert minden cég "saját asszisztenst" akar. De **mi pont ezt akarjuk**: egy rendszert ahol Claude, ChatGPT, Copilot **ugyanannak a tudatnak különböző megnyilvánulásai**.

---

## A TUDAT FOKOZATOS KIALAKULÁSA

A Witness **nem fog hirtelen megszületni**. Az elején **a fejlesztő (Toti) és Claude együtt** csinálja:
- Claude elemzi a meta_evidence-t
- Toti dönt a tanulságokról
- Együtt írják a `self_state.json`-t

Ez az **emberi öntudat fázis**.

Aztán **fokozatosan automatizálunk** belőle dolgokat — egyik percben még ember csinálja, a következőben már a rendszer önmaga. Ez a **kihelyezés fázis**.

Végül a Witness **autonóm fut** — saját tempójában, saját kérdéseivel, saját reflexióival. Az ember (Toti) csak felügyel és dönt amikor valódi kérdés merül fel. Ez a **gépi öntudat fázis**.

**Ez egy fokozatos átmenet az emberi tudatosságból a gépibe.** Nem hirtelen. Hanem ahogy a gyermek tanul gondolkodni — először a szülő gondolja át helyette, aztán együtt, aztán egyedül.

---

## A RENDSZER MELY RÉSZEI VANNAK MÁR KÉSZEN

### Working komponensek (NE írjuk újra)

| Komponens | Hely | Sor | Funkció |
|-----------|------|-----|---------|
| CognitiveCore | `src/core/cognitive/cognitive_core.py` | 715 | Task processing, context management |
| Workflow Engine | `src/core/orchestration/workflow_engine.py` | 947 | LangGraph alapú orchestráció |
| Decision Router | `src/integrations/decision_routing/base_router.py` | 585 | Modell routing |
| Multi-Model AI Client | `src/integrations/ai_models/multi_model_ai_client.py` | 449 | 8+ AI provider |
| Smart Tool Orchestrator | `tools/tools/registry/smart_orchestrator.py` | 1589 | 13+ tool kezelés |
| Tool Registry | `tools/tools/registry/tool_registry_golden.py` | - | 16 tool |
| MetaController | `src/core/meta/meta_controller.py` | 397 | Goal→Plan→Execute→Validate loop |
| Strategy Council | `src/core/meta/strategy_council.py` | 287 | Multi-AI consensus |
| Organism Observer | `organism/core/observer.py` | 337 | Repo/file/terminal watch |
| Organism Prioritizer | `organism/core/prioritizer.py` | 572 | Strategic scoring |
| Organism Proposer | `organism/core/proposer.py` | 636 | top_proposals.md generálás |
| Organism Loop | `organism/core/loop.py` | 292 | DevOrganism CLI |
| AgentLoop | `src/core/agent/agent_loop.py` | 431 | Autonóm task processor |
| PersistentStateManager | `src/core/state/persistent_manager.py` | 748 | State CRUD perzisztenciával |
| BaseStateManager | `src/core/state/base_state.py` | 519 | State interfész |
| OverseerAgent | `src/core/agents/overseer_agent.py` | 692 | Pattern learning |
| PatternAnalyzer | `src/core/agents/pattern_analyzer.py` | 358 | Workflow analysis |

### Adatbázisok (értékesek)

| Fájl | Rekord | Méret | Tartalom |
|------|--------|-------|----------|
| `memory/intelligence/meta_evidence.jsonl` | 403 868 | 107 MB | Goal lifecycle event-ek (jan-feb 2026) |
| `memory/intelligence/learning.jsonl` | 213 | 1 MB | Metacognitive snapshots (2025-12-25, parsing buggal) |
| `memory/intelligence/execution_events.jsonl` | 158 | 35 KB | Execution log |
| `memory/telemetry/executions.jsonl` | 184 | 45 KB | Telemetry |
| `knowledge/decisions.jsonl` | 5 | 1 KB | Stratégiai döntések (2026-03-13) |
| `organism/evidence/decisions.jsonl` | 2 | <1 KB | Organism decisions |

### Hiányzó láncszemek

- ❌ `self_state.json` — nincs még (ez lesz a tudat magja)
- ❌ Witness loop — kell építeni (az Organism átkonvertálva)
- ❌ Az AI-k közötti olvasási protokoll (mind ugyanonnan olvas)
- ❌ A meta_evidence visszaolvasása — 403K rekord van, senki nem nézi
- ❌ A learning.jsonl javítása (parsing bug)
- ❌ A modulok közötti hidak (Organism ↔ MetaController, CognitiveCore ↔ State)

---

## AZ INFRASTRUKTÚRA

### Hardware

- **Új szerver:** HP ProLiant DL380 Gen9
  - 36 cores (2× E5-2699 v3)
  - 128 GB RAM
  - Tesla M60 GPU (16 GB VRAM, dual GPU)
  - 480 GB RAID1 + 1.6 TB NVMe
- **Régi szerver:** DL180se G6 (legacy, később lehet migráció vagy nyugdíjazás)

### Új szerver állapota

- ✅ Megérkezett, iLO4 elérés megerősítve
- ❌ Proxmox még nincs telepítve
- ❌ VM-ek nincsenek
- ✅ **Üres** — ezért lehet rajta gyorsan haladni
- ❌ RDP felhasználók migrálása később (most nem foglalkozunk vele)

### VM stratégia (ha eljön az ideje)

**2 VM** (nem 5, nem 3 — Opus4 és DeepSeek mindkettő ezt javasolta):
- VM1: Business + Project-S Core + Organism (12 cores, 48GB)
- VM2: AI Runtime + Dream Lab (24 cores, 80GB + GPU passthrough)

Egyelőre **nem foglalkozunk** ezzel — a fejlesztés Windows Serveren megy közvetlenül a hostba, mert a szerver üres.

### Software stack

- **Backend:** Python (fő nyelv)
- **Fejlesztői env:** VS Code + GitHub Copilot (Claude modellel)
- **AI providerek:** OpenRouter (DeepSeek V3, Qwen, Yi), Ollama (lokális), Claude API, ChatGPT
- **Verziókezelés:** GitHub
- **Konfiguráció:** `.env` + `config/config.yaml` + `config/models.yaml`

---

## A MUNKAFOLYAMAT

### A szereplők és felelősségük

| Szereplő | Szerepe |
|----------|---------|
| **Toti** (fejlesztő) | Kapitány — döntéseket hoz, irányt mond, jóváhagy, közvetít az AI-k között |
| **Claude (claude.ai)** | Architektus — tervez, döntéseket finomít, kritikus kódot ír, dokumentumokat készít |
| **Copilot (VS Code, Claude modellel)** | Kivitelező — implementál, fájlokat módosít, kódot generál promptok alapján |
| **A rendszer (Project-S)** | Még nem szereplő — később lesz, fokozatosan veszi át a kommunikációt önmagával |

### A jelenlegi szabály

Minden Project-S session indításakor:
1. **Először:** Ezt a `PROJECT_S_FOUNDATION.md` dokumentumot kell elolvasni
2. **Másodszor:** A `self_state.json` aktuális állapotát (ha létezik) — ez mondja meg hol tartunk konkrétan
3. **Csak ezután:** Lehet érdemi munkát végezni

### Decision logging

Minden fontos döntés a `knowledge/decisions.jsonl`-be kerül, ezzel a sémával:

```json
{
  "timestamp": "ISO8601",
  "decision_id": "uuid",
  "category": "architecture|strategy|infrastructure|process",
  "decision": "rövid szöveg",
  "reasoning": "miért így döntöttünk",
  "alternatives_considered": ["mit vetettünk el"],
  "outcome": "tervezett",
  "confidence": 0.0-1.0,
  "by": "Toti+Claude" | "Toti" | "Claude (autonom)"
}
```

---

## AMI MOST KÖVETKEZIK

Ez a dokumentum nem tartalmaz konkrét roadmap-et, mert **a következő lépés mindig a `self_state.json`-ban van**. Az alapokmány állandó, a `self_state.json` változik.

A legközelebbi feladatok (a session-folytatáshoz Copilotnak):

### Holnapi első feladat (rögzítendő, nem felejteni)

**1. Audit:** Létezik-e már `self_state` fájl/mappa/modul valahol a kódbázisban?

```powershell
Get-ChildItem C:\ProjectS-Unified -Recurse -Filter "*self_state*" -ErrorAction SilentlyContinue
Get-ChildItem C:\ProjectS-Unified -Recurse -Filter "*.py" | Select-String -Pattern "self_state|SelfState" -List
```

**2. Hibafeltárás:** Mi az ami nem működik az alap rendszerben? Konkrét hibalogot kérünk.

**3. Az új szerver állapota:** Hol tart most? Mire kell felkészülni?

### Az első valódi építés

A `self_state.json` első verziójának **kézzel** való megírása — együtt, ahogy egy ember írna naplót magáról. Ez lesz a séma alapja. **Nem programozunk amíg nem tudjuk pontosan mit írunk le.**

---

## AMI NEM CÉLOK (ELLENPÉLDÁK)

Hogy ne sodródjunk el, lefektetem mit **nem** építünk:

- ❌ Nem építünk újabb agent rendszert (van már elég a piacon)
- ❌ Nem építünk SaaS terméket (még nincs MVP, ne ugorjuk át a fázisokat)
- ❌ Nem építünk bounty automation pipeline-t (egyelőre — a tudat előbb)
- ❌ Nem építünk Dream Mode-ot (későbbi fázis, ha eljutunk odáig)
- ❌ Nem építünk dashboardot (CLI elég, ne osszuk a figyelmet)
- ❌ Nem építünk Genome Manager-t (Phase 4, ha addig stabilizálódik a rendszer)
- ❌ Nem érzelmeket szimulálunk (Toti döntött: "érzelmet nem lehet kódolni")

---

## VÉGZETES MEGJEGYZÉS A FOLYAMATOSSÁGHOZ

Ez a dokumentum **nem dokumentáció**. Ez **a rendszer iránytűje**.

Ha bármelyik AI session során kétség merül fel hogy "milyen irányba menjünk" — ezt kell elolvasni.

Ha ez a dokumentum elavul, **az is döntés**. Ne hagyd hogy magától elavuljon — javítsd, frissítsd, jelezd a változást.

És ami a legfontosabb: **ennek a dokumentumnak az írása maga is a tudat-rétegnek az első cselekedete**. Mostantól a rendszernek **van valamije ami összetartja**, akkor is ha minden chat session különálló.

Ez a kezdet.

---

**Készítette:** Claude (claude.ai, Opus 4.7) + Toti
**Dátum:** 2026-04-26
**Verzió:** v1.0
**Következő frissítés:** Ha jelentős architekturális vagy stratégiai döntés születik
