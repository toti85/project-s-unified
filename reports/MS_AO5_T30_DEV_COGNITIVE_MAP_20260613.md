# T30 Dev Cognitive Architecture Map — Mission Report

**Generated:** 2026-06-14T01:19:00+03:00
**Task:** AO5_T30_DEV_COGNITIVE_ARCHITECTURE_MAP
**Mode:** READ-ONLY discovery + comparison

---

## Executive Summary

**Recommendation: ARCHIVE** — The `cognitive_core_langgraph.py` variant is a historical orchestrator from 2025-06 whose capabilities have already been superseded by the T16-T22 CWI (CognitiveWorkflowIntegration) series in Unified. No migration needed.

---

## A. Unified Cognitive Infrastructure (Current State)

### src/core/cognitive/
| File | Size | Lines | Modified |
|------|------|-------|----------|
| cognitive_core.py | 27,855 B | 704 | 2025-07-22 |
| enhanced_processor.py | 34,580 B | — | 2025-07-01 |
| semantic_reasoning.py | 40,182 B | — | 2025-07-01 |
| advanced_analyzer.py | 27,687 B | — | 2025-07-01 |
| base_cognitive.py | 14,577 B | — | 2025-07-01 |
| __init__.py | 966 B | — | 2026-06-11 |

**Exports:** CognitiveCore, EnhancedCognitiveProcessor, AdvancedIntentAnalyzer, SemanticReasoningEngine, CognitiveContext, CognitiveResult, IntentMatch, TaskDecomposition

### src/core/infrastructure/
| File | Size | Modified |
|------|------|----------|
| event_bus.py | 3,646 B | 2025-07-01 |
| error_handler.py | 4,586 B | 2025-07-01 |
| execution_events.py | 3,455 B | 2025-12-25 |

### src/core/orchestration/
| File | Size | Classes |
|------|------|---------|
| langgraph_engine.py | 35,900 B | TaskType, LangGraphWorkflowEngine |
| workflow_engine.py | 39,591 B | WorkflowState, EnhancedWorkflowEngine, WorkflowError |
| base_workflow.py | 8,671 B | WorkflowStatus, TaskComplexity, WorkflowResult, BaseWorkflowEngine, WorkflowRegistry |

### cognitive_workflow_integration.py
- 516 lines, 21,150 bytes, modified 2026-06-11
- Class: `CognitiveWorkflowIntegration`
- Imports: LangGraphWorkflowEngine, AdvancedIntentAnalyzer, SemanticReasoningEngine, EnhancedCognitiveProcessor, PersistentStateManager

---

## B. EventBus Location in Unified
- **Path:** `src/core/infrastructure/event_bus.py`
- **Size:** 3,646 bytes
- **Modified:** 2025-07-01

## C. ErrorHandler Location in Unified
- **Path:** `src/core/infrastructure/error_handler.py`
- **Size:** 4,586 bytes
- **Modified:** 2025-07-01

## D. cognitive_core.py Current State
- **Lines:** 704
- **Classes:** MockEventBus, MockExecutor, MockErrorHandler, MockMonitor, CognitiveCore
- **Imports:** stdlib only (logging, asyncio, json, uuid, typing, datetime)
- **Note:** Uses MOCK classes — real infrastructure exists in `src/core/infrastructure/`

## E. cognitive_core_langgraph.py in Unified?
**NO** — Not present anywhere in ProjectS-Unified.

## F. Best _langgraph Candidate
- **Path:** `C:\_cleanup_quarantine\audit_forks_20260609\project-s-agent-main\core\cognitive_core_langgraph.py`
- **Reason:** Largest (1,118 lines), most recent (2025-06-24), from stable codebase

## G. _langgraph Candidate Analysis
- **Lines:** 1,118
- **Size:** 48,893 bytes
- **Classes (7):**
  1. `PathSerializationMixin` (line 29) — JSON serialization for Path objects
  2. `Memory` (line 54) — Pydantic model: conversation, entities, context
  3. `Task` (line 59) — Pydantic model: id, description, status, steps
  4. `CognitiveGraphState` (line 68) — Full graph state model
  5. `CognitiveCoreGraph` (line 82) — Graph-based cognitive core (661 lines)
  6. `CognitiveCoreWithLangGraph` (line 743) — Main orchestrator (361 lines)
  7. `CognitiveCoreWorkflow` (line 1104) — High-level workflow wrapper
- **External imports:** pydantic, langgraph (graph, prebuilt, checkpoint)
- **Project imports:** event_bus, central_executor, error_handler, ai_command_handler, multi_model_integration, langgraph_integration, langgraph_state_manager, langgraph_state_enhanced

## H. Classes in _langgraph but NOT in Unified
| Class | Lines | Port Difficulty |
|-------|-------|----------------|
| PathSerializationMixin | ~23 | TRIVIAL |
| Memory (Pydantic) | ~5 | SIMPLE |
| Task (Pydantic) | ~8 | SIMPLE |
| CognitiveGraphState (Pydantic) | ~13 | SIMPLE |
| CognitiveCoreGraph | ~661 | COMPLEX (needs langgraph deps) |
| CognitiveCoreWithLangGraph | ~361 | COMPLEX (needs langgraph infra) |
| CognitiveCoreWorkflow | ~25 | MODERATE |

## I. CWI Overlap Analysis
| _langgraph Capability | CWI Equivalent | Status |
|----------------------|----------------|--------|
| Graph-based workflow execution | LangGraphWorkflowEngine | COVERED |
| State management with persistence | PersistentStateManager | COVERED |
| Advanced intent analysis | AdvancedIntentAnalyzer | COVERED |
| Semantic reasoning | SemanticReasoningEngine | COVERED |
| Enhanced cognitive processing | EnhancedCognitiveProcessor | COVERED |

## J. Recommendation: ARCHIVE

## K. Reasoning

The `_langgraph` variant is a historical orchestrator from 2025-06 that used LangGraph + Pydantic for graph-based cognitive workflows. However, the T16-T22 series already rebuilt and superseded its core capabilities through CWI + LangGraphWorkflowEngine + EnhancedWorkflowEngine + AdvancedIntentAnalyzer + SemanticReasoningEngine.

The Unified architecture is more modular (separate files for event_bus, error_handler, orchestration) and more recent (2026-06 vs 2025-06). The `_langgraph` variant's Pydantic models are interesting but not directly portable without langgraph dependencies.

**Key design concern:** `CognitiveCore.py` in Unified uses mock classes (MockEventBus, MockExecutor, MockErrorHandler). The real infrastructure classes exist in `src/core/infrastructure/` and are used by CWI. The priority improvement would be replacing mock classes with real infrastructure imports — a TRIVIAL fix.

## L. Migration Not Needed

**Suggested improvement:** Replace MockEventBus/MockExecutor/MockErrorHandler in `cognitive_core.py` with imports from `core.infrastructure`. This is a TRIVIAL fix that would make the current CognitiveCore functional without needing the `_langgraph` variant.

---

## Output Files
- `orchestrator_runtime/sandbox/sz_t30_dev_cognitive_architecture_map.json` — Machine-readable
- `orchestrator_runtime/sandbox/sz_t30_dev_cognitive_architecture_map.md` — Human-readable
- `reports/MS_AO5_T30_DEV_COGNITIVE_MAP_20260613.md` — This formal report

---

*End of Mission Report T30*