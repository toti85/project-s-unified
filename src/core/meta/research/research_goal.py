"""
Research Goal - Defines a bug bounty research objective for Meta Layer execution.
No real hacking tools. Pure research workflow coordination via MetaController.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResearchGoal:
    """
    Defines a bug bounty research objective that can be executed by MetaController.
    
    Attributes:
        target_name: Name of the target (e.g., "Company-X API", "Mobile App Y")
        scope: Scope description (e.g., "authentication endpoints only")
        focus_vectors: List of attack vectors to research
            Example: ["broken_auth", "idor", "api_rate_limits", "session_handling"]
        stop_condition: When to stop research
            Options: "submission_ready", "no_more_leads", "time_limit", "complexity_limit"
    """
    
    target_name: str
    scope: str
    focus_vectors: list[str]
    stop_condition: str
    
    # Optional metadata for tracking
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    max_iterations: int = 5
    
    def __post_init__(self):
        """Validate research goal."""
        valid_stop_conditions = ["submission_ready", "no_more_leads", "time_limit", "complexity_limit"]
        if self.stop_condition not in valid_stop_conditions:
            raise ValueError(f"stop_condition must be one of {valid_stop_conditions}")
        
        if not self.target_name or not self.target_name.strip():
            raise ValueError("target_name cannot be empty")
        
        if not self.focus_vectors:
            raise ValueError("focus_vectors cannot be empty")
        
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MetaController."""
        return {
            "type": "research",
            "target_name": self.target_name,
            "scope": self.scope,
            "focus_vectors": self.focus_vectors,
            "stop_condition": self.stop_condition,
            "description": self.description,
            "priority": self.priority,
        }
