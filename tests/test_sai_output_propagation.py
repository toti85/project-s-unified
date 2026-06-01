"""
test_sai_output_propagation.py
================================

Regression test: SAI MetaController output propagation.

Bizonyítja, hogy a MetaController branch a tényleges executor outputot
adja vissza — nem csak a generic wrapper üzenetet.

Rögzíti a 2026-04-30 bugfix-et: meta_controller.py run_goal() success
return dict-jébe bekerült az "output" és "execution_result" mező, és a
super_intelligent_ai.py MetaController branch ezt felszínre hozza.

Futtatás:
    python tests/test_sai_output_propagation.py
"""
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))


def _simulate_sai_output_extraction(meta_result: dict) -> dict:
    """
    Replication of output extraction logic in super_intelligent_ai.py
    execute_intelligent_task() MetaController branch (fixed version).
    """
    if meta_result.get("status") in ("success", "passed"):
        output = (
            meta_result.get("output")
            or (meta_result.get("execution_result") or {}).get("output")
            or (meta_result.get("final_result") or {}).get("output")
            or f"[OK] MetaController completed goal in {meta_result.get('iterations', 1)} iterations"
        )
        return {
            "success": True,
            "output": output,
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
# Tests: output extraction logic
# ──────────────────────────────────────────────

def test_direct_output_field_propagated():
    """
    meta_result["output"] = "abc" → final output == "abc".
    (meta_controller.py now sets "output" directly in success return dict)
    """
    result = _simulate_sai_output_extraction({
        "status": "passed",
        "output": "witness\\evidence_reader.py\nwitness\\__init__.py",
        "iterations": 1,
    })
    assert result["success"] is True
    assert result["output"] == "witness\\evidence_reader.py\nwitness\\__init__.py", (
        f"REGRESSION: direct output not propagated, got: {result['output']!r}"
    )


def test_execution_result_output_propagated():
    """
    meta_result["execution_result"]["output"] = "abc" → final output == "abc".
    Fallback chain when "output" key is absent but "execution_result" has it.
    """
    result = _simulate_sai_output_extraction({
        "status": "passed",
        "execution_result": {"output": "witness\\evidence_reader.py", "status": "success"},
        "iterations": 1,
    })
    assert result["success"] is True
    assert result["output"] == "witness\\evidence_reader.py", (
        f"REGRESSION: execution_result output not propagated, got: {result['output']!r}"
    )


def test_final_result_output_propagated():
    """
    meta_result["final_result"]["output"] = "abc" → final output == "abc".
    Second fallback: meta_controller.py also sets "final_result" = execution_result.
    """
    result = _simulate_sai_output_extraction({
        "status": "passed",
        "final_result": {"output": "witness\\learning_diagnostic.py", "status": "success"},
        "iterations": 1,
    })
    assert result["success"] is True
    assert result["output"] == "witness\\learning_diagnostic.py", (
        f"REGRESSION: final_result output not propagated, got: {result['output']!r}"
    )


def test_fallback_wrapper_when_no_output():
    """
    When no output field anywhere → fallback to generic wrapper string.
    """
    result = _simulate_sai_output_extraction({
        "status": "passed",
        "iterations": 3,
    })
    assert result["success"] is True
    assert "[OK]" in result["output"]
    assert "3 iterations" in result["output"]


def test_output_priority_direct_over_execution_result():
    """
    Direct "output" field takes priority over "execution_result.output".
    """
    result = _simulate_sai_output_extraction({
        "status": "passed",
        "output": "direct output wins",
        "execution_result": {"output": "execution_result output loses"},
        "iterations": 1,
    })
    assert result["output"] == "direct output wins"


def test_failed_status_not_propagated():
    """
    Failed status → success=False, no output propagation.
    """
    result = _simulate_sai_output_extraction({
        "status": "failed",
        "output": "should not appear",
        "iterations": 5,
    })
    assert result["success"] is False
    assert "[FAIL]" in result["output"]
    assert "should not appear" not in result["output"]


# ──────────────────────────────────────────────
# Integration test: SAI with mocked MetaController that returns output
# ──────────────────────────────────────────────

def test_sai_execute_surfaces_meta_output():
    """
    End-to-end with mocked MetaController: execute_intelligent_task()
    returns the executor's real output, not a generic wrapper.
    """
    from core.super_intelligent_ai import SuperIntelligentAI
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

        mock_mc = MagicMock()
        mock_mc.run_goal = AsyncMock(return_value={
            "status": "passed",
            "output": "witness\\evidence_reader.py\nwitness\\__init__.py\nwitness\\bridges\\organism_to_meta.py",
            "iterations": 1,
            "execution_result": {
                "output": "witness\\evidence_reader.py\nwitness\\__init__.py\nwitness\\bridges\\organism_to_meta.py",
                "status": "success",
            },
        })
        ai.meta_controller = mock_mc
        ai.use_meta_controller = True

        result = asyncio.run(
            ai.execute_intelligent_task("List Python files in witness dir", use_meta_controller=True)
        )

    assert result["success"] is True
    assert "witness\\evidence_reader.py" in result["output"], (
        f"REGRESSION: real file output not surfaced, got: {result['output']!r}"
    )
    assert "[OK] MetaController completed" not in result["output"], (
        f"REGRESSION: generic wrapper returned instead of real output: {result['output']!r}"
    )


# ──────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_direct_output_field_propagated,
        test_execution_result_output_propagated,
        test_final_result_output_propagated,
        test_fallback_wrapper_when_no_output,
        test_output_priority_direct_over_execution_result,
        test_failed_status_not_propagated,
        test_sai_execute_surfaces_meta_output,
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
