"""
Core Orchestration Module - Project-S V2 
=========================================
Workflow engine and orchestration components.
"""

from .base_workflow import (
    WorkflowRegistry,
    WorkflowResult,
    workflow_registry,
)
from .langgraph_engine import LangGraphWorkflowEngine

try:
    from .workflow_engine import *
    WORKFLOW_ENGINE_AVAILABLE = True
except ImportError as e:
    WORKFLOW_ENGINE_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Workflow engine not available: {e}")

__all__ = [
    "WORKFLOW_ENGINE_AVAILABLE",
    "WorkflowRegistry",
    "LangGraphWorkflowEngine",
    "WorkflowResult",
    "workflow_registry",
]

# Bootstrap: register LangGraphWorkflowEngine in the global registry
_engine_instance = LangGraphWorkflowEngine()
workflow_registry.register_workflow(_engine_instance, is_default=True)
