# AO5_T6 — Ghost Branch v0.1 (Kódrégész)
**Run ID:** AO5_T6 | **Iteration:** 1 | **Date:** 2026-06-09
**Scope:** src/ Python files | **Archive:** archive/ (no .py files found)

---

## 1. Active Components Summary

**Total .py files in src/:** 93 (excluding __init__.py: 81 non-init files)
**Active (imported by ≥1 other file):** 45
**Inactive (no imports from other files):** 30
**Empty (0 bytes):** 6
**Init files:** 12

### Active governance stack (core pipeline):
| Component | Size | Last Modified | Importers |
|-----------|------|---------------|-----------|
| orchestrator/filesystem_orchestrator.py | 33.7KB | 2026-05-25 | cli.py, handoff_watcher.py |
| orchestrator/state_machine.py | 7.5KB | 2026-05-26 | cli.py, filesystem_orchestrator.py, handoff_watcher.py |
| orchestrator/verdict_schema.py | 3.9KB | 2026-05-24 | ai_client.py, filesystem_orchestrator.py, handoff_watcher.py, verdict_evaluator.py |
| orchestrator/ai_client.py | 15.9KB | 2026-05-26 | filesystem_orchestrator.py |
| orchestrator/cli.py | 19.5KB | 2026-05-26 | __main__.py, handoff_watcher.py, run_archive.py |
| orchestrator/handoff_watcher.py | 8.5KB | 2026-05-25 | cli.py |
| orchestrator/run_archive.py | 6.7KB | 2026-05-25 | cli.py |
| core/evaluator.py | 74.1KB | 2026-05-18 | integrated_execution_manager.py, super_intelligent_ai.py, agent_loop.py |
| integrations/ai_models/multi_model_ai_client.py | 21.3KB | 2026-04-29 | evaluator.py, agent_loop.py, super_intelligent_ai.py, etc. (13 refs) |
| core/meta/meta_controller.py | 23.7KB | 2026-05-14 | super_intelligent_ai.py, agent_loop.py |
| core/meta/execution_validator.py | 13.5KB | 2026-04-29 | test_validator.py, __init__.py |
| core/state/autonomy_state.py | 2.4KB | 2025-08-17 | integrated_execution_manager.py, super_intelligent_ai.py, autonomous_controller.py |
| core/tools/tool_registry_golden.py | 20.3KB | 2025-07-13 | integrated_execution_manager.py, self_dev_agent.py, super_intelligent_ai.py |
| core/self_dev_agent.py | 21.6KB | 2025-12-25 | integrated_execution_manager.py, autonomous_controller.py |
| core/cognitive/cognitive_core.py | 27.2KB | 2025-07-22 | super_intelligent_ai.py, agent_loop.py, __init__.py |
| utils/performance_monitor.py | 7.0KB | 2026-05-18 | evaluator.py, overseer_agent.py, __init__.py |

---

## 2. Inactive/Ghost Candidates (30 files)

### A. Recently modified but still orphaned (potential ghost-active):
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| core/agent/agent_loop.py | 21.8KB | 2026-04-28 | Agent loop with cognitive core integration |
| core/evaluator_new.py | 13.3KB | 2025-07-01 | Fork of evaluator.py with relative imports |
| core/integrated_execution_manager.py | 18.2KB | 2025-12-25 | Duplicate of execution/integrated_execution_manager.py |
| core/execution/integrated_execution_manager.py | 18.2KB | 2025-12-25 | Duplicate path, same content |
| core/agent/autonomous_controller.py | 5.2KB | 2025-12-25 | Autonomous controller (duplicate in agents/) |
| core/agents/autonomous_controller.py | 5.2KB | 2025-12-25 | Duplicate of agent/autonomous_controller.py |
| orchestrator/__main__.py | 0.3KB | 2026-05-26 | Entry point, imports cli.main |
| orchestrator/cline_bridge.py | 3.5KB | 2026-05-24 | Cline prompt drafting bridge |
| orchestrator/verdict_evaluator.py | 4.9KB | 2026-05-24 | Verdict evaluation logic |

