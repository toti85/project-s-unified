"""
Taste Model v0 - Lightweight learning system.

Tracks user decisions (approvals/rejections) and adjusts future scoring accordingly.
Stores decisions in jsonl format for lightweight learning.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class Decision:
    """User decision on a proposal."""
    
    def __init__(self, task_id: str, action: str, timestamp: Optional[str] = None):
        """
        Args:
            task_id: ID of the task
            action: 'approve', 'reject', 'defer'
            timestamp: ISO timestamp (defaults to now)
        """
        self.task_id = task_id
        self.action = action
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'action': self.action,
            'timestamp': self.timestamp
        }


class TasteModel:
    """
    Simple learning model based on user decisions.
    
    Mechanism:
    - Track all user decisions (approve/reject/defer)
    - Adjust scoring for similar future tasks
    - Lightweight: no ML, just pattern matching
    
    Adjustments:
    - Approved similar task → +0.2 score boost
    - Rejected similar task → -0.3 score penalty
    - Deferred task → remember for urgency decay
    """
    
    def __init__(self, decisions_file: Path):
        """
        Initialize taste model.
        
        Args:
            decisions_file: Path to decisions.jsonl file
        """
        self.decisions_file = Path(decisions_file)
        self.decisions_file.parent.mkdir(parents=True, exist_ok=True)
        self.decisions = self._load_decisions()
    
    def _load_decisions(self) -> list[dict]:
        """Load decision history from jsonl file."""
        decisions = []
        
        if not self.decisions_file.exists():
            return decisions
        
        try:
            with open(self.decisions_file, 'r') as f:
                for line in f:
                    if line.strip():
                        decisions.append(json.loads(line))
        except Exception:
            pass  # Return empty list on error
        
        return decisions
    
    def log_decision(self, decision: Decision) -> None:
        """
        Record a user decision.
        
        Args:
            decision: Decision object
        """
        self.decisions.append(decision.to_dict())
        
        # Append to jsonl
        try:
            with open(self.decisions_file, 'a') as f:
                f.write(json.dumps(decision.to_dict()) + '\n')
        except Exception:
            pass  # Silently fail
    
    def adjust_score(self, task_id: str, base_score: float) -> float:
        """
        Adjust a task's priority score based on decision history.
        
        Args:
            task_id: Task identifier
            base_score: Original score from prioritizer
        
        Returns:
            Adjusted score
        """
        adjustment = 0.0
        
        # Look for similar tasks in decision history
        for decision in self.decisions:
            if decision['task_id'] == task_id:
                # Direct match
                if decision['action'] == 'approve':
                    adjustment += 0.2  # Boost approved tasks
                elif decision['action'] == 'reject':
                    adjustment -= 0.3  # Penalize rejected tasks
                elif decision['action'] == 'defer':
                    adjustment -= 0.1  # Slight decay for deferred
        
        # Look for pattern matches (same file, similar keywords)
        # This is the "learning" part—simple heuristic
        approved_patterns = {}
        rejected_patterns = {}
        
        for decision in self.decisions:
            # Extract file and keyword patterns
            # (In production, this would be more sophisticated)
            if decision['action'] == 'approve':
                approved_patterns[decision['task_id']] = True
            elif decision['action'] == 'reject':
                rejected_patterns[decision['task_id']] = True
        
        # Placeholder for future pattern matching
        # (Would match based on file paths, keywords, etc.)
        
        adjusted_score = base_score + adjustment
        return max(0.0, adjusted_score)  # Floor at 0
    
    def get_decision_stats(self) -> dict:
        """
        Get summary of past decisions.
        
        Returns:
            Dict with counts of approvals, rejections, deferrals
        """
        stats = {
            'total': len(self.decisions),
            'approved': sum(1 for d in self.decisions if d['action'] == 'approve'),
            'rejected': sum(1 for d in self.decisions if d['action'] == 'reject'),
            'deferred': sum(1 for d in self.decisions if d['action'] == 'defer'),
        }
        
        if stats['total'] > 0:
            stats['approval_rate'] = stats['approved'] / stats['total']
        else:
            stats['approval_rate'] = 0.0
        
        return stats
