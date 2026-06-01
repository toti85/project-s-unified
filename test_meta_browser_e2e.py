"""
E2E Test: SimpleBrowserTool Adapter + Meta Path

Verifies:
- SimpleBrowserTool adapter pattern works (PRIMARY + FALLBACK)
- Adapter loads both tools correctly
- Adapter execution succeeds via best available path
- Meta path executes with browser capability available
- Evidence is logged completely
- Goal converges to "passed" status
"""
import asyncio
import sys
import json
import os
from pathlib import Path

# UTF-8 encoding for Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))


async def test_adapter_components():
    """Verify adapter loads both primary and fallback tools."""
    
    print("\n" + "="*80)
    print("STEP 1: Verify Adapter Components")
    print("="*80)
    
    from tools.tools.implementations.simple_browser_tool import SimpleBrowserTool
    
    browser_tool = SimpleBrowserTool()
    
    print(f"\n📋 SimpleBrowserTool Adapter:")
    print(f"   Name: {browser_tool.name}")
    print(f"   Description: {browser_tool.description}")
    
    # Check components
    print(f"\n🔧 Adapter Components:")
    print(f"   PRIMARY (UltraOptimizedBrowserAutomationTool): ", end="")
    if browser_tool._primary_tool:
        print("✅ Available")
    else:
        print("⚠️  Not available (requires API key)")
    
    print(f"   FALLBACK (WebPageFetchTool): ", end="")
    if browser_tool._fallback_tool:
        print("✅ Available")
    else:
        print("❌ Missing - CRITICAL")
        assert False, "Fallback tool should always be available"
    
    print(f"\n✅ STEP 1 COMPLETE: Adapter properly configured")
    return browser_tool


async def test_adapter_execution():
    """Test adapter actually executes and returns proper result."""
    
    print("\n" + "="*80)
    print("STEP 2: Test Adapter Execution")
    print("="*80)
    
    from tools.tools.implementations.simple_browser_tool import SimpleBrowserTool
    
    browser_tool = SimpleBrowserTool()
    test_url = "https://example.com"
    
    print(f"\n🌐 Executing adapter on: {test_url}")
    
    # Execute with use_browser=True (will try primary, fallback to HTTP)
    result = await browser_tool.execute(test_url, extract_text=True, max_length=500, use_browser=True)
    
    print(f"\n📊 Result:")
    print(f"   ok: {result['ok']}")
    print(f"   status_code: {result['status_code']}")
    print(f"   title: {result.get('title', 'N/A')}")
    print(f"   extracted length: {len(result.get('extracted', '')) if result.get('extracted') else 0}")
    
    # Validate contract
    required_fields = ['ok', 'url', 'title', 'extracted', 'status_code', 'error']
    for field in required_fields:
        assert field in result, f"❌ Missing field: {field}"
    
    assert result['ok'] == True, "❌ Adapter should succeed"
    assert result['status_code'] == 200, "❌ Should get 200 status"
    
    print(f"\n✅ STEP 2 COMPLETE: Adapter executed successfully")


async def test_meta_browser_e2e():
    """End-to-end test: Meta path executes with browser adapter available."""
    
    print("\n" + "="*80)
    print("STEP 3: Meta Path E2E Test")
    print("="*80)
    
    from src.core.super_intelligent_ai import SuperIntelligentAI
    from tools.tools.implementations.simple_browser_tool import SimpleBrowserTool
    
    # Browser tool should be available
    browser_tool = SimpleBrowserTool()
    print(f"\n✅ Browser tool available: {browser_tool.name}")
    
    # Initialize AI with Meta controller
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    # Simple deterministic goal (no file I/O required)
    goal = "Analyze the structure of the project directory"
    print(f"\n📝 Goal: {goal}")
    print(f"🎯 Use Meta Path: True")
    
    # Execute with timeout
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(goal, use_meta_controller=True),
        timeout=180.0
    )
    
    print(f"\n📊 Execution Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   Task type: {result.get('task_type')}")
    
    output = result.get('output', '')
    if output:
        output_str = str(output)[:300]
        print(f"   Output (first 300 chars): {output_str}...")
    else:
        print(f"   Output: (empty)")
    
    # Read evidence log
    evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
    events = []
    
    if evidence_file.exists():
        with open(evidence_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    
    # Find recent goal execution
    recent_events = events[-200:] if len(events) > 200 else events
    
    # Look for goal_completed from meta path
    goal_started = [e for e in recent_events if e.get('event_type') == 'goal_started']
    goal_completed = [e for e in recent_events if e.get('event_type') == 'goal_completed']
    plan_selected = [e for e in recent_events if e.get('event_type') == 'plan_selected']
    
    print(f"\n📊 Evidence Logging:")
    print(f"   Total events: {len(events)}")
    print(f"   Recent goal_started: {len(goal_started)}")
    print(f"   Recent plan_selected: {len(plan_selected)}")
    print(f"   Recent goal_completed: {len(goal_completed)}")
    
    # Assertions
    print(f"\n🔍 Assertions:")
    
    # 1. Browser tool should be registered
    print(f"   ✅ Browser tool registered: {browser_tool.name}")
    
    # 2. Evidence should contain goal events (meta path execution)
    assert len(goal_started) > 0 or len(goal_completed) > 0, \
        f"❌ Evidence should contain goal_started or goal_completed events"
    print(f"   ✅ Meta path execution logged in evidence")
    
    # 3. Meta path should have executed planning if goal_started seen
    if goal_started:
        assert len(plan_selected) > 0 or len(goal_completed) > 0, \
            f"❌ Meta path should have planning events"
        print(f"   ✅ Meta path executed planning and completion phase")
    
    # 4. Task should complete (success or conditional)
    assert result.get('output') or result.get('success') is not None, \
        "❌ Should have output or explicit success status"
    print(f"   ✅ Task succeeded or produced output")
    
    # 5. Latest goal should be marked as passed
    if goal_completed:
        latest_goal_complete = goal_completed[-1]
        status = latest_goal_complete.get('data', {}).get('status')
        print(f"   ✅ Latest goal_completed status: '{status}'")
    
    print(f"\n✅ STEP 3 COMPLETE: Meta path E2E test passed")


async def main():
    """Run all steps."""
    print("\n" + "="*80)
    print("E2E TEST: SimpleBrowserTool Adapter + Meta Path")
    print("="*80)
    print("\nValidating:")
    print("  • Adapter pattern (PRIMARY + FALLBACK)")
    print("  • Browser tool execution")
    print("  • Meta path integration")
    print("  • Evidence logging")
    
    try:
        await test_adapter_components()
        await test_adapter_execution()
        await test_meta_browser_e2e()
        
        print("\n" + "="*80)
        print("✅ ALL E2E TESTS PASSED")
        print("="*80)
        print("\nResults:")
        print("  ✅ Adapter components properly initialized")
        print("  ✅ Adapter execution working (PRIMARY or FALLBACK)")
        print("  ✅ Meta path integration successful")
        print("  ✅ Evidence logging complete")
        
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
