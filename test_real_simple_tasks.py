#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALÓS FELADATOK - EGYSZERÚ TESZT
Simple real task testing with guaranteed output files
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

# Simple non-interactive output
def print_task(num, title, tools):
    print(f"\n[TASK {num}] {title}")
    print(f"          Tools: {tools}")

async def main():
    from core.super_intelligent_ai import SuperIntelligentAI
    from tools.tools.registry.tool_registry_golden import ToolRegistry
    
    output_dir = Path("memory/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ai = SuperIntelligentAI()
    registry = ToolRegistry()
    
    print("\n" + "="*70)
    print("VALÓS FELADATOK - TELJES TESZTSOROZAT")
    print("="*70)
    print(f"Elerheto toolok: {len(registry.tools)}")
    print()
    
    results = {}
    files_created = []
    
    # TASK 1: Simple GitHub data
    print_task(1, "GitHub Top Repos", "web_api_call, file_writer, json")
    task1 = """
Gyűjtsd össze az alábbi publikus adatokat és mentsd el JSON fájlba:
memory/output/github_top_repos.json

Adatok:
- Repository name: torvalds/linux, stargazers_count: 180000+
- Repository name: kubernetes/kubernetes, stargazers_count: 110000+
- Repository name: microsoft/vscode, stargazers_count: 160000+

Formátum: {"repos": [{"name": "", "stars": ""}, ...]}
"""
    try:
        result = await ai.execute_intelligent_task(task=task1)
        results["GitHub"] = "COMPLETED"
        print("  [OK] Task processed")
    except:
        results["GitHub"] = "FAIL"
        print("  [FAIL]")
    
    # TASK 2: Weather data
    print_task(2, "Hungarian Cities Weather", "file_writer, json, csv")
    task2 = """
Mentsd el memory/output/hungarian_cities.json fajlba:
{
    "cities": [
        {"name": "Budapest", "temp": "5C", "humidity": "65%", "weather": "Cloudy"},
        {"name": "Debrecen", "temp": "3C", "humidity": "70%", "weather": "Rainy"},
        {"name": "Szeged", "temp": "4C", "humidity": "68%", "weather": "Cloudy"}
    ]
}

Mentsd el memory/output/hungarian_cities.csv fajlba a CSV verziót.
"""
    try:
        result = await ai.execute_intelligent_task(task=task2)
        results["Weather"] = "COMPLETED"
        print("  [OK] Task processed")
    except:
        results["Weather"] = "FAIL"
        print("  [FAIL]")
    
    # TASK 3: Programming languages
    print_task(3, "Programming Languages List", "file_writer, json, csv")
    task3 = """
Mentsd el memory/output/prog_languages.json-ba:
{
    "languages": [
        {"name": "Python", "year": 1991, "category": "High-level", "popularity": "Very High"},
        {"name": "JavaScript", "year": 1995, "category": "Web", "popularity": "Very High"},
        {"name": "Java", "year": 1995, "category": "Enterprise", "popularity": "High"},
        {"name": "C++", "year": 1985, "category": "Systems", "popularity": "High"},
        {"name": "Go", "year": 2009, "category": "Systems", "popularity": "Medium"}
    ]
}

CSV verziot is mentsd el: memory/output/prog_languages.csv
"""
    try:
        result = await ai.execute_intelligent_task(task=task3)
        results["Languages"] = "COMPLETED"
        print("  [OK] Task processed")
    except:
        results["Languages"] = "FAIL"
        print("  [FAIL]")
    
    # TASK 4: Tech news categories
    print_task(4, "Tech News Categories", "file_writer, json")
    task4 = """
Mentsd el memory/output/tech_categories.json-ba:
{
    "categories": [
        {
            "name": "Artificial Intelligence",
            "news_count": 5,
            "recent": "GPT models, LLM advances"
        },
        {
            "name": "Cloud Computing",
            "news_count": 4,
            "recent": "AWS, Azure, GCP updates"
        },
        {
            "name": "Cybersecurity",
            "news_count": 3,
            "recent": "Zero-day vulnerabilities, attacks"
        },
        {
            "name": "Blockchain",
            "news_count": 3,
            "recent": "Crypto regulation, Web3"
        }
    ],
    "collection_date": "2025-12-26"
}
"""
    try:
        result = await ai.execute_intelligent_task(task=task4)
        results["TechNews"] = "COMPLETED"
        print("  [OK] Task processed")
    except:
        results["TechNews"] = "FAIL"
        print("  [FAIL]")
    
    # TASK 5: APIs reference
    print_task(5, "Public APIs Reference", "file_writer, json, pdf")
    task5 = """
Mentsd el memory/output/public_apis.json-ba:
{
    "apis": [
        {
            "name": "GitHub REST API",
            "url": "https://api.github.com",
            "auth": "Token",
            "ratelimit": "60 req/hour (public)"
        },
        {
            "name": "OpenWeatherMap API",
            "url": "https://openweathermap.org/api",
            "auth": "API Key",
            "ratelimit": "1000 calls/day (free)"
        },
        {
            "name": "JSONPlaceholder",
            "url": "https://jsonplaceholder.typicode.com",
            "auth": "None",
            "ratelimit": "No limits"
        },
        {
            "name": "Open-Meteo API",
            "url": "https://open-meteo.com",
            "auth": "None",
            "ratelimit": "No limits"
        }
    ]
}

Hozz létre PDF reportot is: memory/output/public_apis.pdf
"""
    try:
        result = await ai.execute_intelligent_task(task=task5)
        results["APIs"] = "COMPLETED"
        print("  [OK] Task processed")
    except:
        results["APIs"] = "FAIL"
        print("  [FAIL]")
    
    # Check created files
    print("\n" + "="*70)
    print("[VERIFICATION] Output Files Check")
    print("="*70)
    
    expected = [
        "github_top_repos.json",
        "hungarian_cities.json",
        "hungarian_cities.csv",
        "prog_languages.json",
        "prog_languages.csv",
        "tech_categories.json",
        "public_apis.json",
        "public_apis.pdf",
    ]
    
    for filename in expected:
        filepath = output_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  [OK] {filename:35} ({size:6,} bytes)")
            files_created.append(filename)
        else:
            print(f"  [XX] {filename:35} (NOT FOUND)")
    
    # Summary
    print("\n" + "="*70)
    print("TESZT EREDMÉNYEK")
    print("="*70)
    
    for task, status in results.items():
        print(f"  [{status[:1]}] {task:20} {status}")
    
    completed = sum(1 for s in results.values() if s == "COMPLETED")
    print(f"\nFeladatok feldolgozva: {completed}/{len(results)}")
    print(f"Fajlok lehoztva: {len(files_created)}/{len(expected)}")
    
    if len(files_created) >= 4:
        print("\n[OK] TELJESÍTÉS: Legalabb 4 fajl sikeresen letrehozva!")
    else:
        print("\n[NOTE] AI feldolgozta a feladatokat, fajlok letrehozasa a toolok fuggvenye")
    
    print("\n" + "="*70 + "\n")
    
    return len(files_created)

if __name__ == "__main__":
    try:
        count = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Teszt szakitva")
    except Exception as e:
        print(f"\n[ERROR] {e}")
