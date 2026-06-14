# T29 Clean Cognitive_Core Hunt on DEV — UPDATED FINDINGS

Generated: 2026-06-14T01:08:00+03:00
Search scope: C:\ (entire drive, with exclusions)

## KEY DISCOVERY: The "Missing Orchestrator" is cognitive_core_langgraph.py

The architecture is NOT 4 classes in one file. The architecture is **modular**:

- `core/infrastructure/event_bus.py` → EventBus (separate file)
- `core/infrastructure/error_handler.py` → ErrorHandler (separate file)
- `core/cognitive/cognitive_core.py` → CognitiveCore (separate file, imports event_bus + error_handler)

The legacy machine's 1,032-line "clean" cognitive_core.py was a one-time merge experiment on 2025-07-22.

---

## A. CONFIRMED Clean Cognitive_Core (1000+ lines, 4 classes in one file, stdlib)

**Found: 0 candidates**

No files match the T27 signature. The 4-class-in-one-file architecture does not exist on this machine.

---

## B. cognitive_core_langgraph.py — THE REAL "Missing Orchestrator"

**80+ files found in quarantine. NOT present in ProjectS-Unified.**

| Path | Lines | Size | Modified | Classes |
|------|-------|------|----------|---------|
| `C:\_cleanup_quarantine\...\project-s-agent-main\core\cognitive_core_langgraph.py` | **1118** | 48,893 B | 2025-06-24 | 7 classes |
| `C:\_cleanup_quarantine\...\project_s_agent0603\core\cognitive_core_langgraph.py` | 1091 | 48,872 B | 2025-06-19 | 7 classes |
| `C:\_cleanup_quarantine\...\project-s-cognitive-working\core\cognitive_core_langgraph.py` | 954 | 41,599 B | 2025-05-30 | 7 classes |
| `C:\_cleanup_quarantine\...\project_s_stable\core\cognitive_core_langgraph.py` | 954 | 41,565 B | 2025-05-20 | 7 classes |
| `C:\_cleanup_quarantine\...\0614\project_s_agent0603\core\cognitive_core_langgraph.py` | 273 | 11,928 B | 2025-06-16 | partial |

### Classes in 1118-line variant (largest):
- Line 29: `class PathSerializationMixin`
- Line 54: `class Memory(BaseModel, PathSerializationMixin)`
- Line 59: `class Task(BaseModel, PathSerializationMixin)`
- Line 68: `class CognitiveGraphState(BaseModel, PathSerializationMixin)`
- Line 82: `class CognitiveCoreGraph`
- Line 743: `class CognitiveCoreWithLangGraph`
- Line 1104: `class CognitiveCoreWorkflow`

### Imports (first 50 lines):
```python
import logging
import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Set, Tuple, Union, Callable
from datetime import datetime
from pathlib import Path, WindowsPath, PosixPath
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from core.event_bus import event_bus
from core.central_executor import executor
from core.error_handler import error_handler
from core.ai_command_handler import AICommandHandler
from core.multi_model_integration import multi_model_manager
from utils.performance_monitor import monitor_performance
from integrations.langgraph_integration import langgraph_integrator, GraphState
from integrations.langgraph_state_manager import state_manager
from integrations.langgraph_state_enhanced import create_state_linked_workflow
```

**This is a LangGraph-based orchestrator with Pydantic models — a completely different architecture from the simple 704-line cognitive_core.py in Unified.**

---

## C. What EXISTS in ProjectS-Unified

### src/core/infrastructure/
| File | Size | Modified |
|------|------|----------|
| event_bus.py | 3,646 B | 2025-07-01 |
| error_handler.py | 4,586 B | 2025-07-01 |
| execution_events.py | 3,455 B | 2025-12-25 |
| __init__.py | 0 B | 2025-06-29 |

### src/core/cognitive/
| File | Size | Modified |
|------|------|----------|
| cognitive_core.py | 27,855 B (704 lines) | 2025-07-22 |

### MISSING from Unified:
- ❌ `cognitive_core_langgraph.py` — The live LangGraph orchestrator from 2025 summer/fall
- ❌ `ai_command_handler.py` — Referenced by langgraph variant
- ❌ `multi_model_integration.py` — Referenced by langgraph variant
- ❌ `langgraph_integration.py` — Referenced by langgraph variant
- ❌ `langgraph_state_manager.py` — Referenced by langgraph variant
- ❌ `langgraph_state_enhanced.py` — Referenced by langgraph variant

---

## D. Other Cognitive_Core Variants (cognitive_core.py)

| Path | Lines | Size | Modified | Classes | Notes |
|------|-------|------|----------|---------|-------|
| `C:\ProjectS-Unified\src\core\cognitive\cognitive_core.py` | 704 | 27,855 B | 2025-07-22 | CognitiveCore | Current Unified |
| `C:\ProjectS\project-s-code\src\core\cognitive\cognitive_core.py` | 704 | 27,855 B | 2025-07-22 | CognitiveCore | Legacy install |
| `C:\v2_architecture\core\cognitive\cognitive_core.py` | 704 | 27,855 B | 2025-07-04 | CognitiveCore | v2 root |
| `C:\S1\project-s-agent\core\cognitive_core.py` | 198 | 6,857 B | 2025-05-13 | CognitiveCore | Minimal stub |

---

## E. Event Bus / ErrorHandler Files (separate module architecture)

Found 150+ event_bus.py and 140+ error_handler.py files across the DEV machine. All are identical copies of the same modular infrastructure files.

---

## Conclusion

**The "missing orchestrator" is NOT the 1,032-line clean cognitive_core.py from the legacy machine.**

**The "missing orchestrator" is cognitive_core_langgraph.py (1118 lines, 7 classes) — a LangGraph-based orchestrator that was the live system in 2025 summer/fall but was NOT included in the Unified merge.**

The Unified merge included the simpler 704-line cognitive_core.py instead of the richer 1118-line cognitive_core_langgraph.py.

The T16-T22 series may have partially rebuilt this functionality (CWI integration), but the original LangGraph orchestrator code is not in Unified.

### Recommended Next Steps:
1. **T30**: Side-by-side comparison of cognitive_core_langgraph.py (1118 lines) vs current Unified cognitive_core.py (704 lines)
2. **T30**: Identify which LangGraph classes/functionality were NOT carried into Unified
3. **T30**: Determine if T16-T22 CWI integration already rebuilt equivalent functionality
4. **Archive**: Copy cognitive_core_langgraph.py to external_archives for safekeeping