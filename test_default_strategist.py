#!/usr/bin/env python3
"""
Test: StrategyCouncil with auto-injected default strategist.
Verify that empty council still produces decisions via default strategist.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.meta.strategy_council import StrategyCouncil


async def test_empty_council_auto_inject():
    """Test that empty council auto-injects default strategist."""
    
    print("\n" + "="*80)
    print("TEST: StrategyCouncil Empty -> Auto-Inject Default Strategist")
    print("="*80)
    
    # Create empty council
    council = StrategyCouncil(strategists=[])
    print(f"\n[SETUP] Created StrategyCouncil with {len(council.strategists)} strategists")
    
    # Test 1: decide() should auto-inject default strategist
    print("\n[TEST1] Call decide() with empty council...")
    goal = "Create a short report about system status and write to memory/intelligence/demo_report.txt"
    
    try:
        decision = await council.decide(goal)
        print(f"  [OK] Decision reached: {decision.decision}")
        print(f"  [OK] Consensus: {decision.consensus_type}")
        print(f"  [OK] Approval ratio: {decision.approval_ratio:.1%}")
        print(f"  [OK] Strategists now: {len(council.strategists)}")
        print(f"  [OK] Strategist name: {council.strategists[0].ai_name}")
        
        # Verify decision structure
        assert decision.decision in ["approved", "rejected", "conditional"], f"Invalid decision: {decision.decision}"
        assert decision.consensus_type in ["unanimous", "majority", "split"], f"Invalid consensus: {decision.consensus_type}"
        assert len(council.strategists) > 0, "Strategists not injected"
        
        print("\n[PASS] Auto-injection works!")
        return True
        
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_default_strategist_opinion():
    """Test that default strategist returns valid opinions."""
    
    print("\n" + "="*80)
    print("TEST: Default Strategist Opinion Content")
    print("="*80)
    
    council = StrategyCouncil(strategists=[])
    
    # Test different goals
    goals = [
        "Search for API documentation",
        "Write analysis to output.txt",
        "Create summary and save to memory/report.json"
    ]
    
    for goal in goals:
        print(f"\n[TEST] Goal: {goal}")
        decision = await council.decide(goal)
        
        # Check opinion structure
        if decision.opinions:
            opinion = decision.opinions[0]
            print(f"  Opinion: {opinion.recommendation}")
            print(f"  Feasibility: {opinion.feasibility_score}")
            print(f"  Confidence: {opinion.confidence_score}")
            print(f"  Reasoning: {opinion.reasoning[:100]}...")
            
            assert 0 <= opinion.feasibility_score <= 100, "Invalid feasibility score"
            assert 0 <= opinion.confidence_score <= 100, "Invalid confidence score"
            assert opinion.recommendation in ["approve", "reject", "conditional"], "Invalid recommendation"
    
    print("\n[PASS] All opinions valid!")
    return True


async def main():
    """Run all tests."""
    
    print("\nTesting StrategyCouncil Default Strategist Injection")
    
    test1 = await test_empty_council_auto_inject()
    test2 = await test_default_strategist_opinion()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Auto-inject test: {'PASS' if test1 else 'FAIL'}")
    print(f"Opinion content test: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print("\n[FAIL] Some tests failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
