#!/usr/bin/env python3
"""Async execution test - minimal version."""

import asyncio
import sys
from pathlib import Path
import logging
import os

# Fix Windows encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Suppress all logging  
logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI

async def test_standard():
    """Test standard path execution."""
    print("\n[STD] Starting standard path test...")
    try:
        ai = SuperIntelligentAI(use_meta_controller=False)
        print("  [STD] AI created")
        
        goal = "Write 'test output' to memory/intelligence/test_std.txt"
        print(f"  [STD] Goal: {goal}")
        
        # Use timeout to prevent hanging
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=False),
            timeout=20.0
        )
        
        print(f"  [STD] Result: {result.get('success')}")
        
        # Check file
        if Path("memory/intelligence/test_std.txt").exists():
            print(f"  [STD] File created: YES")
            return True
        else:
            print(f"  [STD] File created: NO")
            return False
            
    except asyncio.TimeoutError:
        print("  [STD] TIMEOUT - execution exceeded 20 seconds")
        return False
    except Exception as e:
        print(f"  [STD] ERROR: {e}")
        return False

async def test_meta():
    """Test meta path execution."""
    print("\n[META] Starting meta path test...")
    try:
        ai = SuperIntelligentAI(use_meta_controller=True)
        print("  [META] AI created")
        
        goal = "Write 'test output' to memory/intelligence/test_meta.txt"
        print(f"  [META] Goal: {goal}")
        
        # Use timeout to prevent hanging
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=True),
            timeout=20.0
        )
        
        print(f"  [META] Result: {result.get('success')}")
        
        # Check file
        if Path("memory/intelligence/test_meta.txt").exists():
            print(f"  [META] File created: YES")
            return True
        else:
            print(f"  [META] File created: NO")
            return False
            
    except asyncio.TimeoutError:
        print("  [META] TIMEOUT - execution exceeded 20 seconds")
        return False
    except Exception as e:
        print(f"  [META] ERROR: {e}")
        return False

async def main():
    print("="*80)
    print("ASYNC EXECUTION TEST")
    print("="*80)
    
    std_ok = await test_standard()
    meta_ok = await test_meta()
    
    print("\n" + "="*80)
    print(f"Standard: {'PASS' if std_ok else 'FAIL'}")
    print(f"Meta:     {'PASS' if meta_ok else 'FAIL'}")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
