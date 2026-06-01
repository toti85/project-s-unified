#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUPERINTELLIGENT AI - FELADAT INTERFACE
Te adhatsz feladatot, az AI feldolgozza azonnal!
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI
from tools.tools.registry.tool_registry_golden import ToolRegistry

async def run_user_task():
    """Egyszeru feladat interface - te adsz meg feladatot"""
    
    print("\n" + "="*70)
    print("SUPERINTELLIGENT AI - FELADAT ADASA")
    print("="*70)
    
    # Initialize
    print("\n[OK] Rendszer betoltese...")
    registry = ToolRegistry()
    ai = SuperIntelligentAI()
    print(f"[OK] {len(registry.tools)} tool elerheto\n")
    
    # Get task from user or use example
    print("LEHETOSEGEK:")
    print("1. Pelda feladat lefuttatasa")
    print("2. Saját feladat megadasa")
    print()
    
    choice = input("Valassz (1 vagy 2): ").strip()
    
    if choice == "1":
        # Example tasks
        tasks = {
            "a": {
                "nev": "Magyarorszag adatai",
                "feladat": """
Gujts ossze informaciokat Magyarorszagrol:
- Fovaros: Budapest
- Terület: ~93000 km2
- Lakossag: ~9.7 millio
- Legmagasabb pont: Kekes (1014m)
- Fő ekonomiai szektor: turizmus, agrariumF IT

Mentsd el memory/output/magyarorszag_info.json fajlba JSON formatumban!
"""
            },
            "b": {
                "nev": "Programozasi nyelvek",
                "feladat": """
Szamold ossze a legismertebb programozasi nyelveket:
1. Python - adattudomany, webfejlesztes
2. JavaScript - webfrontend, Node.js
3. Java - nagyszalas alkalmazasok
4. C++ - rendszerprogramozas, jatek motor
5. Go - masodlagos szervrek

Mentsd el memory/output/nyelvek.json fajlba JSON formatumban!
"""
            },
            "c": {
                "nev": "Aktualis ora es sorszam adatok",
                "feladat": """
Gyujtsd ossze a kovetkezo adatokat es mentsd memory/output/status.json-ba:
1. Jelenlegi datum es ora (UTC)
2. Python verzio
3. Az operacios rendszer neve
4. Az aktualis munkakonyvtar

Formatum: JSON, kucs-ertek parok.
"""
            }
        }
        
        print("\nPELDA FELADATOK:")
        for key, task in tasks.items():
            print(f"{key}) {task['nev']}")
        
        task_choice = input("\nValassz (a/b/c): ").strip().lower()
        if task_choice in tasks:
            user_task = tasks[task_choice]["feladat"]
            print(f"\nFutatas: {tasks[task_choice]['nev']}\n")
        else:
            user_task = tasks["a"]["feladat"]
            print(f"\nFutatas: Magyarorszag adatai (alapertelmezett)\n")
    
    else:
        user_task = input("\nIrd be a feladatod (vagy Enter az egyszeru pelda): ").strip()
        if not user_task:
            user_task = "Adj meg 3 magyar varos nevét es 1-2 mondatos leirasát!"
    
    print("-" * 70)
    print(f"FELADAT:\n{user_task}\n")
    print("-" * 70)
    
    # Execute
    print("\n[OK] AI feldolgozas indulasa...\n")
    
    try:
        result = await ai.execute_intelligent_task(task=user_task)
        
        print("\n" + "="*70)
        print("EREDMENY:")
        print("="*70 + "\n")
        
        # Display result
        if isinstance(result, dict):
            if "output" in result:
                # Remove problematic chars for display
                output = result["output"]
                output = output.replace('\U0001f9e0', '[BRAIN]')
                output = output.replace('\U0001f680', '[START]')
                output = output.replace('🎯', '[GOAL]')
                output = output.replace('📊', '[DATA]')
                print(output)
            elif "success" in result:
                print(f"Siker: {result['success']}")
                if "error" in result:
                    print(f"Hiba: {result['error']}")
                else:
                    print("Feladat feldolgozva!")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
        
        print("\n" + "="*70)
        
        # Check output files
        output_dir = Path("memory/output")
        if output_dir.exists():
            files = sorted(output_dir.glob("*.json")) + sorted(output_dir.glob("*.csv"))
            if files:
                print("\n[DIR] Letrehozott fajlok:")
                for f in files[-5:]:
                    print(f"  {f.name} ({f.stat().st_size} byte)")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("Vege!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(run_user_task())
    except KeyboardInterrupt:
        print("\n\n[STOP] Leallitva a felhasznalo altal.")
    except Exception as e:
        print(f"\n[FATAL] {e}")
