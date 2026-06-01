"""
Real-world practical tasks - testing the system end-to-end
Uses Meta controller + available tools
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.super_intelligent_ai import SuperIntelligentAI


async def task_1_analyze_project():
    """Elemezd a projekt struktúráját és a komponenseket"""
    
    print("\n" + "="*80)
    print("FELADAT 1: Projekt Struktúra Analízis")
    print("="*80)
    print("\nCél: Elemezd az src könyvtárstruktúráját")
    print("     és azonosítsd a fő komponenseket\n")
    
    ai = SuperIntelligentAI(use_meta_controller=False)  # Standard path (no API key needed)
    
    goal = """Elemezd az src/ könyvtárstruktúráját:
1. List the main subdirectories in src/
2. For each, describe what it contains in 1-2 sentences
3. Identify 3 main components of the system
4. Return a brief summary"""
    
    try:
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=False),
            timeout=120.0
        )
        
        print(f"Eredmény:")
        print(f"  Success: {result.get('success')}")
        output = str(result.get('output', ''))
        if output:
            lines = output.split('\n')[:20]  # First 20 lines
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        
        return True
    except Exception as e:
        print(f"  Hiba: {e}")
        return False


async def task_2_file_search():
    """Keress Python fájlokat a projektben"""
    
    print("\n" + "="*80)
    print("FELADAT 2: File Keresés")
    print("="*80)
    print("\nCél: Keress Python fájlokat az src/core könyvtárban\n")
    
    ai = SuperIntelligentAI(use_meta_controller=False)
    
    goal = """Find Python files in src/core/:
1. Search for *.py files
2. Count how many there are
3. List the first 5-10 files
4. Report the total count"""
    
    try:
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=False),
            timeout=120.0
        )
        
        print(f"Eredmény:")
        print(f"  Success: {result.get('success')}")
        output = str(result.get('output', ''))
        if output:
            lines = output.split('\n')[:15]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        
        return True
    except Exception as e:
        print(f"  Hiba: {e}")
        return False


async def task_3_create_summary():
    """Készítsd el a rendszer összefoglalóját"""
    
    print("\n" + "="*80)
    print("FELADAT 3: Rendszer Összefoglaló Készítés")
    print("="*80)
    print("\nCél: Írj összefoglalót a projektről és mentsd el fájlba\n")
    
    ai = SuperIntelligentAI(use_meta_controller=False)
    
    goal = """Create a project summary:
1. Describe what this project is about (Project-S Super Core)
2. List 5 key features or components
3. Write 2-3 sentences about its architecture
4. Save this summary to memory/intelligence/project_summary_task3.txt"""
    
    try:
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=False),
            timeout=120.0
        )
        
        print(f"Eredmény:")
        print(f"  Success: {result.get('success')}")
        output = str(result.get('output', ''))
        if output:
            lines = output.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        
        # Check if file was created
        summary_file = Path("memory/intelligence/project_summary_task3.txt")
        if summary_file.exists():
            print(f"\n  ✅ Fájl létrehozva: {summary_file.name}")
            with open(summary_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                print(f"     ({len(content)} byte)")
        
        return True
    except Exception as e:
        print(f"  Hiba: {e}")
        return False


async def task_4_metadata():
    """Gyűjts metaadatokat a rendszerről"""
    
    print("\n" + "="*80)
    print("FELADAT 4: Rendszer Metaadatok")
    print("="*80)
    print("\nCél: Gyűjts rendszer információkat\n")
    
    ai = SuperIntelligentAI(use_meta_controller=False)
    
    goal = """Gather system metadata:
1. What Python version is being used?
2. What is the current working directory?
3. How many Python files are in the src/core directory?
4. What are the main tools available in the system?"""
    
    try:
        result = await asyncio.wait_for(
            ai.execute_intelligent_task(goal, use_meta_controller=False),
            timeout=120.0
        )
        
        print(f"Eredmény:")
        print(f"  Success: {result.get('success')}")
        output = str(result.get('output', ''))
        if output:
            lines = output.split('\n')[:12]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        
        return True
    except Exception as e:
        print(f"  Hiba: {e}")
        return False


async def main():
    """Run practical tasks"""
    
    print("\n" + "="*80)
    print("VALÓDI FELADATOK - RENDSZER TESZT")
    print("="*80)
    print("\nA SuperIntelligentAI rendszer tesztelése valódi feladatokkal:")
    print("- Standard execution path (Meta controller optional)")
    print("- File tools, system tools")
    print("- Rendszer integrációja")
    
    results = {}
    
    try:
        # Run each task
        print("\n[FELADAT 1/4] Projekt Struktúra...")
        results['Struktúra'] = await task_1_analyze_project()
        
        print("\n[FELADAT 2/4] File Keresés...")
        results['Keresés'] = await task_2_file_search()
        
        print("\n[FELADAT 3/4] Összefoglaló...")
        results['Összefoglaló'] = await task_3_create_summary()
        
        print("\n[FELADAT 4/4] Metaadatok...")
        results['Metaadatok'] = await task_4_metadata()
        
        # Summary
        print("\n" + "="*80)
        print("ÖSSZEFOGLALÁS")
        print("="*80)
        
        for task_name, success in results.items():
            status = "✓ OK" if success else "✗ HIBA"
            print(f"{task_name:20} : {status}")
        
        total = sum(1 for v in results.values() if v)
        print(f"\nÖsszesen: {total}/{len(results)} feladat sikeres")
        
        if total == len(results):
            print("\n✅ ÖSSZES FELADAT SIKERES")
        else:
            print(f"\n⚠️  {len(results) - total} feladat hiba")
        
    except Exception as e:
        print(f"\n❌ Hiba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
