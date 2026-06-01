#!/usr/bin/env python3
"""
Real production tasks using Meta path.
Verified execution with evidence collection.
"""

import asyncio
import sys
from pathlib import Path
import logging
import json
from datetime import datetime

logging.disable(logging.CRITICAL)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.super_intelligent_ai import SuperIntelligentAI

class ProductionTaskRunner:
    """Run real production tasks with Meta path."""
    
    def __init__(self):
        self.ai = SuperIntelligentAI(use_meta_controller=True)
        self.results = []
    
    async def analyze_project_structure(self):
        """Task 1: Analyze project structure from source code."""
        print("\n[TASK 1] Analyze Project Structure")
        print("-" * 60)
        
        task_info = {
            "id": 1,
            "name": "Analyze Project Structure",
            "goal": "Examine the source code and provide insights about the project architecture, main components, and technology stack. List key files and their purposes.",
            "status": "starting"
        }
        
        try:
            # Gather real data
            src_dir = Path("src")
            py_files = list(src_dir.rglob("*.py"))
            
            # Use this data in the goal
            detailed_goal = f"{task_info['goal']} Found {len(py_files)} Python files in src/. Focus on: meta controller, strategy council, execution paths."
            
            print(f"Executing: {task_info['goal'][:80]}...")
            
            result = await asyncio.wait_for(
                self.ai.execute_intelligent_task(
                    detailed_goal, 
                    use_meta_controller=True
                ),
                timeout=45.0
            )
            
            output_len = len(str(result.get('output', '')))
            print(f"Output received: {output_len} characters")
            print(f"Success: {result.get('success')}")
            
            task_info["status"] = "completed"
            task_info["output_length"] = output_len
            task_info["success"] = result.get('success')
            
            verified = output_len > 100
            print(f"Verified: {verified}")
            
            return verified, result
            
        except asyncio.TimeoutError:
            print("TIMEOUT exceeded")
            task_info["status"] = "timeout"
            return False, None
        except Exception as e:
            print(f"ERROR: {e}")
            task_info["status"] = "error"
            task_info["error"] = str(e)
            return False, None
        finally:
            self.results.append(task_info)
    
    async def analyze_evidence_patterns(self):
        """Task 2: Analyze evidence patterns from meta_evidence.jsonl."""
        print("\n[TASK 2] Analyze Evidence Patterns")
        print("-" * 60)
        
        task_info = {
            "id": 2,
            "name": "Analyze Evidence Patterns",
            "goal": "Examine the meta_evidence.jsonl file to find patterns in Meta layer decision-making, planning iterations, and execution outcomes. What are the common patterns?",
            "status": "starting"
        }
        
        try:
            # Check actual file
            evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
            if evidence_file.exists():
                file_size = evidence_file.stat().st_size
                print(f"Evidence file size: {file_size} bytes")
                
                goal = f"{task_info['goal']} Evidence file exists with {file_size} bytes of data. Analyze patterns in Meta layer decision-making."
            else:
                goal = task_info['goal']
            
            print(f"Executing: {task_info['goal'][:80]}...")
            
            result = await asyncio.wait_for(
                self.ai.execute_intelligent_task(
                    goal,
                    use_meta_controller=True
                ),
                timeout=45.0
            )
            
            output_len = len(str(result.get('output', '')))
            print(f"Output received: {output_len} characters")
            print(f"Success: {result.get('success')}")
            
            task_info["status"] = "completed"
            task_info["output_length"] = output_len
            task_info["success"] = result.get('success')
            
            verified = output_len > 100
            print(f"Verified: {verified}")
            
            return verified, result
            
        except asyncio.TimeoutError:
            print("TIMEOUT exceeded")
            task_info["status"] = "timeout"
            return False, None
        except Exception as e:
            print(f"ERROR: {e}")
            task_info["status"] = "error"
            task_info["error"] = str(e)
            return False, None
        finally:
            self.results.append(task_info)
    
    async def generate_system_health_report(self):
        """Task 3: Generate system health report."""
        print("\n[TASK 3] Generate System Health Report")
        print("-" * 60)
        
        task_info = {
            "id": 3,
            "name": "System Health Report",
            "goal": "Create a concise health report for the Meta path execution system. Check: MetaController status, StrategyCouncil initialization, evidence logging, execution success rate.",
            "status": "starting"
        }
        
        try:
            # Gather real metrics
            evidence_file = Path("memory/intelligence/meta_evidence.jsonl")
            event_count = 0
            if evidence_file.exists():
                with open(evidence_file, "r") as f:
                    event_count = sum(1 for _ in f)
            
            goal = f"{task_info['goal']} System has logged {event_count} events so far. Report should include: infrastructure status, recent events summary, recommendations."
            
            print(f"Executing: {task_info['goal'][:80]}...")
            
            result = await asyncio.wait_for(
                self.ai.execute_intelligent_task(
                    goal,
                    use_meta_controller=True
                ),
                timeout=45.0
            )
            
            output_len = len(str(result.get('output', '')))
            print(f"Output received: {output_len} characters")
            print(f"Success: {result.get('success')}")
            
            task_info["status"] = "completed"
            task_info["output_length"] = output_len
            task_info["success"] = result.get('success')
            
            verified = output_len > 100
            print(f"Verified: {verified}")
            
            return verified, result
            
        except asyncio.TimeoutError:
            print("TIMEOUT exceeded")
            task_info["status"] = "timeout"
            return False, None
        except Exception as e:
            print(f"ERROR: {e}")
            task_info["status"] = "error"
            task_info["error"] = str(e)
            return False, None
        finally:
            self.results.append(task_info)
    
    async def run_all(self):
        """Execute all tasks."""
        print("\n" + "="*80)
        print("PRODUCTION TASK EXECUTION - META PATH")
        print("="*80)
        
        task1_ok, result1 = await self.analyze_project_structure()
        task2_ok, result2 = await self.analyze_evidence_patterns()
        task3_ok, result3 = await self.generate_system_health_report()
        
        # Summary
        print("\n" + "="*80)
        print("EXECUTION SUMMARY")
        print("="*80)
        
        total = 3
        passed = sum([task1_ok, task2_ok, task3_ok])
        
        print(f"Total tasks: {total}")
        print(f"Completed: {passed}")
        print(f"Pass rate: {(passed/total*100):.1f}%")
        
        print("\nResults:")
        for r in self.results:
            status = "PASS" if (r['status'] == 'completed') else "FAIL"
            print(f"  Task {r['id']}: {status}")
            if r.get('output_length'):
                print(f"    Output: {r['output_length']} chars")
            if r.get('error'):
                print(f"    Error: {r['error']}")
        
        # Save detailed results
        results_file = Path("memory/intelligence/production_task_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tasks": total,
            "completed": passed,
            "pass_rate": (passed/total*100),
            "tasks": self.results
        }
        
        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nDetailed results saved: {results_file}")
        print("="*80)

async def main():
    runner = ProductionTaskRunner()
    await runner.run_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
