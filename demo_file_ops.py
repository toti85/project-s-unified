#!/usr/bin/env python
"""Demonstrate file creation and editing through AI system."""

import asyncio
from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

async def demo_file_operations():
    """Demo file creation and editing."""
    
    print("="*80)
    print("FILE OPERATIONS DEMO - Creation & Editing")
    print("="*80)
    print()
    
    orchestrator = SmartToolOrchestrator()
    
    # Task 1: Create a file
    print("1. FILE CREATION")
    print("-" * 80)
    task1 = "Create a file named project_status.txt with project information"
    print(f"Task: {task1}")
    
    result1 = await orchestrator.orchestrate_task(task1)
    print(f"Status: {result1.get('status')}")
    print(f"Tools used: {result1.get('tools_used')}")
    
    if result1.get('execution_results'):
        for exe in result1['execution_results']:
            if exe.get('status') == 'success':
                output = exe.get('result', {}).get('output', '')
                print(f"Result: {output[:200]}...")
    print()
    
    # Task 2: Create another file with JSON
    print("2. JSON FILE CREATION")
    print("-" * 80)
    task2 = "Create a file named config.json with JSON configuration data"
    print(f"Task: {task2}")
    
    result2 = await orchestrator.orchestrate_task(task2)
    print(f"Status: {result2.get('status')}")
    print(f"Tools used: {result2.get('tools_used')}")
    
    if result2.get('execution_results'):
        for exe in result2['execution_results']:
            if exe.get('status') == 'success':
                output = exe.get('result', {}).get('output', '')
                print(f"Result: {output[:200]}...")
    print()
    
    # Task 3: Create a report file
    print("3. REPORT FILE CREATION")
    print("-" * 80)
    task3 = "Generate a report.md with AI system analysis"
    print(f"Task: {task3}")
    
    result3 = await orchestrator.orchestrate_task(task3)
    print(f"Status: {result3.get('status')}")
    print(f"Tools used: {result3.get('tools_used')}")
    
    if result3.get('execution_results'):
        for exe in result3['execution_results']:
            if exe.get('status') == 'success':
                output = exe.get('result', {}).get('output', '')
                print(f"Result: {output[:200]}...")
    print()
    
    print("="*80)
    print("All file operations completed successfully!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(demo_file_operations())
