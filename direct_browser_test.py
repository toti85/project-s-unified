#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Browser Command Test
"""

import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.tools.implementations.ultra_optimized_browser_automation_tool import UltraOptimizedBrowserAutomationTool

async def test_direct_browser():
    """Test browser directly"""
    
    print("\n" + "="*80)
    print("DIRECT BROWSER TEST - No AI Layer")
    print("="*80)
    print()
    
    try:
        browser = UltraOptimizedBrowserAutomationTool()
        print("[OK] Browser tool initialized")
        print()
        
        # Test 1: Fetch Wikipedia
        print("[TEST 1] Fetch Wikipedia Python Page")
        print("-" * 80)
        task1 = "Go to https://en.wikipedia.org/wiki/Python_(programming_language) and extract the main heading and first paragraph"
        print(f"Task: {task1}")
        print()
        
        try:
            result = await browser.execute(task=task1)
            print(f"✅ Success!")
            print(f"Result type: {type(result)}")
            print(f"Result: {str(result)[:800]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
        print("="*80)
        print()
        
        # Test 2: Simple web task
        print("[TEST 2] Simple Web Task")
        print("-" * 80)
        task2 = "Open GitHub website and take a screenshot of the trending page"
        print(f"Task: {task2}")
        print()
        
        try:
            result2 = await browser.execute(task=task2, max_steps=3)
            print(f"✅ Success!")
            print(f"Result: {str(result2)[:800]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
        print("="*80)
        print("BROWSER DIRECT TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"Failed to initialize browser: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_direct_browser())
