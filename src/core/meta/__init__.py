"""
META layer: Multi-AI strategic decision making and execution validation.

Components:

Phase 1 - Strategy Council (Decision Making):
- Decision: Data structures for decisions and opinions
- AIStrategist: Individual AI strategist with specialized role
- StrategyCouncil: Consensus coordinator for multiple strategists

Phase 2 - Execution Validator (Result Validation):
- ValidationResult: Multi-AI validation consensus
- ValidationIssue: Individual validation issue
- ValidationCheck: Single AI validator's result
- AIValidator: Individual AI validator with specialized check type
- ExecutionValidator: Multi-AI validation orchestrator

Phase 3 - Meta Controller (Orchestration Loop):
- MetaController: Orchestrates decision→execute→validate→replan loop
- MetaControllerConfig: Configuration for MetaController
"""

from .decision import Decision, AIOpinion
from .ai_strategist import AIStrategist
from .strategy_council import StrategyCouncil
from .validation_result import ValidationResult, ValidationCheck, ValidationIssue
from .ai_validator import AIValidator
from .execution_validator import ExecutionValidator
from .meta_controller import MetaController, MetaControllerConfig

__all__ = [
    # Phase 1: Strategy Council
    "Decision",
    "AIOpinion",
    "AIStrategist",
    "StrategyCouncil",
    # Phase 2: Execution Validator
    "ValidationResult",
    "ValidationCheck",
    "ValidationIssue",
    "AIValidator",
    "ExecutionValidator",
    # Phase 3: Meta Controller
    "MetaController",
    "MetaControllerConfig"
]

