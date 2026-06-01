"""
Decision and opinion data structures for META layer strategy council.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class AIOpinion:
    """Opinion from a single AI strategist on a decision."""
    
    ai_name: str
    role: str  # e.g., "strategic", "security", "technical"
    recommendation: str  # "approve", "reject", "conditional"
    feasibility_score: float  # 0-100
    confidence_score: float  # 0-100
    reasoning: str
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    conditions: Optional[List[str]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate scores are in valid range."""
        if not 0 <= self.feasibility_score <= 100:
            raise ValueError(f"feasibility_score must be 0-100, got {self.feasibility_score}")
        if not 0 <= self.confidence_score <= 100:
            raise ValueError(f"confidence_score must be 0-100, got {self.confidence_score}")


@dataclass
class Decision:
    """Strategic decision with consensus from council."""
    
    decision_id: str
    goal: str
    decision: str  # "approved", "rejected", "conditional"
    consensus_type: str  # "unanimous", "majority", "split"
    approval_ratio: float  # 0.0-1.0
    avg_feasibility: float
    avg_confidence: float
    opinions: List[AIOpinion] = field(default_factory=list)
    aggregated_risks: List[str] = field(default_factory=list)
    aggregated_benefits: List[str] = field(default_factory=list)
    recommended_plan: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate decision parameters."""
        valid_decisions = {"approved", "rejected", "conditional"}
        if self.decision not in valid_decisions:
            raise ValueError(f"decision must be one of {valid_decisions}")
        
        valid_consensus = {"unanimous", "majority", "split"}
        if self.consensus_type not in valid_consensus:
            raise ValueError(f"consensus_type must be one of {valid_consensus}")
        
        if not 0 <= self.approval_ratio <= 1.0:
            raise ValueError(f"approval_ratio must be 0.0-1.0, got {self.approval_ratio}")
