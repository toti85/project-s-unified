#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Direct Task - English Version
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
    """Run a simple task"""
    
    print("\n" + "="*80)
    print("DIRECT TASK EXECUTION - English Version")
    print("="*80)
    print()
    
    ai = SuperIntelligentAI()
    print("[OK] AI System ready")
    print()
    
    # Simple task in English
    task = """
    Create a JSON file with top 10 most populous countries (2025):
    - Country name
    - Population (estimated)
    - Country code (2 letters)
    - Continent
    
    Save to: memory/output/countries_data.json
    
    Use real, accurate data only.
    """
    
    print("[TASK]:")
    print("-" * 80)
    print(task)
    print("-" * 80)
    print()
    print("[EXECUTING...]")
    print()
    
    result = await ai.execute_intelligent_task(task=task)
    
    print("\n" + "="*80)
    print("DONE!")
    print("="*80)
    
    # Check for new files
    output_dir = Path("memory/output")
    if output_dir.exists():
        print("\nCreated files:")
        for f in sorted(output_dir.glob("countries*.json")):
            print(f"  ✓ {f.name}")

if __name__ == "__main__":
    asyncio.run(run_task())
