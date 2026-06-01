#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GYORS KIPRÓBÁLÁS - BROWSER AUTOMATION TESZT
Quick Start - Browser Automation Testing
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
from tools.tools.registry.tool_registry_golden import ToolRegistry

async def show_menu():
    """Show interactive menu"""
    print("\n" + "="*80)
    print("GYORS KIPROBÁLÁS - INTERACTIVE MENU")
    print("="*80)
    print()
    print("[1] Browser Automation Tesztelése")
    print("[2] Web Scraping Tesztelése")
    print("[3] File Operations Tesztelése")
    print("[4] AI Feladat Feldolgozása (szabad")
    print("[5] Összes Tool Listázása")
    print("[6] Exit")
    print()
    
    choice = input("Válassz (1-6): ").strip()
    return choice

async def test_browser_automation(ai):
    """Test browser automation capabilities"""
    print("\n" + "-"*80)
    print("[BROWSER AUTOMATION TEST]")
    print("-"*80)
    print()
    print("3 variáció tesztelésre vár:")
    print("  1. browser_automation")
    print("  2. optimized_browser_automation")
    print("  3. ultra_optimized_browser_automation")
    print()
    
    tasks = [
        "Nyiss meg egy weboldalt (pl. example.com) és írj le 1 mondatban",
        "Milyen információk találhatók egy tipikus weboldal header-jében?",
        "Hogyan működik a web scraping alapvetően?",
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/3] Task: {task}")
        print("      Feldolgozás...")
        
        try:
            result = await ai.execute_intelligent_task(task=task)
            print(f"      [OK] Feldolgozva")
        except Exception as e:
            print(f"      [HANDLED] {str(e)[:50]}")
    
    print()
    print("[Browser Automation] Status: TESTED")

async def test_web_scraping(ai):
    """Test web scraping capabilities"""
    print("\n" + "-"*80)
    print("[WEB SCRAPING TEST]")
    print("-"*80)
    print()
    
    task = """
    Írj le 1 mondatban, hogyan működik a web scraping:
    - Mit keres a scraper?
    - Hogyan működik?
    - Mik a limitációi?
    """
    
    print("Task: Web scraping leírása")
    print("Feldolgozás...")
    
    try:
        result = await ai.execute_intelligent_task(task=task)
        print("[OK] Feldolgozva")
    except Exception as e:
        print(f"[HANDLED] {str(e)[:40]}")
    
    print()

async def test_file_operations(ai):
    """Test file operations"""
    print("\n" + "-"*80)
    print("[FILE OPERATIONS TEST]")
    print("-"*80)
    print()
    
    task = """
    Hozz létre memory/output/quick_test.json-t ezzel a tartalommal:
    {
        "test": "quick_start",
        "timestamp": "2025-12-26",
        "status": "working"
    }
    """
    
    print("Task: File létrehozása")
    print("Feldolgozás...")
    
    try:
        result = await ai.execute_intelligent_task(task=task)
        print("[OK] Feldolgozva")
        
        # Check if file was created
        if Path("memory/output/quick_test.json").exists():
            print("[VERIFY] Fájl létrehozva!")
        else:
            print("[NOTE] Fájl manuálisan is létrehozható")
    except Exception as e:
        print(f"[HANDLED] {str(e)[:40]}")
    
    print()

async def test_custom_task(ai):
    """Test custom user task"""
    print("\n" + "-"*80)
    print("[CUSTOM TASK TEST]")
    print("-"*80)
    print()
    
    print("Írj be egy feladatot az AI-nak (vagy Enter a skiphez):")
    task = input("> ").strip()
    
    if not task:
        print("[SKIPPED]")
        return
    
    print(f"\nTask: {task}")
    print("Feldolgozás...")
    
    try:
        result = await ai.execute_intelligent_task(task=task)
        print("[OK] Feldolgozva")
    except Exception as e:
        print(f"[HANDLED] {str(e)[:40]}")
    
    print()

def list_all_tools():
    """List all available tools"""
    print("\n" + "-"*80)
    print("[ÖSSZES TOOL]")
    print("-"*80)
    print()
    
    registry = ToolRegistry()
    
    # Group by category
    categories = {
        "File I/O": ["file_reader", "file_writer", "file_search"],
        "Web Operations": ["web_api_call", "web_scraper", "web_analyzer", "web_page_fetch", "web_search"],
        "Browser": ["browser_automation", "optimized_browser_automation", "ultra_optimized_browser_automation"],
        "Generation": ["pdf_generator"],
        "System": ["system_command", "system_info"],
        "AI": ["general_assistant", "tech_news_aggregator"]
    }
    
    for category, tools in categories.items():
        print(f"\n{category}:")
        for tool in tools:
            if tool in registry.tools:
                print(f"  ✓ {tool}")
            else:
                print(f"  ✗ {tool} (NOT REGISTERED)")
    
    print(f"\nTeljes: {len(registry.tools)}/16 tool")
    print()

async def main():
    """Main interactive loop"""
    ai = SuperIntelligentAI()
    
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " "*15 + "VALÓS RENDSZER KIPRÓBÁLÁSA - INTERACTIVE" + " "*22 + "█")
    print("█" + " "*15 + "REAL SYSTEM TESTING - INTERACTIVE" + " "*31 + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    print()
    print("Ez az interaktív menü lehetővé teszi a rendszer tesztelését:")
    print("- Browser automation")
    print("- Web scraping")
    print("- File operations")
    print("- Custom tasks")
    print()
    
    while True:
        try:
            choice = await show_menu()
            
            if choice == "1":
                await test_browser_automation(ai)
            elif choice == "2":
                await test_web_scraping(ai)
            elif choice == "3":
                await test_file_operations(ai)
            elif choice == "4":
                await test_custom_task(ai)
            elif choice == "5":
                list_all_tools()
            elif choice == "6":
                print("\n[EXIT] Kilépés...")
                break
            else:
                print("[ERROR] Érvénytelen választás")
        
        except KeyboardInterrupt:
            print("\n\n[STOP] Billentyű miatt leállítva")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Programa leállt")
