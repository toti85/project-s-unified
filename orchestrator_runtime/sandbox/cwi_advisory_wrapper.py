"""
CWI Advisory Wrapper — Sandbox Prototype
==========================================

Advisory-only wrapper for cognitive_workflow_integration.py integration
into bridge_runner.py consume_executor_output() pre-consumption phase.

DESIGN PRINCIPLES:
- NEVER raise exceptions to caller
- NEVER block pipeline execution
- NEVER modify input context
- NEVER write files
- Always return dict with: enabled, status, advisory, error

Usage:
    from cwi_advisory_wrapper import get_cwi_advisory
    result = get_cwi_advisory(
        task_description="Search for files containing 'import os' in src/",
        context={"integration": "bridge_runner", "run_id": "AO5_T9_TEST"},
        user_id="ao5_system"
    )

RISK_010 COMPLIANCE: This wrapper does NOT modify last_output.md or output_ready.json.
"""

import copy
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default timeout for CWI processing (seconds)
CWI_TIMEOUT = 30


def get_cwi_advisory(
    task_description: str,
    context: Optional[dict] = None,
    user_id: str = "operator"
) -> dict:
    """
    Get cognitive advisory for a task description.

    This is the main entry point for CWI integration. It is designed to be
    called from bridge_runner.py consume_executor_output() in the pre-consumption
    phase, after the kill switch check and before output_ready.json validation.

    Args:
        task_description: Natural language description of the task
        context: Additional context dict (NOT mutated — a copy is made internally)
        user_id: User identifier for personalization

    Returns:
        dict with keys:
        - enabled (bool): Whether CWI module was successfully imported
        - status (str): "OK" | "IMPORT_FAILED" | "PROCESSING_FAILED" | "TIMEOUT"
        - advisory (dict|None): The cognitive advisory if successful, None otherwise
        - error (str|None): Error message if failed, None if successful

    Example success:
        {
            "enabled": True,
            "status": "OK",
            "advisory": {
                "intent_analysis": {...},
                "task_decomposition": {...},
                "semantic_reasoning": {...},
                "processing_context": {...}
            },
            "error": None
        }

    Example import failure:
        {
            "enabled": False,
            "status": "IMPORT_FAILED",
            "advisory": None,
            "error": "No module named 'core.cognitive_workflow_integration'"
        }
    """
    # Ensure context is not mutated — make a shallow copy for logging only
    safe_context = dict(context) if context is not None else {}

    # ── Step 1: Try to import CWI ──
    try:
        # Add project root to path if not already present
        project_root = Path(__file__).parents[2]
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from core.cognitive_workflow_integration import (
            get_cognitive_workflow_integration
        )
    except ImportError as e:
        logger.warning(f"CWI import failed: {e}")
        return {
            "enabled": False,
            "status": "IMPORT_FAILED",
            "advisory": None,
            "error": str(e)
        }
    except Exception as e:
        logger.warning(f"CWI import unexpected error: {e}")
        return {
            "enabled": False,
            "status": "IMPORT_FAILED",
            "advisory": None,
            "error": f"Unexpected import error: {e}"
        }

    # ── Step 2: Try to get CWI instance and process task ──
    try:
        cwi = get_cognitive_workflow_integration()

        # Run async processing in a new event loop if needed
        import asyncio
        import inspect

        async def _run_async():
            result = cwi.process_task_cognitively(
                task_description=task_description,
                context={
                    **safe_context,
                    "integration": "bridge_runner_pre_consume"
                },
                user_id=user_id
            )
            # Handle both coroutine and direct dict return (for mocking)
            if inspect.iscoroutine(result):
                return await result
            return result

        raw_advisory = asyncio.run(_run_async())

        # Validate advisory structure
        if not isinstance(raw_advisory, dict):
            raise ValueError(f"CWI returned non-dict: {type(raw_advisory)}")

        # ── T24 Adapter: normalize CWI output shape ──
        # CWI process_task_cognitively returns:
        #   {success, results, cognitive_analysis, learning_insights, execution_metrics, timestamp}
        # Bridge_runner telemetry expects flat keys:
        #   {success, intent_analysis, task_decomposition, semantic_reasoning, processing_context}
        # Adapter promotes cognitive_analysis sub-keys to top level.
        advisory = dict(raw_advisory)  # shallow copy
        ca = raw_advisory.get("cognitive_analysis")
        if isinstance(ca, dict):
            for key in ("intent_analysis", "task_decomposition", "semantic_reasoning", "processing_context"):
                if key in ca and key not in advisory:
                    advisory[key] = ca[key]

        # Required top-level keys (advisory may have more)
        required_keys = [
            "success",
            "intent_analysis",
            "task_decomposition",
            "semantic_reasoning",
            "processing_context"
        ]
        for key in required_keys:
            if key not in advisory:
                raise KeyError(f"Missing required key in advisory: {key}")

        return {
            "enabled": True,
            "status": "OK",
            "advisory": advisory,
            "error": None
        }

    except asyncio.TimeoutError:  # type: ignore
        logger.warning(f"CWI processing timed out for task: {task_description[:50]}...")
        return {
            "enabled": True,
            "status": "TIMEOUT",
            "advisory": None,
            "error": f"CWI processing timed out after {CWI_TIMEOUT}s"
        }
    except Exception as e:
        logger.warning(f"CWI processing failed: {e}")
        return {
            "enabled": True,
            "status": "PROCESSING_FAILED",
            "advisory": None,
            "error": str(e)
        }


def get_cwi_advisory_safe(
    task_description: str,
    context: Optional[dict] = None,
    user_id: str = "operator"
) -> dict:
    """
    Ultra-safe wrapper: guarantees no exceptions escape.

    This is a double-wrapping layer around get_cwi_advisory.
    Even if get_cwi_advisory raises an unexpected exception,
    this function catches it and returns a safe failure dict.

    Use this in production bridge_runner.py integration.
    """
    try:
        return get_cwi_advisory(
            task_description=task_description,
            context=context,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"CWI advisory wrapper unexpected error: {e}")
        return {
            "enabled": False,
            "status": "WRAPPER_ERROR",
            "advisory": None,
            "error": f"Wrapper error: {e}"
        }


# ── Fallback advisory for when CWI is disabled ──

def get_fallback_advisory() -> dict:
    """
    Return a default advisory when CWI is explicitly disabled.

    This is used when CWI_ADVISORY_ENABLED = False in config.
    """
    return {
        "enabled": False,
        "status": "DISABLED",
        "advisory": None,
        "error": "CWI advisory explicitly disabled via config"
    }


# ── CLI entry point for testing ──

if __name__ == "__main__":
    import json

    # Test with a simple task
    test_task = "Search for Python files containing 'import os' in src/"

    print("=" * 60)
    print("CWI Advisory Wrapper — Manual Test")
    print("=" * 60)
    print(f"Task: {test_task}")
    print()

    result = get_cwi_advisory_safe(
        task_description=test_task,
        context={"test": True},
        user_id="sandbox_test"
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print()
    print("=" * 60)
    print("Test complete.")