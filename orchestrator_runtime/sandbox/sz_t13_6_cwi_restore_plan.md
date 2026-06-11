# AO5_T13.6 CWI Restore Plan

Generated: 2026-06-10

Mode: planning only. No source files copied or modified. Legacy source was read only.

## Executive Verdict

The initial expectation that four of five cognitive files were missing is incorrect. All five files already exist in Unified and are byte-for-byte identical to the selected legacy source. The CWI failure is an export-surface defect: `src/core/cognitive/__init__.py` exports only `CognitiveCore`, while `cognitive_workflow_integration.py` imports eight additional names from the package.

Recommended strategy: **COPY_WITH_SHIM**, specifically an export-only variant. Do not copy the four implementation files because they are already present and identical. Replace or extend only the package export shim in a later implementation mission, with controlled import order and smoke tests.

## 1. Current vs Legacy Diff

Legacy root: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive`

Current root: `C:\ProjectS-Unified\src\core\cognitive`

| File | Unified exists? | Legacy lines | Current lines | Delta | Class delta | Function delta | SHA-256 identical? | Verdict |
|---|:---:|---:|---:|---:|---|---|:---:|---|
| `base_cognitive.py` | yes | 413 | 413 | 0 | none | none | yes | Already restored; no copy needed |
| `enhanced_processor.py` | yes | 795 | 795 | 0 | none | none | yes | Already restored; no copy needed |
| `advanced_analyzer.py` | yes | 641 | 641 | 0 | none | none | yes | Already restored; no copy needed |
| `semantic_reasoning.py` | yes | 908 | 908 | 0 | none | none | yes | Already restored; no copy needed |
| `__init__.py` | yes | 11 | 11 | 0 | none | none | yes | Identical legacy export defect |

Files compared: **5/5**. Files missing in Unified: **0**.

### Structural finding

The implementations and required symbols are already in Unified:

- `base_cognitive.py`: `cognitive_registry`, `CognitiveContext`, `CognitiveResult`, `IntentMatch`, `TaskDecomposition`.
- `enhanced_processor.py`: `EnhancedCognitiveProcessor`.
- `advanced_analyzer.py`: `AdvancedIntentAnalyzer`.
- `semantic_reasoning.py`: `SemanticReasoningEngine`.

The current and legacy `__init__.py` both contain only a guarded import of `CognitiveCore` and `__all__ = ["CognitiveCore"]`. Therefore, copying legacy files verbatim would reproduce the same failure.

## 2. Singleton and Circular Import Audit

### Singleton execution

`base_cognitive.py:413` executes the following at module level:

```python
cognitive_registry = CognitiveRegistry()
```

This is an import-time singleton. Python normally initializes it once per module object in `sys.modules`, but duplicate package identities or manual reloads can create a second registry.

The implementation modules also have import-time side effects:

- `enhanced_processor.py:794-795`: constructs `EnhancedCognitiveProcessor()` and registers it.
- `advanced_analyzer.py:639-641`: constructs `AdvancedIntentAnalyzer()` and registers it.
- `semantic_reasoning.py:906-908`: constructs `SemanticReasoningEngine()` and registers it.

Consequently, an export shim that imports these modules also initializes and populates the registry.

### Legacy modules importing `base_cognitive`

- `enhanced_processor.py` imports base classes, data models, priorities, and `cognitive_registry`.
- `advanced_analyzer.py` imports analyzer contracts/data models and later `cognitive_registry`.
- `semantic_reasoning.py` imports reasoning contracts/data models and later `cognitive_registry`.

### Import graph

```text
core.cognitive.__init__ -> cognitive_core
core.cognitive_workflow_integration -> core.cognitive package
 enhanced_processor -> base_cognitive
 advanced_analyzer -> base_cognitive
 semantic_reasoning -> base_cognitive
