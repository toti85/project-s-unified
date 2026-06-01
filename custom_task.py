#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Egyedi feladat futtatása az AI-val
Custom Task Execution with SuperIntelligentAI
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

async def run_custom_task():
    """Egyedi feladat futtatása"""
    
    print("\n" + "="*80)
    print("EGYEDI FELADAT - SuperIntelligentAI")
    print("="*80)
    print()
    
    # Inicializálás
    print("[1] AI rendszer indítása...")
    ai = SuperIntelligentAI()
    print("    [OK] SuperIntelligentAI készen áll")
    print()
    
    # EGYEDI FELADAT
    task = """
    Hozz létre egy JSON fájlt az alábbi adatokkal:
    
    1. A top 10 legnépesebb ország nevével és lakosságával (2025)
    2. Minden ország 2 karakteres kódja
    3. Kontinentuma
    
    Formátum: JSON, mentsd: memory/output/top_countries.json
    
    Csak valós, széles körben ismert adatok - pontosság fontos!
    """
    
    print("[2] FELADAT:")
    print("-" * 80)
    print(task)
    print("-" * 80)
    print()
    print("[3] AI feldolgozza...")
    print()
    
    try:
        result = await ai.execute_intelligent_task(task=task)
        
        print("\n" + "="*80)
        print("✅ FELADAT KÉSZ!")
        print("="*80)
        
        # Check results
        import os
        output_dir = Path("memory/output")
        if output_dir.exists():
            print("\n📁 Létrehozott fájlok:")
            for f in output_dir.glob("*.json"):
                if "top_countries" in f.name or "country" in f.name.lower():
                    print(f"  ✓ {f.name}")
                    # Show preview
                    try:
                        import json
                        with open(f, 'r', encoding='utf-8') as file:
                            data = json.load(file)
                            print(f"    Tartalom: {str(data)[:150]}...")
                    except:
                        pass
        
        print("\n✨ Az AI sikeresen feldolgozta a feladatot!")
        
    except Exception as e:
        print(f"\n❌ Hiba: {str(e)[:200]}")

if __name__ == "__main__":
    asyncio.run(run_custom_task())
