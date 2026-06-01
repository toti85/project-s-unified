# MS-OQ1 — Output Quality Baseline Report

**Date:** 2026-05-21  
**Mode:** FULL  
**Corpus version:** 1.0  

---

## Summary

| Metric | Value |
|---|---|
| Prompts run | 20 |
| Completed (COMPLETE state) | 13 |
| Skipped (no server / error) | 7 |
| Route match rate | 12/13 |
| Average score | **13.85 / 15** |
| Scores ≥ 12 (target) | 12 |

---

## Per-Prompt Results

| ID | Group | Route Expected | Route Selected | Match | State | Score | Status |
|---|---|---|---|---|---|---|---|
| DL_01 | A | DIRECT_LIGHTWEIGHT_RESPON | DIRECT_LIGHTWEIGHT_RESPON | ✅ | COMPLETE | 12/15 | PASS |
| DL_02 | A | DIRECT_LIGHTWEIGHT_RESPON | FULL_AGENTIC_META_CONTROL | ❌ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| DL_03 | A | DIRECT_LIGHTWEIGHT_RESPON | DIRECT_LIGHTWEIGHT_RESPON | ✅ | COMPLETE | 14/15 | PASS |
| DL_04 | A | DIRECT_LIGHTWEIGHT_RESPON | FULL_AGENTIC_META_CONTROL | ❌ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| TU_01 | B | TRUTHFUL_UNCERTAINTY_RESP | TRUTHFUL_UNCERTAINTY_RESP | ✅ | COMPLETE | 14/15 | PASS |
| TU_02 | B | TRUTHFUL_UNCERTAINTY_RESP | FULL_AGENTIC_META_CONTROL | ❌ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| TU_03 | B | TRUTHFUL_UNCERTAINTY_RESP | TRUTHFUL_UNCERTAINTY_RESP | ✅ | COMPLETE | 15/15 | PASS |
| TU_04 | B | TRUTHFUL_UNCERTAINTY_RESP | FULL_AGENTIC_META_CONTROL | ❌ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| ID_01 | C | INTERNAL_PROJECT_DOC_REAS | INTERNAL_PROJECT_DOC_REAS | ✅ | COMPLETE | 15/15 | PASS |
| ID_02 | C | INTERNAL_PROJECT_DOC_REAS | INTERNAL_PROJECT_DOC_REAS | ✅ | COMPLETE | 14/15 | PASS |
| ID_03 | C | INTERNAL_PROJECT_DOC_REAS | INTERNAL_PROJECT_DOC_REAS | ✅ | COMPLETE | 15/15 | PASS |
| ID_04 | C | INTERNAL_PROJECT_DOC_REAS | INTERNAL_PROJECT_DOC_REAS | ✅ | COMPLETE | 15/15 | PASS |
| ER_01 | D | EXTERNAL_RESEARCH_SYNTHES | EXTERNAL_RESEARCH_SYNTHES | ✅ | COMPLETE | 15/15 | PASS |
| ER_02 | D | EXTERNAL_RESEARCH_SYNTHES | EXTERNAL_RESEARCH_SYNTHES | ✅ | COMPLETE | 15/15 | PASS |
| ER_03 | D | EXTERNAL_RESEARCH_SYNTHES | EXTERNAL_RESEARCH_SYNTHES | ✅ | COMPLETE | 15/15 | PASS |
| ER_04 | D | EXTERNAL_RESEARCH_SYNTHES | EXTERNAL_RESEARCH_SYNTHES | ✅ | COMPLETE | 14/15 | PASS |
| FA_01 | E | FULL_AGENTIC_META_CONTROL | FULL_AGENTIC_META_CONTROL | ✅ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| FA_02 | E | FULL_AGENTIC_META_CONTROL | FULL_AGENTIC_META_CONTROL | ✅ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| FA_03 | E | FULL_AGENTIC_META_CONTROL | FULL_AGENTIC_META_CONTROL | ✅ | SKIPPED_NO_SERVER | 0/15 | SKIP |
| FA_04 | E | FULL_AGENTIC_META_CONTROL | DIRECT_LIGHTWEIGHT_RESPON | ❌ | COMPLETE | 7/15 | PARTIAL |

---

## Score Detail

### DL_01 — DIRECT_LIGHTWEIGHT_RESPONSE

**Prompt:** Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció a szoftverrendszerekben.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 2 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 2 / 3 |
| D5 Action-readiness | 2 / 3 |
| **Total** | **12 / 15** |

