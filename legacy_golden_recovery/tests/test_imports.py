#!/usr/bin/env python3
"""
legacy_golden_recovery/tests/test_imports.py

Teszteli, hogy a 4 Golden Age fájl importálható-e a jelenlegi workspaceben.
NEM módosít semmit — csak diagnosztika.

Futtatás:
  cd C:\ProjectS-Unified
  python legacy_golden_recovery\tests\test_imports.py
"""

import sys
import os
import traceback
from pathlib import Path

# Workspace gyökér beállítása
WORKSPACE_ROOT = Path(__file__).parent.parent.parent  # C:\ProjectS-Unified
LEGACY_ROOT = Path(__file__).parent.parent             # legacy_golden_recovery/
COMPONENTS_DIR = LEGACY_ROOT / "golden_components"

sys.path.insert(0, str(WORKSPACE_ROOT / "src"))
sys.path.insert(0, str(WORKSPACE_ROOT))

PASS = "PASS"
FAIL = "FAIL"

results = []

def test(name, stmt, expected_error=None):
    try:
        exec(stmt, {})
        results.append((PASS, name, None))
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        results.append((FAIL, name, err))


print("=" * 72)
print("GOLDEN AGE IMPORT COMPATIBILITY TEST")
print(f"Workspace: {WORKSPACE_ROOT}")
print("=" * 72)

# --- TEST 1: AIClient (meta_launcher_browser dependency) ---
test(
    "AIClient",
    "from src.integrations.ai_models.multi_model_ai_client import AIClient"
)

# --- TEST 2: ToolRegistry golden (meta_launcher_browser dependency) ---
test(
    "ToolRegistry_golden",
    "from tools.tools.registry.tool_registry_golden import ToolRegistry"
)

# --- TEST 3: FileWriteTool (meta_launcher_browser dependency) ---
test(
    "FileWriteTool",
    "from tools.tools.implementations.file_tools import FileWriteTool"
)

# --- TEST 4: BrowserAutomationTool (direkt, registry nélkül) ---
test(
    "BrowserAutomationTool (direct import)",
    "from tools.tools.implementations.browser_automation_tool import BrowserAutomationTool"
)

# --- TEST 5: langgraph (workflow_engine dependency) ---
test(
    "langgraph",
    "import langgraph"
)

# --- TEST 6: langgraph StateGraph (advanced_decision_router dependency) ---
test(
    "langgraph.graph.StateGraph",
    "from langgraph.graph import StateGraph, END"
)

# --- TEST 7: langgraph ToolNode ---
test(
    "langgraph.prebuilt.ToolNode",
    "from langgraph.prebuilt import ToolNode"
)

# --- TEST 8: playwright ---
test(
    "playwright.async_api",
    "from playwright.async_api import async_playwright"
)

# --- TEST 9: browser_use Agent ---
test(
    "browser_use Agent+BrowserSession",
    "from browser_use import Agent, BrowserSession"
)

# --- TEST 10: smart_orchestrator (golden_components, régi import útvonalakkal) ---
# Külön path-al, hogy ne befolyásolja a workspace importokat
test(
    "smart_orchestrator (old path: tools.file_tools)",
    "from tools.file_tools import FileReadTool"
)
test(
    "smart_orchestrator (old path: tools.web_tools)",
    "from tools.web_tools import WebPageFetchTool"
)

# --- TEST 11: advanced_decision_router belső függőségei ---
test(
    "core.event_bus (0603 internal)",
    "from core.event_bus import event_bus"
)
test(
    "core.error_handler (0603 internal)",
    "from core.error_handler import error_handler"
)
test(
    "integrations.langgraph_types (0603 internal)",
    "from integrations.langgraph_types import GraphState"
)
test(
    "integrations.decision_router (0603 internal)",
    "from integrations.decision_router import DecisionRouter"
)
test(
    "core.cognitive_core (0603 internal)",
    "from core.cognitive_core import cognitive_core"
)

# --- Eredmények kiírása ---
print()
passed = [r for r in results if r[0] == PASS]
failed = [r for r in results if r[0] == FAIL]

print(f"RESULTS: {len(passed)} PASS / {len(failed)} FAIL")
print()

for status, name, err in results:
    if status == PASS:
        print(f"  ✓ PASS  {name}")
    else:
        print(f"  ✗ FAIL  {name}")
        print(f"         → {err}")

print()
print("=" * 72)
print("IMPORT COMPATIBILITY SUMMARY")
print("=" * 72)

# Kritikus komponensek a meta_launcher_browser számára
meta_deps = ["AIClient", "ToolRegistry_golden", "FileWriteTool",
             "BrowserAutomationTool (direct import)", "playwright.async_api",
             "browser_use Agent+BrowserSession"]
meta_result = all(r[0] == PASS for r in results if r[1] in meta_deps)
print(f"meta_launcher_browser deps:    {'ALL PASS' if meta_result else 'PARTIAL FAIL'}")

# Golden Age core komponensek
golden_core_deps = ["langgraph", "langgraph.graph.StateGraph", "langgraph.prebuilt.ToolNode"]
golden_core_result = all(r[0] == PASS for r in results if r[1] in golden_core_deps)
print(f"Golden Age core (langgraph):   {'ALL PASS' if golden_core_result else 'PARTIAL FAIL'}")

# Régi 0603 belső függőségek
old_internal = ["core.event_bus (0603 internal)", "core.error_handler (0603 internal)",
                "integrations.langgraph_types (0603 internal)",
                "integrations.decision_router (0603 internal)",
                "core.cognitive_core (0603 internal)"]
old_result = all(r[0] == PASS for r in results if r[1] in old_internal)
print(f"0603 internal deps (adapter?): {'ALL PASS — no adapter needed' if old_result else 'FAIL — adapter required'}")

print()

# Exit code
sys.exit(0 if len(failed) == 0 else 1)