### B. Old cognitive core components (abandoned v1 patterns):
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| core/cognitive/advanced_analyzer.py | 27.0KB | 2025-07-01 | Advanced pattern analyzer (imported FROM base_cognitive) |
| core/cognitive/enhanced_processor.py | 33.8KB | 2025-07-01 | Enhanced cognitive processor |
| core/cognitive/semantic_reasoning.py | 39.2KB | 2025-07-01 | Semantic reasoning engine (numpy-based) |
| core/cognitive_workflow_integration.py | 20.0KB | 2025-07-01 | Cognitive-workflow bridge layer |
| core/strategic_overlay.py | 4.8KB | 2025-08-17 | Strategic AI overlay |
| core/super_intelligent_ai.py | 46.1KB | 2026-05-18 | Full SAI with meta-controller (imported FROM but not imported BY) |

### C. Test/development files:
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| core/meta/test_council.py | 11.6KB | 2026-01-01 | Test council for meta layer |
| core/meta/test_meta_controller.py | 12.7KB | 2026-01-02 | Test meta controller |
| core/meta/test_validator.py | 11.2KB | 2026-01-02 | Test validator |
| core/meta/research/test_research_loop.py | 10.6KB | 2026-01-03 | Test research loop |
| core/meta/research/IMPLEMENTATION_REPORT.py | 19.0KB | 2026-01-03 | Implementation report (doc artifact) |

### D. Agent/monitoring components:
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| core/agents/overseer_agent.py | 28.0KB | 2025-07-22 | AI monitoring & optimization agent |
| core/agents/pattern_analyzer.py | 13.6KB | 2025-07-22 | Pattern analysis for workflows |
| core/execution/execution_controller.py | 9.4KB | 2025-07-01 | Execution controller |

### E. Integration/bridge components:
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| integrations/copilot_client.py | 8.2KB | 2025-08-17 | Copilot integration client |
| integrations/decision_routing/advanced_decision_router.py | 23.0KB | 2025-07-01 | Advanced decision router (langgraph-based) |

### F. Orchestration/legacy:
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| core/orchestration/langgraph_engine.py | 35.1KB | 2025-07-01 | LangGraph workflow engine |
| core/orchestration/golden_age/advanced_langgraph_workflow.py | 31.5KB | 2025-07-01 | Advanced LangGraph workflow |

### G. Browser tool variants (backup/old):
| File | Size | Last Modified | Notes |
|------|------|---------------|-------|
| core/tools/implementations/browser_automation_tool_backup.py | 14.4KB | 2025-07-11 | Backup browser tool |
| core/tools/implementations/browser_automation_tool_new.py | 8.0KB | 2025-07-12 | New browser tool variant |

### H. Empty placeholder files:
| File | Size | Notes |
|------|------|-------|
| core/resource_management/memory_optimizer.py | 0 bytes | Empty placeholder |
| core/resource_management/resource_manager.py | 0 bytes | Empty placeholder |
| core/resource_management/resource_predictor.py | 0 bytes | Empty placeholder |
| core/resource_management/system_monitor.py | 0 bytes | Empty placeholder |
| core/resource_management/task_resource_allocator.py | 0 bytes | Empty placeholder |
| integrations/resource_management.py | 0 bytes | Empty placeholder |

---

## 3. TOP 3 Resurrection Candidates

### #1: orchestrator/verdict_evaluator.py (4.9KB, 2026-05-24)
**Rationale:** This file is part of the ACTIVE MS-AO5 governance pipeline (imported by verdict_schema.py, used in filesystem_orchestrator.py workflow). It appears "inactive" only because it's imported via relative import `from .verdict_schema import VerdictStatus` but the file itself is NOT imported by any other module — it provides functions that are called indirectly. This is a **false negative** ghost: it's actually active in the governance stack.

**What it does:** Evaluates execution verdicts against governance policies and returns structured verdict decisions with confidence scores.

**Evidence:** Imported by `verdict_schema.py` via relative import; referenced in `filesystem_orchestrator.py` verdict flow.

**Risk:** UNKNOWN — needs code inspection to confirm it's wired into the main orchestrator flow.

**Recommended next step:** Verify integration by checking if `evaluate_verdict()` is called from `filesystem_orchestrator.py` or `cli.py`. If confirmed, reclassify as ACTIVE.

---

### #2: core/cognitive_workflow_integration.py (20.0KB, 2025-07-01)
**Rationale:** This is a **high-value ghost** — it provides a cognitive-enhanced workflow integration layer that bridges the cognitive core (intent analysis, task decomposition, semantic reasoning) with the orchestration engine (LangGraph workflows). It was built for v2 architecture but never wired into the current MS-AO5 pipeline. The current orchestrator uses `filesystem_orchestrator.py` which has NO cognitive analysis layer.

