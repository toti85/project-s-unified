"""
CWI Advisory Wrapper — Sandbox Tests
=====================================

Tests for orchestrator_runtime/sandbox/cwi_advisory_wrapper.py

Run with:
    python orchestrator_runtime/sandbox/test_cwi_advisory_wrapper.py

These tests use monkeypatch/mocking to verify wrapper behavior
without requiring actual CWI dependencies to be importable.
"""

import sys
import copy
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add sandbox to path for import
sys.path.insert(0, str(Path(__file__).parent))
# Add project root for wrapper import
sys.path.insert(0, str(Path(__file__).parents[1]))

from cwi_advisory_wrapper import (
    get_cwi_advisory,
    get_cwi_advisory_safe,
    get_fallback_advisory
)

# ── Test Results Tracking ──

tests_run = 0
tests_passed = 0
tests_failed = 0
test_results = []


def run_test(name, fn):
    """Run a test and track results."""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    try:
        fn()
        tests_passed += 1
        test_results.append((name, "PASS", None))
        print(f"  PASS: {name}")
    except Exception as e:
        tests_failed += 1
        test_results.append((name, "FAIL", str(e)))
        print(f"  FAIL: {name} - {e}")


# ── Test A: Import failure path does not raise ──

def test_import_failure():
    """Verify wrapper returns safe dict when CWI import fails."""
    original = sys.modules.pop("core.cognitive_workflow_integration", None)
    try:
        with patch("builtins.__import__") as mock_import:
            def side_effect(name, *args, **kwargs):
                if "cognitive_workflow" in name:
                    raise ImportError(f"No module named '{name}'")
                return __import__(name, *args, **kwargs)
            mock_import.side_effect = side_effect

            result = get_cwi_advisory_safe(
                task_description="test task",
                context={"test": True},
                user_id="test"
            )

        # Verify result structure
        assert isinstance(result, dict), "Result must be a dict"
        assert result["enabled"] is False, f"enabled must be False on import failure, got {result['enabled']}"
        assert result["status"] == "IMPORT_FAILED", f"Expected IMPORT_FAILED, got {result['status']}"
        assert result["advisory"] is None, "advisory must be None on import failure"
        assert result["error"] is not None, "error must be set on import failure"
        assert "blocking" not in result, "Result must not contain 'blocking' key"
    finally:
        if original is not None:
            sys.modules["core.cognitive_workflow_integration"] = original


# ── Test B: Malformed/empty task does not raise ──

def test_malformed_task():
    """Verify wrapper handles empty/None task gracefully."""
    # Mock the entire import chain to avoid actual imports
    mock_cwi_class = MagicMock()
    mock_cwi_instance = MagicMock()
    mock_cwi_instance.process_task_cognitively = MagicMock(
        return_value={
            "success": True,
            "intent_analysis": {"intent_type": "general", "confidence": 0.5},
            "task_decomposition": {"subtasks": [], "total_complexity": 0},
            "semantic_reasoning": {"strategy": "default", "confidence": 0.5},
            "processing_context": {"user_id": "test", "session_id": "test", "task_type": "general"}
        }
    )
    mock_cwi_class.return_value = mock_cwi_instance

    with patch.dict(sys.modules, {
        "core": MagicMock(),
        "core.cognitive_workflow_integration": MagicMock(),
        "core.cognitive": MagicMock(),
        "core.orchestration": MagicMock(),
        "integrations": MagicMock(),
        "integrations.decision_routing": MagicMock(),
        "core.state": MagicMock(),
    }):
        sys.modules["core.cognitive_workflow_integration"].get_cognitive_workflow_integration = MagicMock(return_value=mock_cwi_instance)

        # Test empty string
        result_empty = get_cwi_advisory_safe(
            task_description="",
            context={"test": True},
            user_id="test"
        )
        assert isinstance(result_empty, dict), "Empty task must return dict"
        assert "blocking" not in result_empty, "Must not contain blocking key"

        # Test whitespace task
        result_ws = get_cwi_advisory_safe(
            task_description="   ",
            context={"test": True},
            user_id="test"
        )
        assert isinstance(result_ws, dict), "Whitespace task must return dict"
        assert "blocking" not in result_ws, "Must not contain blocking key"


