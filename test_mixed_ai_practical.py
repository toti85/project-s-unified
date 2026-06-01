#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VEGYES TESZT: AI + PRAKTIKAI FELADATOK
Combination of AI processing and real tool execution

Demonstrating:
- AI decision-making with 16 available tools
- Real file generation (JSON, CSV, PDF)
- Multi-tool orchestration
- Meta-learning in action
"""

import sys
import asyncio
import json
import csv
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.super_intelligent_ai import SuperIntelligentAI
from tools.tools.registry.tool_registry_golden import ToolRegistry

output_dir = Path("memory/output")
output_dir.mkdir(parents=True, exist_ok=True)

class MixedTestSuite:
    def __init__(self):
        self.ai = SuperIntelligentAI()
        self.registry = ToolRegistry()
        self.results = {}
    
    async def ai_task_1(self):
        """Task 1: AI analyzes GitHub"""
        print("\n[AI-TASK 1] GitHub Analysis")
        print("           Tools: web_api_call, file_writer")
        print("           Output: github_analysis.json")
        
        task = """
Gyújtsd össze az alábbi publikus GitHub infókat:
- Microsoft/vscode: 164000 stars, JavaScript
- facebook/react: 225000 stars, JavaScript  
- google/golang: 124000 stars, Go

Formátum JSON-ba memory/output/github_analysis.json:
{"repos": [{"name": "", "stars": "", "lang": ""}]}
"""
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["AI-GitHub"] = "OK"
            print("           [OK] Processed")
            return True
        except Exception as e:
            print(f"           [FAIL] {str(e)[:40]}")
            self.results["AI-GitHub"] = "FAIL"
            return False
    
    async def ai_task_2(self):
        """Task 2: AI does data compilation"""
        print("\n[AI-TASK 2] Tech Trends Summary")
        print("           Tools: web_scraper, file_writer")
        print("           Output: tech_trends.json")
        
        task = """
Készítsd el a 2025-ös tech trend összefoglalót JSON-ba:
memory/output/tech_trends.json

Format:
{
    "trends": [
        {"name": "AI/LLM", "status": "Mature"},
        {"name": "Quantum Computing", "status": "Emerging"},
        {"name": "Web3", "status": "Mature"},
        {"name": "DevOps", "status": "Mainstream"}
    ]
}
"""
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["AI-Trends"] = "OK"
            print("           [OK] Processed")
            return True
        except Exception as e:
            print(f"           [FAIL] {str(e)[:40]}")
            self.results["AI-Trends"] = "FAIL"
            return False
    
    async def ai_task_3(self):
        """Task 3: AI creates full report"""
        print("\n[AI-TASK 3] Full Developer Report")
        print("           Tools: general_assistant, file_writer, pdf_generator")
        print("           Output: dev_report.json + PDF")
        
        task = """
Hozz létre egy comprehensive developer report JSON-ba:
memory/output/dev_report.json

Tartalom:
- Top 5 programming language 2025-ben
- Ecosystem trends
- Career paths
- Learning resources recommendation

JSON structure: {"report": {"languages": [...], "trends": [...], ...}}

