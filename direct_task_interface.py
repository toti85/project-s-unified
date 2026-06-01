#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIREKT FELADATADAS: Kozvetlenul megmondod az AI-nak mit csinaljon

Ez az interface lehetove teszi, hogy:
1. Egyszerű feladatot adj meg szovegben
2. Az AI azonnal feldolgozza
3. Megoldast kapsz vissza
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Change console encoding to UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI
from tools.tools.registry.tool_registry_golden import ToolRegistry

async def direct_task_assignment():
    """
    INTERFACE: Direkt feladat megadása az AI-nak
    """
    
    print("\n" + "="*80)
    print("DIREKT FELADATADÁS - SuperIntelligentAI Interface")
    print("="*80)
    print()
    print("Az AI közvetlenül feldolgozza a te feladataidat!")
    print()
    
    # Initialize AI and Registry
    print("[1] Rendszer inicializálása...")
    registry = ToolRegistry()
    ai = SuperIntelligentAI()
    
    print(f"    [OK] Registry: {len(registry.tools)} tool")
    print(f"    [OK] AI System: SuperIntelligentAI")
    print()
    
    # Example tasks that you can modify or add
    tasks = [
        {
            "name": "Alapinformáció-gyűjtés",
            "description": """
            Gyűjtsd össze a következő magyar városok alapadatait:
            - Budapest
            - Debrecen  
            - Szeged
            
            Minden városnál adj meg: név, régió, népesség (becsült), fő látnivalók (2-3 db).
            
            Mentsd el az eredményt JSON formátumban: memory/output/magyar_varosok.json
            
            Nincs hallucináció - csak valós, széles körben ismert információ!
            """,
            "timeout": 60
        },
        {
            "name": "Weboldal-elemzés",
            "description": """
            Elemezd a https://github.com/torvalds/linux repository-t (publikus adat):
            - Projekt neve, URL
            - Rövid leírás
            - Fő programozási nyelvek (ha elérhető)
            
            Mentsd el JSON-ba: memory/output/github_analysis_simple.json
            """,
            "timeout": 90
        }
    ]
    
    print("[2] Elérhető feladatok:")
    print()
    for i, task in enumerate(tasks, 1):
        print(f"    {i}. {task['name']}")
        print(f"       {task['description'][:60]}...")
    print()
    
    print("[3] Feladat végrehajtása...")
    print("-" * 80)
    
    # Execute first task as demo
    task = tasks[0]
    
    print(f"\nFeladat: {task['name']}")
    print(f"Leírás: {task['description'][:100]}...\n")
    
    try:
        # This is the DIRECT TASK ASSIGNMENT
        result = await ai.execute_intelligent_task(
            task=task['description']
        )
        
        print(f"\n✅ FELADAT FELDOLGOZVA!")
        print(f"\nEredmény:")
        print("-" * 80)
        
        if isinstance(result, dict):
            if "output" in result:
                print(result["output"])
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result)
            
        print("-" * 80)
        
        # Check if output files were created
        output_dir = Path("memory/output")
        if output_dir.exists():
            output_files = list(output_dir.glob("*.json")) + list(output_dir.glob("*.csv")) + list(output_dir.glob("*.pdf"))
            print(f"\n📁 Létrehozott fájlok:")
            for f in output_files[-3:]:  # Show last 3 files
                print(f"    - {f.name} ({f.stat().st_size} byte)")
        
    except Exception as e:
        print(f"\n❌ Hiba a feladat feldolgozása során: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TESTRESZABÁS:")
    print("="*80)
    print("""
Az alábbi módokon adhatsz feladatokat az AI-nak:

1. EGYSZERŰ FELADAT:
   ```python
   result = await ai.execute_task(
       task="Hozz létre egy JSON-t 5 magyar város névével"
   )
   ```

2. KOMPLEX FELADAT PARAMÉTEREKKEL:
   ```python
   result = await ai.execute_task(
       task="Elemezd a GitHub-ot és hozz létre PDF-et",
       max_iterations=5,
       timeout=120
   )
   ```

3. TÖBB FELADAT EGYMÁS UTÁN:
   ```python
   for task_text in task_list:
       result = await ai.execute_task(task=task_text)
   ```

Módosítsd a kódot és futtasd újra - az AI feldolgozza az új feladataidat!
""")

async def custom_task_example():
    """
    TE EHHEZ MÓDOSÍTSD:
    Ide írhatod a saját feladataidat
    """
    ai = SuperIntelligentAI()
    
    # Saját feladat - módosítsd ezt!
    my_task = """
    Gyűjtsd össze a következő információkat:
    1. A jelenlegi dátum és idő (UTC)
    2. A Python verzió
    3. A rendszer operációs rendszere
    
    Mentsd el JSON-ba: memory/output/rendszer_info.json
    """
    
    print("\n" + "="*80)
    print("SAJÁT FELADAT:")
    print("="*80)
    print(f"\nFeladat: {my_task}\n")
    
    result = await ai.execute_task(task=my_task)
    
    print("Eredmény:")
    print(json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else result)

if __name__ == "__main__":
    header = """
DIREKT FELADATADASAS - SUPERINTELLIGENT AI

Mondj egy feladatot szovegben, az AI azonnal feldolgozza!
"""
    print(header)
    
    # Run main interface
    asyncio.run(direct_task_assignment())
    
    # Uncomment to run custom task example
    # asyncio.run(custom_task_example())
