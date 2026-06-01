#!/usr/bin/env python
"""Test browser automation through the fixed orchestrator."""

import asyncio
import json
from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

async def main():
    """Run browser automation task."""
    
    orchestrator = SmartToolOrchestrator()
    
    # Real browser automation tasks
    tasks = [
        "Open GitHub and search for 'asyncio' repository and count stars",
        "Visit python.org and find the current Python version",
        "Extract the top 5 trending repositories from GitHub today"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*80}")
        print(f"TASK {i}: {task}")
        print('='*80)
        
        try:
            result = await orchestrator.orchestrate_task(task)
            
            # Show results
            print(f"Analysis Type: {result.get('task_analysis', {}).get('task_type')}")
            print(f"Tools Used: {result.get('tools_used')}")
            print(f"Status: {result.get('status')}")
            
            # Show execution results
            if result.get('execution_results'):
                for exe_result in result['execution_results']:
                    tool_name = exe_result.get('tool', {}).get('name')
                    exec_status = exe_result.get('status')
                    print(f"\nTool: {tool_name}")
                    print(f"Status: {exec_status}")
                    
                    if exec_status == 'success':
                        output = exe_result.get('result', {}).get('output', '')
                        print(f"Output: {output[:300]}...")
                    else:
                        error = exe_result.get('result', {}).get('error', '')
                        print(f"Error: {error[:200]}")
            
            # Show final output summary
            if result.get('final_output'):
                print(f"\nSummary: {result['final_output'].get('summary')}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    print(f"\n{'='*80}")
    print("Browser automation tests completed")
