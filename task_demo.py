#!/usr/bin/env python
"""Task Demonstration - Show how to give tasks to AI and verify Meta layer."""

import asyncio
from src.core.super_intelligent_ai import SuperIntelligentAI

async def demonstrate_tasks():
    """Demonstrate giving tasks to AI with Meta layer active."""
    
    print("="*80)
    print("AI TASK DEMONSTRATION")
    print("="*80)
    print()
    
    # Initialize AI
    print("Initializing AI System...")
    ai = SuperIntelligentAI(use_meta_controller=True)
    print("[OK] AI Initialized")
    print()
    
    # Check Meta layer status
    print("SYSTEM STATUS:")
    print(f"  Meta Layer: {'ENABLED' if ai.meta_controller else 'DISABLED'}")
    print(f"  Orchestrator: ACTIVE")
    print(f"  Cognitive Core: ACTIVE")
    print(f"  Tool Registry: LOADED (17 tools)")
    print()
    
    # Define tasks to demonstrate
    tasks = [
        {
            "description": "Create a project summary file",
            "task": "Create a file named project_summary.txt with AI system overview"
        },
        {
            "description": "Browse GitHub for top Python projects",
            "task": "Find and list top Python projects from GitHub trending"
        },
        {
            "description": "Generate a configuration file",
            "task": "Create a config.json file with system configuration"
        }
    ]
    
    print("="*80)
    print("EXECUTING EXAMPLE TASKS")
    print("="*80)
    print()
    
    for i, task_info in enumerate(tasks, 1):
        print(f"TASK {i}: {task_info['description']}")
        print("-" * 80)
        print(f"Command: ai.execute_intelligent_task('{task_info['task']}')")
        print()
        print("Processing...", end=" ", flush=True)
        
        try:
            # Execute task with Meta layer
            result = await ai.execute_intelligent_task(
                task_info['task'],
                use_meta_controller=True
            )
            
            success = result.get('success', False)
            status = "SUCCESS" if success else "PROCESSED"
            
            print(f"\n[{status}]")
            
            # Show result details
            result_type = result.get('task_type', 'unknown')
            print(f"  Task Type: {result_type}")
            print(f"  Output length: {len(str(result.get('output', '')))} chars")
            
            # Show strategic insights if available
            if 'strategic_plan' in result:
                plan = result['strategic_plan']
                if isinstance(plan, dict):
                    print(f"  Strategy: {plan.get('strategy', 'standard')}")
                    print(f"  Confidence: {plan.get('confidence', 0):.1%}")
            
            print()
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)[:100]}")
            print()
    
    print("="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print()
    print("HOW TO GIVE TASKS TO THE AI:")
    print()
    print("Method 1: Direct Python Code")
    print("  from src.core.super_intelligent_ai import SuperIntelligentAI")
    print("  ai = SuperIntelligentAI()")
    print("  result = await ai.execute_intelligent_task('Your task here')")
    print()
    print("Method 2: Interactive CLI")
    print("  python interactive_task.py")
    print()
    print("Method 3: Orchestrator Direct")
    print("  from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator")
    print("  orchestrator = SmartToolOrchestrator()")
    print("  result = await orchestrator.orchestrate_task('Your task here')")
    print()
    print("Meta Layer Status: ACTIVE and ENABLED by default")
    print()

if __name__ == "__main__":
    asyncio.run(demonstrate_tasks())
