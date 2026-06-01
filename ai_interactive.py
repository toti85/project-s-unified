#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Task Interface - Interactive Mode
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

async def interactive_ai():
    """Interactive AI task interface"""
    
    print("\n" + "="*80)
    print("INTERACTIVE AI TASK INTERFACE")
    print("="*80)
    print()
    print("Feladataidat közvetlenül adhatsz az AI-nak")
    print("Enter 'quit' vagy 'exit' a kilépéshez")
    print()
    print("Példák:")
    print("  - 'Összegezd röviden a Python programozást'")
    print("  - 'Mi a termodinamika első törvénye?'")
    print("  - 'Hozz létre egy 3 soros vicot'")
    print("  - 'Elemezd az AI etikai kérdéseit'")
    print()
    print("="*80)
    print()
    
    ai = SuperIntelligentAI()
    print("[OK] AI System ready")
    print()
    
    while True:
        try:
            # Get task from user
            print()
            task = input("📝 Feladat: ").strip()
            
            if task.lower() in ['quit', 'exit', 'kilépés', 'vége']:
                print("\n👋 Viszlát!")
                break
            
            if not task:
                print("❌ Üres feladat, próbálj újra!")
                continue
            
            print()
            print("⏳ AI feldolgozza...")
            print("-" * 80)
            
            # Execute task
            try:
                result = await ai.execute_intelligent_task(task=task)
                
                print()
                print("✅ EREDMÉNY:")
                print("-" * 80)
                
                if isinstance(result, dict):
                    if 'output' in result:
                        output = result['output']
                    elif 'meta_result' in result and 'final_result' in result['meta_result']:
                        output = result['meta_result']['final_result'].get('output', str(result))
                    else:
                        output = str(result)
                else:
                    output = str(result)
                
                # Clean up the output
                if isinstance(output, str):
                    output = output.replace('❌ MetaController failed: passed', '')
                    output = output.strip()
                
                if output and output != 'Task processed with backup systems:':
                    print(output[:1000])
                else:
                    print("(Feldolgozás megtörtént)")
                
                print("-" * 80)
                
            except Exception as e:
                print(f"❌ Hiba: {str(e)[:300]}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Leállítva")
            break
        except EOFError:
            print("\n👋 Viszlát!")
            break

if __name__ == "__main__":
    try:
        asyncio.run(interactive_ai())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
