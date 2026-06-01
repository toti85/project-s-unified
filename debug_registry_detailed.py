#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed registry debugging script
"""
import sys
import os
import traceback
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

print("[DEBUG] Starting detailed registry debug...")

# Test 1: Direct import of web tools
print("\n[TEST 1] Direct import of web tools...")
try:
    from tools.tools.implementations.web_tools import WebScraperTool, WebAnalyzerTool, WebPageFetchTool, WebApiCallTool, WebSearchTool
    print("[OK] Web tools imported successfully!")
    print(f"    - WebScraperTool: {WebScraperTool}")
    print(f"    - WebAnalyzerTool: {WebAnalyzerTool}")
    print(f"    - WebPageFetchTool: {WebPageFetchTool}")
    print(f"    - WebApiCallTool: {WebApiCallTool}")
    print(f"    - WebSearchTool: {WebSearchTool}")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    traceback.print_exc()

# Test 2: Instantiate web tools individually
print("\n[TEST 2] Instantiate WebApiCallTool individually...")
try:
    from tools.tools.implementations.web_tools import WebApiCallTool
    web_api = WebApiCallTool()
    print(f"[OK] WebApiCallTool instantiated: {web_api}")
    print(f"    - Name: {web_api.name}")
    print(f"    - Description: {web_api.description}")
except Exception as e:
    print(f"[ERROR] Instantiation failed: {e}")
    traceback.print_exc()

# Test 3: Now test the ToolRegistry
print("\n[TEST 3] Instantiate ToolRegistry...")
try:
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    registry = ToolRegistry()
    print(f"[OK] ToolRegistry instantiated")
    print(f"    - Total tools: {len(registry.tools)}")
    print(f"    - Tools list: {list(registry.tools.keys())}")
    print(f"    - Has web_api_call: {'web_api_call' in registry.tools}")
except Exception as e:
    print(f"[ERROR] Registry instantiation failed: {e}")
    traceback.print_exc()

# Test 4: Check the actual registry.tools dict details
print("\n[TEST 4] Registry tools detail...")
try:
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    registry = ToolRegistry()
    
    for name, tool in registry.tools.items():
        print(f"    - {name}: {type(tool).__name__}")
        
    print(f"\n[INFO] Total registered: {len(registry.tools)}")
except Exception as e:
    print(f"[ERROR] Failed to inspect tools: {e}")
    traceback.print_exc()

# Test 5: Check if logging is being captured
print("\n[TEST 5] Check logging output...")
try:
    import logging
    logger = logging.getLogger("tools.tools.registry.tool_registry_golden")
    logger.setLevel(logging.DEBUG)
    
    # Add a handler to see logs
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    print("[OK] Logging configured, now creating registry with logs visible...")
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    registry = ToolRegistry()
    print(f"[OK] Registry created, tools: {list(registry.tools.keys())}")
except Exception as e:
    print(f"[ERROR] Logging setup failed: {e}")
    traceback.print_exc()

print("\n[DEBUG] Detailed debug complete!")