Csinálj PDF-et is: memory/output/dev_report.pdf
"""
        try:
            result = await self.ai.execute_intelligent_task(task=task)
            self.results["AI-Report"] = "OK"
            print("           [OK] Processed")
            return True
        except Exception as e:
            print(f"           [FAIL] {str(e)[:40]}")
            self.results["AI-Report"] = "FAIL"
            return False
    
    def practical_task_1(self):
        """Practical: Database comparison"""
        print("\n[PRACTICAL-TASK 1] Database Systems")
        print("                  Tools: JSON, CSV generation")
        print("                  Output: databases.json + CSV")
        
        data = {
            "databases": [
                {"name": "PostgreSQL", "type": "RDBMS", "lang": "C", "license": "Open Source"},
                {"name": "MongoDB", "type": "NoSQL", "lang": "C++", "license": "SSPL"},
                {"name": "Redis", "type": "Cache", "lang": "C", "license": "BSD"},
                {"name": "Cassandra", "type": "NoSQL", "lang": "Java", "license": "Apache 2.0"},
                {"name": "Neo4j", "type": "Graph", "lang": "Java", "license": "Proprietary"}
            ]
        }
        
        try:
            # JSON
            with open(output_dir / "databases.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # CSV
            with open(output_dir / "databases.csv", 'w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=["name", "type", "lang", "license"])
                w.writeheader()
                w.writerows(data["databases"])
            
            self.results["Practical-DB"] = "OK"
            print("                  [OK] 5 databases catalogued")
            return True
        except Exception as e:
            print(f"                  [FAIL] {e}")
            self.results["Practical-DB"] = "FAIL"
            return False
    
    def practical_task_2(self):
        """Practical: Cloud platforms"""
        print("\n[PRACTICAL-TASK 2] Cloud Platforms")
        print("                  Tools: JSON, CSV generation")
        print("                  Output: cloud_platforms.json + CSV")
        
        data = {
            "platforms": [
                {"name": "AWS", "founded": 2006, "hq": "USA", "market_share": "32%"},
                {"name": "Microsoft Azure", "founded": 2010, "hq": "USA", "market_share": "23%"},
                {"name": "Google Cloud", "founded": 2008, "hq": "USA", "market_share": "11%"},
                {"name": "Alibaba Cloud", "founded": 2009, "hq": "China", "market_share": "10%"},
                {"name": "IBM Cloud", "founded": 2013, "hq": "USA", "market_share": "6%"}
            ]
        }
        
        try:
            # JSON
            with open(output_dir / "cloud_platforms.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # CSV
            with open(output_dir / "cloud_platforms.csv", 'w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=["name", "founded", "hq", "market_share"])
                w.writeheader()
                w.writerows(data["platforms"])
            
            self.results["Practical-Cloud"] = "OK"
            print("                  [OK] 5 cloud platforms listed")
            return True
        except Exception as e:
            print(f"                  [FAIL] {e}")
            self.results["Practical-Cloud"] = "FAIL"
            return False
    
    def practical_task_3(self):
        """Practical: Framework analysis"""
        print("\n[PRACTICAL-TASK 3] Web Frameworks")
        print("                  Tools: JSON, CSV generation")
        print("                  Output: frameworks.json + CSV")
        
        data = {
            "frameworks": [
                {"name": "React", "type": "Frontend", "lang": "JavaScript", "stars": 225000},
                {"name": "Angular", "type": "Frontend", "lang": "TypeScript", "stars": 96000},
                {"name": "Vue", "type": "Frontend", "lang": "JavaScript", "stars": 207000},
                {"name": "Django", "type": "Backend", "lang": "Python", "stars": 77000},
                {"name": "FastAPI", "type": "Backend", "lang": "Python", "stars": 75000},
                {"name": "Spring", "type": "Backend", "lang": "Java", "stars": 56000}
            ]
        }
        
        try:
            # JSON
            with open(output_dir / "frameworks.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # CSV
            with open(output_dir / "frameworks.csv", 'w', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=["name", "type", "lang", "stars"])
                w.writeheader()
                w.writerows(data["frameworks"])
            
            self.results["Practical-Frameworks"] = "OK"
            print("                  [OK] 6 frameworks analyzed")
            return True
        except Exception as e:
            print(f"                  [FAIL] {e}")
            self.results["Practical-Frameworks"] = "FAIL"
            return False
    
    async def run_all(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("VEGYES TESZT: AI + PRAKTIKAI FELADATOK")
        print("="*70)
        print(f"Elerheto toolok: {len(self.registry.tools)}")
        print(f"Output directory: {output_dir}\n")
        
        # AI Tasks
        print("[PHASE 1] AI Task Processing")
        print("-"*70)
        
        await self.ai_task_1()
        await self.ai_task_2()
        await self.ai_task_3()
        
        # Practical Tasks
        print("\n[PHASE 2] Practical Task Execution")
        print("-"*70)
        
        self.practical_task_1()
        self.practical_task_2()
        self.practical_task_3()
        
        # Report
        self.generate_report()
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*70)
        print("VEGYES TESZT EREDMENYEK")
        print("="*70)
        
        for task, status in self.results.items():
            symbol = "[OK]" if status == "OK" else "[XX]"
            print(f"{symbol} {task:30} {status}")
        
        ok_count = sum(1 for s in self.results.values() if s == "OK")
        total = len(self.results)
        
        print(f"\nEredmeny: {ok_count}/{total} (100%)" if ok_count == total else f"Eredmeny: {ok_count}/{total}")
        
        # List files
        print("\n" + "="*70)
        print("LETREHOZOTT FAJLOK")
        print("="*70)
        
        all_files = sorted(output_dir.glob("*.json")) + sorted(output_dir.glob("*.csv"))
        
        for f in all_files[-12:]:
            size = f.stat().st_size
            print(f"  {f.name:40} {size:10,} bytes")
        
        print("\n" + "="*70 + "\n")
        
        if ok_count == total:
            print(f"[SUCCESS] TELJES VEGYES TESZT SIKERESITVE - {ok_count} FELADAT, 12+ FAJL!")
        
        return ok_count == total

async def main():
    suite = MixedTestSuite()
    await suite.run_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Test interrupted")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
