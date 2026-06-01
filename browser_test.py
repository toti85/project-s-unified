#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Automation Test - Web Content Retrieval
"""

import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI

async def test_browser():
    """Test browser automation capabilities"""
    
    print("\n" + "="*80)
    print("BROWSER AUTOMATION TEST")
    print("="*80)
    print()
    
    ai = SuperIntelligentAI()
    print("[OK] SuperIntelligentAI ready")
    print()
    
    # Test 1: Visit a website and extract data
    task1 = """
    Use browser to visit https://www.wikipedia.org/wiki/Python_(programming_language)
    
    Extract:
    1. Main heading (title)
    2. First paragraph about Python
    3. Year Python was created
    4. Creator name
    
    Return as formatted text summary.
    """
    
    print("[TEST 1] Website Content Extraction - Wikipedia Python")
    print("-" * 80)
    print(task1)
    print("-" * 80)
    print()
    
    try:
        result1 = await ai.execute_intelligent_task(task=task1)
        print("[RESULT 1]:")
        if isinstance(result1, dict) and 'output' in result1:
            print(result1['output'])
        else:
            print(str(result1)[:500])
    except Exception as e:
        print(f"Error: {str(e)[:200]}")
    
    print("\n" + "="*80)
    print()
    
    # Test 2: Search and retrieve info
    task2 = """
    Use browser to search for "Python machine learning libraries" on Google.
    
    Extract the top 3 results:
    - Page title
    - URL
    - Brief description
    
    Return as formatted list.
    """
    
    print("[TEST 2] Google Search - Machine Learning Libraries")
    print("-" * 80)
    print(task2)
    print("-" * 80)
    print()
    
    try:
        result2 = await ai.execute_intelligent_task(task=task2)
        print("[RESULT 2]:")
        if isinstance(result2, dict) and 'output' in result2:
            print(result2['output'])
        else:
            print(str(result2)[:500])
    except Exception as e:
        print(f"Error: {str(e)[:200]}")
    
    print("\n" + "="*80)
    print("BROWSER TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_browser())
