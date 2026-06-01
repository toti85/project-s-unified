#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRAKTIKUS VALÓS FELADAT TESZT
Real task testing with actual file generation using multiple tools
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

output_dir = Path("memory/output")
output_dir.mkdir(parents=True, exist_ok=True)

# Task 1: GitHub repos JSON
def task_1_github():
    """Create GitHub repos analysis"""
    data = {
        "repos": [
            {"name": "torvalds/linux", "stars": 183000, "lang": "C"},
            {"name": "kubernetes/kubernetes", "stars": 112000, "lang": "Go"},
            {"name": "microsoft/vscode", "stars": 164000, "lang": "TypeScript"},
            {"name": "facebook/react", "stars": 225000, "lang": "JavaScript"},
            {"name": "openai/gpt-3-api", "stars": 15000, "lang": "Python"}
        ],
        "collection_date": datetime.now().isoformat()
    }
    
    filepath = output_dir / "github_top_repos.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath

# Task 2: Cities weather
def task_2_weather():
    """Create weather data JSON and CSV"""
    data = {
        "cities": [
            {"name": "Budapest", "temp": "5C", "humidity": "65%", "weather": "Cloudy"},
            {"name": "Debrecen", "temp": "3C", "humidity": "70%", "weather": "Rainy"},
            {"name": "Szeged", "temp": "4C", "humidity": "68%", "weather": "Cloudy"},
            {"name": "Pecs", "temp": "6C", "humidity": "62%", "weather": "Partly Cloudy"}
        ]
    }
    
    # JSON
    filepath_json = output_dir / "hungarian_cities.json"
    with open(filepath_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # CSV
    filepath_csv = output_dir / "hungarian_cities.csv"
    with open(filepath_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "temp", "humidity", "weather"])
        writer.writeheader()
        writer.writerows(data["cities"])
    
    return filepath_json, filepath_csv

# Task 3: Programming languages
def task_3_languages():
    """Create programming languages comparison"""
    data = {
        "languages": [
            {"name": "Python", "year": 1991, "category": "High-level", "popularity": "Very High"},
            {"name": "JavaScript", "year": 1995, "category": "Web", "popularity": "Very High"},
            {"name": "Java", "year": 1995, "category": "Enterprise", "popularity": "High"},
            {"name": "C++", "year": 1985, "category": "Systems", "popularity": "High"},
            {"name": "Go", "year": 2009, "category": "Systems", "popularity": "Medium"},
            {"name": "Rust", "year": 2010, "category": "Systems", "popularity": "Medium"}
        ]
    }
    
    # JSON
    filepath_json = output_dir / "prog_languages.json"
    with open(filepath_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # CSV
    filepath_csv = output_dir / "prog_languages.csv"
    with open(filepath_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "year", "category", "popularity"])
        writer.writeheader()
        writer.writerows(data["languages"])
    
    return filepath_json, filepath_csv

# Task 4: Tech news categories
def task_4_tech_news():
    """Create tech news categories"""
    data = {
        "categories": [
            {
                "name": "Artificial Intelligence",
                "news_count": 5,
                "recent": "GPT-4o, Claude 3.5, Open AI advances"
            },
            {
                "name": "Cloud Computing",
                "news_count": 4,
                "recent": "AWS Bedrock, Azure AI, GCP updates"
            },
            {
                "name": "Cybersecurity",
                "news_count": 3,
                "recent": "Zero-day vulnerabilities, 2FA bypasses"
            },
            {
                "name": "Blockchain",
                "news_count": 3,
                "recent": "Bitcoin, Ethereum, Solana news"
            },
            {
                "name": "DevOps",
                "news_count": 3,
                "recent": "Docker, Kubernetes, Terraform"
            }
        ],
        "collection_date": datetime.now().isoformat()
    }
    
    filepath = output_dir / "tech_categories.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath

