#!/usr/bin/env python
"""Test if the orchestrator fix works - should now execute real tools instead of failing silently."""

import asyncio
import logging
from src.core.super_intelligent_ai import SuperIntelligentAI

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_real_execution():
    """Test task execution with the fixed orchestrator."""
    
    logger.info("=" * 80)
    logger.info("TESTING ORCHESTRATOR FIX - Real Tool Execution")
    logger.info("=" * 80)
    
    # Initialize AI without Meta layer
    ai = SuperIntelligentAI(use_meta_controller=False)
    logger.info("✅ AI initialized (Meta layer disabled)")
    logger.info("")
    
    # Test 1: Web scraping task
    logger.info("TEST 1: Web Scraping Task")
    logger.info("-" * 80)
    task1 = "Extract the number of stars from the GitHub repository asyncio"
    result1 = await ai.execute_intelligent_task(task1, use_meta_controller=False)
    logger.info(f"Task: {task1}")
    logger.info(f"Result: {result1.get('final_output', 'NO OUTPUT')}")
    logger.info("")
    
    # Test 2: File creation task  
    logger.info("TEST 2: File Creation Task")
    logger.info("-" * 80)
    task2 = "Create a JSON file with test data"
    result2 = await ai.execute_intelligent_task(task2, use_meta_controller=False)
    logger.info(f"Task: {task2}")
    logger.info(f"Result: {result2.get('final_output', 'NO OUTPUT')}")
    logger.info("")
    
    # Test 3: System command
    logger.info("TEST 3: System Command Task")
    logger.info("-" * 80)
    task3 = "Execute a system command to list directory"
    result3 = await ai.execute_intelligent_task(task3, use_meta_controller=False)
    logger.info(f"Task: {task3}")
    logger.info(f"Result: {result3.get('final_output', 'NO OUTPUT')}")
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_real_execution())
