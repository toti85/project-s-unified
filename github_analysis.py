#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending Analysis - Direct Tool + AI
"""

import sys
import asyncio
from pathlib import Path
import json

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.tools.implementations.web_tools import WebPageFetchTool
from core.super_intelligent_ai import SuperIntelligentAI
from bs4 import BeautifulSoup

async def analyze_github_trending():
    """Analyze GitHub trending with combined approach"""
    
    print("\n" + "="*80)
    print("GITHUB TRENDING ANALYSIS")
    print("="*80)
    print()
    
    # Step 1: Fetch raw content
    print("[STEP 1] Fetching GitHub Trending page...")
    browser = WebPageFetchTool()
    
    result = await browser.execute(url="https://github.com/trending")
    
    if not result.get('success'):
        print(f"❌ Failed to fetch: {result.get('error')}")
        return
    
    print(f"✅ Fetched! Content size: {len(result['html'])} bytes")
    print()
    
    # Step 2: Parse HTML and extract repos
    print("[STEP 2] Parsing HTML and extracting repositories...")
    html = result['html']
    soup = BeautifulSoup(html, 'html.parser')
    
    repos = []
    repo_articles = soup.find_all('article', class_='Box-row')[:10]
    
    for article in repo_articles:
        try:
            # Get repo name/link
            h2 = article.find('h2')
            if not h2:
                continue
            
            link = h2.find('a')
            if not link:
                continue
            
            repo_name = link.get_text(strip=True)
            repo_url = link.get('href', '').strip()
            
            # Get description
            desc_elem = article.find('p', class_='col-9')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Get language
            lang_elem = article.find('span', attrs={'itemprop': 'programmingLanguage'})
            language = lang_elem.get_text(strip=True) if lang_elem else "Unknown"
            
            # Get stars
            stars_elem = article.find('span', class_='d-inline-block float-sm-right')
            stars = stars_elem.get_text(strip=True) if stars_elem else "N/A"
            
            repos.append({
                'name': repo_name,
                'url': f"https://github.com{repo_url}",
                'description': description,
                'language': language,
                'stars': stars
            })
        except Exception as e:
            continue
    
    print(f"✅ Extracted {len(repos)} repositories!")
    print()
    
    # Step 3: Display results
    print("[STEP 3] Top 5 Trending Repositories:")
    print("-" * 80)
    
    for i, repo in enumerate(repos[:5], 1):
        print(f"\n{i}. {repo['name']}")
        print(f"   URL: {repo['url']}")
        print(f"   Language: {repo['language']}")
        print(f"   Stars: {repo['stars']}")
        print(f"   Description: {repo['description'][:100]}...")
    
    print()
    print("="*80)
    
    # Step 4: Use AI to summarize
    print("\n[STEP 4] AI Summary...")
    print("-" * 80)
    
    ai = SuperIntelligentAI()
    
    repos_text = "\n".join([
        f"- {r['name']} ({r['language']}) - {r['description'][:50]}..."
        for r in repos[:5]
    ])
    
    task = f"""
    Analyze these trending GitHub repositories and provide insights:
    
    {repos_text}
    
    What programming languages are trending? What are the main use cases?
    Provide 2-3 sentence summary.
    """
    
    try:
        ai_result = await ai.execute_intelligent_task(task=task)
        if isinstance(ai_result, dict) and 'output' in ai_result:
            print(ai_result['output'])
        else:
            print(str(ai_result)[:500])
    except Exception as e:
        print(f"AI analysis: {str(e)[:200]}")
    
    print()
    print("="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(analyze_github_trending())
    except KeyboardInterrupt:
        print("\n❌ Interrupted")
    except Exception as e:
        print(f"Error: {str(e)}")
