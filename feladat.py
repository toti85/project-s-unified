#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FELADAT - Egyszeruen csak a feladatodat adj meg!

Hasznalat:
  python feladat.py "Hozz letre egy JSON fajlt az elerheto toolok listajarol"
"""

import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI
from tools.tools.registry.tool_registry_golden import ToolRegistry

async def main():
    # Get task from command line
    if len(sys.argv) > 1:
        feladat = " ".join(sys.argv[1:])
    else:
        feladat = input("\nFeladat: ")
    
    if not feladat.strip():
        print("Feladat megadasahoz irj valamit!")
        return
    
    print("\n" + "="*60)
    print(f"FELADAT: {feladat}")
    print("="*60)
    print("\n[OK] AI feldolgozasa indulasa...\n")
    
    # Initialize
    registry = ToolRegistry()
    ai = SuperIntelligentAI()
    
    # Run task
    try:
        result = await ai.execute_intelligent_task(task=feladat)
        
        print("\n" + "="*60)
        print("EREDMENY:")
        print("="*60 + "\n")
        
        if isinstance(result, dict):
            if "output" in result:
                output = result["output"]
                # Remove emojis
                for emoji, text in [
                    ('\U0001f9e0', '[BRAIN]'),
                    ('\U0001f680', '[START]'),
                    ('🎯', '[GOAL]'),
                    ('📊', '[DATA]'),
                    ('✅', '[OK]'),
                    ('❌', '[FAIL]'),
                ]:
                    output = output.replace(emoji, text)
                print(output)
            else:
                print(f"Siker: {result.get('success', 'N/A')}")
                if result.get('error'):
                    print(f"Hiba: {result['error']}")
                else:
                    print("Feladat sikeresen feldolgozva!")
        else:
            print(result)
        
        # Check output files
        output_dir = Path("memory/output")
        if output_dir.exists():
            files = sorted(output_dir.glob("*.*"))[-3:]
            if files:
                print("\n[DIR] Legujabb fajlok:")
                for f in files:
                    print(f"  {f.name}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP]")
