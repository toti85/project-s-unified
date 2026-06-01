"""
Core Loop - Orchestrates the full Dev Organism pipeline.

Pipeline:
1. Observe → collect activity data
2. Prioritize → rank tasks by multi-metric scoring
3. Propose → generate human-readable recommendations
4. Learn → apply taste model adjustments

Runs ONCE per invocation (not infinite loop).
"""

import argparse
import json
from pathlib import Path
from typing import Optional

from .observer import Observer, Task
from .prioritizer import PriorityEngine
from .proposer import Proposer
from .state_observer import read_self_state_gaps
from .state_observer import read_self_state_gaps
from ..modules.taste_model import TasteModel, Decision


class DevOrganism:
    """
    The Dev Organism: a living development environment.
    
    Observes developer activity, prioritizes tasks, and proposes actions.
    Learns from user decisions to improve future priorities.
    
    NOT autonomous—requires explicit human approval.
    """
    
    def __init__(self, repo_root: str, evidence_dir: str):
        """
        Initialize the organism.
        
        Args:
            repo_root: Path to git repository
            evidence_dir: Path to evidence directory
        """
        self.repo_root = Path(repo_root)
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.observer = Observer(str(self.repo_root))
        self.priority_engine = PriorityEngine()
        self.proposer = Proposer(self.evidence_dir)
        self.taste_model = TasteModel(self.evidence_dir / "decisions.jsonl")
    
    def _convert_observation_to_tasks(self) -> list[Task]:
        """
        Convert observation data to Task objects for prioritization.
        
        Returns:
            List of Task objects
        """
        tasks: list[Task] = []
        observation = self.observer.observe()
        
        # 1. Convert TODOs to tasks (using unique task_ids from observer)
        for todo in observation.todos:
            task = Task(
                task_id=todo['task_id'],  # Use unique ID from observer (SHA1-based)
                description=f"[{todo['priority']}] {todo['text']} ({todo['file']}:{todo['line']})",
                source='todo',
                file=todo['file'],
                line=todo['line'],
                metadata={'priority': todo['priority']},
                text=todo['text'],  # Original TODO/FIXME text
                snippet=todo['snippet'],  # 3-line code context
                source_path=todo['file'],  # Track source path for filtering
                issue_url=todo.get('issue_url', '')  # GitHub/issue tracker URL if present
            )
            tasks.append(task)
        
        # 2. Convert significant repo changes to tasks
        for idx, change in enumerate(observation.repo_changes):
            if change['lines_added'] + change['lines_removed'] > 5:  # Significant change
                task = Task(
                    task_id=f"change_{change['file'].replace('/', '_')}_{idx}",
                    description=f"Review {change['file']} ({change['status']}: +{change['lines_added']}/-{change['lines_removed']})",
                    source='change',
                    file=change['file'],
                    metadata=change
                )
                tasks.append(task)
        
        # 3. Convert terminal patterns to tasks
        for idx, pattern in enumerate(observation.terminal_patterns):
            if pattern['frequency'] >= 3:  # Highly repeated
                task = Task(
                    task_id=f"pattern_{idx}",
                    description=f"Automate repeated command: `{pattern['command']}` (run {pattern['frequency']}x)",
                    source='pattern',
                    metadata=pattern
                )
                tasks.append(task)

        # 4. GAP_008 megoldás: self_state.json ACTIVE gap-ek hozzáadása
        # state_observer.py — új forrás, observer.py nem módosítva
        tasks.extend(read_self_state_gaps())

        return tasks

    def run_once(self, top_n: int = 5, use_taste_model: bool = True) -> dict:
        """
        Execute a single complete organism cycle.
        
        Pipeline:
        1. Observe developer activity
        2. Convert observations to ranked tasks
        3. Generate proposals
        4. Return results for human review
        
        Args:
            top_n: Number of top tasks to propose
            use_taste_model: Apply taste model adjustments
        
        Returns:
            Results dict with status, proposals, stats
        """
        results = {
            'status': 'success',
            'timestamp': str(Path(self.evidence_dir / "run_latest.txt").read_text() if (self.evidence_dir / "run_latest.txt").exists() else ''),
            'observation': None,
            'tasks_collected': 0,
            'top_proposals': [],
            'proposals_file': None,
            'taste_stats': None,
            'errors': []
        }
        
        try:
            # 1. OBSERVE
            print("[1/4] Observing developer activity...")
            observation = self.observer.observe()
            results['observation'] = observation.to_dict()
            
            # 2. COLLECT TASKS
            print("[2/4] Converting observations to tasks...")
            tasks = self._convert_observation_to_tasks()
            results['tasks_collected'] = len(tasks)
            print(f"   Found {len(tasks)} tasks")
            
            if not tasks:
                results['status'] = 'no_tasks'
                print("   No tasks found in this cycle.")
                return results
            
            # 3. PRIORITIZE with taste model adjustment
            print("[3/4] Prioritizing tasks...")
            all_scored = self.priority_engine.rank(tasks, top_n=min(top_n * 3, len(tasks)))
            
            if use_taste_model:
                # Adjust scores based on decision history
                adjusted = []
                for scored in all_scored:
                    adjusted_score = self.taste_model.adjust_score(
                        scored['task_id'],
                        scored['score']
                    )
                    scored['score'] = adjusted_score
                    adjusted.append(scored)
                all_scored = adjusted
                
                # Re-sort after adjustment
                all_scored = sorted(all_scored, key=lambda x: x['score'], reverse=True)
            
            top_scored = all_scored[:top_n]
            results['top_proposals'] = top_scored
            
            for idx, prop in enumerate(top_scored, 1):
                print(f"   [{idx}] {prop['description'][:50]}... (score: {prop['score']:.2f})")
            
            # 4. PROPOSE
            print("[4/4] Generating proposals...")
            proposals_file = self.proposer.generate(top_scored, all_tasks=all_scored)
            results['proposals_file'] = str(proposals_file)
            print(f"   Proposals saved to: {proposals_file}")
            
            # Get taste stats
            results['taste_stats'] = self.taste_model.get_decision_stats()
            
            # Log this run
            (self.evidence_dir / "run_latest.txt").write_text(
                json.dumps(results, indent=2, default=str),
                encoding='utf-8'
            )
            
        except Exception as e:
            import traceback
            results['status'] = 'error'
            results['errors'].append(str(e))
            tb_str = traceback.format_exc()
            print(f"   ERROR: {e}")
            print(f"   Traceback:\n{tb_str}")
        
        return results
    
    def record_decision(self, task_id: str, action: str) -> None:
        """
        Record a user approval/rejection/deferral decision.
        
        Args:
            task_id: Task ID to record decision for
            action: 'approve', 'reject', or 'defer'
        """
        if action not in ['approve', 'reject', 'defer']:
            raise ValueError(f"Invalid action: {action}")
        
        decision = Decision(task_id, action)
        self.taste_model.log_decision(decision)
        print(f"Decision recorded: {task_id} → {action}")


