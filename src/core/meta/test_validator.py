"""
Test suite for Execution Validator consensus mechanism.

Tests:
1. Unanimous pass (all validators pass)
2. Critical issue failure (critical security issue)
3. Majority pass (2/3 validators pass)
4. Quality issues (minor quality concerns)
"""
import asyncio
import logging
from typing import Dict, Any, List
from .ai_validator import AIValidator
from .validation_result import ValidationIssue, ValidationCheck
from .execution_validator import ExecutionValidator


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def test_unanimous_pass():
    """
    Test 1: Unanimous pass scenario.
    
    All validators pass with no critical issues.
    Expected: passed=True, consensus_type="unanimous_pass"
    """
    print("\n" + "="*70)
    print("TEST 1: UNANIMOUS PASS")
    print("="*70)
    
    # Create validator with 3 check types
    validator = ExecutionValidator()
    validator.add_validator(AIValidator("qwen3-235b", "correctness"))
    validator.add_validator(AIValidator("gpt-4o", "security"))
    validator.add_validator(AIValidator("claude-opus", "quality"))
    
    # Successful execution result
    execution_result = {
        "status": "success",
        "goal": "Analyze security report",
        "output": "Report analyzed successfully",
        "steps": 5,
        "execution_time": "2.3s",
        "errors": []
    }
    
    goal = "Analyze security report and generate recommendations"
    context = {"report_type": "security", "complexity": "medium"}
    
    print(f"\n[GOAL] {goal}")
    print(f"[EXECUTION STATUS] {execution_result['status']}")
    
    result = await validator.validate(execution_result, goal, context)
    
    print(f"\n[RESULT] Passed: {result.passed}")
    print(f"[RESULT] Consensus Type: {result.consensus_type}")
    print(f"[RESULT] Confidence: {result.confidence:.1f}%")
    
    print(f"\n[VALIDATORS]")
    for check in result.checks:
        status = "✅ PASS" if check.passed else "❌ FAIL"
        print(f"  {check.validator_name} ({check.check_type}): {status} "
              f"({check.confidence:.0f}% confidence, {len(check.issues)} issues)")
    
    print(f"\n[ISSUES SUMMARY] {result.get_issue_summary()}")
    
    # Assertions
    assert result.passed, f"Expected passed=True, got {result.passed}"
    assert result.consensus_type == "unanimous_pass", f"Expected 'unanimous_pass', got '{result.consensus_type}'"
    assert result.confidence >= 75, f"Expected confidence >= 75, got {result.confidence}"
    
    print("\n[PASS] ✅ UNANIMOUS PASS TEST PASSED")
    return True


async def test_critical_issue_fails():
    """
    Test 2: Critical issue failure.
    
    One validator finds critical security issue.
    Expected: passed=False, consensus_type="failed"
    """
    print("\n" + "="*70)
    print("TEST 2: CRITICAL ISSUE FAILURE")
    print("="*70)
    
    class CustomValidator(AIValidator):
        """Custom validator that finds security issues."""
        
        def _validate_security(self, execution_result, original_goal, context):
            """Override to report critical issue."""
            
            issue = ValidationIssue(
                severity="critical",
                category="security",
                description="API key hardcoded in execution result",
                found_by=self.model_name,
                location="execution_result.config.api_key",
                recommendation="Move API key to environment variables or secure vault"
            )
            
            return ValidationCheck(
                validator_name=self.model_name,
                check_type=self.check_type,
                passed=False,
                confidence=95,
                issues=[issue],
                reasoning="Critical security vulnerability detected: API key exposure"
            )
    
    validator = ExecutionValidator()
    validator.add_validator(AIValidator("qwen3-235b", "correctness"))
    validator.add_validator(CustomValidator("gpt-4o", "security"))
    validator.add_validator(AIValidator("claude-opus", "quality"))
    
    execution_result = {
        "status": "success",
        "output": "API initialized",
        "config": {
            "api_key": "sk-1234567890abcdef"  # ⚠️ Hardcoded key
        }
    }
    
    goal = "Connect to external API and fetch data"
    
    print(f"\n[GOAL] {goal}")
    print(f"[ISSUE] API key hardcoded in result")
    
    result = await validator.validate(execution_result, goal)
    
    print(f"\n[VALIDATION RESULT]")
    print(f"  Passed: {result.passed}")
    print(f"  Consensus Type: {result.consensus_type}")
    print(f"  Confidence: {result.confidence:.1f}%")
    print(f"  Critical Issues Found: {len(result.critical_issues)}")
    
    if result.critical_issues:
        print(f"\n[CRITICAL ISSUE DETAILS]")
        for issue in result.critical_issues:
            print(f"  Severity: {issue.severity.upper()}")
            print(f"  Category: {issue.category}")
            print(f"  Description: {issue.description}")
            print(f"  Recommendation: {issue.recommendation}")
    
    # Assertions
    assert not result.passed, f"Expected passed=False, got {result.passed}"
    assert result.consensus_type == "failed", f"Expected 'failed', got '{result.consensus_type}'"
    assert len(result.critical_issues) > 0, "Expected critical issues"
    
    print("\n[TEST STATUS] ✅ PASS - Validator correctly returned FAIL for critical security issue")
    return True


