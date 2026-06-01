"""
Real-world tasks: Test tools and Meta path with actual work
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.super_intelligent_ai import SuperIntelligentAI


async def task_1_browser_content():
    """TASK 1: Nyerj ki információt egy weblapról"""
    
    print("\n" + "="*80)
    print("TASK 1: Web Content Extraction")
    print("="*80)
    print("\nFeladat: Nyerj ki információt az https://example.com oldalról")
    print("- Cím, tartalom\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    goal = """Nyiss meg a https://example.com oldalt és:
1. Nyerd ki az oldal címét (title)
2. Nyerd ki az oldal fő tartalmát (főszöveg)
3. Foglald össze 2-3 mondatban, hogy miről szól az oldal"""
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(goal, use_meta_controller=True),
        timeout=300.0
    )
    
    print(f"\n📊 Eredmény:")
    print(f"  Success: {result.get('success')}")
    output = str(result.get('output', ''))[:500]
    print(f"  Output:\n{output}")
    
    return result.get('success', False)


async def task_2_file_analysis():
    """TASK 2: Elemezz egy file-t"""
    
    print("\n" + "="*80)
    print("TASK 2: File Analysis")
    print("="*80)
    print("\nFeladat: Elemezd az src könyvtárstruktúráját")
    print("- Listázd a fő mappákat és azok rendeltetéseit\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    goal = """Elemezd az src/ könyvtárstruktúráját:
1. Listázd a fő almappákat
2. Mindegyikhez írj 1-2 mondatos leírást, hogy mire való
3. Azonosíts 3-4 fontos komponenst a rendszerben"""
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(goal, use_meta_controller=True),
        timeout=300.0
    )
    
    print(f"\n📊 Eredmény:")
    print(f"  Success: {result.get('success')}")
    output = str(result.get('output', ''))[:500]
    print(f"  Output:\n{output}")
    
    return result.get('success', False)


async def task_3_combined():
    """TASK 3: Kombinált feladat - webes info + mentés"""
    
    print("\n" + "="*80)
    print("TASK 3: Combined Task (Browser + File)")
    print("="*80)
    print("\nFeladat: Nyerj ki webes adatot és mentsd el")
    print("- Letöltés + elemzés + mentés\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    goal = """Végezd el ezt az adatelemzési folyamatot:
1. Nyiss meg https://httpbin.org/html oldalt
2. Nyerd ki a HTML title-t
3. Készíts egy rövid összefoglalót az oldalról
4. Mentsd el az eredményt memory/intelligence/task3_result.txt fájlba"""
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(goal, use_meta_controller=True),
        timeout=300.0
    )
    
    print(f"\n📊 Eredmény:")
    print(f"  Success: {result.get('success')}")
    output = str(result.get('output', ''))[:500]
    print(f"  Output:\n{output}")
    
    # Check if file was created
    result_file = Path("memory/intelligence/task3_result.txt")
    if result_file.exists():
        print(f"\n✅ File létrehozva: {result_file}")
        with open(result_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            print(f"  Tartalom ({len(content)} byte):\n{content[:300]}")
    else:
        print(f"\n⚠️  File nem létrehozva: {result_file}")
    
    return result.get('success', False)


async def task_4_system_info():
    """TASK 4: Rendszer információk összegyűjtése"""
    
    print("\n" + "="*80)
    print("TASK 4: System Information")
    print("="*80)
    print("\nFeladat: Gyűjts össze rendszer információkat\n")
    
    ai = SuperIntelligentAI(use_meta_controller=True)
    
    goal = """Gyűjts össze információkat a projektről:
1. Python verzió
2. Elérhető memória
3. Jelenlegi munkamappa
4. Az src/core könyvtárban található Python fájlok száma"""
    
    result = await asyncio.wait_for(
        ai.execute_intelligent_task(goal, use_meta_controller=True),
        timeout=300.0
    )
    
    print(f"\n📊 Eredmény:")
    print(f"  Success: {result.get('success')}")
    output = str(result.get('output', ''))[:500]
    print(f"  Output:\n{output}")
    
    return result.get('success', False)


async def main():
    """Run all real-world tasks"""
    
    print("\n" + "="*80)
    print("REAL-WORLD TASK TEST SUITE")
    print("="*80)
    print("\nValódi feladatok - eszközök és Meta path tesztelése")
    print("- Browser tool adapter (PRIMARY + FALLBACK)")
    print("- File tools")
    print("- System tools")
    print("- Meta controller convergence")
    
    results = {}
    
    try:
        # Task 1: Browser content extraction
        results['Browser Content'] = await task_1_browser_content()
        
        # Task 2: File/directory analysis
        results['File Analysis'] = await task_2_file_analysis()
        
        # Task 3: Combined browser + file
        results['Combined Task'] = await task_3_combined()
        
        # Task 4: System info
        results['System Info'] = await task_4_system_info()
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        for task_name, success in results.items():
            status = "✅ SUCCESS" if success else "⚠️  INCOMPLETE"
            print(f"{task_name}: {status}")
        
        total_success = sum(1 for v in results.values() if v)
        print(f"\nTotal: {total_success}/{len(results)} tasks successful")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
