# AO5_T13 Parallel CWI Symbol Hunt

Generated: 2026-06-10 14:29:52

> Correction: legacy paths moved during disk cleanup were resolved under `C:\_cleanup_quarantine\audit_forks_20260609`. The quarantine was read only.

## Scan Scope Status
- OK (relocated to quarantine): requested `C:\1225\project_s_super_core`; scanned `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core`
- OK: requested `C:\Users\Admin\project_s_super_core`; scanned `C:\Users\Admin\project_s_super_core`
- OK: requested `C:\ProjectS\project-s-code`; scanned `C:\ProjectS\project-s-code`
- OK: requested `C:\ProjectS-Snapshot-Staging`; scanned `C:\ProjectS-Snapshot-Staging`
- OK (relocated to quarantine): requested `C:\project-s-clean`; scanned `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean`
- OK (relocated to quarantine): requested `C:\0703\v2_architecture`; scanned `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture`
- OK (relocated to quarantine): requested `C:\0725\v2_architecture`; scanned `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture`

## 1. Summary Table (8 Missing Symbols)
| Symbol | Found? | Definition location(s) | Type | Definition size |
|---|---|---|---|---:|
| cognitive_registry | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:413; C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:413; C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:413; C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:413 (+4 more definitions) | instance/variable definition | 1, 1, 1, 1 lines |
| EnhancedCognitiveProcessor | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\enhanced_processor.py:44; C:\Users\Admin\project_s_super_core\src\core\cognitive\enhanced_processor.py:44; C:\ProjectS\project-s-code\src\core\cognitive\enhanced_processor.py:44; C:\ProjectS-Snapshot-Staging\src\core\cognitive\enhanced_processor.py:44 (+4 more definitions) | class definition | 750, 750, 750, 750 lines |
| AdvancedIntentAnalyzer | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\advanced_analyzer.py:50; C:\Users\Admin\project_s_super_core\src\core\cognitive\advanced_analyzer.py:50; C:\ProjectS\project-s-code\src\core\cognitive\advanced_analyzer.py:50; C:\ProjectS-Snapshot-Staging\src\core\cognitive\advanced_analyzer.py:50 (+4 more definitions) | class definition | 589, 589, 589, 589 lines |
| SemanticReasoningEngine | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\semantic_reasoning.py:90; C:\Users\Admin\project_s_super_core\src\core\cognitive\semantic_reasoning.py:90; C:\ProjectS\project-s-code\src\core\cognitive\semantic_reasoning.py:90; C:\ProjectS-Snapshot-Staging\src\core\cognitive\semantic_reasoning.py:90 (+4 more definitions) | class definition | 816, 816, 816, 816 lines |
| CognitiveContext | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:54; C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:54; C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:54; C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:54 (+4 more definitions) | class definition | 14, 14, 14, 14 lines |
| CognitiveResult | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:97; C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:97; C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:97; C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:97 (+4 more definitions) | class definition | 12, 12, 12, 12 lines |
| IntentMatch | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:68; C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:68; C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:68; C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:68 (+4 more definitions) | class definition | 18, 18, 18, 18 lines |
| TaskDecomposition | yes | C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:86; C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:86; C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:86; C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:86 (+4 more definitions) | class definition | 11, 11, 11, 11 lines |

## 2. Per-Symbol Detail
### cognitive_registry
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-22 23:27:51
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\base_cognitive.py:413` | instance/variable definition | approx. 1 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `cognitive_registry = CognitiveRegistry()`
- Additional reference hits: 102
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:413`

### EnhancedCognitiveProcessor
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-22 23:27:51
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\enhanced_processor.py:44` | class definition | approx. 750 lines | file 795 lines | mtime 2025-07-01 00:32:15
  - `class EnhancedCognitiveProcessor(BaseCognitiveProcessor):`
- Additional reference hits: 24
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\enhanced_processor.py:44`

### AdvancedIntentAnalyzer
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-22 23:27:51
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\advanced_analyzer.py:50` | class definition | approx. 589 lines | file 641 lines | mtime 2025-07-01 00:32:15
  - `class AdvancedIntentAnalyzer(BaseIntentAnalyzer):`
- Additional reference hits: 24
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\advanced_analyzer.py:50`

