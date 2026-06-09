# cognitive_workflow_integration.py — Modul Evolúciós Térkép

## Verziók időrendben

| Verzió | Path | Date | Size | Lines | Methods | Unique features |
|--------|------|------|------|-------|---------|-----------------|
| v1 (only known) | `src/core/cognitive_workflow_integration.py` | 2025-07-01 | 20,430 bytes | 512 | 10 public methods, 1 class | 4-phase cognitive task processing, intent-driven workflow selection, semantic reasoning integration, decision router-based workflow routing, learning pattern storage |

**Note:** No other versions found in external paths:
- `C:\ProjectS\project-s-code\` — NOT FOUND
- `C:\Users\Admin\project_s_super_core\` — NOT FOUND
- `C:\ProjectS-Snapshot-Staging\` — NOT FOUND
- `C:\1225\project_s_super_core\` — NOT FOUND

Only the current `src/core/cognitive_workflow_integration.py` exists.

## Capabilities (method signatures)

```python
class CognitiveWorkflowIntegration:
    def __init__(self, config: Optional[Dict[str, Any]] = None)
    async def process_task_cognitively(task_description, context, user_id) -> Dict[str, Any]
    async def _perform_cognitive_analysis(task_description, context, user_id) -> Dict[str, Any]
    async def _select_and_configure_workflow(cognitive_analysis) -> Dict[str, Any]
    async def _execute_cognitive_workflow(workflow_config, cognitive_analysis) -> Dict[str, Any]
    async def _post_process_and_learn(execution_result, cognitive_analysis, start_time) -> Dict[str, Any]
    def _update_metrics(start_time, success) -> None
    def get_performance_metrics() -> Dict[str, Any]

# Module-level functions:
def get_cognitive_workflow_integration(config) -> CognitiveWorkflowIntegration
async def process_task_with_cognitive_enhancement(task_description, context, user_id, config) -> Dict[str, Any]
```

## Import dependencies

```python
from core.cognitive import (
    cognitive_registry,
    EnhancedCognitiveProcessor,
    AdvancedIntentAnalyzer,
    SemanticReasoningEngine,
    CognitiveContext,
    CognitiveResult,
    IntentMatch,
    TaskDecomposition
)
from core.orchestration import (
    WorkflowRegistry,
    LangGraphWorkflowEngine,
    WorkflowResult,
    workflow_registry
)
from integrations.decision_routing import (
    DecisionRouterRegistry,
    AdvancedDecisionRouter,
    router_registry
)
from core.state import (
    PersistentStateManager,
    default_state_manager,
    StateType
)
```

## Complexity Score

| Metric | Value |
|--------|-------|
| Lines of code | 512 |
| Classes | 1 (CognitiveWorkflowIntegration) |
| Public methods | 10 |
| Private methods | 4 |
| Module-level functions | 2 |
| Import dependencies | 4 major modules |
| External component count | 15+ (cognitive, orchestration, routing, state) |

## Mit tudott korábban (elveszett funkciók)

- **4-phase cognitive task processing pipeline**: Intent analysis → Task decomposition → Semantic reasoning → Workflow execution → Learning insights
- **Intent-driven workflow selection**: Uses `AdvancedIntentAnalyzer` to detect task intent and route to appropriate workflow type
- **Decision router integration**: Uses `AdvancedDecisionRouter` to select workflow type based on complexity, intent, and reasoning strategy
- **Learning pattern storage**: Stores execution patterns in `PersistentStateManager` for future optimization
- **Performance metrics tracking**: Tracks success rate, average processing time, cognitive insights generated

## Mit nyert (új funkciók)

Nincs korábbi verzió, így nem lehet "nyert" funkciókat azonosítani. Ez az egyetlen ismert verzió.

## Legjobb verzió: `src/core/cognitive_workflow_integration.py` — miért?

Ez az egyetlen ismert verzió, és egyben a legteljesebb is. 2025-07-01-ről származik, a v2 Architecture korszak terméke. A következő erősségekkel bír:

1. **Teljes 4-fázisú pipeline**: Cognitive analysis → Workflow selection → Cognitive-enhanced execution → Post-processing with learning
2. **DRY compliance**: Global registry pattern (`cognitive_registry`, `workflow_registry`, `router_registry`)
3. **State management integration**: Uses `PersistentStateManager` for learning pattern storage
4. **Performance tracking**: Built-in metrics with success rate calculation
5. **Convenience API**: Module-level `get_cognitive_workflow_integration()` and `process_task_with_cognitive_enhancement()` functions

## Bekötési terv a jelenlegi Sz governance-be

### Integrációs pont: `filesystem_orchestrator.py`

```python
# In filesystem_orchestrator.py, before OrchestratedRun.execute():

from core.cognitive_workflow_integration import get_cognitive_workflow_integration

# Pre-processing wrapper
cwi = get_cognitive_workflow_integration()
cognitive_result = await cwi.process_task_cognitively(
    task_description=goal_string,
    context={"governance_pipeline": "MS-AO5"},
    user_id="ao5_system"
)

# Extract workflow guidance
intent_type = cognitive_result["intent_analysis"]["intent_type"]
subtasks = cognitive_result["task_decomposition"]["subtasks"]
reasoning_strategy = cognitive_result["semantic_reasoning"]["strategy"]

# Pass to existing orchestrator with cognitive guidance
result = await OrchestratedRun.execute(
    goal=goal_string,
    cognitive_guidance=cognitive_result
)
```

### Alternatív bekötés: `cli.py`

```python
# In cli.py main() function, before task execution:

from core.cognitive_workflow_integration import process_task_with_cognitive_enhancement

# Wrap the entire task execution
enhanced_result = await process_task_with_cognitive_enhancement(
    task_description=task_input,
    context={"source": "cli", "pipeline": "MS-AO5"}
)
```

### Required dependencies check:
- `core.cognitive` — ✅ ACTIVE (imported by super_intelligent_ai.py, agent_loop.py)
- `core.orchestration` — ✅ EXISTS (langgraph_engine.py, advanced_langgraph_workflow.py)
- `integrations.decision_routing` — ✅ EXISTS (advanced_decision_router.py)
- `core.state` — ✅ ACTIVE (autonomy_state.py, persistent_manager.py)

### Risk assessment:
- **Import risk**: LOW — all dependencies are active components
- **Integration risk**: MEDIUM — requires async context in cli.py or filesystem_orchestrator.py
- **Performance risk**: LOW — cognitive analysis adds ~1-2 AI calls, already accounted for in budget