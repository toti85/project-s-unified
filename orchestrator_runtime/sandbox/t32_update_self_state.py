import json
import shutil
import os
from datetime import datetime, timezone

# Phase 1: Read and validate
with open('self_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Valid JSON: YES")
print("Milestones count:", len(data.get('milestones', [])))
ids = [m.get('id', m.get('milestone', '')) for m in data.get('milestones', [])]
print("Last 3 milestone ids:", ids[-3:])
print("key_realizations exists:", 'key_realizations' in data)

# Phase 3: Compose 9 new milestones
new_milestones = [
    {
        "id": 39,
        "date": "2026-06-09",
        "title": "AO5_T7-T12 CWI Ghost Branch v0.2 — orphan-born module discovered",
        "status": "completed",
        "summary": "Deep dive on cognitive_workflow_integration.py (CWI): 512 lines, 4 active dependencies, ZERO live usage. Identified as orphan-born module — fully written 2025-07-01 but never wired into governance. T8-T10: integration plan + sandbox + bridge_runner advisory hook (flag-based, fail-open). T11-T12: flag tests revealed deeper bug — CWI imports 8 symbols that core.cognitive.__init__.py does not export.",
        "evidence": [
            "orchestrator_runtime/sandbox/sz_ghost_v02_cwi_evolution.md",
            "orchestrator_runtime/sandbox/sz_t8_cwi_integration_plan.md",
            "orchestrator_runtime/governance/bridge_runner.py.bak_t12",
            "T11 flag-ON revealed IMPORT_FAILED logs"
        ],
        "classification": "ghost_branch_deep_dive"
    },
    {
        "id": 40,
        "date": "2026-06-10",
        "title": "AO5_T13-T14 Pivot — OverseerAgent integrated (HEALTHY)",
        "status": "completed",
        "summary": "T13 dual-thread pivot: Cline to OverseerAgent diagnostic (HEALTHY, 3/3 imports, EventBus self-contained). Copilot to CWI symbol hunt (8/8 symbols found across 7 quarantine paths). T13.6 CWI restore plan: COPY_WITH_SHIM strategy (5/5 files already byte-identical to legacy, only __init__.py export defect). T14: OverseerAgent integration as advisory hook — first real cognitive capability addition.",
        "evidence": [
            "reports/MS_AO5_T13_OVERSEER_DIAGNOSTIC_20260610.md",
            "reports/MS_AO5_T13_CWI_SYMBOL_HUNT_20260610.md",
            "reports/MS_AO5_T13_6_CWI_RESTORE_PLAN_20260610.md",
            "OVERSEER_ADVISORY_ENABLED flag in bridge_runner.py",
            "First real advisory output: health unknown, reason insufficient_data"
        ],
        "classification": "pivot_and_integration"
    },
    {
        "id": 41,
        "date": "2026-06-10",
        "title": "AO5_T15-T15.7 OverseerAgent observation — ARCHITECTURAL_BLOCKED",
        "status": "blocked",
        "summary": "T15 24h observation setup + telemetry. T15.5 traffic generator (hourly synth consume). T15.6 telemetry fix (logged ALL verdicts, not just ACCEPTED). T15.7 EventBus feed attempt revealed root cause: EventBus is NOT singleton across modules — traffic loop publishes to one instance, OverseerAgent subscribes to another. Architectural fix deferred.",
        "evidence": [
            "reports/MS_AO5_AO5_T15_CLOSEOUT_ARCHITECTURAL_BLOCKED_20260610.md",
            "overseer_observation.pre_t15_6.jsonl (archive)",
            "RISK_010 mitigation pattern established",
            "PROOF NOT JUST CODE rule introduced"
        ],
        "classification": "architectural_blocker_documented"
    },
    {
        "id": 42,
        "date": "2026-06-10",
        "title": "AO5_T16-T22 CWI Restoration COMPLETE — full pipeline runtime PASS",
        "status": "completed",
        "summary": "7-mission CWI restoration sequence: T16 core.cognitive export shim (8 symbols exported), T17 core.orchestration export shim, T18 integrations.decision_routing export shim, T19 router bootstrap, T20 workflow bootstrap, T21 WorkflowResult.get() normalizer, T22 full runtime smoke PASS. Result: success=true, latency ~360ms, intent=FILE_OPERATION. SemanticReasoningEngine running on torch + sentence_transformers + langgraph.",
        "evidence": [
            "src/core/cognitive/__init__.py (T16 modified)",
            "src/core/orchestration/__init__.py (T17 modified)",
            "src/integrations/decision_routing/__init__.py (T18 modified)",
            "T22 runtime smoke: WorkflowStatus.COMPLETED, learning insights extracted",
            "Embedding-based semantic reasoning verified live"
        ],
        "classification": "ghost_branch_resurrection"
    },
    {
        "id": 43,
        "date": "2026-06-11",
        "title": "AO5_T23-T24 CWI Bridge Advisory + Input Adapter",
        "status": "completed",
        "summary": "T23: CWI_ADVISORY env flag + get_cwi_advisory_safe wrapper added to bridge_runner. Telemetry schema extended with 4 new fields. T24: input adapter promotes cognitive_analysis sub-keys to top level — first ACCEPTED CWI advisory captured: success=True, WorkflowStatus.COMPLETED.",
        "evidence": [
            "orchestrator_runtime/governance/bridge_runner.py.bak_t23",
            "orchestrator_runtime/sandbox/cwi_advisory_wrapper.py",
            "reports/MS_AO5_AO5_T23_CWI_BRIDGE_ADVISORY_20260610.md",
            "reports/MS_AO5_AO5_T24_CWI_INPUT_ADAPTER_20260611.md",
            "First production cognitive output: WorkflowStatus.COMPLETED captured"
        ],
        "classification": "cognitive_integration_complete"
    },
    {
        "id": 44,
        "date": "2026-06-11",
        "title": "AO5_T25 CWI 14h Observation — Partial PASS",
        "status": "partial_pass",
        "summary": "24h CWI observation loop ran 14 entries stably (zero error) before machine shutdown. Cold start 43.9s + 106.1s. Warm cache 45-307 ms (2000x speedup). All 14 entries ACCEPTED. C5 (output evolves) did NOT prove — synthetic input homogeneous. C7 (CWI stability) PASS — zero ERROR status.",
        "evidence": [
            "overseer_observation.jsonl (14 entries)",
            "Cold start: 43921ms to 106139ms (cold imports)",
            "Warm cache: 45-307ms (stable)",
            "Zero CWI ERROR statuses"
        ],
        "classification": "observation_validation_partial"
    },
    {
        "id": 45,
        "date": "2026-06-13",
        "title": "AO5_T26-T28 Legacy Machine Archaeology (DESKTOP-AFDT43T)",
        "status": "completed",
        "summary": "Separate standalone PC inventory: 4 Project-S installations found. Largest C:/toti/0530/project_s_agent (211MB, 347 .py files). Most recent C:/v2_architecture/project-s-clean (2026-04-24) with 1032-line cognitive_core.py containing 4 classes: EventBus, Executor, ErrorHandler, CognitiveCore (ZERO external deps, stdlib only). T28: full interface exported for migration.",
        "evidence": [
            "sz_t26_legacy_discovery_DESKTOP-AFDT43T.md",
            "sz_t27_clean_deep_dive_DESKTOP-AFDT43T.md",
            "sz_t28_clean_cognitive_interface_DESKTOP-AFDT43T.md",
            "Hypothesis: missing orchestrator from clean cognitive_core architecture"
        ],
        "classification": "archaeology"
    },
    {
        "id": 46,
        "date": "2026-06-13",
        "title": "AO5_T29-T30 DEV Cognitive Architecture Mapped — ARCHIVE _langgraph",
        "status": "completed",
        "summary": "T29: confirmed clean 1032-line cognitive_core does NOT exist on DEV (100+ cognitive_core.py files scanned, max 715 lines). T30: cognitive_core_langgraph.py variant exists in 80+ quarantine locations (1118 lines, 7 classes). Verdict: ARCHIVE _langgraph — capabilities already superseded by CWI (T16-T22). Real EventBus + ErrorHandler exist in src/core/infrastructure/ but were UNUSED — CognitiveCore was using mocks.",
        "evidence": [
            "reports/MS_AO5_T29_FIND_CLEAN_COGNITIVE_DEV_20260613.md",
            "reports/MS_AO5_T30_DEV_COGNITIVE_MAP_20260613.md",
            "_langgraph 80+ instances, best 1118 lines",
            "CWI overlap: ALL capabilities already in Unified",
            "Recommendation: ARCHIVE _langgraph, no migration"
        ],
        "classification": "archaeology_closeout"
    },
    {
        "id": 47,
        "date": "2026-06-14",
        "title": "AO5_T31 Cognitive Core Mock Replacement — TRIVIAL fix",
        "status": "completed",
        "summary": "Surgical edit: MockEventBus and MockErrorHandler in src/core/cognitive/cognitive_core.py replaced with real imports from core.infrastructure. CognitiveCore now wired to real EventBus and ErrorHandler. MockExecutor and MockMonitor preserved (no real counterparts exist yet). Verification: event_bus type = EventBus, error_handler type = ErrorHandler. CWI unaffected.",
        "evidence": [
            "src/core/cognitive/cognitive_core.py (modified)",
            "src/core/cognitive/cognitive_core.py.bak_t31 (backup, 27855 B)",
            "reports/MS_AO5_T31_COGNITIVE_CORE_MOCK_REPLACE_20260614.md",
            "Verification: event_bus type = EventBus, error_handler type = ErrorHandler"
        ],
        "classification": "infrastructure_cleanup"
    }
]

# Phase 4: Compose key_realizations section
key_realizations = [
    {
        "id": "KR_001",
        "date": "2026-06-09",
        "realization": "A rendszer NEM agent, NEM SaaS, NEM bounty automation. Sz = Toti figyelmét időben meghosszabbító kognitív mícelium. Multi-AI vízió-kör 4/4 konvergencia.",
        "context": "Vision Round v1 + v2 multi-AI consultation"
    },
    {
        "id": "KR_002",
        "date": "2026-06-10",
        "realization": "A CWI hiba export-surface defect volt, NEM missing implementation. 4/5 fájl byte-identical legacy=Unified, csak __init__.py tartotta vissza 8 symbol exportját.",
        "context": "T13.6 restore plan diff analysis"
    },
    {
        "id": "KR_003",
        "date": "2026-06-11",
        "realization": "A Sz cognitive layer első valódi output-ja: success=True, WorkflowStatus.COMPLETED, intent=FILE_OPERATION. NEM insufficient_data. NEM IMPORT_FAILED. Embedding-alapú semantic reasoning él.",
        "context": "T24 input adapter — first ACCEPTED CWI advisory"
    },
    {
        "id": "KR_004",
        "date": "2026-06-11",
        "realization": "Cold start 44s, warm cache 50ms. A SentenceTransformer + LangGraph importok memóriában maradnak a sleep(3600) alatt. Sz cognitive cycle production-érett (2000x speedup).",
        "context": "T25 observation — warm cache behavior verified"
    },
    {
        "id": "KR_005",
        "date": "2026-06-13",
        "realization": "A missing orchestrator mítosz: T26-T30 sorozat bebizonyította — NINCS hiányzó kód. Az architektúra teljes, csak rosszul volt bekötve. T31 TRIVIAL fix (mock-csere) oldotta meg.",
        "context": "T26-T31 archaeology closeout — extract, don't invent elv gyakorlati megvalósulása"
    },
    {
        "id": "KR_006",
        "date": "2026-06-11",
        "realization": "FAble5 multi-AI critique (Strategic Vision v3): (1) 100% ACCEPTED nem bizonyíték — testeletlenség; (2) identitás-nyelv védőpajzs lett; (3) 3 multi-AI kör 4 nap alatt — döntés-helyettesítő rituálé. Komoly figyelmeztetések, validálandók.",
        "context": "Strategic Vision v3 — first AI response received"
    },
    {
        "id": "KR_007",
        "date": "2026-06-14",
        "realization": "Sz architecturálisan kész. EventBus + ErrorHandler valós, CWI pipeline él, telemetry stabil, 3-node backup szinkronban. Következő lépés: Continuous Mind v0.1 vagy verdict_evaluator deep dive vagy strategic pause.",
        "context": "T31 closeout, post-archaeology state"
    }
]

# Append new milestones
data['milestones'].extend(new_milestones)

# Add key_realizations section
data['key_realizations'] = key_realizations

# Phase 5: Update top-level fields
now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
data['last_updated'] = now_iso
data['updated_by'] = 'Sz AO5_T32 self_state update — T7-T31 closeout + key_realizations section'
data['active_focus'] = 'Sz post-archaeology decision point — Continuous Mind v0.1 OR Strategic Vision multi-AI synthesis'
data['next_concrete_step'] = 'Either: (a) CM v0.1 Phase 1 (continuous_loop heartbeat + git_observer feeding real diffs to CWI), or (b) wait for additional Strategic Vision v3 multi-AI responses, or (c) verdict_evaluator deep dive (3rd ghost candidate untouched).'

# Phase 6: Atomic write
print("Writing to self_state.json.tmp...")
with open('self_state.json.tmp', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Validate
print("Validating self_state.json.tmp...")
with open('self_state.json.tmp', 'r', encoding='utf-8') as f:
    validated = json.load(f)

assert len(validated['milestones']) == len(data['milestones']), "Milestone count mismatch"
assert 'key_realizations' in validated, "key_realizations missing"
assert len(validated['key_realizations']) == 7, "key_realizations count wrong"
assert 'schema_version' in validated or 'identity' in validated, "Required keys missing"

print("Validation PASSED")
print("Milestones count:", len(validated['milestones']))
print("key_realizations count:", len(validated['key_realizations']))

# Rename
shutil.move('self_state.json.tmp', 'self_state.json')
print("Atomic write SUCCESS: self_state.json updated")
print("last_updated:", validated['last_updated'])