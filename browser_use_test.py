#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser-Use Tool Test - Direct Execution
"""

import sys
import asyncio
from pathlib import Path
import os

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Suppress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def test_browser_use():
    """Test browser_use tool"""
    
    print("\n" + "="*80)
    print("BROWSER-USE TOOL TEST")
    print("="*80)
    print()
    
    # Import after path setup
    try:
        print("[1] Importing UltraOptimizedBrowserAutomationTool...")
        from tools.tools.implementations.ultra_optimized_browser_automation_tool import UltraOptimizedBrowserAutomationTool
        print("    ✅ Imported successfully")
        print()
    except Exception as e:
        print(f"    ❌ Import failed: {str(e)[:200]}")
        return
    
    # Initialize tool
    try:
        print("[2] Initializing tool (may take time due to Ollama)...")
        browser = UltraOptimizedBrowserAutomationTool()
        print("    ✅ Tool initialized")
        print()
    except Exception as e:
        print(f"    ❌ Initialization failed: {str(e)[:200]}")
        return
    
    # Test 1: Simple task
    print("[3] TEST 1 - Simple Google Search")
    print("-" * 80)
    task1 = "Go to Google and search for 'Python programming'"
    print(f"Task: {task1}")
    print()
    
    try:
        print("    Executing (timeout ~30s)...")
        result1 = await asyncio.wait_for(
            browser.execute(task=task1, max_steps=3, headless=True),
            timeout=35.0
        )
        print(f"    ✅ Success!")
        print(f"    Result: {str(result1)[:500]}...")
    except asyncio.TimeoutError:
        print("    ⏱️ Timeout (tool took too long)")
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:200]}")
    
    print()
    print("="*80)
    print()
    
    # Test 2: Another task
    print("[4] TEST 2 - Wikipedia Access")
    print("-" * 80)
    task2 = "Open Wikipedia and find the article about Python programming language"
    print(f"Task: {task2}")
    print()
    
    try:
        print("    Executing (timeout ~30s)...")
        result2 = await asyncio.wait_for(
            browser.execute(task=task2, max_steps=2, headless=True),
            timeout=35.0
        )
        print(f"    ✅ Success!")
        print(f"    Result: {str(result2)[:500]}...")
    except asyncio.TimeoutError:
        print("    ⏱️ Timeout (tool took too long)")
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:200]}")
    
    print()
    print("="*80)
    print("BROWSER-USE TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(test_browser_use())
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)[:300]}")