# ── Test C: Normal task returns dict with required keys ──

def test_normal_task():
    """Verify wrapper returns correct structure for successful CWI call."""
    mock_cwi_instance = MagicMock()
    mock_cwi_instance.process_task_cognitively = MagicMock(
        return_value={
            "success": True,
            "intent_analysis": {
                "intent_type": "file_search",
                "confidence": 0.85,
                "operation": "search",
                "parameters": {},
                "suggested_approach": "sequential"
            },
            "task_decomposition": {
                "subtasks": [
                    {"id": "sub1", "description": "Search files", "priority": "high", "complexity": 2}
                ],
                "total_complexity": 2,
                "execution_strategy": "sequential"
            },
            "semantic_reasoning": {
                "strategy": "sequential_execution",
                "confidence": 0.75,
                "explanation": "Standard file search pattern",
                "similar_patterns": ["file_search", "grep"]
            },
            "processing_context": {
                "user_id": "ao5_system",
                "session_id": "session_test",
                "task_type": "file_search"
            }
        }
    )

    with patch.dict(sys.modules, {
        "core": MagicMock(),
        "core.cognitive_workflow_integration": MagicMock(),
        "core.cognitive": MagicMock(),
        "core.orchestration": MagicMock(),
        "integrations": MagicMock(),
        "integrations.decision_routing": MagicMock(),
        "core.state": MagicMock(),
    }):
        sys.modules["core.cognitive_workflow_integration"].get_cognitive_workflow_integration = MagicMock(return_value=mock_cwi_instance)

        result = get_cwi_advisory_safe(
            task_description="Search for files containing 'import os' in src/",
            context={"integration": "bridge_runner", "run_id": "AO5_T9_TEST"},
            user_id="ao5_system"
        )

        # Verify structure
        assert isinstance(result, dict), "Result must be a dict"
        assert result["enabled"] is True, f"enabled must be True on success, got {result['enabled']}"
        assert result["status"] == "OK", f"Expected OK, got {result['status']}"
        assert result["advisory"] is not None, "advisory must not be None on success"
        assert result["error"] is None, "error must be None on success"

        # Verify advisory keys
        advisory = result["advisory"]
        required_keys = [
            "success",
            "intent_analysis",
            "task_decomposition",
            "semantic_reasoning",
            "processing_context"
        ]
        for key in required_keys:
            assert key in advisory, f"Missing required key in advisory: {key}"

        # Verify no blocking key
        assert "blocking" not in result, "Result must not contain 'blocking' key"
        assert "block" not in result, "Result must not contain 'block' key"


# ── Test D: Wrapper never returns a blocking decision field ──

def test_no_blocking_field():
    """Verify wrapper never includes blocking decision in result."""
    mock_cwi_instance = MagicMock()
    mock_cwi_instance.process_task_cognitively = MagicMock(
        return_value={
            "success": True,
            "intent_analysis": {"intent_type": "general", "confidence": 0.5},
            "task_decomposition": {"subtasks": [], "total_complexity": 0},
            "semantic_reasoning": {"strategy": "default", "confidence": 0.5},
            "processing_context": {"user_id": "test", "session_id": "test", "task_type": "general"}
        }
    )

    with patch.dict(sys.modules, {
        "core": MagicMock(),
        "core.cognitive_workflow_integration": MagicMock(),
        "core.cognitive": MagicMock(),
        "core.orchestration": MagicMock(),
        "integrations": MagicMock(),
        "integrations.decision_routing": MagicMock(),
        "core.state": MagicMock(),
    }):
        sys.modules["core.cognitive_workflow_integration"].get_cognitive_workflow_integration = MagicMock(return_value=mock_cwi_instance)

        result = get_cwi_advisory_safe(
            task_description="test",
            context={"test": True},
            user_id="test"
        )

        # Verify no blocking-related keys at any level
        def check_no_blocking(d, path="root"):
            if isinstance(d, dict):
                for key in d:
                    if "block" in key.lower():
                        raise AssertionError(f"Found blocking key '{key}' at {path}")
                    check_no_blocking(d[key], f"{path}.{key}")
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    check_no_blocking(item, f"{path}[{i}]")

        check_no_blocking(result)