def main():
    """CLI entry point for the Dev Organism."""
    parser = argparse.ArgumentParser(
        description="Dev Organism - Living development environment"
    )
    parser.add_argument(
        '--repo',
        type=str,
        default='.',
        help='Path to git repository (default: current directory)'
    )
    parser.add_argument(
        '--evidence',
        type=str,
        help='Path to evidence directory (default: organism/evidence)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=5,
        help='Number of top proposals to generate (default: 5)'
    )
    parser.add_argument(
        '--approve',
        type=str,
        help='Record approval of a task (task_id)'
    )
    parser.add_argument(
        '--reject',
        type=str,
        help='Record rejection of a task (task_id)'
    )
    parser.add_argument(
        '--defer',
        type=str,
        help='Record deferral of a task (task_id)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = Path(args.repo).resolve()
    evidence_dir = Path(args.evidence) if args.evidence else repo_root / 'organism' / 'evidence'
    
    # Initialize organism
    organism = DevOrganism(str(repo_root), str(evidence_dir))
    
    # Handle decisions
    if args.approve:
        organism.record_decision(args.approve, 'approve')
        return
    
    if args.reject:
        organism.record_decision(args.reject, 'reject')
        return
    
    if args.defer:
        organism.record_decision(args.defer, 'defer')
        return
    
    # Run complete cycle
    print("\n" + "="*60)
    print("DEV ORGANISM - OBSERVATION CYCLE")
    print("="*60 + "\n")
    
    results = organism.run_once(top_n=args.top)
    
    print("\n" + "="*60)
    print(f"Status: {results['status'].upper()}")
    print(f"Tasks collected: {results['tasks_collected']}")
    if results['top_proposals']:
        print(f"Top proposals generated: {len(results['top_proposals'])}")
    if results['proposals_file']:
        print(f"\n-> Open proposals here: {results['proposals_file']}")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
