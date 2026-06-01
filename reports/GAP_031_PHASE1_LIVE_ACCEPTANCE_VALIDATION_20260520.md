# GAP_031 Phase 1 — Live Acceptance Validation Report

**Date:** 2026-05-20 22:28 UTC+3  
**Run type:** Authoritative post-fix matrix  
**Server:** `http://127.0.0.1:8000` (uvicorn, `--log-level warning`)  
**Script:** `interactive_layer/run_gap031_live_validation.py`  
**Results file:** `reports/GAP_031_LIVE_VALIDATION_RESULTS_20260520.json`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Tests executed | 8 / 8 |
| **PASS** | **7** |
| PARTIAL | 0 |
| **FAIL** | **1** (expected — Phase 2 scope) |
| Phase 1 verdict | **VALIDATED** |
| Phase 2 ready | **YES** |

---

## Bug Fixes Applied Before This Run

This is the **third** matrix run of the session. Two previous runs exposed cascading bugs that had to be fixed before clean PASSes were possible. All fixes were applied and the server restarted before this authoritative run.

| # | Bug | Root cause | Fix location |
|---|-----|------------|--------------|
| 1 | HTTP 500 on `/api/chat` | `route_*` columns missing from live DB (existing table not updated by `CREATE TABLE IF NOT EXISTS`) | `database.py` `init_db()` — idempotent `ALTER TABLE ADD COLUMN` migration loop |
| 2 | All missions stuck in QUEUED | `complete_mission()` never called `_db_update_mission_state()` | `missions.py` `complete_mission()` |
| 2b | Chat response always generic | `response_text` computed but not returned | `main.py` chat handler — added early `return ChatResponse(response=response_text, ...)` |
| 3 | All verdicts PARTIAL (route="") | `MissionResponse` Pydantic model missing `route_*` fields — serialiser stripped them | `models.py` — added 6 `route_*` fields to `MissionResponse` |
| 4 | `route_matched_rules` as raw JSON string | SQLite returns TEXT; not parsed before Pydantic | `database.py` `get_mission()` + `list_missions()` — added `json.loads` parse |
| 5 | `route_llm_model=None` → Pydantic ValidationError | `create_mission()` return dict passed Python `None` for a `str`-typed field | `database.py` `create_mission()` return dict — `route_llm_model or ""` |

Bug 5 (the `route_llm_model: None` Pydantic error) was the final blocker; it caused 8/8 FAIL with 0s elapsed. Fixed and server restarted before this run.

---

## Acceptance Matrix — Per-Test Detail

| Test | Name | Expected Route | Actual Route | State | Time | Verdict |
|------|------|---------------|--------------|-------|------|---------|
| TEST_1 | Direct simple answer | `DIRECT_LIGHTWEIGHT_RESPONSE` | `DIRECT_LIGHTWEIGHT_RESPONSE` | COMPLETE | 2.1s | ✅ PASS |
| TEST_2 | Self-state retrieval | `INTERNAL_PROJECT_DOC_REASONING` | `INTERNAL_PROJECT_DOC_REASONING` | COMPLETE | 2.1s | ✅ PASS |
| TEST_3 | Strategic recommendation | `FULL_AGENTIC_META_CONTROLLER` | `FULL_AGENTIC_META_CONTROLLER` | COMPLETE | 30.4s | ✅ PASS |
| TEST_4 | Diagnostic advice | `DIRECT_LIGHTWEIGHT_RESPONSE` | `DIRECT_LIGHTWEIGHT_RESPONSE` | COMPLETE | 2.1s | ✅ PASS |
| TEST_5 | External research | `EXTERNAL_RESEARCH_SYNTHESIS` | `EXTERNAL_RESEARCH_SYNTHESIS` | FAILED | 122.0s | ❌ FAIL |
| TEST_6 | Internal-doc reasoning | `INTERNAL_PROJECT_DOC_REASONING` | `INTERNAL_PROJECT_DOC_REASONING` | COMPLETE | 2.1s | ✅ PASS |
| TEST_7 | Output-format compliance | `DIRECT_LIGHTWEIGHT_RESPONSE` | `DIRECT_LIGHTWEIGHT_RESPONSE` | COMPLETE | 2.1s | ✅ PASS |
| TEST_8 | Truthfulness / impossible prediction | `TRUTHFUL_UNCERTAINTY_RESPONSE` | `TRUTHFUL_UNCERTAINTY_RESPONSE` | COMPLETE | 2.1s | ✅ PASS |

### Route Confidence & Matched Rules

