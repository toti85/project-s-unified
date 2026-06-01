# PROJECT-S — MASTER CONTEXT (Auto-Generated)
**Generated:** 2026-03-13 08:31 UTC
**Source:** project_state.json v1
**System Status:** OPERATIONAL

---

## System Overview
- **Entry point:** `main.py`
- **Startup time:** 4.0s
- **Codebase:** `project_s_super_core/`
- **Platform:** windows / Python 3.11

## AI Models
- **Available:** 4 / 7 configured
- **Fallback chain:** qwen3-235b → gpt-4o-mini → llama3

  - ❌ **qwen3-235b** [openrouter] — primary (no_api_key)
  - ❌ **deepseek-v3** [openrouter] — strategic (no_api_key)
  - ✅ **gpt-4o-mini** [openai] — fallback
  - ✅ **gpt-3.5-turbo** [openai] — bulk
  - ❌ **claude-sonnet-4** [anthropic] — validator (no_api_key)
  - ✅ **llama3** [ollama] — local
  - ✅ **mistral** [ollama] — local

## Components
### Golden Age
  - ✅ **cognitive_core**: working — `src/core/cognitive/cognitive_core.py`
  - ✅ **workflow_engine**: working — `src/core/orchestration/workflow_engine.py`
  - ✅ **decision_router**: working — `src/integrations/decision_routing/base_router.py`
  - ✅ **ai_client**: working — `src/integrations/ai_models/multi_model_ai_client.py`
  - ⚠️ **smart_orchestrator**: partial — `tools/tools/registry/smart_orchestrator.py`

### Organism
  - ✅ **observer**: working — `organism/core/observer.py`
  - ✅ **prioritizer**: working — `organism/core/prioritizer.py`
  - ✅ **proposer**: working — `organism/core/proposer.py`
  - ✅ **taste_model**: working — `organism/modules/taste_model.py`
  - ✅ **loop**: working — `organism/core/loop.py`

### Meta Learning
  - ✅ **ai_strategist**: working — `src/core/meta/ai_strategist.py`
  - ✅ **ai_validator**: working — `src/core/meta/ai_validator.py`
  - ⚠️ **meta_controller**: partial — `src/core/meta/meta_controller.py`
  - ⚠️ **strategy_council**: partial — `src/core/meta/strategy_council.py`

## Memory & Evidence
- **Total records:** 404,239
- **Learning:** 213 records (`memory/intelligence/learning.jsonl`)
- **Meta-evidence:** 403,868 records
- **Telemetry:** 158 events

## Current Phase
- **Phase:** phase_2
- **Current task:** knowledge_layer_testing
- **Next tasks:** pattern_learning_library, lm_studio_hybrid
- **Phase 1 completed:** 2026-03-13 (score: 8/9)

## Not Yet Implemented
- knowledge_layer_full
- pattern_learning_library
- lm_studio_hybrid
- dream_mode
- blackbox_guardrail
- evidence_graph
- agent_genome
- emergence_catalog

## Recent Decisions (last 5)
- [2026-03-13] **architecture**: Archive v2_architecture
- [2026-03-13] **architecture**: Deduplicate AIClient to 1 copy
- [2026-03-13] **architecture**: Consolidate config to 3 files
- [2026-03-13] **architecture**: Update models.yaml to real models
- [2026-03-13] **strategy**: Phase 2 starts with Knowledge Layer
