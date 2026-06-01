"""
Quick task test - fallback path only (no API key needed)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.tools.implementations.simple_browser_tool import SimpleBrowserTool


async def test_task_browser_only():
    """Test browser tool directly - fallback path"""
    
    print("\n" + "="*80)
    print("QUICK TEST: Browser Tool (Fallback Path)")
    print("="*80)
    
    tool = SimpleBrowserTool()
    
    print("\nTest 1: example.com")
    result = await tool.execute("https://example.com", use_browser=False)  # Force fallback
    
    print(f"  URL: {result['url']}")
    print(f"  OK: {result['ok']}")
    print(f"  Status: {result['status_code']}")
    print(f"  Title: {result['title']}")
    print(f"  Content length: {len(result['extracted']) if result['extracted'] else 0}")
    
    assert result['ok'] == True
    assert result['status_code'] == 200
    assert result['title'] == "Example Domain"
    assert result['extracted'] and len(result['extracted']) > 0
    
    print("  ✅ PASS")
    
    print("\nTest 2: httpbin.org")
    result = await tool.execute("https://httpbin.org/html", use_browser=False)  # Force fallback
    
    print(f"  URL: {result['url']}")
    print(f"  OK: {result['ok']}")
    print(f"  Status: {result['status_code']}")
    print(f"  Title: {result['title']}")
    print(f"  Content length: {len(result['extracted']) if result['extracted'] else 0}")
    
    assert result['ok'] == True
    assert result['status_code'] == 200
    assert result['extracted'] and len(result['extracted']) > 0
    
    print("  ✅ PASS")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_task_browser_only())