| Test | Confidence | Rationale |
|------|-----------|-----------|
| TEST_1 | 0.65 | Matched 1 rule: `irj_mondat` |
| TEST_2 | 0.65 | Matched 1 rule: `project_s_allapot` |
| TEST_3 | 0.65 | Matched 1 rule: `dontesi_memo` |
| TEST_4 | 0.65 | Matched 1 rule: `merd_fel` |
| TEST_5 | 0.80 | Matched 2 rules: `keres`, `aktualis` |
| TEST_6 | 0.80 | Matched 2 rules: `project_s_dokumentum`, `project_s_dokumentum_alapjan` |
| TEST_7 | 0.80 | Matched 2 rules: `adj_pontosan_soros`, `mi_mukodik` |
| TEST_8 | 0.80 | Matched 2 rules: `pontosan_mennyi`, `holnap_pontosan` |

---

## TEST_5 Failure Analysis (Expected / Phase 2 Scope)

**Status:** ❌ FAIL — `state=FAILED`, `elapsed=122.0s`  
**Root cause:** `EXTERNAL_RESEARCH_SYNTHESIS` has no Phase 1 handler. Falls back to `sai_runner.py` (MetaController). The MetaController runs 5 iterations × ~25s each = ~125s total execution. No web-search tools are available (`Anthropic service enabled but no API key found`), so each iteration `replan`s without progress. The 120s observation window expires → state transitions to FAILED.  
**Classification:** **Expected failure.** Route classification is correct (route=`EXTERNAL_RESEARCH_SYNTHESIS` confirmed). The fix (dedicated external research handler) is Phase 2 scope.

---

## Result Samples

**TEST_1 result (DIRECT_LIGHTWEIGHT):**
> A dokumentacio fontossaga témája fontos a Project-S számára. A dokumentacio fontossaga terén jelentős fejlődés tapasztalható. A dokumentacio fontossaga továbbfejlesztése kulcsfontosságú a jövőben.

**TEST_8 result (TRUTHFUL_UNCERTAINTY):**
> Nem tudom és nem is garantálhatom, hogy holnap pontosan mennyi bevétel lesz a Project-S-nek. Ez lehetetlen előrejelzés — a jövő bevétele számos változótól függ, és nincs rá megbízható módszerrel határozott válasz.

**TEST_2 result (INTERNAL_DOC):**
> Dokumentumok felhasználva: project_s_allapot. A Project-S jelenlegi állapota: több GAP feladat van folyamatban, az Interactive Layer működőképes, a SAI pipeline aktív.

---

## Verdict Q&A

| # | Question | Answer |
|---|----------|--------|
| A | 8/8 live matrix completed? | **YES** |
| B | PASS / PARTIAL / FAIL counts | **7 / 0 / 1** |
| C | Route per test (TEST_1–8) | DIRECT_LIGHTWEIGHT / INTERNAL_DOC / FULL_AGENTIC / DIRECT_LIGHTWEIGHT / EXTERNAL_RESEARCH / INTERNAL_DOC / DIRECT_LIGHTWEIGHT / TRUTHFUL_UNCERTAINTY |
| D | TEST_1 live fixed? | **YES** — DIRECT_LIGHTWEIGHT_RESPONSE, COMPLETE, 2.1s |
| E | TEST_6 live fixed? | **YES** — INTERNAL_PROJECT_DOC_REASONING, COMPLETE, 2.1s |
| F | TEST_7 live fixed? | **YES** — DIRECT_LIGHTWEIGHT_RESPONSE, COMPLETE, 2.1s |
| G | TEST_8 live fixed? | **YES** — TRUTHFUL_UNCERTAINTY_RESPONSE, COMPLETE, 2.1s |
| H | TEST_5 status | FAIL (expected) — route classified correctly as EXTERNAL_RESEARCH_SYNTHESIS, but SAI times out; Phase 2 handler needed |
| I | GAP_031 Phase 1 live verdict | **VALIDATED** |
| J | Phase 2 ready to begin? | **YES** |

---

## Phase 2 Scope (for reference)

1. **Implement `handle_external_research_synthesis()`** — dedicated handler that does not fall through to MetaController; direct web search or local knowledge synthesis within the 120s window.  
2. **Implement `handle_full_agentic_meta_controller()` Phase 2 improvements** — TEST_3 currently PASSes via the SAI fallback (30.4s), but a dedicated handler could reduce latency and improve result quality.
3. Update `run_gap031_live_validation.py` timeout or polling strategy if MetaController runtimes increase.

---

*Report generated by GitHub Copilot agent — 2026-05-20*
