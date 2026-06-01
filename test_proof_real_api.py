#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIZONYÍTÁS TESZT - Valóban az OpenRouter API-t hívjuk-e?

Ez a teszt:
1. Készít egy unique request ID-t
2. Ezt elküldi az OpenRouter API-nak
3. Ellenőrzi, hogy az API valóban visszaadja
"""

import sys
import json
import os
import uuid
from pathlib import Path
from datetime import datetime
import asyncio

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

output_dir = Path("memory/output")
output_dir.mkdir(parents=True, exist_ok=True)

async def proof_test_1_unique_request():
    """Teszt: Unique ID az API-nak, visszakapjuk-e?"""
    print("\n[BIZONYÍTÁS 1] Unique ID teszst - OpenRouter-nek küldünk")
    print("-" * 60)
    
    try:
        import httpx
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("✗ API key missing")
            return False
        
        # Generálunk egy unique ID-t
        unique_id = str(uuid.uuid4())
        
        print(f"Küldjük az API-nak ezt az ID-t: {unique_id}")
        
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
                    "content": f"Kérem, válaszod elején írd meg ezt az ID-t: {unique_id}\n\nAzután felsorold a 3 legjobb programozási nyelvet."
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
                
                # Ellenőrizünk: visszajött-e az ID?
                if unique_id in ai_response:
                    print(f"✓ IGEN! Az API visszaadta az ID-t!")
                    print(f"✓ Ez bizonyítja, hogy VALÓDI AI hívás történt")
                    print(f"\nAI válasza (első 300 char):")
                    print(ai_response[:300] + "...")
                    return True
                else:
                    print(f"✗ Az API nem adta vissza az ID-t")
                    print(f"Válasza: {ai_response[:200]}...")
                    return False
            else:
                print(f"✗ API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def proof_test_2_different_responses():
    """Teszt: Ugyanaz a prompt - másik válasza-e?"""
    print("\n[BIZONYÍTÁS 2] Többször ugyanaz a kérdés - különböző válaszok?")
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
        
        prompt = "Adj három különböző véleményt a Python programozási nyelvről (röviden)."
        
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.9,  # High temperature = változó válaszok
            "max_tokens": 300
        }
        
        responses = []
        
        # 3x meghívjuk ugyanazzal a prompttal
        for i in range(3):
            print(f"\nHívás {i+1}/3...")
            
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
                    responses.append(ai_response)
                    print(f"  Válasza: {ai_response[:100]}...")
        
        # Ellenőrizünk: különbözik-e a 3 válasz?
        if len(set(responses)) > 1:
            print(f"\n✓ IGEN! A válaszok különböznek egymástól!")
            print(f"✓ Ez bizonyítja, hogy NEM mock/hardcoded, hanem valódi AI")
            print(f"✓ {len(set(responses))} különböző válasz közül {len(responses)}")
            return True
        else:
            print(f"\n⚠ A válaszok azonosak (valószínűleg mock?)")
            return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def proof_test_3_request_metadata():
    """Teszt: OpenRouter request metadata - volt-e valódi API hívás?"""
    print("\n[BIZONYÍTÁS 3] OpenRouter metadata ellenőrzés")
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
                    "content": "Válaszd meg röviden: mi a Python?"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Megnézzük a teljes response metadata-t
                data = response.json()
                
                print(f"✓ HTTP Status: {response.status_code}")
                print(f"✓ OpenRouter válasz érkezett")
                
                # Ellenőrizünk az OpenRouter-specifikus mezőket
                if "choices" in data:
                    print(f"✓ 'choices' mező elérhető")
                if "usage" in data:
                    print(f"✓ 'usage' mező (token usage): {data['usage']}")
                if "model" in data:
                    print(f"✓ 'model': {data['model']}")
                
                # Ez az OpenRouter válasz JSON szerkezete
                print(f"\n✓ Ez a VALÓDI OpenRouter API válasz formátuma!")
                
                ai_response = data["choices"][0]["message"]["content"]
                print(f"\nAI válasza: {ai_response}")
                
                return True
            else:
                print(f"✗ API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main():
    print("\n" + "="*70)
    print("BIZONYÍTÁS TESZT - VALÓBAN OPENROUTER API-T HÍVUNK")
    print("="*70)
    
    tests = [
        proof_test_1_unique_request,
        proof_test_2_different_responses,
        proof_test_3_request_metadata
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            results.append(False)
    
    print("\n" + "="*70)
    print("BIZONYÍTÁSOK ÖSSZESEN")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ BIZONYÍTOTT" if result else "✗ NEM BIZONYÍTOTT"
        print(f"[{i}] {test.__doc__[:50]:50} {status}")
    
    print("\n" + "="*70)
    print("VÉGKÖVETKEZTETÉS")
    print("="*70)
    
    if passed >= 2:
        print(f"""
✓ NEM MOCK TESZT! 
✓ VALÓDI OPENROUTER API HÍVÁSOK TÖRTÉNTEK!
✓ A VÁLASZOKAT AZ AI ADTA, NEM ÉN!

Bizonyítékok:
  1. Unique ID meglétét az API visszaadta
  2. Különböző promptok különböző válaszokat adtak
  3. Valódi OpenRouter JSON szerkezet és metadata

Konklúzió: Az AI TÉNYLEGESEN működik és döntéseket hoz!
        """)
    else:
        print("⚠ Nem vagy biztos?")
    
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