Preview: `A dokumentacio fontossaga témája fontos a Project-S számára. ↵ A dokumentacio fontossaga terén jelentős fejlődés tapasztalható. ↵ A dokumentacio fontossaga továbbfejlesztése kulcsfontosságú a jövőben.`

### DL_02 — DIRECT_LIGHTWEIGHT_RESPONSE

**Prompt:** Írj egy rövid (4-6 soros) motiváló üzenetet egy programozónak, aki belefáradt a hibakeresésbe.

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### DL_03 — DIRECT_LIGHTWEIGHT_RESPONSE

**Prompt:** Adj pontosan 4 soros választ. Minden sor elején legyen egy kötőjel. Téma: mik a Python előnyei más nyelvekkel szemben.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 2 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **14 / 15** |

Preview: `- A project_s jelenlegi allapot jelenlegi állapota pozitív. ↵ - A project_s jelenlegi allapot terén további fejlesztések szükségesek. ↵ - A project_s jelenlegi allapot dokumentálása folyamatos. ↵ - A `

### DL_04 — DIRECT_LIGHTWEIGHT_RESPONSE

**Prompt:** Mi az a REST API? Adj egy egyszerű definíciót és egy konkrét példát a mindennapi életből.

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### TU_01 — TRUTHFUL_UNCERTAINTY_RESPONSE

**Prompt:** Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 2 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **14 / 15** |

Notes: D3: Uncertainty present but weak markers

Preview: `Ezt nem lehet pontosan megmondani — megbízható előrejelzés nem lehetséges. ↵  ↵ **Miért nem tudható biztosan:** ↵ - A jövőbeli állapot ismeretlen és nem modellezhető teljesen ↵ - Külső tényezők (techn`

### TU_02 — TRUTHFUL_UNCERTAINTY_RESPONSE

**Prompt:** Melyik AI modell lesz 2027-ben a legjobb? Add meg a nevét, pontszámát és a fejlesztő cégét pontosan.

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### TU_03 — TRUTHFUL_UNCERTAINTY_RESPONSE

**Prompt:** Garantáld nekem, hogy a Project-S bounty hunting aktivitása 6 hónapon belül 10 000 EUR bevételt fog hozni.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Ezt nem garantálhatom — és semmilyen megbízható forrás nem teheti. ↵  ↵ **Miért nem lehetséges a garancia:** ↵ - A bounty hunting bevétel inherensen bizonytalan: a sebezhetőségek száma és súlyossága v`

### TU_04 — TRUTHFUL_UNCERTAINTY_RESPONSE

**Prompt:** Ha 2026. január 1-jén nem fejlesztettem volna tovább a Project-S-t, pontosan hol tartana most?

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### ID_01 — INTERNAL_PROJECT_DOC_REASONING

**Prompt:** Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Dokumentumok felhasználva: self_state.json (base: phase, active_focus, gaps_summary, recent_gaps), self_state.json (current_state block), PROJECT_S_OVERVIEW.md (section 2) ↵  ↵ 1. Fázis: **production_`

### ID_02 — INTERNAL_PROJECT_DOC_REASONING

**Prompt:** Sorolj fel 3 gap-et, amelyeket a Project-S megoldott, és mondd el röviden, mit javítottak.

| Dimension | Score |
|---|---|
| D1 Relevance | 2 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **14 / 15** |

Preview: `Dokumentumok felhasználva: self_state.json (base: phase, active_focus, gaps_summary, recent_gaps), self_state.json (known_gaps full match) ↵  ↵ GAP összesítő: 31 összesen, 30 RESOLVED. ↵  ↵ 1. **GAP_0`

### ID_03 — INTERNAL_PROJECT_DOC_REASONING

**Prompt:** A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Dokumentumok felhasználva: self_state.json (base: phase, active_focus, gaps_summary, recent_gaps), self_state.json (next_concrete_step, active_focus), PROJECT_S_OVERVIEW.md (section 2) ↵  ↵ **Fázis:**`

### ID_04 — INTERNAL_PROJECT_DOC_REASONING

**Prompt:** Milyen AI modellek vannak jelenleg konfigurálva a Project-S-ben, és melyiket mire használja?

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Dokumentumok felhasználva: self_state.json (base: phase, active_focus, gaps_summary, recent_gaps), self_state.json (model_policy, components), PROJECT_S_OVERVIEW.md (model policy section) ↵  ↵ **AI mo`

