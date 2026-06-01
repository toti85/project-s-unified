"""
Research State - Tracks the state of ongoing bug bounty research.
Updated by MetaController via state management during iterations.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    """A single research finding."""
    hypothesis: str
    vector: str
    confidence: float  # 0.0 to 1.0
    evidence: str  # Description of evidence
    status: str  # "promising", "false_positive", "low_impact", "duplicate"


@dataclass
class ResearchState:
    """
    Tracks the state of bug bounty research across iterations.
    
    Attributes:
        current_hypothesis: The hypothesis being tested in this iteration
        explored_vectors: List of vectors already tested
        discarded_vectors: List of vectors that produced false positives or low impact
        findings: List of validated findings (promising, not false positives)
        iteration: Current iteration number
    """
    
    current_hypothesis: Optional[str] = None
    explored_vectors: list[str] = field(default_factory=list)
    discarded_vectors: list[str] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)
    iteration: int = 0
    
    # Additional tracking
    last_validator_feedback: Optional[str] = None
    confidence_trend: list[float] = field(default_factory=list)
    
    def mark_vector_explored(self, vector: str):
        """Record a vector as explored."""
        if vector not in self.explored_vectors:
            self.explored_vectors.append(vector)
    
    def discard_vector(self, vector: str, reason: str):
        """Record a vector as discarded with reason."""
        if vector not in self.discarded_vectors:
            self.discarded_vectors.append(vector)
        self.last_validator_feedback = reason
    
    def add_finding(self, hypothesis: str, vector: str, confidence: float, 
                   evidence: str, status: str = "promising"):
        """Record a research finding."""
        finding = {
            "hypothesis": hypothesis,
            "vector": vector,
            "confidence": confidence,
            "evidence": evidence,
            "status": status,
            "iteration": self.iteration,
        }
        self.findings.append(finding)
        self.confidence_trend.append(confidence)
    
    def get_remaining_vectors(self, all_vectors: list[str]) -> list[str]:
        """Get vectors not yet explored or discarded."""
        used = set(self.explored_vectors) | set(self.discarded_vectors)
        return [v for v in all_vectors if v not in used]
    
    def to_dict(self) -> dict:
        """Convert state to dictionary for MetaController state management."""
        return {
            "current_hypothesis": self.current_hypothesis,
            "explored_vectors": self.explored_vectors,
            "discarded_vectors": self.discarded_vectors,
            "findings": self.findings,
            "iteration": self.iteration,
            "last_validator_feedback": self.last_validator_feedback,
        }
    
    @staticmethod
    def from_dict(data: dict) -> "ResearchState":
        """Create ResearchState from dictionary."""
        state = ResearchState()
        state.current_hypothesis = data.get("current_hypothesis")
        state.explored_vectors = data.get("explored_vectors", [])
        state.discarded_vectors = data.get("discarded_vectors", [])
        state.findings = data.get("findings", [])
        state.iteration = data.get("iteration", 0)
        state.last_validator_feedback = data.get("last_validator_feedback")
        return state
