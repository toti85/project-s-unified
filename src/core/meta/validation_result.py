"""
Validation result data structures for execution validation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ValidationIssue:
    """Single validation issue found during execution review."""
    
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "correctness", "security", "quality", "performance"
    description: str
    found_by: str  # AI model name that found it
    location: str  # Where in result (e.g., "output.status", "error_handling")
    recommendation: str  # How to fix or improve
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate severity and category."""
        valid_severities = {"critical", "high", "medium", "low"}
        if self.severity not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}")
        
        valid_categories = {"correctness", "security", "quality", "performance"}
        if self.category not in valid_categories:
            raise ValueError(f"category must be one of {valid_categories}")


@dataclass
class ValidationCheck:
    """Single AI validator's validation check result."""
    
    validator_name: str  # "qwen3-235b", "gpt-4o", "claude-opus"
    check_type: str  # "correctness", "security", "quality"
    passed: bool
    confidence: float  # 0-100, how confident in the check result
    issues: List[ValidationIssue] = field(default_factory=list)
    reasoning: str = ""
    check_time_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate check parameters."""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"confidence must be 0-100, got {self.confidence}")
        
        valid_types = {"correctness", "security", "quality"}
        if self.check_type not in valid_types:
            raise ValueError(f"check_type must be one of {valid_types}")
        
        if self.check_time_ms < 0:
            raise ValueError(f"check_time_ms must be >= 0, got {self.check_time_ms}")


@dataclass
class ValidationResult:
    """Multi-AI execution validation consensus."""
    
    passed: bool
    confidence: float  # Average confidence across all checks (0-100)
    consensus_type: str  # "unanimous_pass", "majority_pass", "conditional", "failed"
    
    checks: List[ValidationCheck] = field(default_factory=list)
    
    # Aggregated issues
    all_issues: List[ValidationIssue] = field(default_factory=list)
    critical_issues: List[ValidationIssue] = field(default_factory=list)
    high_issues: List[ValidationIssue] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    total_validation_time_ms: int = 0
    validation_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """Validate result parameters."""
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"confidence must be 0-100, got {self.confidence}")
        
        valid_consensus = {"unanimous_pass", "majority_pass", "conditional", "failed"}
        if self.consensus_type not in valid_consensus:
            raise ValueError(f"consensus_type must be one of {valid_consensus}")
        
        if self.total_validation_time_ms < 0:
            raise ValueError(f"total_validation_time_ms must be >= 0")
    
    def get_issue_summary(self) -> Dict[str, int]:
        """Get count of issues by severity."""
        return {
            "critical": len(self.critical_issues),
            "high": len(self.high_issues),
            "medium": len([i for i in self.all_issues if i.severity == "medium"]),
            "low": len([i for i in self.all_issues if i.severity == "low"]),
            "total": len(self.all_issues)
        }
    
    def get_category_breakdown(self) -> Dict[str, List[ValidationIssue]]:
        """Get issues grouped by category."""
        breakdown = {
            "correctness": [],
            "security": [],
            "quality": [],
            "performance": []
        }
        for issue in self.all_issues:
            breakdown[issue.category].append(issue)
        return breakdown
