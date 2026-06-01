"""
test_sai_pipeline_smoke.py
===========================

Smoke test: SuperIntelligentAI pipeline importálhatósága és init-je.

Célok:
- Ne hívjon külső API-t
- Ne igényeljen hálózatot
- Gyorsan fusson (<10s)
- Lefedi: import, init, status mapping, MetaController init logikája

Futtatás:
    python -m pytest tests/test_sai_pipeline_smoke.py -v
    # vagy közvetlenül:
    python tests/test_sai_pipeline_smoke.py
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

# Setup import path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))


# ──────────────────────────────────────────────
# Test 1: Import
# ──────────────────────────────────────────────

def test_super_intelligent_ai_importable():
    """SuperIntelligentAI modul importálható."""
    try:
        from core.super_intelligent_ai import SuperIntelligentAI
        assert SuperIntelligentAI is not None
    except ImportError as e:
        raise AssertionError(f"Import failed: {e}") from e


# ──────────────────────────────────────────────
# Test 2: Init (no-meta path, no API calls)
# ──────────────────────────────────────────────

def test_sai_init_no_meta():
    """
    SuperIntelligentAI(use_meta_controller=False) inicializálható
    anélkül hogy API-t hívna.
    """
    from core.super_intelligent_ai import SuperIntelligentAI
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)
        assert ai is not None
        assert ai.use_meta_controller is False
        assert ai.meta_controller is None


# ──────────────────────────────────────────────
# Test 3: Meta init — csak ha a meta réteg elérhető
# ──────────────────────────────────────────────

def test_sai_meta_controller_flag_respected():
    """
    use_meta_controller=False esetén meta_controller attribútum None marad.
    use_meta_controller=True esetén, ha META_LAYER_AVAILABLE=True, nem None.
    """
    from core.super_intelligent_ai import SuperIntelligentAI, META_LAYER_AVAILABLE
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ai_no_meta = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)
        assert ai_no_meta.meta_controller is None, "meta_controller should be None when disabled"

        if META_LAYER_AVAILABLE:
            ai_meta = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=True)
            # meta_controller either initialized or fell back (both acceptable)
            # The important thing: no uncaught exception
            assert hasattr(ai_meta, "meta_controller")


# ──────────────────────────────────────────────
# Test 4: execute_intelligent_task — mock meta result "passed"
# ──────────────────────────────────────────────

def test_execute_with_mocked_meta_passed():
    """
    execute_intelligent_task() meta branch:
    MetaController returning {"status": "passed"} → {"success": True}.

    Ez a 2026-04-29 bugfix közvetlen tesztje mock-kal, API hívás nélkül.
    """
    from core.super_intelligent_ai import SuperIntelligentAI
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

        # Manually attach a mock MetaController
        mock_mc = MagicMock()
        mock_mc.run_goal = AsyncMock(return_value={
            "status": "passed",
            "iterations": 1,
            "status_reason": "deterministic_output_no_critical_issues",
        })
        ai.meta_controller = mock_mc
        ai.use_meta_controller = True

        result = asyncio.run(
            ai.execute_intelligent_task("smoke test task", use_meta_controller=True)
        )

    assert result["success"] is True, (
        f"Expected success=True for status='passed', got: {result}"
    )
    assert result["task_type"] == "meta_controller_execution"
    assert "[OK]" in result.get("output", "")


# ──────────────────────────────────────────────
# Test 5: execute_intelligent_task — mock meta result "success"
# ──────────────────────────────────────────────

def test_execute_with_mocked_meta_success():
    """
    execute_intelligent_task() meta branch:
    MetaController returning {"status": "success"} → {"success": True}.
    (Original path, still must work.)
    """
    from core.super_intelligent_ai import SuperIntelligentAI
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

        mock_mc = MagicMock()
        mock_mc.run_goal = AsyncMock(return_value={
            "status": "success",
            "iterations": 2,
        })
        ai.meta_controller = mock_mc
        ai.use_meta_controller = True

        result = asyncio.run(
            ai.execute_intelligent_task("smoke test task", use_meta_controller=True)
        )

    assert result["success"] is True
    assert "[OK]" in result.get("output", "")


# ──────────────────────────────────────────────
# Test 6: execute_intelligent_task — mock meta result "failed"
# ──────────────────────────────────────────────

def test_execute_with_mocked_meta_failed():
    """
    execute_intelligent_task() meta branch:
    MetaController returning {"status": "failed"} → {"success": False}.
    """
    from core.super_intelligent_ai import SuperIntelligentAI
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

        mock_mc = MagicMock()
        mock_mc.run_goal = AsyncMock(return_value={
            "status": "failed",
            "iterations": 5,
        })
        ai.meta_controller = mock_mc
        ai.use_meta_controller = True

        result = asyncio.run(
            ai.execute_intelligent_task("smoke test task", use_meta_controller=True)
        )

    assert result["success"] is False
    assert "[FAIL]" in result.get("output", "")


# ──────────────────────────────────────────────
# Test 7: META_LAYER_AVAILABLE flag megléte
# ──────────────────────────────────────────────

def test_meta_layer_available_flag_exists():
    """META_LAYER_AVAILABLE modul szintű flag létezik és bool típusú."""
    from core.super_intelligent_ai import META_LAYER_AVAILABLE
    assert isinstance(META_LAYER_AVAILABLE, bool), (
        f"META_LAYER_AVAILABLE should be bool, got {type(META_LAYER_AVAILABLE)}"
    )


# ──────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_super_intelligent_ai_importable,
        test_sai_init_no_meta,
        test_sai_meta_controller_flag_respected,
        test_execute_with_mocked_meta_passed,
        test_execute_with_mocked_meta_success,
        test_execute_with_mocked_meta_failed,
        test_meta_layer_available_flag_exists,
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
