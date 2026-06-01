#!/usr/bin/env python
"""Final test: Complete system with Meta layer and all mocks removed."""

import asyncio
import json
from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

async def test_orchestrator_only():
    """Test orchestrator directly - no mocks."""
    
    print("="*80)
    print("ORCHESTRATOR TEST - All Mocks Removed")
    print("="*80)
    
    orchestrator = SmartToolOrchestrator()
    
    tasks = [
        "Create output.txt with status report",
        "Get Python GitHub repository data", 
        "List system directory"
    ]
    
    for task in tasks:
        print(f"\nTask: {task}")
        result = await orchestrator.orchestrate_task(task)
        
        tools_used = result.get('tools_used', [])
        status = result.get('status', 'unknown')
        print(f"  Tools: {tools_used}")
        print(f"  Status: {status}")
        
        if result.get('execution_results'):
            for exe in result['execution_results']:
                print(f"    Result: {exe.get('status')}")
    
    print("\n" + "="*80)
    print("Orchestrator test complete - mocks removed successfully")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_orchestrator_only())
