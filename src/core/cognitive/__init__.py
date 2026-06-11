"""
Cognitive Package - Project-S Unified Cognitive Core
====================================================
Exports all cognitive symbols required by cognitive_workflow_integration.py.
"""

# 1. Base cognitive symbols
from .base_cognitive import (
    cognitive_registry,
    CognitiveContext,
    CognitiveResult,
    IntentMatch,
    TaskDecomposition,
)

# 2. EnhancedCognitiveProcessor
from .enhanced_processor import EnhancedCognitiveProcessor

# 3. AdvancedIntentAnalyzer
from .advanced_analyzer import AdvancedIntentAnalyzer

# 4. SemanticReasoningEngine
from .semantic_reasoning import SemanticReasoningEngine

# 5. CognitiveCore
from .cognitive_core import CognitiveCore

__all__ = [
    "CognitiveCore",
    "cognitive_registry",
    "CognitiveContext",
    "CognitiveResult",
    "IntentMatch",
    "TaskDecomposition",
    "EnhancedCognitiveProcessor",
    "AdvancedIntentAnalyzer",
    "SemanticReasoningEngine",
]