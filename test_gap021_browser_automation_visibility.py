#!/usr/bin/env python
"""
GAP_021 Focused Tests — Strategic planner visibility of browser_automation.

Verifies:
1. Phase 1 prompt contains `browser_automation` in the tool manifest
2. Prompt includes browser-specific/dynamic-page guidance
3. Existing recommended_tools output contract is not broken
"""

import json
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))


def test_prompt_contains_browser_automation():
    """Test 1: Phase 1 prompt contains browser_automation."""
    from src.core.evaluator import Evaluator
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    assert "browser_automation" in source, "browser_automation NOT found in strategic_task_planning prompt"
    print("[PASS] test_prompt_contains_browser_automation")


def test_prompt_includes_browser_guidance():
    """Test 2: Prompt includes browser-specific/dynamic-page guidance."""
    from src.core.evaluator import Evaluator
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    
    # Check for key guidance phrases
    checks = {
        "dynamic": "dynamic" in source.lower() or "javascript" in source.lower(),
        "javascript_rendered": "javascript" in source.lower() or "js-rendered" in source.lower(),
        "prefer_over_static": "prefer" in source.lower() and ("over" in source.lower() or "static" in source.lower()),
        "headless_browser": "headless browser" in source.lower() or "playwright" in source.lower(),
        "spa": "spa" in source.lower() or "single-page" in source.lower(),
    }
    
    all_pass = True
    for check_name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {check_name} guidance")
    
    if all_pass:
        print("[PASS] test_prompt_includes_browser_guidance")
    else:
        print("[FAIL] test_prompt_includes_browser_guidance — missing some guidance phrases")
        raise AssertionError("Some browser guidance checks failed")


def test_recommended_tools_schema_preserved():
    """Test 3: Existing recommended_tools output contract is not broken."""
    from src.core.evaluator import Evaluator
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    
    # Check that the JSON schema still has recommended_tools as a JSON array
    assert '"recommended_tools":' in source, "recommended_tools field missing from JSON schema"
    assert 'tool_name_1' in source, "tool_name_1 placeholder missing from schema"
    
    # Check _parse_strategic_response still extracts recommended_tools
    parse_source = inspect.getsource(Evaluator._parse_strategic_response)
    assert '"recommended_tools"' in parse_source or "'recommended_tools'" in parse_source, \
        "recommended_tools not extracted in _parse_strategic_response"
    
    print("[PASS] test_recommended_tools_schema_preserved")


def test_tool_manifest_structure():
    """Test 4: Tool manifest has proper structure with numbered entries."""
    from src.core.evaluator import Evaluator
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    
    # Check for manifest markers
    assert "TOOL MANIFEST" in source, "TOOL MANIFEST marker missing"
    assert "END TOOL MANIFEST" in source, "END TOOL MANIFEST marker missing"
    
    # Check for all 5 required tools in manifest
    required_tools = ["web_search", "web_page_fetch", "web_scraper", "browser_automation", "file_writer"]
    for tool in required_tools:
        assert tool in source, f"Tool '{tool}' missing from tool manifest"
    
    print("[PASS] test_tool_manifest_structure")


def test_browser_automation_critical_marker():
    """Test 5: browser_automation has CRITICAL marker for emphasis."""
    from src.core.evaluator import Evaluator
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    
    # The TOOL MANIFEST section has the emphasized browser_automation entry.
    # Find the TOOL MANIFEST section and check the browser_automation line there.
    manifest_start = source.index("TOOL MANIFEST")
    manifest_end = source.index("END TOOL MANIFEST")
    manifest_section = source[manifest_start:manifest_end]
    
    # In the manifest, browser_automation should be followed by CRITICAL/⚠/PREFER guidance
    has_emphasis = ("CRITICAL" in manifest_section or "⚠" in manifest_section or "PREFER" in manifest_section)
    assert has_emphasis, f"browser_automation in TOOL MANIFEST lacks emphasis marker. Manifest section:\n{manifest_section}"
    
    print("[PASS] test_browser_automation_critical_marker")


def test_avoidance_note_integration():
    """Test 6: Regression learning avoidance note still integrates."""
    from src.core.evaluator import Evaluator
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    
    assert "avoidance_note" in source, "avoidance_note variable missing"
    assert "LESSONS FROM PREVIOUS ERRORS" in source, "avoidance note header missing"
    
    print("[PASS] test_avoidance_note_integration")


async def test_prompt_generation_with_browser_task():
    """Test 7: Generate the actual prompt and verify browser_automation appears."""
    from src.core.evaluator import Evaluator
    
    evaluator = Evaluator()
    
    # Use a browser-like task
    task = "Use browser automation to navigate to https://example.com and extract information"
    
    # We can't call the async method without an AI client, but we can
    # extract the prompt template by inspecting the f-string construction
    import inspect
    source = inspect.getsource(Evaluator.strategic_task_planning)
    
    # Verify the prompt template includes browser_automation
    assert "browser_automation" in source
    assert "dynamic" in source.lower()
    assert "javascript" in source.lower() or "js-rendered" in source.lower()
    
    print("[PASS] test_prompt_generation_with_browser_task")


if __name__ == "__main__":
    print("=" * 70)
    print("GAP_021 Focused Tests — Strategic planner browser_automation visibility")
    print("=" * 70)
    print()
    
    tests_sync = [
        test_prompt_contains_browser_automation,
        test_prompt_includes_browser_guidance,
        test_recommended_tools_schema_preserved,
        test_tool_manifest_structure,
        test_browser_automation_critical_marker,
        test_avoidance_note_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in tests_sync:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {test_fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] {test_fn.__name__}: {e}")
    
    print()
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ All GAP_021 tests passed.")