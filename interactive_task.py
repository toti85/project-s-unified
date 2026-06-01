#!/usr/bin/env python
"""Interactive Task Interface - Give tasks to the AI system."""

import asyncio
from src.core.super_intelligent_ai import SuperIntelligentAI

async def interactive_task_interface():
    """Interactive interface to give tasks to AI."""
    
    print("="*80)
    print("AI TASK INTERFACE - Interactive Mode")
    print("="*80)
    print()
    
    # Initialize AI
    print("Initializing AI system...")
    ai = SuperIntelligentAI(use_meta_controller=True)  # Meta layer ENABLED
    print("[OK] AI Ready")
    print("[OK] Meta Layer: ENABLED")
    print()
    
    print("SYSTEM CAPABILITIES:")
    print("  - File creation and editing")
    print("  - Web browsing and scraping")
    print("  - System command execution")
    print("  - Browser automation")
    print("  - Meta-learning enabled")
    print()
    
    # Example tasks
    example_tasks = [
        "Create a status.txt file with current system info",
        "Extract top 5 Python repositories from GitHub",
        "List files in current directory",
        "Create a config.json file with settings"
    ]
    
    print("EXAMPLE TASKS YOU CAN GIVE:")
    for i, task in enumerate(example_tasks, 1):
        print(f"  {i}. {task}")
    print()
    
    # Interactive loop
    while True:
        print("-" * 80)
        user_input = input("Enter task (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            print("Please enter a task.")
            continue
        
        print(f"\nProcessing task: {user_input}")
        print("Please wait...")
        print()
        
        try:
            result = await ai.execute_intelligent_task(user_input, use_meta_controller=True)
            
            print(f"Status: {result.get('success', False)}")
            print(f"Task type: {result.get('task_type', 'unknown')}")
            
            output = result.get('output', 'No output')
            if isinstance(output, str):
                print(f"\nOutput:\n{output[:500]}")
                if len(output) > 500:
                    print("... (truncated)")
            
            print()
            
        except KeyboardInterrupt:
            print("\nTask cancelled.")
            break
        except Exception as e:
            print(f"Error: {str(e)[:200]}")
            print()

if __name__ == "__main__":
    try:
        asyncio.run(interactive_task_interface())
    except KeyboardInterrupt:
        print("\nExiting...")
