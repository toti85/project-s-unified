#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Scraping Task - Test with Real Output
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

async def run_task():
    """Run a web scraping task"""
    
    print("\n" + "="*80)
    print("WEB SCRAPING TASK - List GitHub Trending Repos")
    print("="*80)
    print()
    
    ai = SuperIntelligentAI()
    
    # Task: Get trending repos from GitHub
    task = """
    Find the top 5 trending Python repositories from GitHub.
    
    For each repo, get:
    1. Repository name
    2. Owner/Author
    3. Brief description
    4. Star count
    5. Main language
    
    Return as a formatted text summary.
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
    print(result)

if __name__ == "__main__":
    asyncio.run(run_task())
