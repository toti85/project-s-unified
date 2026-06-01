"""
Integration tests for MetaController + SuperIntelligentAI.

Tests the complete decision→execute→validate→replan loop within SuperIntelligentAI,
verifying evidence logging and loop iteration behavior.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

# Setup path
import sys
from pathlib import Path as _Path
_src_dir = str(_Path(__file__).parent / "src")
_repo_root = str(_Path(__file__).parent)
sys.path.insert(0, _repo_root)
sys.path.insert(0, _src_dir)

from src.core.super_intelligent_ai import SuperIntelligentAI
from src.core.meta import ValidationResult, ValidationCheck, ValidationIssue, Decision


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def test_meta_controller_integration_fail_replan_pass():
    """
    Test: MetaController integration with SuperIntelligentAI.
    
    Scenario: FAIL → REPLAN → PASS
    - First execution fails validation
    - Council replans with updated constraints
    - Second execution passes
    
    Verify:
    - Evidence JSONL contains goal_started and goal_completed
    - Validation FAIL triggers replan_triggered
    - Evidence shows at least 2 iterations
    - Final result indicates success
    """
    print("\n" + "="*70)
    print("INTEGRATION TEST: MetaController + SuperIntelligentAI (FAIL→REPLAN→PASS)")
    print("="*70)
    
    # Create temporary test directory
    test_dir = Path("test_meta_integration_tmp")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize SuperIntelligentAI with MetaController
        ai = SuperIntelligentAI(base_dir=test_dir, use_meta_controller=True)
        
        # Verify MetaController was initialized
        assert ai.use_meta_controller, "MetaController not enabled"
        assert ai.meta_controller is not None, "MetaController not initialized"
        print(f"\n✅ SuperIntelligentAI initialized with MetaController")
        
        # Mock the StrategyCouncil to return approvals
        original_council_decide = ai.meta_controller.council.decide
        call_count = [0]
        
        async def mock_council_decide(goal, state, constraints=None):
            call_count[0] += 1
            return Decision(
                decision_id=f"dec_{call_count[0]}",
                goal=goal,
                decision="approved",
                consensus_type="unanimous",
                approval_ratio=1.0,
                avg_feasibility=95,
                avg_confidence=95,
                recommended_plan=f"Plan {call_count[0]}: {'Standard approach' if call_count[0] == 1 else 'Revised approach (with fixes)'}"
            )
        
        ai.meta_controller.council.decide = mock_council_decide
        
        # Mock the validators to FAIL first, then PASS
        original_executor = ai.meta_controller.executor
        exec_calls = [0]
        
        async def mock_executor(goal, decision):
            exec_calls[0] += 1
            return {
                "status": "success",
                "output": f"Task completed (attempt {exec_calls[0]})",
                "execution_time_ms": 100 + (exec_calls[0] * 50)
            }
        
        ai.meta_controller.executor.execute = mock_executor
        
        # Mock validator to FAIL first, PASS second
        original_validator_validate = ai.meta_controller.validator.validate
        val_calls = [0]
        
        async def mock_validator_validate(result, goal, context=None):
            val_calls[0] += 1
            
            if val_calls[0] == 1:
                # First validation: FAIL
                issue = ValidationIssue(
                    severity="high",
                    category="quality",
                    description="Missing execution metrics",
                    found_by="test",
                    location="result",
                    recommendation="Add timing information"
                )
                return ValidationResult(
                    passed=False,
                    confidence=60,
                    consensus_type="failed",
                    checks=[],
                    all_issues=[issue],
                    critical_issues=[],
                    validation_id=f"val_{val_calls[0]}"
                )
            else:
                # Second validation: PASS
                return ValidationResult(
                    passed=True,
                    confidence=95,
                    consensus_type="unanimous_pass",
                    checks=[],
                    all_issues=[],
                    critical_issues=[],
                    validation_id=f"val_{val_calls[0]}"
                )
        
        ai.meta_controller.validator.validate = mock_validator_validate
        
        # Execute goal through SuperIntelligentAI
        goal = "Test integration: complete a task"
        print(f"\n🎯 Running goal: {goal}")
        
        result = await ai.execute_intelligent_task(goal, use_meta_controller=True)
        
        print(f"\n[RESULT] Status: {result.get('task_type')}")
        print(f"[RESULT] Success: {result.get('success')}")
        print(f"[RESULT] Output: {result.get('output')[:100]}...")
        
        # Verify result
        assert result.get("success"), f"Execution failed: {result}"
        assert result.get("task_type") == "meta_controller_execution", f"Wrong task type: {result.get('task_type')}"
        
        meta_result = result.get("meta_result")
        assert meta_result is not None, "Missing meta_result"
        assert meta_result.get("status") == "success", f"Goal not successful: {meta_result.get('status')}"
        assert meta_result.get("iterations") == 2, f"Expected 2 iterations, got {meta_result.get('iterations')}"
        
        print(f"\n✅ Execution succeeded in {meta_result.get('iterations')} iterations")
        
        # Verify evidence logging
        evidence_log_path = ai.evidence_logger.get_log_path()
        evidence_file = Path(evidence_log_path)
        assert evidence_file.exists(), f"Evidence log not created: {evidence_log_path}"
        
        print(f"\n📊 Evidence log created: {evidence_log_path}")
        
        # Read and analyze evidence
        events = []
        with open(evidence_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except json.JSONDecodeError:
                    pass
        
        print(f"[EVIDENCE] Total events: {len(events)}")
        event_types = [e['event_type'] for e in events]
        print(f"[EVIDENCE] Event types: {event_types}")
        
        # Verify key events
        assert 'goal_started' in event_types, "Missing goal_started event"
        assert 'goal_completed' in event_types, "Missing goal_completed event"
        assert 'replan_triggered' in event_types, "Missing replan_triggered event (should have replanned after first failure)"
        
        # Count validation_done events (should be 2 for FAIL then PASS)
        val_done_count = sum(1 for e in events if e['event_type'] == 'validation_done')
        assert val_done_count == 2, f"Expected 2 validation_done events, got {val_done_count}"
        
        print(f"✅ Evidence verification passed")
        print(f"   - goal_started: present")
        print(f"   - replan_triggered: present")
        print(f"   - validation_done: {val_done_count} events")
        print(f"   - goal_completed: present")
        
        print("\n[PASS] ✅ INTEGRATION TEST PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}", exc_info=True)
        print(f"\n[FAIL] ❌ TEST FAILED: {e}")
        return False
        
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)


async def test_meta_controller_disabled():
    """
    Test: SuperIntelligentAI with MetaController disabled (use_meta_controller=False).
    
    Verify: Standard execution path still works when MetaController is disabled.
    """
    print("\n" + "="*70)
    print("INTEGRATION TEST: MetaController Disabled (Standard Path)")
    print("="*70)
    
    test_dir = Path("test_meta_disabled_tmp")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize SuperIntelligentAI WITHOUT MetaController
        ai = SuperIntelligentAI(base_dir=test_dir, use_meta_controller=False)
        
        assert not ai.use_meta_controller, "MetaController should be disabled"
        assert ai.meta_controller is None, "MetaController should not be initialized"
        print(f"\n✅ SuperIntelligentAI initialized WITHOUT MetaController")
        
        # Execute goal (should use standard path)
        goal = "Test standard path: analyze data"
        result = await ai.execute_intelligent_task(goal, use_meta_controller=False)
        
        print(f"\n[RESULT] Task type: {result.get('task_type')}")
        print(f"[RESULT] Success: {result.get('success')}")
        
        # Should NOT be meta_controller_execution
        assert result.get("task_type") != "meta_controller_execution", "Should not use MetaController"
        assert result.get("success"), "Standard execution should succeed"
        
        print(f"\n✅ Standard path executed successfully")
        print("\n[PASS] ✅ STANDARD PATH TEST PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Standard path test failed: {e}", exc_info=True)
        print(f"\n[FAIL] ❌ TEST FAILED: {e}")
        return False
        
    finally:
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)


async def run_all_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("METACONTROLLER + SUPERINTELLIGENTAI INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {
        "fail_replan_pass": False,
        "disabled_path": False
    }
    
    try:
        results["fail_replan_pass"] = await test_meta_controller_integration_fail_replan_pass()
    except Exception as e:
        logger.error(f"FAIL_REPLAN_PASS test error: {e}", exc_info=True)
        print(f"\n[ERROR] ❌ TEST ERROR: {e}")
    
    try:
        results["disabled_path"] = await test_meta_controller_disabled()
    except Exception as e:
        logger.error(f"DISABLED_PATH test error: {e}", exc_info=True)
        print(f"\n[ERROR] ❌ TEST ERROR: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED - METACONTROLLER INTEGRATION VERIFIED")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_integration_tests())
    exit(0 if success else 1)
