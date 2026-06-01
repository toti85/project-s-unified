"""
Test suite for Strategy Council consensus mechanism.

Tests:
1. Unanimous consensus (all strategists approve)
2. Majority consensus (2/3 approve)
3. Split consensus (less than 2/3 approve)
"""
import asyncio
import logging
from datetime import datetime
from .ai_strategist import AIStrategist
from .strategy_council import StrategyCouncil


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def test_unanimous_consensus():
    """
    Test 1: Unanimous consensus scenario.
    
    All strategists agree on approval.
    Expected: decision="approved", consensus_type="unanimous"
    """
    print("\n" + "="*70)
    print("TEST 1: UNANIMOUS CONSENSUS")
    print("="*70)
    
    # Create council with 3 strategists
    council = StrategyCouncil()
    council.add_strategist(AIStrategist("qwen3-235b", "strategic"))
    council.add_strategist(AIStrategist("claude-opus", "security"))
    council.add_strategist(AIStrategist("deepseek-v3", "technical"))
    
    # Test goal
    goal = "Create a bug bounty research automation tool"
    context = {
        "scope": "internal research tool",
        "complexity": "medium",
        "timeline": "4 weeks"
    }
    
    print(f"\n[GOAL] {goal}")
    print(f"[CONTEXT] {context}")
    
    # Get decision
    decision = await council.decide(goal, context)
    
    # Verify unanimous
    print(f"\n[RESULT] Decision: {decision.decision}")
    print(f"[RESULT] Consensus Type: {decision.consensus_type}")
    print(f"[RESULT] Approval Ratio: {decision.approval_ratio:.1%}")
    print(f"[RESULT] Avg Feasibility: {decision.avg_feasibility:.1f}")
    print(f"[RESULT] Avg Confidence: {decision.avg_confidence:.1f}")
    
    print(f"\n[OPINIONS]")
    for opinion in decision.opinions:
        print(f"  {opinion.ai_name} ({opinion.role}): {opinion.recommendation}")
        print(f"    Feasibility: {opinion.feasibility_score}, Confidence: {opinion.confidence_score}")
        print(f"    Reasoning: {opinion.reasoning[:80]}...")
    
    print(f"\n[RISKS] {len(decision.aggregated_risks)} identified:")
    for risk in decision.aggregated_risks[:3]:
        print(f"  - {risk}")
    
    print(f"\n[BENEFITS] {len(decision.aggregated_benefits)} identified:")
    for benefit in decision.aggregated_benefits[:3]:
        print(f"  + {benefit}")
    
    # Assertions
    assert decision.decision == "approved", f"Expected 'approved', got '{decision.decision}'"
    assert decision.consensus_type == "unanimous", f"Expected 'unanimous', got '{decision.consensus_type}'"
    assert decision.approval_ratio == 1.0, f"Expected 1.0, got {decision.approval_ratio}"
    
    print("\n[PASS] ✅ UNANIMOUS CONSENSUS TEST PASSED")
    return True


async def test_majority_consensus():
    """
    Test 2: Majority consensus scenario.
    
    2 out of 3 strategists approve (majority).
    Expected: decision="approved", consensus_type="majority"
    """
    print("\n" + "="*70)
    print("TEST 2: MAJORITY CONSENSUS")
    print("="*70)
    
    # Create custom strategists with specific behaviors
    class CustomStrategist(AIStrategist):
        def __init__(self, ai_name, role, recommendation_override=None):
            super().__init__(ai_name, role)
            self.recommendation_override = recommendation_override
        
        def _analyze_mock(self, goal, context=None):
            from .decision import AIOpinion
            
            if self.recommendation_override:
                rec = self.recommendation_override
            else:
                rec = "approve"
            
            return AIOpinion(
                ai_name=self.ai_name,
                role=self.role,
                recommendation=rec,
                feasibility_score=75 if rec != "reject" else 40,
                confidence_score=80 if rec != "reject" else 50,
                reasoning=f"{self.role.capitalize()} perspective: {rec.upper()}",
                risks=["Standard risk"] if rec == "reject" else [],
                benefits=["Enhanced capability"]
            )
    
    council = StrategyCouncil()
    council.add_strategist(CustomStrategist("qwen3-235b", "strategic", "approve"))
    council.add_strategist(CustomStrategist("claude-opus", "security", "approve"))
    council.add_strategist(CustomStrategist("deepseek-v3", "technical", "reject"))
    
    goal = "Implement advanced ML-based threat detection system"
    context = {"complexity": "high", "timeline": "8 weeks"}
    
    print(f"\n[GOAL] {goal}")
    print(f"[STRATEGISTS] 2 approve, 1 rejects")
    
    decision = await council.decide(goal, context)
    
    print(f"\n[RESULT] Decision: {decision.decision}")
    print(f"[RESULT] Consensus Type: {decision.consensus_type}")
    print(f"[RESULT] Approval Ratio: {decision.approval_ratio:.1%}")
    
    print(f"\n[OPINIONS]")
    for opinion in decision.opinions:
        print(f"  {opinion.ai_name}: {opinion.recommendation}")
    
    # Assertions
    assert decision.consensus_type == "majority", f"Expected 'majority', got '{decision.consensus_type}'"
    assert decision.approval_ratio == (2/3), f"Expected 0.667, got {decision.approval_ratio}"
    
    print("\n[PASS] ✅ MAJORITY CONSENSUS TEST PASSED")
    return True


