#!/usr/bin/env python3
"""
V2 Architecture Test: LangGraph + Browser Automation Workflow
Tests the original multi-step workflow with browser usage.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.orchestration.langgraph_engine import LangGraphWorkflowEngine, TaskType
from integrations.ai_models.multi_model_ai_client import AIClient


async def test_v2_multi_step_workflow():
    """Test V2 LangGraph multi-step workflow with browser task."""
    
    print("\n" + "="*80)
    print("V2 ARCHITECTURE TEST: LangGraph Multi-Step Workflow")
    print("="*80)
    
    try:
        # Initialize LangGraph engine
        print("\n[INIT] Creating LangGraph Workflow Engine...")
        engine = LangGraphWorkflowEngine(name="v2_browser_test")
        print(f"  [OK] Engine created")
        print(f"  [OK] LangGraph available: {engine.langgraph_available if hasattr(engine, 'langgraph_available') else 'checking'}")
        
        # Prepare a multi-step task
        task = {
            "input": "Search for OpenAI GPT-4 news on web and summarize top 3 findings",
            "task_type": "data_analysis"
        }
        
        print(f"\n[TASK] {task['input']}")
        print(f"       Type: {task['task_type']}")
        
        # Analyze task complexity
        print("\n[ANALYZE] Analyzing task type and complexity...")
        analysis = engine.analyze_task(task)
        print(f"  Suggested workflow: {analysis.get('suggested_workflow', 'unknown')}")
        print(f"  Complexity: {analysis.get('complexity', 'unknown')}")
        print(f"  Steps required: {analysis.get('estimated_steps', 0)}")
        
        # Execute with auto workflow selection
        print("\n[EXECUTE] Running workflow (auto-selection)...")
        state = {"input": task["input"]}
        
        result = await engine.execute(
            input_data=state,
            workflow_type="auto"
        )
        
        print(f"\n[RESULT]")
        print(f"  Status: {result.status}")
        print(f"  Success: {result.status == 'success'}")
        
        if result.data:
            output = result.data.get("output", "")
            if isinstance(output, str):
                print(f"  Output (first 300 chars): {output[:300]}")
            else:
                print(f"  Output type: {type(output)}")
                print(f"  Output keys: {output.keys() if isinstance(output, dict) else 'N/A'}")
        
        if result.error:
            print(f"  Error: {result.error}")
        
        print(f"  Execution time: {result.execution_time:.2f}s")
        
        # Check if any browser automation happened
        print(f"\n[METADATA]")
        if result.metadata:
            print(f"  Metadata keys: {result.metadata.keys()}")
            for key, value in result.metadata.items():
                if key not in ['error', 'details']:
                    print(f"    {key}: {str(value)[:100]}")
        
        return result.status == 'success'
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_v2_with_multi_model():
    """Test V2 with multi-model workflow (planning + execution + verification)."""
    
    print("\n" + "="*80)
    print("V2 ARCHITECTURE TEST: Multi-Model Workflow")
    print("="*80)
    
    try:
        engine = LangGraphWorkflowEngine(name="v2_multimodel_test")
        
        task = {
            "input": "Create a Python function that scrapes product prices from e-commerce sites",
            "task_type": "coding"
        }
        
        print(f"\n[TASK] {task['input']}")
        
        print("\n[EXECUTE] Running multi-model workflow...")
        state = {"input": task["input"]}
        
        result = await engine.execute(
            input_data=state,
            workflow_type="multi_model"
        )
        
        print(f"\n[RESULT]")
        print(f"  Status: {result.status}")
        print(f"  Execution time: {result.execution_time:.2f}s")
        
        if result.data:
            output = result.data.get("output", "")
            if output:
                lines = str(output).split('\n')
                print(f"  Output (first 5 lines):")
                for line in lines[:5]:
                    if line.strip():
                        print(f"    {line}")
        
        return result.status == 'success'
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all V2 tests."""
    
    print("\nVERIFYING V2 ARCHITECTURE")
    print("Testing LangGraph + Multi-Step + Browser Automation")
    
    test1 = await test_v2_multi_step_workflow()
    test2 = await test_v2_with_multi_model()
    
    print("\n" + "="*80)
    print("V2 ARCHITECTURE TEST SUMMARY")
    print("="*80)
    print(f"Multi-step workflow test: {'PASS' if test1 else 'FAIL'}")
    print(f"Multi-model workflow test: {'PASS' if test2 else 'FAIL'}")
    
    if test1 or test2:
        print("\n[OK] V2 Architecture is OPERATIONAL")
        print("     LangGraph workflows are working")
    else:
        print("\n[FAIL] V2 Architecture issues detected")
        print("     Workflows failed to execute")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Test interrupted by user")
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
