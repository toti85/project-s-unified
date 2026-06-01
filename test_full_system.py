#!/usr/bin/env python
"""Test complete system with Meta layer enabled."""

import asyncio
from src.core.super_intelligent_ai import SuperIntelligentAI

async def test_complete_system():
    """Test the complete AI system with Meta layer."""
    
    print("="*80)
    print("FULL SYSTEM TEST - META LAYER ENABLED")
    print("="*80)
    
    # Initialize with Meta layer ENABLED
    ai = SuperIntelligentAI(use_meta_controller=True)
    print("[OK] AI initialized WITH Meta layer")
    print("")
    
    tasks = [
        "Create a report.txt file with AI project status",
        "Extract top Python repositories from GitHub",
        "Run a system command to list files"
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*80}")
        print(f"TASK {i}: {task}")
        print('='*80)
        
        try:
            result = await ai.execute_intelligent_task(task, use_meta_controller=True)
            
            print(f"\nSuccess: {result.get('success', False)}")
            print(f"Task Type: {result.get('task_type', 'unknown')}")
            
            # Show output
            output = result.get('output', 'No output')
            if isinstance(output, str):
                print(f"Output: {output[:400]}...")
            else:
                print(f"Output: {str(output)[:400]}...")
                
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\n{'='*80}")
    print("TESTS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_complete_system())