async def test_split_consensus():
    """
    Test 3: Split consensus scenario.
    
    Less than majority agree (below 2/3).
    Expected: decision="rejected", consensus_type="split"
    """
    print("\n" + "="*70)
    print("TEST 3: SPLIT CONSENSUS")
    print("="*70)
    
    class CustomStrategist(AIStrategist):
        def __init__(self, ai_name, role, recommendation_override=None):
            super().__init__(ai_name, role)
            self.recommendation_override = recommendation_override
        
        def _analyze_mock(self, goal, context=None):
            from .decision import AIOpinion
            
            if self.recommendation_override:
                rec = self.recommendation_override
            else:
                rec = "approve"
            
            return AIOpinion(
                ai_name=self.ai_name,
                role=self.role,
                recommendation=rec,
                feasibility_score=55 if rec == "reject" else 65,
                confidence_score=50 if rec == "reject" else 70,
                reasoning=f"{self.role.capitalize()}: {rec.upper()}",
                risks=["High implementation risk"] if rec == "reject" else [],
                benefits=["Moderate benefit"]
            )
    
    council = StrategyCouncil()
    council.add_strategist(CustomStrategist("qwen3-235b", "strategic", "approve"))
    council.add_strategist(CustomStrategist("claude-opus", "security", "reject"))
    council.add_strategist(CustomStrategist("deepseek-v3", "technical", "reject"))
    
    goal = "Bypass security verification for performance gains"
    context = {"risky": True}
    
    print(f"\n[GOAL] {goal}")
    print(f"[STRATEGISTS] 1 approves, 2 reject")
    
    decision = await council.decide(goal, context)
    
    print(f"\n[RESULT] Decision: {decision.decision}")
    print(f"[RESULT] Consensus Type: {decision.consensus_type}")
    print(f"[RESULT] Approval Ratio: {decision.approval_ratio:.1%}")
    
    print(f"\n[OPINIONS]")
    for opinion in decision.opinions:
        print(f"  {opinion.ai_name}: {opinion.recommendation}")
    
    # Assertions
    assert decision.consensus_type == "split", f"Expected 'split', got '{decision.consensus_type}'"
    assert decision.approval_ratio == (1/3), f"Expected 0.333, got {decision.approval_ratio}"
    assert decision.decision == "rejected", f"Expected 'rejected', got '{decision.decision}'"
    
    print("\n[PASS] ✅ SPLIT CONSENSUS TEST PASSED")
    return True


async def test_conditional_approval():
    """
    Test 4: Conditional approval scenario.
    
    Approval granted with conditions that must be met.
    Expected: decision="conditional"
    """
    print("\n" + "="*70)
    print("TEST 4: CONDITIONAL APPROVAL")
    print("="*70)
    
    class CustomStrategist(AIStrategist):
        def __init__(self, ai_name, role, with_conditions=False):
            super().__init__(ai_name, role)
            self.with_conditions = with_conditions
        
        def _analyze_mock(self, goal, context=None):
            from .decision import AIOpinion
            
            conditions = None
            if self.with_conditions and self.role == "security":
                conditions = [
                    "Implement API key rotation every 90 days",
                    "Add rate limiting to all external calls",
                    "Validate all inputs against whitelist"
                ]
            
            return AIOpinion(
                ai_name=self.ai_name,
                role=self.role,
                recommendation="conditional" if conditions else "approve",
                feasibility_score=75,
                confidence_score=80,
                reasoning=f"{self.role.capitalize()}: Approved with conditions",
                risks=["API exposure risk"] if conditions else [],
                benefits=["Enhanced capability"],
                conditions=conditions
            )
    
    council = StrategyCouncil()
    council.add_strategist(CustomStrategist("qwen3-235b", "strategic"))
    council.add_strategist(CustomStrategist("claude-opus", "security", with_conditions=True))
    council.add_strategist(CustomStrategist("deepseek-v3", "technical"))
    
    goal = "Integrate with external API for threat intelligence"
    
    print(f"\n[GOAL] {goal}")
    
    decision = await council.decide(goal, context={"api": "threat_intelligence"})
    
    print(f"\n[RESULT] Decision: {decision.decision}")
    print(f"[RESULT] Consensus Type: {decision.consensus_type}")
    
    if decision.decision == "conditional":
        print(f"\n[CONDITIONS]")
        for opinion in decision.opinions:
            if opinion.conditions:
                for condition in opinion.conditions:
                    print(f"  ☐ {condition}")
    
    print("\n[PASS] ✅ CONDITIONAL APPROVAL TEST PASSED")
    return True


async def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "="*70)
    print("STRATEGY COUNCIL TEST SUITE")
    print("="*70)
    
    try:
        results = {
            "unanimous": await test_unanimous_consensus(),
            "majority": await test_majority_consensus(),
            "split": await test_split_consensus(),
            "conditional": await test_conditional_approval()
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
            print("\n🎉 ALL TESTS PASSED - COUNCIL READY FOR PRODUCTION")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed - review before production")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
