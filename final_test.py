#!/usr/bin/env python
"""Simple final test - no unicode issues."""

import asyncio
import json
from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

async def main():
    """Test all three task types."""
    orchestrator = SmartToolOrchestrator()
    
    tests = [
        ("Create a test.json file", "creation"),
        ("Extract stars from github", "analysis"),
        ("Run a dir command", "execution")
    ]
    
    for task, expected_type in tests:
        print(f"\n{'='*60}")
        print(f"Test: {task}")
        print(f"Expected type: {expected_type}")
        print('-'*60)
        
        result = await orchestrator.orchestrate_task(task)
        
        # Show key info
        print(f"Task analysis type: {result.get('task_analysis', {}).get('task_type')}")
        print(f"Tools used: {result.get('tools_used')}")
        print(f"Status: {result.get('status')}")
        
        if result.get('execution_results'):
            for exe_result in result['execution_results']:
                tool_name = exe_result.get('tool', {}).get('name')
                exec_status = exe_result.get('status')
                print(f"  - {tool_name}: {exec_status}")
                if exec_status == 'success':
                    output = exe_result.get('result', {}).get('output', '')
                    print(f"    Output: {output[:100]}...")

asyncio.run(main())
print("\n" + "="*60)
print("All tests completed")
