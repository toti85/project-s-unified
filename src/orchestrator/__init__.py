"""
src.orchestrator — MS-FA1 Internal Orchestrator Package

This package provides the internal Project-S orchestrator layer for
filesystem-based task automation between Project-S and Cline.

Components:
    - filesystem_orchestrator: Goal/prompt lifecycle management
    - state_machine: Run state transitions and tracking
    - verdict_schema: Verdict creation, validation, and storage
    - cline_bridge: Prompt drafting and output parsing for Cline
    - run_archive: Run folder creation, archiving, and retrieval

Status:
    - Scaffold only (Phase 0)
    - No deep logic implemented yet
    - No automatic Cline invocation
    - No SAI integration yet
"""

__version__ = "0.1.0"
__status__ = "scaffold"