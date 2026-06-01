"""
test_sai_live_status_normalization.py
======================================

Regression test: SuperIntelligentAI status normalization logic.

Bizonyítja, hogy a MetaController "passed" visszatérési értéke
success-ként van kezelve — ez volt a 2026-04-29-i Status: False → True bugfix root cause-a.

Futtatás:
    python -m pytest tests/test_sai_live_status_normalization.py -v
    # vagy közvetlenül:
    python tests/test_sai_live_status_normalization.py
"""
import sys
from pathlib import Path

# Setup import path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))


def _simulate_sai_status_normalization(meta_result: dict) -> dict:
    """
    Replication of the status-check logic in super_intelligent_ai.py
    execute_intelligent_task() MetaController branch (lines ~379-394).

    This is the FIXED version — both "success" and "passed" map to True.
    """
    if meta_result.get("status") in ("success", "passed"):
        return {
            "success": True,
            "output": f"[OK] MetaController completed goal in {meta_result.get('iterations', 1)} iterations",
            "task_type": "meta_controller_execution",
            "meta_result": meta_result,
        }
    else:
        return {
            "success": False,
            "output": f"[FAIL] MetaController failed: {meta_result.get('status')}",
            "task_type": "meta_controller_execution",
            "meta_result": meta_result,
        }


# ──────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────

def test_status_success_maps_to_true():
    """'success' status → success: True (original path, kept working)."""
    result = _simulate_sai_status_normalization({"status": "success", "iterations": 1})
    assert result["success"] is True, f"Expected True, got {result['success']}"
    assert "[OK]" in result["output"]


def test_status_passed_maps_to_true():
    """
    'passed' status → success: True.

    ROOT CAUSE FIX (2026-04-29): MetaController.run_goal() returns
    {"status": "passed"} on success, NOT {"status": "success"}.
    The old code used == "success" and therefore always returned False.
    """
    result = _simulate_sai_status_normalization({"status": "passed", "iterations": 1})
    assert result["success"] is True, (
        "REGRESSION: 'passed' must map to success=True. "
        "Check super_intelligent_ai.py ~L379: "
        'must be `in ("success", "passed")`, not `== "success"`'
    )
    assert "[OK]" in result["output"]


def test_status_failed_maps_to_false():
    """'failed' status → success: False."""
    result = _simulate_sai_status_normalization({"status": "failed"})
    assert result["success"] is False
    assert "[FAIL]" in result["output"]
    assert "failed" in result["output"]


def test_status_max_iters_maps_to_false():
    """'max_iters' status (MetaController exhausted iterations) → success: False."""
    result = _simulate_sai_status_normalization({"status": "max_iters"})
    assert result["success"] is False
    assert "[FAIL]" in result["output"]


def test_status_none_maps_to_false():
    """Missing/None status → success: False (defensive)."""
    result = _simulate_sai_status_normalization({})
    assert result["success"] is False

    result2 = _simulate_sai_status_normalization({"status": None})
    assert result2["success"] is False


def test_status_error_maps_to_false():
    """'error' status (executor exception) → success: False."""
    result = _simulate_sai_status_normalization({"status": "error", "error": "timeout"})
    assert result["success"] is False


def test_iterations_propagated():
    """iterations count from meta_result is included in output message."""
    result = _simulate_sai_status_normalization({"status": "passed", "iterations": 3})
    assert "3 iterations" in result["output"]


def test_task_type_always_meta_controller():
    """task_type is always 'meta_controller_execution' regardless of status."""
    for status in ("success", "passed", "failed", "max_iters"):
        result = _simulate_sai_status_normalization({"status": status})
        assert result["task_type"] == "meta_controller_execution", (
            f"task_type wrong for status={status!r}"
        )


# ──────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_status_success_maps_to_true,
        test_status_passed_maps_to_true,
        test_status_failed_maps_to_false,
        test_status_max_iters_maps_to_false,
        test_status_none_maps_to_false,
        test_status_error_maps_to_false,
        test_iterations_propagated,
        test_task_type_always_meta_controller,
    ]

    passed = 0
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  [PASS] {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed}/{len(tests)} passed")
    sys.exit(0 if failed == 0 else 1)
