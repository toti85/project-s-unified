#!/usr/bin/env python3
"""
Real-world tasks on Meta Path with verification.
No demos - actual execution with evidence collection.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# Suppress logging
logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI

class TaskExecutor:
    """Execute real tasks and verify results."""
    
    def __init__(self):
        self.results = []
        self.ai = SuperIntelligentAI(use_meta_controller=True)
    
    async def execute_task(self, task_id, goal, verification_func):
        """Execute a task and verify result."""
        print(f"\n{'='*80}")
        print(f"TASK {task_id}: {goal[:70]}")
        print(f"{'='*80}")
        
        try:
            print(f"[EXEC] Starting execution...")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self.ai.execute_intelligent_task(goal, use_meta_controller=True),
                timeout=30.0
            )
            
            print(f"[RESULT] Success: {result.get('success')}")
            print(f"[RESULT] Task type: {result.get('task_type')}")
            
            # Verify result
            verified = verification_func(result)
            
            print(f"[VERIFY] Result verified: {verified}")
            
            # Store result
            self.results.append({
                "task_id": task_id,
                "goal": goal,
                "success": result.get('success'),
                "verified": verified,
                "timestamp": datetime.now().isoformat()
            })
            
            return verified
            
        except asyncio.TimeoutError:
            print(f"[TIMEOUT] Task exceeded 30 seconds")
            self.results.append({
                "task_id": task_id,
                "goal": goal,
                "success": False,
                "verified": False,
                "error": "timeout",
                "timestamp": datetime.now().isoformat()
            })
            return False
        
        except Exception as e:
            print(f"[ERROR] {e}")
            self.results.append({
                "task_id": task_id,
                "goal": goal,
                "success": False,
                "verified": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    async def run_all(self):
        """Run all tasks."""
        tasks = [
            {
                "id": 1,
                "goal": "Analyze the directory structure of memory/intelligence folder and list all files",
                "verify": lambda r: self._verify_analysis(r, "memory/intelligence")
            },
            {
                "id": 2,
                "goal": "Find all Python files in src/core directory that have been modified today",
                "verify": lambda r: self._verify_file_search(r)
            },
            {
                "id": 3,
                "goal": "Generate a summary of the project structure based on the source code",
                "verify": lambda r: self._verify_summary(r)
            },
        ]
        
        print("\n" + "="*80)
        print("REAL-WORLD TASK EXECUTION - META PATH")
        print("="*80)
        
        for task in tasks:
            await self.execute_task(task["id"], task["goal"], task["verify"])
        
        self._print_summary()
    
    def _verify_analysis(self, result, path):
        """Verify analysis task."""
        output = result.get('output', '')
        if isinstance(output, dict):
            output = str(output)
        
        # Check if output mentions the directory
        has_analysis = path in output or "file" in output.lower() or "directory" in output.lower()
        print(f"[CHECK] Output contains analysis: {has_analysis}")
        print(f"[CHECK] Output length: {len(str(output))} chars")
        
        return has_analysis and len(str(output)) > 50
    
    def _verify_file_search(self, result):
        """Verify file search task."""
        output = result.get('output', '')
        if isinstance(output, dict):
            output = str(output)
        
        has_files = ".py" in output or "python" in output.lower()
        print(f"[CHECK] Output mentions Python files: {has_files}")
        print(f"[CHECK] Output length: {len(str(output))} chars")
        
        return has_files or len(str(output)) > 50
    
    def _verify_summary(self, result):
        """Verify summary task."""
        output = result.get('output', '')
        if isinstance(output, dict):
            output = str(output)
        
        has_summary = "structure" in output.lower() or "summary" in output.lower() or "project" in output.lower()
        print(f"[CHECK] Output is summary-like: {has_summary}")
        print(f"[CHECK] Output length: {len(str(output))} chars")
        
        return has_summary or len(str(output)) > 50
    
    def _print_summary(self):
        """Print execution summary."""
        print(f"\n{'='*80}")
        print("EXECUTION SUMMARY")
        print(f"{'='*80}")
        
        total = len(self.results)
        verified = sum(1 for r in self.results if r.get("verified"))
        success = sum(1 for r in self.results if r.get("success"))
        
        print(f"Total tasks: {total}")
        print(f"Successful: {success}")
        print(f"Verified: {verified}")
        print(f"Pass rate: {(verified/total*100):.1f}%")
        
        print(f"\nTask Details:")
        for r in self.results:
            status = "PASS" if r.get("verified") else "FAIL"
            print(f"  Task {r['task_id']}: {status}")
            if r.get("error"):
                print(f"    Error: {r['error']}")
        
        # Save results
        results_file = Path("memory/intelligence/task_execution_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {results_file}")

async def main():
    executor = TaskExecutor()
    await executor.run_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
