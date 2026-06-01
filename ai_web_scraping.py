#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Web Scraping - Simple Tool Version
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

async def run_web_task():
    """Run web scraping task with AI"""
    
    print("\n" + "="*80)
    print("AI WEB SCRAPING TASK")
    print("="*80)
    print()
    
    ai = SuperIntelligentAI()
    print("[OK] AI System initialized")
    print()
    
    # Task: Get trending repos from GitHub
    task = """
    Fetch and analyze the GitHub trending page (https://github.com/trending).
    
    Extract:
    1. Top 5 trending repositories
    2. For each repo: name, description, language
    3. Return as formatted list
    """
    
    print("[TASK]:")
    print("-" * 80)
    print(task)
    print("-" * 80)
    print()
    print("[AI PROCESSING...]")
    print()
    
    result = await ai.execute_intelligent_task(task=task)
    
    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    
    if isinstance(result, dict):
        if 'output' in result:
            print(result['output'])
        else:
            print(str(result)[:1500])
    else:
        print(result)
    
    print("\n" + "="*80)
    print("✅ AI TASK COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_web_task())
