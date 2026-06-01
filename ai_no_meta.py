#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Execution - META LAYER DISABLED
Az AI valós feladatokat hajt végre - Meta Controller nélkül
"""

import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI

async def test_without_meta():
    """AI futtatása Meta Controller nélkül"""
    
    print("\n" + "="*80)
    print("AI EXECUTION - META CONTROLLER DISABLED")
    print("="*80)
    print()
    
    # Initialize AI WITHOUT MetaController
    ai = SuperIntelligentAI(use_meta_controller=False)
    print("[OK] AI initialized WITHOUT MetaController")
    print()
    
    tasks = [
        "GitHub trending repositorykáról írj egy 3 mondatos összegzést",
        "Mi a Python programozás lényege? Röviden",
        "Hozz létre egy JSON-t 5 szín nevével és HEX kódjukkal",
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n[TASK {i}] {task}")
        print("-" * 80)
        
        try:
            result = await ai.execute_intelligent_task(task=task, use_meta_controller=False)
            
            print(f"✅ Feldolgozva!")
            
            if isinstance(result, dict):
                if 'output' in result:
                    output = result['output']
                else:
                    output = str(result)
            else:
                output = str(result)
            
            # Truncate very long outputs
            if len(output) > 500:
                print(output[:500] + "...")
            else:
                print(output)
        
        except Exception as e:
            print(f"❌ Hiba: {str(e)[:200]}")
        
        print()
    
    print("="*80)
    print("✅ TESZTEK KÉSZ")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(test_without_meta())
    except Exception as e:
        print(f"Fatal: {str(e)[:300]}")
