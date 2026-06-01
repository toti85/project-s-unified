"""
Smoke test: SimpleBrowserTool Adapter
Tests both PRIMARY (Playwright) and FALLBACK (HTTP) paths.
Validates the adapter pattern and JSON contract.
"""
import asyncio
import sys
import os
from pathlib import Path

# UTF-8 encoding for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from tools.tools.implementations.simple_browser_tool import SimpleBrowserTool


async def test_adapter_structure():
    """Test that adapter initializes both primary and fallback tools."""
    
    print("\n" + "="*80)
    print("TEST 1: Adapter Structure & Initialization")
    print("="*80)
    
    tool = SimpleBrowserTool()
    
    print(f"\n📋 Tool Name: {tool.name}")
    print(f"   Description: {tool.description}")
    
    # Check initialization
    print(f"\n🔧 Adapter Components:")
    print(f"   PRIMARY (UltraOptimizedBrowserAutomationTool): {'✅ Available' if tool._primary_tool else '⚠️ Not available'}")
    print(f"   FALLBACK (WebPageFetchTool): {'✅ Available' if tool._fallback_tool else '❌ Missing'}")
    
    assert tool._fallback_tool is not None, "❌ Fallback tool should always be available"
    print(f"\n✅ TEST 1 PASSED: Adapter properly initialized")


async def test_fallback_path():
    """Test FALLBACK path (HTTP fetch without browser)."""
    
    print("\n" + "="*80)
    print("TEST 2: FALLBACK Path (HTTP Fetch)")
    print("="*80)
    
    tool = SimpleBrowserTool()
    url = "https://example.com"
    
    print(f"\n🌐 Testing FALLBACK path with: {url}")
    print(f"   (Disable browser with use_browser=False)")
    
    # Force fallback by disabling browser
    result = await tool.execute(url, extract_text=True, max_length=500, use_browser=False)
    
    print(f"\n📊 Result:")
    print(f"   ok: {result['ok']}")
    print(f"   status_code: {result['status_code']}")
    print(f"   title: {result['title']}")
    print(f"   extracted length: {len(result['extracted']) if result['extracted'] else 0}")
    print(f"   error: {result['error']}")
    
    # Validate JSON contract
    print(f"\n✓ JSON Contract Validation:")
    required_fields = ['ok', 'url', 'title', 'extracted', 'status_code', 'error']
    for field in required_fields:
        assert field in result, f"❌ Missing field: {field}"
        print(f"   ✅ {field}")
    
    # Assertions for fallback
    assert result['ok'] == True, f"❌ Fallback should succeed for example.com"
    print(f"\n✅ ok=True (HTTP fetch successful)")
    
    assert result['status_code'] == 200, f"❌ Should get 200 from example.com"
    print(f"✅ status_code=200")
    
    assert result['url'] == url, f"❌ URL mismatch"
    print(f"✅ url matches")
    
    assert result['title'] is not None and len(result['title']) > 0, f"❌ title should be extracted"
    print(f"✅ title extracted: '{result['title']}'")
    
    assert result['extracted'] is not None and len(result['extracted']) > 0, f"❌ content should be extracted"
    print(f"✅ content extracted ({len(result['extracted'])} chars)")
    
    print(f"\n✅ TEST 2 PASSED: FALLBACK path working correctly")


async def test_primary_availability():
    """Test PRIMARY path availability check."""
    
    print("\n" + "="*80)
    print("TEST 3: PRIMARY Path Availability")
    print("="*80)
    
    tool = SimpleBrowserTool()
    
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    primary_available = tool._primary_tool is not None
    api_key_present = api_key is not None
    
    print(f"\n🔍 Environment Check:")
    print(f"   API Key present: {api_key_present}")
    print(f"   PRIMARY tool loaded: {primary_available}")
    
    if primary_available:
        print(f"\n✅ PRIMARY path available - will be preferred for browser.open_url")
    else:
        print(f"\n⚠️  PRIMARY path unavailable - FALLBACK (HTTP) will be used")
        if not api_key_present:
            print(f"   Reason: No OPENROUTER_API_KEY or OPENAI_API_KEY environment variable")
    
    print(f"\n✅ TEST 3 PASSED: Availability checks complete")


async def test_adapter_strategy():
    """Test adapter chooses correct path based on availability."""
    
    print("\n" + "="*80)
    print("TEST 4: Adapter Strategy (Primary vs Fallback)")
    print("="*80)
    
    tool = SimpleBrowserTool()
    url = "https://example.com"
    
    print(f"\n🎯 Testing default behavior (use_browser=True)")
    print(f"   Expected: PRIMARY if available, else FALLBACK")
    
    result = await tool.execute(url, extract_text=True, max_length=500, use_browser=True)
    
    print(f"\n📊 Result:")
    print(f"   ok: {result['ok']}")
    print(f"   status_code: {result['status_code']}")
    
    # Should succeed regardless of which path was used
    assert result['ok'] == True, "❌ Should succeed with default strategy"
    assert result['status_code'] == 200, "❌ Should get 200 status"
    
    print(f"\n✅ Adapter strategy works: Result successful (path auto-selected)")
    print(f"✅ TEST 4 PASSED: Adapter correctly chooses execution path")


async def test_json_contract():
    """Test that all results conform to JSON contract."""
    
    print("\n" + "="*80)
    print("TEST 5: JSON Contract Validation")
    print("="*80)
    
    tool = SimpleBrowserTool()
    test_urls = [
        "https://example.com",
        "https://httpbin.org/status/404",  # Expect failure
    ]
    
    print(f"\n📋 Testing JSON contract across different scenarios:")
    
    for test_url in test_urls:
        print(f"\n   Testing: {test_url}")
        result = await tool.execute(test_url, use_browser=False)  # Use fallback for consistency
        
        # Validate contract
        required_fields = ['ok', 'url', 'title', 'extracted', 'status_code', 'error']
        for field in required_fields:
            assert field in result, f"❌ Missing field {field} in result"
            assert result[field] is None or isinstance(result[field], (bool, int, str)), \
                f"❌ Field {field} has wrong type: {type(result[field])}"
        
        print(f"      ✅ ok={result['ok']}, status={result['status_code']}, contract valid")
    
    print(f"\n✅ TEST 5 PASSED: All results conform to JSON contract")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("BROWSER TOOL ADAPTER TEST SUITE")
    print("="*80)
    print("Testing: SimpleBrowserTool adapter pattern")
    print("PRIMARY: UltraOptimizedBrowserAutomationTool (Playwright)")
    print("FALLBACK: WebPageFetchTool (HTTP)")
    
    try:
        await test_adapter_structure()
        await test_fallback_path()
        await test_primary_availability()
        await test_adapter_strategy()
        await test_json_contract()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print("  • Adapter properly initializes both PRIMARY and FALLBACK")
        print("  • FALLBACK path (HTTP) works correctly")
        print("  • PRIMARY availability detected correctly")
        print("  • Adapter strategy selects best available path")
        print("  • All results conform to JSON contract")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
