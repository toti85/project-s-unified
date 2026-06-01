#!/usr/bin/env python3
"""
Real execution test - actually run tasks, don't just check infrastructure.
"""

import asyncio
import sys
from pathlib import Path
import logging
import json

# Fix Windows console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI

async def execute_real_task():
    """Execute a real task through Meta path."""
    print("\n" + "="*80)
    print("REAL TASK EXECUTION TEST")
    print("="*80)
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    # Task 1: Simple analysis
    print("\n[TASK] Analyze: What is in the src/core directory?")
    
    goal = "List the Python files in src/core directory and categorize them by purpose"
    
    print(f"[EXEC] Running: {goal}")
    print(f"[EXEC] Use Meta Path: True")
    print(f"[EXEC] Timeout: 30 seconds")
    
    try:
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=True),
            timeout=120.0
        )
        
        print(f"\n[RESULT]")
        print(f"  Success: {result.get('success')}")
        print(f"  Task type: {result.get('task_type')}")
        
        output = result.get('output', '')
        if output:
            output_str = str(output)[:500]
            print(f"  Output (first 500 chars):")
            print(f"  {output_str}")
            print(f"  ... [total: {len(str(output))} chars]")
        else:
            print(f"  Output: (empty)")
        
        # Check if something was actually generated
        has_output = len(str(output)) > 50
        return result.get('success'), has_output, result
        
    except asyncio.TimeoutError:
        print(f"\n[TIMEOUT] Exceeded 30 seconds")
        return False, False, None
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False, False, None

async def main():
    success, has_output, result = await execute_real_task()
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    print(f"Task executed: {success}")
    print(f"Output generated: {has_output}")
    
    if has_output:
        print(f"Status: REAL EXECUTION CONFIRMED")
        return 0
    else:
        print(f"Status: NO OUTPUT - Check if execution actually happened")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal: {e}")
        sys.exit(1)
