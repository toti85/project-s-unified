#!/usr/bin/env python
"""Debug test to check what's actually returned from orchestrator."""

import asyncio
import json
from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

async def debug_test():
    """Test orchestrator directly."""
    
    orchestrator = SmartToolOrchestrator()
    
    # Test task
    task = "Create a JSON file with test data"
    
    print(f"Testing task: {task}")
    print("-" * 80)
    
    # Test orchestration
    result = await orchestrator.orchestrate_task(task)
    
    print(f"\nResult keys: {result.keys()}")
    print(f"\nFull result:")
    print(json.dumps(result, indent=2, default=str))

asyncio.run(debug_test())