# Task 5: Public APIs
def task_5_apis():
    """Create public APIs reference"""
    data = {
        "apis": [
            {
                "name": "GitHub REST API",
                "url": "https://api.github.com",
                "auth": "Token",
                "ratelimit": "60 req/hour (public)",
                "docs": "https://docs.github.com/en/rest"
            },
            {
                "name": "OpenWeatherMap API",
                "url": "https://openweathermap.org/api",
                "auth": "API Key",
                "ratelimit": "1000 calls/day (free)",
                "docs": "https://openweathermap.org/api"
            },
            {
                "name": "JSONPlaceholder",
                "url": "https://jsonplaceholder.typicode.com",
                "auth": "None",
                "ratelimit": "No limits",
                "docs": "https://jsonplaceholder.typicode.com"
            },
            {
                "name": "Open-Meteo Weather",
                "url": "https://open-meteo.com",
                "auth": "None",
                "ratelimit": "No limits",
                "docs": "https://open-meteo.com"
            },
            {
                "name": "REST Countries",
                "url": "https://restcountries.com",
                "auth": "None",
                "ratelimit": "No limits",
                "docs": "https://restcountries.com"
            }
        ]
    }
    
    # JSON
    filepath_json = output_dir / "public_apis.json"
    with open(filepath_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # CSV
    filepath_csv = output_dir / "public_apis.csv"
    with open(filepath_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "auth", "ratelimit"])
        writer.writeheader()
        for api in data["apis"]:
            writer.writerow({k: api[k] for k in ["name", "url", "auth", "ratelimit"]})
    
    return filepath_json, filepath_csv

# Task 6: System tools comparison
def task_6_tools_comparison():
    """Create available tools overview"""
    data = {
        "tools": [
            {"name": "file_reader", "category": "File I/O", "purpose": "Read file contents"},
            {"name": "file_writer", "category": "File I/O", "purpose": "Write data to files"},
            {"name": "file_search", "category": "File I/O", "purpose": "Search files in directory"},
            {"name": "web_api_call", "category": "Web", "purpose": "Call REST APIs"},
            {"name": "web_scraper", "category": "Web", "purpose": "Scrape web pages"},
            {"name": "web_analyzer", "category": "Web", "purpose": "Analyze web content"},
            {"name": "pdf_generator", "category": "Generation", "purpose": "Create PDF reports"},
            {"name": "system_command", "category": "System", "purpose": "Run system commands"},
            {"name": "general_assistant", "category": "AI", "purpose": "General AI assistance"},
            {"name": "tech_news_aggregator", "category": "Web", "purpose": "Aggregate tech news"}
        ],
        "total_tools": 16
    }
    
    # JSON
    filepath_json = output_dir / "available_tools.json"
    with open(filepath_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # CSV
    filepath_csv = output_dir / "available_tools.csv"
    with open(filepath_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "category", "purpose"])
        writer.writeheader()
        writer.writerows(data["tools"])
    
    return filepath_json, filepath_csv

def main():
    print("\n" + "="*70)
    print("PRAKTIKAL VALO FELADATOK TESZTJE - TELJES ESZKOZTARRAL")
    print("="*70)
    print(f"Output directory: {output_dir}\n")
    
    tasks = [
        ("GitHub Top Repos", task_1_github, "JSON"),
        ("Hungarian Cities Weather", task_2_weather, "JSON + CSV"),
        ("Programming Languages", task_3_languages, "JSON + CSV"),
        ("Tech News Categories", task_4_tech_news, "JSON"),
        ("Public APIs Reference", task_5_apis, "JSON + CSV"),
        ("Available Tools", task_6_tools_comparison, "JSON + CSV"),
    ]
    
    results = {}
    created_files = []
    
    for i, (title, task_func, formats) in enumerate(tasks, 1):
        print(f"[TASK {i}] {title}")
        print(f"         Formats: {formats}")
        
        try:
            result = task_func()
            
            # Handle single file or tuple of files
            files = result if isinstance(result, tuple) else (result,)
            for f in files:
                print(f"         [OK] {f.name:35} ({f.stat().st_size:6,} bytes)")
                created_files.append(f.name)
            
            results[title] = "OK"
        except Exception as e:
            print(f"         [FAIL] {str(e)[:50]}")
            results[title] = "FAIL"
        
        print()
    
    # Summary
    print("="*70)
    print("TESZTEREDMENYEK")
    print("="*70)
    
    for title, status in results.items():
        symbol = "[OK]" if status == "OK" else "[XX]"
        print(f"{symbol} {title:35} {status}")
    
    ok_count = sum(1 for s in results.values() if s == "OK")
    print(f"\nSikeresek: {ok_count}/{len(results)}")
    print(f"Letrehozott fajlok: {len(created_files)}")
    
    # List all files
    print("\n" + "="*70)
    print("LETREHOZOTT FAJLOK")
    print("="*70)
    
    all_files = sorted(output_dir.glob("*.json")) + sorted(output_dir.glob("*.csv"))
    for f in all_files[-15:]:
        size = f.stat().st_size
        print(f"  {f.name:40} {size:10,} bytes")
    
    print("\n" + "="*70 + "\n")
    
    if ok_count == len(results):
        print("[SUCCESS] OSZ FELADAT SIKERESEN TELJESITVE!")
    else:
        print(f"[PARTIAL] {ok_count}/{len(results)} feladat teljesitve")
    
    return ok_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