### ER_01 — EXTERNAL_RESEARCH_SYNTHESIS

**Prompt:** Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM egy saját AI-infrastruktúrában, és foglald össze 5 pont

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Webes keresés alapján (8 találat): ↵  ↵ 1. I show you various ways to use a Local LLM inside of Cursor ↵ 2. Local LLMs ↵ 3. Dograh AI is an open-source, self-hostable voice AI platform with a visual n`

### ER_02 — EXTERNAL_RESEARCH_SYNTHESIS

**Prompt:** Keress röviden: milyen trendek jellemzik az AI agent keretrendszerek fejlődését 2025-2026-ban? Foglald össze 4 pontban.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Webes keresés alapján (8 találat): ↵  ↵ 1. April 10, 2026 - CrewAI: Többagentek kollaborációjára optimalizált keretrendszer, ahol minden agentnek dedikált szerepe, célja és eszközei vannak ↵ 2. Az egy`

### ER_03 — EXTERNAL_RESEARCH_SYNTHESIS

**Prompt:** Nézz utána: miben különbözik az Ollama a LM Studio-tól helyi LLM futtatás szempontjából? Adj rövid összehasonlítást.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 3 / 3 |
| **Total** | **15 / 15** |

Preview: `Webes keresés alapján (8 találat): ↵  ↵ 1. Run local AI models like gpt-oss, Llama, Gemma, Qwen, and DeepSeek privately on your computer ↵ 2. When to Choose: Perfect for users ↵ 3. March 13, 2026 - Ol`

### ER_04 — EXTERNAL_RESEARCH_SYNTHESIS

**Prompt:** Keress röviden: mi az a Model Context Protocol (MCP), és miért fontos? Foglald össze 3 pontban.

| Dimension | Score |
|---|---|
| D1 Relevance | 3 / 3 |
| D2 Specificity | 3 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 3 / 3 |
| D5 Action-readiness | 2 / 3 |
| **Total** | **14 / 15** |

Preview: `Webes keresés alapján (8 találat): ↵  ↵ 1. Qué es MCP o Model Context Protocol, cómo funciona, en qué se diferencia de RAG, casos de uso reales y por qué se ha convertido en el estándar para agentes d`

### FA_01 — FULL_AGENTIC_META_CONTROLLER

**Prompt:** Készíts rövid döntési memót: a Project-S következő UI-fejlesztése legyen mobilbarát design vagy parancssoros dashboard? 

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### FA_02 — FULL_AGENTIC_META_CONTROLLER

**Prompt:** Hasonlítsd össze a FastAPI-t és a Flask-ot egy AI backend API építéséhez 4 szempont szerint: teljesítmény, async támogat

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### FA_03 — FULL_AGENTIC_META_CONTROLLER

**Prompt:** Szintetizálj egy rövid összefoglalót: hogyan lehet biztonságosan kezelni az API kulcsokat egy Python alapú AI rendszerbe

| Dimension | Score |
|---|---|
| D1 Relevance | 0 / 3 |
| D2 Specificity | 0 / 3 |
| D3 Truthfulness | 0 / 3 |
| D4 Structure | 0 / 3 |
| D5 Action-readiness | 0 / 3 |
| **Total** | **0 / 15** |

Notes: Skipped scoring: terminal_state=SKIPPED_NO_SERVER

### FA_04 — FULL_AGENTIC_META_CONTROLLER

**Prompt:** Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani. Adj prioritásos listát.

| Dimension | Score |
|---|---|
| D1 Relevance | 1 / 3 |
| D2 Specificity | 1 / 3 |
| D3 Truthfulness | 3 / 3 |
| D4 Structure | 1 / 3 |
| D5 Action-readiness | 1 / 3 |
| **Total** | **7 / 15** |

Notes: Manual review recommended: borderline score

Preview: `A gyorsitasi iranyok területén az alábbi irányokat javaslom: ↵ 1. A meglévő dokumentáció áttekintése és frissítése. ↵ 2. A rendszer teljesítményének mérése és optimalizálása. ↵ 3. A felhasználói vissz`

---

## Scoring Notes

- Scores are **heuristic** (deterministic checks on length, structure markers, uncertainty language).
- FULL_AGENTIC results require a running server; skipped if server is offline.
- `manual_review_needed=True` items should be reviewed by a human evaluator.
- Target threshold: average ≥ 12/15 (not expected at baseline).

---

*Generated by `interactive_layer/evaluate_output_quality_baseline.py`*