# ── Test E: Input context is not mutated ──

def test_context_not_mutated():
    """Verify wrapper does not mutate the input context dict."""
    mock_cwi_instance = MagicMock()
    mock_cwi_instance.process_task_cognitively = MagicMock(
        return_value={
            "success": True,
            "intent_analysis": {"intent_type": "general", "confidence": 0.5},
            "task_decomposition": {"subtasks": [], "total_complexity": 0},
            "semantic_reasoning": {"strategy": "default", "confidence": 0.5},
            "processing_context": {"user_id": "test", "session_id": "test", "task_type": "general"}
        }
    )

    original_context = {"integration": "bridge_runner", "run_id": "AO5_T9_TEST", "original": True}
    context_copy = copy.deepcopy(original_context)

    with patch.dict(sys.modules, {
        "core": MagicMock(),
        "core.cognitive_workflow_integration": MagicMock(),
        "core.cognitive": MagicMock(),
        "core.orchestration": MagicMock(),
        "integrations": MagicMock(),
        "integrations.decision_routing": MagicMock(),
        "core.state": MagicMock(),
    }):
        sys.modules["core.cognitive_workflow_integration"].get_cognitive_workflow_integration = MagicMock(return_value=mock_cwi_instance)

        result = get_cwi_advisory_safe(
            task_description="test",
            context=original_context,
            user_id="test"
        )

        # Verify context was not mutated
        assert original_context == context_copy, \
            f"Context was mutated: {original_context} != {context_copy}"


# ── Test F: Fallback advisory returns correct structure ──

def test_fallback_advisory():
    """Verify get_fallback_advisory returns correct structure."""
    result = get_fallback_advisory()

    assert isinstance(result, dict), "Fallback must return dict"
    assert result["enabled"] is False, "Fallback enabled must be False"
    assert result["status"] == "DISABLED", f"Expected DISABLED, got {result['status']}"
    assert result["advisory"] is None, "Fallback advisory must be None"
    assert result["error"] is not None, "Fallback error must be set"
    assert "blocking" not in result, "Fallback must not contain blocking key"


# ── Test G: get_cwi_advisory (not safe) also catches exceptions ──

def test_get_cwi_advisory_catches():
    """Verify get_cwi_advisory (non-safe) also catches exceptions."""
    with patch("builtins.__import__") as mock_import:
        def side_effect(name, *args, **kwargs):
            if "cognitive_workflow" in name:
                raise ImportError(f"No module named '{name}'")
            return __import__(name, *args, **kwargs)
        mock_import.side_effect = side_effect

        result = get_cwi_advisory(
            task_description="test",
            context={"test": True},
            user_id="test"
        )

        assert isinstance(result, dict), "Result must be dict"
        assert result["enabled"] is False, "enabled must be False"
        assert "blocking" not in result, "Must not contain blocking key"


# ── Run Tests ──

if __name__ == "__main__":
    print("=" * 60)
    print("CWI Advisory Wrapper - Sandbox Tests")
    print("=" * 60)

    # Run all test functions
    run_test("A: Import failure path does not raise", test_import_failure)
    run_test("B: Malformed/empty task does not raise", test_malformed_task)
    run_test("C: Normal task returns dict with required keys", test_normal_task)
    run_test("D: Wrapper never returns a blocking decision field", test_no_blocking_field)
    run_test("E: Input context is not mutated", test_context_not_mutated)
    run_test("F: Fallback advisory returns correct structure", test_fallback_advisory)
    run_test("G: get_cwi_advisory catches exceptions", test_get_cwi_advisory_catches)

    print()
    print("=" * 60)
    print(f"Results: {tests_passed}/{tests_run} passed, {tests_failed} failed")
    print("=" * 60)

    if tests_failed > 0:
        sys.exit(1)
    else:
        print("All tests passed.")
        sys.exit(0)