async def test_majority_pass():
    """
    Test 3: Majority pass.
    
    2 out of 3 validators pass, 1 fails.
    Expected: passed=True, consensus_type="majority_pass"
    """
    print("\n" + "="*70)
    print("TEST 3: MAJORITY PASS")
    print("="*70)
    
    class FailingValidator(AIValidator):
        """Validator that finds issues but not critical."""
        
        def _validate_quality(self, execution_result, original_goal, context):
            issue = ValidationIssue(
                severity="medium",
                category="quality",
                description="Missing execution metrics",
                found_by=self.model_name,
                location="execution_result",
                recommendation="Add execution_time and memory_usage metrics"
            )
            
            return ValidationCheck(
                validator_name=self.model_name,
                check_type=self.check_type,
                passed=False,  # Fail but not critical
                confidence=70,
                issues=[issue],
                reasoning="Quality check failed: Insufficient metrics"
            )
    
    validator = ExecutionValidator()
    validator.add_validator(AIValidator("qwen3-235b", "correctness"))
    validator.add_validator(AIValidator("gpt-4o", "security"))
    validator.add_validator(FailingValidator("claude-opus", "quality"))
    
    execution_result = {
        "status": "success",
        "output": "Task completed",
        "steps": 3
    }
    
    goal = "Process data and generate report"
    
    print(f"\n[GOAL] {goal}")
    print(f"[VALIDATORS] 2 pass, 1 fails (non-critical)")
    
    result = await validator.validate(execution_result, goal)
    
    print(f"\n[RESULT] Passed: {result.passed}")
    print(f"[RESULT] Consensus Type: {result.consensus_type}")
    print(f"[VALIDATORS PASSED] {sum(1 for c in result.checks if c.passed)}/3")
    
    print(f"\n[ISSUES]")
    for issue in result.all_issues:
        print(f"  [{issue.severity.upper()}] {issue.category}: {issue.description}")
    
    # Assertions
    assert result.passed, f"Expected passed=True, got {result.passed}"
    assert result.consensus_type == "majority_pass", f"Expected 'majority_pass', got '{result.consensus_type}'"
    
    print("\n[PASS] ✅ MAJORITY PASS TEST PASSED")
    return True


async def test_quality_issues():
    """
    Test 4: Quality concerns.
    
    Minor quality issues but no security/correctness problems.
    Expected: passed=True, consensus_type="unanimous_pass" or "majority_pass"
    """
    print("\n" + "="*70)
    print("TEST 4: QUALITY CONCERNS")
    print("="*70)
    
    validator = ExecutionValidator()
    validator.add_validator(AIValidator("qwen3-235b", "correctness"))
    validator.add_validator(AIValidator("gpt-4o", "security"))
    validator.add_validator(AIValidator("claude-opus", "quality"))
    
    # Result with missing quality metrics
    execution_result = {
        "status": "success",
        "output": "Task succeeded",
        # Missing: execution_time, steps, metadata
    }
    
    goal = "Extract and validate data from CSV file"
    
    print(f"\n[GOAL] {goal}")
    print(f"[EXECUTION] Success but missing quality metrics")
    
    result = await validator.validate(execution_result, goal)
    
    print(f"\n[RESULT] Passed: {result.passed}")
    print(f"[RESULT] Consensus Type: {result.consensus_type}")
    print(f"[ISSUES FOUND] {result.get_issue_summary()}")
    
    print(f"\n[ISSUES BY CATEGORY]")
    by_category = result.get_category_breakdown()
    for category, issues in by_category.items():
        if issues:
            print(f"  {category.upper()}: {len(issues)} issues")
            for issue in issues[:2]:
                print(f"    - {issue.description}")
    
    print(f"\n[RECOMMENDATIONS]")
    for rec in result.recommendations:
        print(f"  {rec}")
    
    # Assertions
    assert result.passed, f"Expected passed=True, got {result.passed}"
    assert len(result.all_issues) > 0, "Expected quality issues to be found"
    assert len(result.critical_issues) == 0, "Expected no critical issues"
    
    print("\n[PASS] ✅ QUALITY CONCERNS TEST PASSED")
    return True


async def run_all_tests():
    """Run all validator test scenarios."""
    print("\n" + "="*70)
    print("EXECUTION VALIDATOR TEST SUITE")
    print("="*70)
    
    try:
        results = {
            "unanimous_pass": await test_unanimous_pass(),
            "critical_failure": await test_critical_issue_fails(),
            "majority_pass": await test_majority_pass(),
            "quality_issues": await test_quality_issues()
        }
        
        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.upper()}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED - VALIDATOR READY FOR PRODUCTION")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed - review before production")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
