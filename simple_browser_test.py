#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Browser Tool Test - No Ultra-Optimized
"""

import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.tools.implementations.web_tools import WebPageFetchTool

async def test_simple_browser():
    """Test simple browser tool"""
    
    print("\n" + "="*80)
    print("SIMPLE BROWSER TEST - WebPageFetchTool")
    print("="*80)
    print()
    
    try:
        browser = WebPageFetchTool()
        print("[OK] WebPageFetchTool initialized")
        print()
        
        # Test 1: Fetch Wikipedia
        print("[TEST 1] Fetch Wikipedia Python Page")
        print("-" * 80)
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        print(f"URL: {url}")
        print()
        
        try:
            result = await browser.execute(url=url)
            print(f"✅ Success!")
            print(f"Result type: {type(result)}")
            if isinstance(result, dict) and 'content' in result:
                content = result['content']
            else:
                content = str(result)
            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:600]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")
        
        print()
        print("="*80)
        print()
        
        # Test 2: Fetch GitHub
        print("[TEST 2] Fetch GitHub Trending")
        print("-" * 80)
        url2 = "https://github.com/trending"
        print(f"URL: {url2}")
        print()
        
        try:
            result2 = await browser.execute(url=url2)
            print(f"✅ Success!")
            print(f"Result type: {type(result2)}")
            if isinstance(result2, dict) and 'content' in result2:
                content2 = result2['content']
            else:
                content2 = str(result2)
            print(f"Content length: {len(content2)}")
            print(f"Content preview: {content2[:600]}...")
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")
        
        print()
        print("="*80)
        print("SIMPLE BROWSER TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"Failed to initialize browser: {str(e)[:200]}")

if __name__ == "__main__":
    asyncio.run(test_simple_browser())
