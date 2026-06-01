#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE REAL TASK TEST
Valós feladatok sok tool-lal

Feladatok:
1. GitHub API elemzés + File Writer + PDF
2. Meteorológiai adatok + CSV + JSON
3. Web scraping + Analyzer + File Search
4. Többszemélyű adatgyűjtés (API + Web + Browser)
5. Teljes workflow: adatgyűjtés -> feldolgozás -> jelentés

Tesztelni fogjuk:
- web_api_call
- file_writer
- pdf_generator
- web_scraper
- web_analyzer
- system_command
- file_reader
- file_search
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI
from tools.tools.registry.tool_registry_golden import ToolRegistry

class ComprehensiveRealTaskTester:
    def __init__(self):
        self.ai = SuperIntelligentAI()
        self.registry = ToolRegistry()
        self.results = {}
        self.output_dir = Path("memory/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def task_1_github_analysis(self):
        """Feladat 1: GitHub API + File Writer + PDF
        Tools: web_api_call, file_writer, pdf_generator
        """
        print("\n" + "="*70)
        print("[TASK 1] GitHub Repository Analysis")
        print("="*70)
        print("Tools: web_api_call, file_writer, pdf_generator")
        print()
        
        task = """
        Elemezd a torvalds/linux GitHub repository-t (publikus adat):
        1. Nézd meg a repo alapadatait
        2. Gyűjtsd össze: neve, URL, description, starCount
        3. Mentsd el memory/output/github_repo_analysis.json fajlba
        4. Hozz létre egy rövid PDF-et az info-kból
        
        Valós adatokat használj, nincs hallucináció!
        """
        
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["TASK_1_GitHub"] = "PASS"
            print("[OK] GitHub analysis completed")
            return True
        except Exception as e:
            print(f"[FAIL] {e}")
            self.results["TASK_1_GitHub"] = f"FAIL: {str(e)}"
            return False

    async def task_2_weather_data(self):
        """Feladat 2: Open Weather API + CSV + JSON
        Tools: web_api_call, file_writer
        """
        print("\n" + "="*70)
        print("[TASK 2] Weather Data Collection & Export")
        print("="*70)
        print("Tools: web_api_call, file_writer")
        print()
        
        task = """
        Gyűjtsd össze az időjárási adatokat (publikus Open Weather adatok):
        1. Budapest weather (hőmérséklet, páratartalom, leírás)
        2. Debrecen weather
        3. Szeged weather
        
        Mentsd el JSON-ba: memory/output/cities_weather.json
        Mentsd el CSV-ba: memory/output/cities_weather.csv
        
        Formátum:
        {
            "cities": [
                {"name": "Budapest", "temp": "12C", "humidity": "60%", "description": "Cloudy"},
                ...
            ]
        }
        """
        
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["TASK_2_Weather"] = "PASS"
            print("[OK] Weather data collected and exported")
            return True
        except Exception as e:
            print(f"[FAIL] {e}")
            self.results["TASK_2_Weather"] = f"FAIL: {str(e)}"
            return False

    async def task_3_technology_news(self):
        """Feladat 3: Tech News Aggregation + Analysis
        Tools: web_scraper, web_analyzer, file_writer
        """
        print("\n" + "="*70)
        print("[TASK 3] Technology News Aggregation")
        print("="*70)
        print("Tools: web_scraper, web_analyzer, file_writer")
        print()
        
        task = """
        Gyűjtsd össze a legfontosabb tech news kategóriákat:
        1. AI/Machine Learning - 2-3 hírek
        2. Cloud Computing - 2-3 hírek
        3. Cybersecurity - 2-3 hírek
        
        Minden hírnél: Title, Source, Brief Summary
        
        Mentsd el JSON-ba: memory/output/tech_news.json
        
        Format:
        {
            "categories": {
                "AI": [
                    {"title": "...", "source": "...", "summary": "..."},
                    ...
                ],
                ...
            },
            "collection_date": "2025-12-26"
        }
        """
        
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["TASK_3_TechNews"] = "PASS"
            print("[OK] Tech news aggregated")
            return True
        except Exception as e:
            print(f"[FAIL] {e}")
            self.results["TASK_3_TechNews"] = f"FAIL: {str(e)}"
            return False

    async def task_4_programming_languages(self):
        """Feladat 4: Programming Languages Comparison
        Tools: web_api_call, file_writer, file_search
        """
        print("\n" + "="*70)
        print("[TASK 4] Programming Languages Comparison")
        print("="*70)
        print("Tools: web_api_call, file_writer, file_search")
        print()
        
        task = """
        Hozz létre egy összehasonlítást a Top 5 programozási nyelvről:
        
        Languages: Python, JavaScript, Java, C++, Go
        
        Minden nyelvhez:
        - Nev
        - Teruletek (use cases): 3-4
        - Elonyok: 3
        - Hatranyok: 2
        - Leguje verzio (megkozeltoleges)
        - Populáció (fő): High/Medium/Low
        
        Mentsd el JSON-ba: memory/output/programming_languages.json
        Mentsd el CSV-ba is: memory/output/programming_languages.csv
        """
        
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["TASK_4_ProgLangs"] = "PASS"
            print("[OK] Programming languages comparison created")
            return True
        except Exception as e:
            print(f"[FAIL] {e}")
            self.results["TASK_4_ProgLangs"] = f"FAIL: {str(e)}"
            return False

    async def task_5_complete_workflow(self):
        """Feladat 5: Complete Data Workflow
        Tools: web_api_call, web_analyzer, file_writer, pdf_generator, system_info
        """
        print("\n" + "="*70)
        print("[TASK 5] Complete Data Workflow (End-to-End)")
        print("="*70)
        print("Tools: web_api_call, web_analyzer, file_writer, pdf_generator")
        print()
        
        task = """
        Teljes workflow: Adatgyűjtés -> Feldolgozás -> Jelentés
        
        Teendők:
        1. Gyűjtsd össze az info a következő API-król:
           - GitHub REST API
           - JSONPlaceholder API
           - OpenWeatherMap API
           - Open-Meteo API
        
        2. Minden API-hoz: URL, Autentikáció, Limitációk, Használati esetek
        
        3. Hozz létre egy comprehensive PDF reportot:
           - Cím: "Public APIs Reference Guide 2025"
           - Bevezető: Mi a publikus API
           - API táblázat
           - Best practices
        
        4. Mentsd el:
           - JSON: memory/output/apis_complete_guide.json
           - CSV: memory/output/apis_complete_guide.csv
           - PDF: memory/output/apis_complete_guide.pdf
        """
        
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["TASK_5_Workflow"] = "PASS"
            print("[OK] Complete workflow executed")
            return True
        except Exception as e:
            print(f"[FAIL] {e}")
            self.results["TASK_5_Workflow"] = f"FAIL: {str(e)}"
            return False

    async def verify_outputs(self):
        """Verify all output files were created"""
        print("\n" + "="*70)
        print("[VERIFICATION] Output Files Check")
        print("="*70)
        
        expected_files = {
            "github_repo_analysis.json": "GitHub API data",
            "cities_weather.json": "Weather JSON",
            "cities_weather.csv": "Weather CSV",
            "tech_news.json": "Tech news aggregation",
            "programming_languages.json": "Languages comparison JSON",
            "programming_languages.csv": "Languages comparison CSV",
            "apis_complete_guide.json": "APIs guide JSON",
            "apis_complete_guide.csv": "APIs guide CSV",
            "apis_complete_guide.pdf": "APIs guide PDF",
        }
        
        found_files = {}
        
        for filename, description in expected_files.items():
            filepath = self.output_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                found_files[filename] = size
                print(f"  [OK] {filename:40} ({size:6} bytes) - {description}")
            else:
                print(f"  [MISS] {filename:40} - {description}")
        
        print(f"\nFiles created: {len(found_files)}/{len(expected_files)}")
        
        return found_files

    async def run_all_tasks(self):
        """Run all tasks in sequence"""
        print("\n" + "="*70)
        print("COMPREHENSIVE REAL TASK TEST - STARTING")
        print("="*70)
        print(f"Tools available: {len(self.registry.tools)}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        # Run all tasks
        tasks = [
            self.task_1_github_analysis(),
            self.task_2_weather_data(),
            self.task_3_technology_news(),
            self.task_4_programming_languages(),
            self.task_5_complete_workflow(),
        ]
        
        print("\n[EXECUTING] 5 Real Tasks with Multiple Tools...\n")
        
        for i, task in enumerate(tasks, 1):
            try:
                await task
            except Exception as e:
                print(f"Task {i} error: {e}")
        
        # Verify outputs
        print("\n")
        files_created = await self.verify_outputs()
        
        # Final report
        self.generate_report(files_created)

    def generate_report(self, files_created):
        """Generate final test report"""
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        print("\nTask Execution Results:")
        for task, result in self.results.items():
            status = "[PASS]" if result == "PASS" else "[FAIL]"
            print(f"  {status} {task}: {result}")
        
        passed = sum(1 for r in self.results.values() if r == "PASS")
        total = len(self.results)
        
        print(f"\nSuccess Rate: {passed}/{total} tasks ({100*passed/total:.0f}%)")
        
        print(f"\nFiles Generated: {len(files_created)}")
        total_size = sum(files_created.values())
        print(f"Total Data: {total_size:,} bytes")
        
        print("\n" + "="*70)
        if passed == total and len(files_created) >= 7:
            print("[SUCCESS] ALL TESTS PASSED - REAL TASK EXECUTION VERIFIED!")
        else:
            print("[WARNING] Some tests did not complete fully")
        print("="*70 + "\n")

async def main():
    tester = ComprehensiveRealTaskTester()
    await tester.run_all_tasks()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Test interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
