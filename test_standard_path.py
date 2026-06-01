#!/usr/bin/env python3
"""
Smoke test: Run WITHOUT MetaController to verify standard path works.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI


async def main():
    print("\n" + "="*80)
    print("SMOKE TEST: SuperIntelligentAI STANDARD PATH (no MetaController)")
    print("="*80)
    
    try:
        # Initialize WITHOUT MetaController
        print("\n[INIT] Creating SuperIntelligentAI (standard path)...")
        ai = SuperIntelligentAI(use_meta_controller=False)
        print("  [OK] Initialized")
        
        # Simple goal that generates demo_report.txt
        goal = "Write a brief status report to memory/intelligence/demo_report.txt about the system capabilities"
        print(f"\n[GOAL] {goal}")
        
        print("\n[EXEC] Running goal (standard path)...")
        result = await ai.execute_intelligent_task(goal, use_meta_controller=False)
        
        print("\n[RESULT]")
        print(f"  Success: {result.get('success')}")
        print(f"  Task type: {result.get('task_type')}")
        if result.get('output'):
            output = result.get('output', '')
            print(f"  Output: {output[:300]}")
        
        # Check demo_report.txt
        print("\n[CHECK] Verifying demo_report.txt...")
        demo_path = Path("memory/intelligence/demo_report.txt")
        if demo_path.exists():
            print(f"  [OK] File exists: {demo_path}")
            with open(demo_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            print(f"  [OK] First 10 lines:")
            for i, line in enumerate(lines[:10], 1):
                print(f"    {i}: {line.rstrip()}")
        else:
            print(f"  [INFO] File not created")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
