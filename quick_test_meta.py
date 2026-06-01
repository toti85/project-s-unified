#!/usr/bin/env python3
"""Quick test of MetaController with auto-injected default strategist."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI


async def main():
    print("\n" + "="*80)
    print("QUICK TEST: MetaController with Default Strategist")
    print("="*80 + "\n")
    
    try:
        # Initialize
        print("[1] Initializing SuperIntelligentAI...")
        ai = SuperIntelligentAI(use_meta_controller=True)
        print(f"    OK - MetaController: {ai.meta_controller is not None}")
        
        # Simple goal
        goal = "Analyze the project structure"
        print(f"\n[2] Goal: {goal}")
        
        # Run with timeout
        print(f"\n[3] Executing (timeout: 20 seconds)...")
        try:
            result = await asyncio.wait_for(
                ai.execute_intelligent_task(goal, use_meta_controller=True),
                timeout=20.0
            )
            print(f"    OK - Completed (no timeout)")
        except asyncio.TimeoutError:
            print(f"    FAIL - execution exceeded 20 seconds")
            result = {"success": False, "error": "timeout"}
        
        # Show result
        print(f"\n[4] Result:")
        print(f"    Success: {result.get('success')}")
        print(f"    Task type: {result.get('task_type')}")
        if result.get('meta_result'):
            print(f"    Meta status: {result.get('meta_result').get('status')}")
            print(f"    Iterations: {result.get('meta_result').get('iterations', 'N/A')}")
        
        # Check evidence
        evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
        if evidence_file.exists():
            print(f"\n[5] Evidence logged to: {evidence_file}")
            with open(evidence_file, "r") as f:
                lines = f.readlines()
            print(f"    Events: {len(lines)}")
            for i, line in enumerate(lines[-3:], 1):
                print(f"      Event {len(lines)-3+i}: {line[:80]}...")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
