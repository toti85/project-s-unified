#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOMPLETT AI TESZT - Valós feladatok AI-val

Ez a teszt valós AI-s feladatokat futtat az OpenRouter API-val.
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
import asyncio

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path.cwd() / "src"))

output_dir = Path("memory/output")
output_dir.mkdir(parents=True, exist_ok=True)

async def test_1_direct_ai_query():
    """Test 1: Direkt AI kérés - Programozási nyelvek"""
    print("\n[TEST 1] Direkt AI kérés - Programozási nyelvek")
    print("-" * 60)
    
    try:
        import httpx
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("✗ API key missing")
            return False
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Project-S"
        }
        
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": "Adj vissza egy JSON-t a 5 legjobb backend programozási nyelvről ezzel a formátummal: {\"languages\": [{\"name\": \"\", \"rating\": 1-10, \"reason\": \"\"}]}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                print("✓ AI válasza (első 200 char):")
                print(ai_response[:200] + "...")
                
                # Save to file
                result_file = output_dir / "ai_backend_languages.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(ai_response)
                
                print(f"✓ Mentve: {result_file.name}")
                return True
            else:
                print(f"✗ API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_2_ai_analysis():
    """Test 2: AI analízis - Web technológiák"""
    print("\n[TEST 2] AI analízis - Web technológiák")
    print("-" * 60)
    
    try:
        import httpx
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("✗ API key missing")
            return False
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Project-S"
        }
        
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": "Összefoglalj 3 mondatban a legjobb modern web frontend keretrendszereket (React, Vue, Angular, Svelte) és azok előnyeit."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                print("✓ AI válasza:")
                print(ai_response[:300] + "...")
                
                # Save to file
                result_file = output_dir / "ai_web_frameworks.txt"
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(ai_response)
                
                print(f"✓ Mentve: {result_file.name}")
                return True
            else:
                print(f"✗ API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_3_ai_data_generation():
    """Test 3: AI adatgenerálás - Tech trends"""
    print("\n[TEST 3] AI adatgenerálás - Tech trends")
    print("-" * 60)
    
    try:
        import httpx
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("✗ API key missing")
            return False
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Project-S"
        }
        
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": "Generálj egy JSON-t a 2025-es tech trendekről ezzel a formátummal: {\"trends\": [{\"trend\": \"\", \"relevance\": \"high/medium/low\", \"description\": \"\"}]}"
                }
            ],
            "temperature": 0.8,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                print("✓ AI válasza (első 200 char):")
                print(ai_response[:200] + "...")
                
                # Save to file
                result_file = output_dir / "ai_tech_trends.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(ai_response)
                
                print(f"✓ Mentve: {result_file.name}")
                return True
            else:
                print(f"✗ API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main():
    print("\n" + "="*60)
    print("KOMPLETT AI TESZT - VALÓS FELADATOK")
    print("="*60)
    
    tests = [
        test_1_direct_ai_query,
        test_2_ai_analysis,
        test_3_ai_data_generation
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print("TESZTEREDMÉNYEK")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"[{i}] {test.__doc__[:40]:40} {status}")
    
    print("\n" + "="*60)
    print(f"ÖSSZESEN: {passed}/{total} teszt sikeres")
    
    if passed == total:
        print("✓ AI TELJESEN MŰKÖDŐKÉPES!")
    elif passed >= 2:
        print("✓ AI JÓL MŰKÖDIK (szinte teljesen)")
    else:
        print("✗ AI PROBLÉMA")
    
    print("="*60)
    
    # Save summary
    summary = {
        "test": "Complete AI Test",
        "timestamp": datetime.now().isoformat(),
        "results": {
            "direct_query": results[0],
            "analysis": results[1],
            "data_generation": results[2]
        },
        "passed": passed,
        "total": total,
        "status": "FULLY_OPERATIONAL" if passed == total else "PARTIAL" if passed >= 2 else "FAILING"
    }
    
    summary_file = output_dir / "ai_complete_test_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Összefoglaló mentve: {summary_file.name}")
    
    return 0 if passed >= 2 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