```

AST graph analysis found **no direct A -> B -> A cycle** in the legacy cognitive package.

A controlled shim can safely use this order:

1. Import shared models and registry from `base_cognitive`.
2. Import the three implementation classes/modules so their registration side effects run.
3. Import `CognitiveCore` independently.
4. Publish the deliberate `__all__` list.

### Hidden dependency exposure

`semantic_reasoning.py` imports:

- `numpy`
- `scipy.spatial.distance`
- `sentence_transformers`
- `torch`

Eagerly importing it from package `__init__.py` means every `import core.cognitive` requires this complete ML dependency stack. A missing or incompatible package could make the entire package import fail. The shim should either use guarded imports with explicit diagnostics or defer semantic-engine loading while preserving a clear failure mode for CWI.

### CognitiveCore relationship

`cognitive_core.py` defines the current `CognitiveCore`, and several active modules import it directly:

- `core.agent.agent_loop`
- `core.agent.agent_loop_backup`
- `core.super_intelligent_ai`

`cognitive_core.py` also creates `legacy_cognitive_core = CognitiveCore()` at module level. This is a separate singleton from `cognitive_registry`; it does not form an observed circular import with the four legacy cognitive modules, but both systems coexist and must not be conflated.

## 3. Restore Strategy

### Recommendation: COPY_WITH_SHIM

Use the **COPY_WITH_SHIM** strategy in an export-only form:

- Copy **zero** implementation files; all four are already byte-identical.
- Modify only `src/core/cognitive/__init__.py` in the implementation mission.
- Preserve `CognitiveCore` as the current canonical agent-facing core.
- Add the eight CWI-required package exports without renaming or merging the two cognitive abstractions.

STRAIGHT_COPY is rejected because legacy `__init__.py` has the same incomplete export surface. MERGE_LEGACY_AND_CURRENT is unnecessary because there is no implementation divergence to reconcile. ABORT is not warranted because no direct cycle was detected.

### Concrete implementation steps for the next mission

1. Snapshot the current import behavior with a failing smoke test for all eight names.
2. Update only `src/core/cognitive/__init__.py`.
3. Import shared symbols first from `.base_cognitive`.
4. Import `EnhancedCognitiveProcessor` from `.enhanced_processor`.
5. Import `AdvancedIntentAnalyzer` from `.advanced_analyzer`.
6. Import `SemanticReasoningEngine` from `.semantic_reasoning`, with a deliberate policy for optional ML dependency failures.
7. Preserve the existing `.cognitive_core import CognitiveCore` path.
8. Define an explicit `__all__` containing `CognitiveCore` plus the eight CWI names.
9. Run isolated package-import and CWI-import smoke tests in a fresh Python process.
10. Assert that registry component IDs are present exactly once after import.
11. Run focused tests for agent-loop `CognitiveCore` imports to ensure no regression.
12. Do not merge `CognitiveCore` and the registry-based processor architecture in this mission.

## 4. Risk Table

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Singleton double-init | Medium | High | Use one canonical package path; avoid reloads; assert registry IDs and object identity in smoke tests |
| Duplicate component registration | Medium | Medium | Import in deterministic order; verify one processor/analyzer/engine per expected ID |
| Circular import | Low | High | Keep `base_cognitive` dependency-free from implementation modules; package shim imports base before implementations |
| Conflict with current `CognitiveCore` | Medium | High | Preserve `CognitiveCore` unchanged; treat registry architecture as a parallel compatibility surface |
| Hidden dependency on missing ML modules | High | High | Preflight `numpy`, `scipy`, `sentence_transformers`, and `torch`; use guarded semantic import with actionable diagnostics |
| Package-wide failure from eager import | Medium | High | Decide between guarded import and lazy export; test clean interpreter import paths |
| Legacy `print` warning hides failure | Medium | Medium | Replace broad print-and-empty-`__all__` behavior with explicit logging/diagnostics in the new shim |
| Import-order-dependent empty registry | Medium | High | Ensure implementation modules load before CWI reads registry; assert expected registered IDs |
| Two singleton systems misunderstood as one | Medium | Medium | Document `legacy_cognitive_core` and `cognitive_registry` as separate objects with separate responsibilities |
| Tests absent around legacy package exports | High | Medium | Add focused import/export and registry-population tests before broader integration tests |

## 5. Direct Answers

A. Files compared (5/5)? **YES**.

B. Files missing in Unified: **0**. List: none.

C. Singleton risk confirmed? **YES**. Registry and three component instances are created at module import time; `cognitive_core.py` also creates a separate core singleton.

D. Circular import detected? **NO** direct cycle was found by AST import-graph analysis.

E. Recommended restore strategy: **COPY_WITH_SHIM** (export-only; no implementation copies).

F. Concrete next mission: modify only `src/core/cognitive/__init__.py` to expose the eight existing symbols in deterministic order, then run fresh-process import, registry-identity, and CWI smoke tests.

G. Estimated total effort: **2-4 hours**, including dependency preflight, shim implementation, focused tests, and one regression pass.

Files modified outside Unified or in `src/`: **NO**.