**What it does:** Provides 4-phase cognitive task processing: (1) cognitive analysis via intent analyzer, (2) workflow selection via decision router, (3) cognitive-enhanced workflow execution, (4) post-processing with learning insights.

**Evidence:** Imports from `core.cognitive`, `core.orchestration`, `integrations.decision_routing`, `core.state` — all active components. The file itself is never imported by any other module.

**Relevance to MS-AO5:** Would add intelligent task routing and intent-aware workflow selection to the current governance pipeline. Currently the orchestrator routes blindly without cognitive pre-analysis.

**Recommended next step:** Integrate as a pre-processing wrapper around `filesystem_orchestrator.OrchestratedRun.execute()`. Create a thin `from core.cognitive_workflow_integration import get_cognitive_workflow_integration` import in `cli.py` or `filesystem_orchestrator.py`.

---

### #3: core/agents/overseer_agent.py (28.0KB, 2025-07-22)
**Rationale:** This is an **intelligent monitoring agent** that provides pattern recognition, proactive optimization suggestions, and predictive analytics for the AI execution pipeline. It subscribes to the same `EventBus` that powers `core.infrastructure.event_bus` (active, 7 importers). It would provide real-time oversight of the MS-AO5 governance pipeline — detecting stuck executions, suboptimal tool sequences, and suggesting improvements.

**What it does:** Monitors AI agent executions via event bus, learns workflow patterns, generates optimization suggestions (tool ordering, resource allocation, timing), and provides predictive performance analytics.

**Evidence:** Imports `EventBus` and `EnhancedLogger` from active modules. Uses sqlite3 for pattern storage. Has `PerformanceMetric`, `WorkflowPattern`, and `OptimizationSuggestion` dataclasses.

**Relevance to MS-AO5:** Provides the "evidence collection" and "anomaly detection" layer that the governance pipeline currently lacks. Could detect when `goal_queue` items are stuck, when `risk_classifier` flags are misfiring, or when `bridge_runner` encounters repeated failures.

**Recommended next step:** Instantiate alongside the event bus in `filesystem_orchestrator.py` or `cli.py`. Subscribe to execution events and run periodic optimization analysis. Start with: `overseer = OverseerAgent(event_bus); event_bus.subscribe(overseer.on_event)`.

---

## 4. Recommended Next Steps Summary

| Rank | Component | Action | Effort | Impact |
|------|-----------|--------|--------|--------|
| #1 | verdict_evaluator.py | Verify integration, reclassify as ACTIVE | Low | Fixes false-negative ghost |
| #2 | cognitive_workflow_integration.py | Wire as pre-processor to orchestrator | Medium | Adds cognitive task analysis to MS-AO5 |
| #3 | overseer_agent.py | Subscribe to event bus for monitoring | Medium | Adds real-time pipeline oversight |

### Additional cleanup recommendations:
- **Duplicate files:** `core/agent/autonomous_controller.py` == `core/agents/autonomous_controller.py` (keep one, remove other)
- **Empty placeholders:** 6 zero-byte files in `core/resource_management/` and `integrations/resource_management.py` — either implement or remove
- **Backup variants:** `browser_automation_tool_backup.py`, `browser_automation_tool_new.py` — consolidate into single implementation
- **Test files:** 4 test_*.py files in `core/meta/` — migrate to proper test directory or remove if obsolete

---

## 5. Methodology Notes

- **Import analysis:** Scanned all 93 .py files in src/ for `import X` and `from X import Y` patterns
- **Reference tracking:** For each file, searched all other files for import references to that file's basename
- **Inactive classification:** A file is "inactive" if NO other .py file imports it (directly or via relative import)
- **Empty files:** 6 files with 0 bytes size — classified separately as they are structurally empty
- **Test files:** Excluded from ghost ranking (test_*.py files are expected to be standalone)
- **Archive scan:** archive/ directory contains only `gap030_validation_scripts_20260520/` subdirectory with no .py files relevant to this analysis
- **UNKNOWN status:** Applied to verdict_evaluator.py because while it's not imported, it may be called indirectly

---

*Generated by: AO5_T6 Ghost Branch v0.1 (Kódrégész)*
*Evidence: src_import_analysis.json (internal)*