### SemanticReasoningEngine
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-22 23:27:51
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\semantic_reasoning.py:90` | class definition | approx. 816 lines | file 908 lines | mtime 2025-07-01 00:32:15
  - `class SemanticReasoningEngine(BaseReasoningEngine):`
- Additional reference hits: 24
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\semantic_reasoning.py:90`

### CognitiveContext
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-22 23:27:51
  - `class CognitiveContext:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\base_cognitive.py:54` | class definition | approx. 14 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveContext:`
- Additional reference hits: 272
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:54`

### CognitiveResult
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-22 23:27:51
  - `class CognitiveResult:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\base_cognitive.py:97` | class definition | approx. 12 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class CognitiveResult:`
- Additional reference hits: 56
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:97`

### IntentMatch
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-22 23:27:51
  - `class IntentMatch:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\base_cognitive.py:68` | class definition | approx. 18 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class IntentMatch:`
- Additional reference hits: 88
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:68`

### TaskDecomposition
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Definition: `C:\Users\Admin\project_s_super_core\src\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Definition: `C:\ProjectS\project-s-code\src\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Definition: `C:\ProjectS-Snapshot-Staging\src\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-22 23:27:51
  - `class TaskDecomposition:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Definition: `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture\project-s-clean\core\cognitive\base_cognitive.py:86` | class definition | approx. 11 lines | file 413 lines | mtime 2025-07-01 00:32:14
  - `class TaskDecomposition:`
- Additional reference hits: 64
- Best source: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:86`

## 3. Best-Source Recommendation
- **cognitive_registry**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:413` (instance/variable definition, approx. 1 definition lines)
- **EnhancedCognitiveProcessor**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\enhanced_processor.py:44` (class definition, approx. 750 definition lines)
- **AdvancedIntentAnalyzer**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\advanced_analyzer.py:50` (class definition, approx. 589 definition lines)
- **SemanticReasoningEngine**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\semantic_reasoning.py:90` (class definition, approx. 816 definition lines)
- **CognitiveContext**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:54` (class definition, approx. 14 definition lines)
- **CognitiveResult**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:97` (class definition, approx. 12 definition lines)
- **IntentMatch**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:68` (class definition, approx. 18 definition lines)
- **TaskDecomposition**: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core\src\core\cognitive\base_cognitive.py:86` (class definition, approx. 11 definition lines)

### Recommended source module set
- Primary codebase: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core`
- `src/core/cognitive/base_cognitive.py`: registry and shared data models/base contracts.
- `src/core/cognitive/enhanced_processor.py`: EnhancedCognitiveProcessor.
- `src/core/cognitive/advanced_analyzer.py`: AdvancedIntentAnalyzer.
- `src/core/cognitive/semantic_reasoning.py`: SemanticReasoningEngine.
- `src/core/cognitive/__init__.py`: expected public re-export surface.

## 4. Reconstruction Feasibility Verdict
- A. Symbols found: **8/8**; concrete definitions found: **8/8**.
- B. All 8 occur together: **YES** in `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core`.
- C. Most likely original codebase: `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core` (8/8 concrete symbols).
- D. Reconstruction feasibility: **SIMPLE**.
- E. Dependency risk: **MEDIUM-HIGH**. The symbols span four implementation modules plus package exports; copying one file is insufficient, and module-level singleton registration can create import-order/circular-import risk.
- Recommended next action: compare the legacy `src/core/cognitive/__init__.py` and four implementation modules against Unified, then restore only the missing export contract with guarded import smoke tests.
- Files modified outside Unified: **NO**.

## Codebases With Hits
- `C:\ProjectS-Snapshot-Staging`: 8/8 concrete definitions
- `C:\ProjectS\project-s-code`: 8/8 concrete definitions
- `C:\Users\Admin\project_s_super_core`: 8/8 concrete definitions
- `C:\_cleanup_quarantine\audit_forks_20260609\0703\v2_architecture`: 8/8 concrete definitions
- `C:\_cleanup_quarantine\audit_forks_20260609\0725\v2_architecture`: 8/8 concrete definitions
- `C:\_cleanup_quarantine\audit_forks_20260609\1225\project_s_super_core`: 8/8 concrete definitions
- `C:\_cleanup_quarantine\audit_forks_20260609\project-s-clean`: 8/8 concrete definitions
