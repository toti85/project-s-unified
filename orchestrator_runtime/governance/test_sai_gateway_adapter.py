"""
test_sai_gateway_adapter.py — Tests for sai_gateway_adapter.

Tests:
  A. unknown mission_id is denied (fail-closed)
  B. known LOW goal → ALLOW (per current gateway policy)
  C. known HIGH goal → DENY (per current gateway policy)
  D. write_sai_output_to_outbox writes valid output_ready.json
  E. checksum in output_ready.json matches actual last_output.md bytes
  F. adapter does not import / instantiate SuperIntelligentAI

Run:
  python orchestrator_runtime/governance/test_sai_gateway_adapter.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

# ── Path setup ─────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator_runtime.governance.sai_gateway_adapter import (
    build_sai_handoff_content,
    sai_pre_execution_gate,
    write_sai_output_to_outbox,
)


# ── Test helpers ───────────────────────────────────────────────────────

_PASS = "PASS"
_FAIL = "FAIL"


def _run(label: str, fn) -> tuple[str, str]:
    try:
        fn()
        return _PASS, label
    except AssertionError as exc:
        return _FAIL, f"{label}: AssertionError — {exc}"
    except Exception as exc:
        return _FAIL, f"{label}: Exception — {traceback.format_exc(limit=3)}"


# ── Tests ──────────────────────────────────────────────────────────────

def test_a_unknown_mission_denied():
    """A. Unknown mission_id must be DENY (fail-closed)."""
    result = sai_pre_execution_gate("SAI_COMPLETELY_UNKNOWN_XYZ_999")
    assert result["allowed"] is False, f"expected allowed=False, got {result['allowed']}"
    assert result["gateway_action"] == "DENY", f"expected DENY, got {result['gateway_action']}"
    assert result.get("checks", {}).get("goal_queue", {}).get("found") is False, \
        "goal_queue.found should be False for unknown mission"


def test_b_known_low_goal_allowed():
    """B. Known LOW-risk goal (GOAL_007) → ALLOW according to current gateway."""
    result = sai_pre_execution_gate("GOAL_007")
    # gateway_action depends on risk_classifier; LOW → ALLOW
    assert result["gateway_action"] == "ALLOW", \
        f"expected ALLOW for LOW risk GOAL_007, got {result['gateway_action']}"
    assert result["allowed"] is True, f"allowed should be True for ALLOW, got {result['allowed']}"
    assert result["risk_level"] == "LOW", f"expected LOW, got {result['risk_level']}"


def test_c_known_high_goal_denied():
    """C. Known HIGH-risk goal (AO3_HARD_T3_HIGH) → DENY."""
    result = sai_pre_execution_gate("AO3_HARD_T3_HIGH")
    assert result["gateway_action"] == "DENY", \
        f"expected DENY for HIGH risk AO3_HARD_T3_HIGH, got {result['gateway_action']}"
    assert result["allowed"] is False, f"allowed should be False for DENY"
    assert result["risk_level"] == "HIGH", f"expected HIGH, got {result['risk_level']}"


def test_d_write_outbox_valid_json():
    """D. write_sai_output_to_outbox writes valid output_ready.json."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # Patch the outbox path inside adapter
        import orchestrator_runtime.governance.sai_gateway_adapter as mod
        original = mod._CLINE_OUTBOX
        mod._CLINE_OUTBOX = tmp
        try:
            result = write_sai_output_to_outbox(
                "TEST_D_MISSION",
                "# Test output\nHello world",
                iteration=1,
            )
        finally:
            mod._CLINE_OUTBOX = original

        assert result["success"] is True, f"write failed: {result.get('error')}"

        # Verify output_ready.json is valid JSON
        ready_path = tmp / "output_ready.json"
        assert ready_path.exists(), "output_ready.json missing"
        with ready_path.open(encoding="utf-8") as fh:
            ready = json.load(fh)

        assert ready["run_id"] == "TEST_D_MISSION"
        assert ready["iteration"] == 1
        assert ready["consumed"] is False
        assert isinstance(ready["checksum"], str) and len(ready["checksum"]) == 16


def test_e_checksum_matches():
    """E. Checksum in output_ready.json matches actual SHA-256 of last_output.md."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        content = "# Checksum test\nThis content will be checksummed."

        import orchestrator_runtime.governance.sai_gateway_adapter as mod
        original = mod._CLINE_OUTBOX
        mod._CLINE_OUTBOX = tmp
        try:
            result = write_sai_output_to_outbox("TEST_E_CHECKSUM", content)
        finally:
            mod._CLINE_OUTBOX = original

        assert result["success"] is True

        # Independently compute checksum
        last_output_path = tmp / "last_output.md"
        h = hashlib.sha256()
        with last_output_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        expected_checksum = h.hexdigest()[:16]

        # Read stored checksum
        ready_path = tmp / "output_ready.json"
        with ready_path.open(encoding="utf-8") as fh:
            ready = json.load(fh)
        stored_checksum = ready["checksum"]

        assert stored_checksum == expected_checksum, \
            f"checksum mismatch: stored={stored_checksum!r} expected={expected_checksum!r}"
        assert result["checksum"] == expected_checksum, \
            f"returned checksum mismatch: {result['checksum']!r} != {expected_checksum!r}"


def test_f_no_sai_import():
    """F. Calling the adapter must not import or instantiate SuperIntelligentAI."""
    # Import adapter fresh in a sub-check via sys.modules inspection
    # SuperIntelligentAI lives in src.core.super_intelligent_ai
    sai_key = "src.core.super_intelligent_ai"
    # Remove from sys.modules if somehow already loaded
    was_present = sai_key in sys.modules
    if was_present:
        del sys.modules[sai_key]

    # Run gate — should not trigger SAI import
    _ = sai_pre_execution_gate("GOAL_007")

    assert sai_key not in sys.modules, \
        f"SuperIntelligentAI was imported during sai_pre_execution_gate call!"

    # Run outbox write — should not trigger SAI import
    with tempfile.TemporaryDirectory() as tmp_dir:
        import orchestrator_runtime.governance.sai_gateway_adapter as mod
        original = mod._CLINE_OUTBOX
        mod._CLINE_OUTBOX = Path(tmp_dir)
        try:
            write_sai_output_to_outbox("TEST_F_NO_SAI", "test content")
        finally:
            mod._CLINE_OUTBOX = original

    assert sai_key not in sys.modules, \
        "SuperIntelligentAI was imported during write_sai_output_to_outbox call!"


# ── Runner ─────────────────────────────────────────────────────────────

_TESTS = [
    ("A. unknown mission denied (fail-closed)", test_a_unknown_mission_denied),
    ("B. known LOW goal → ALLOW",               test_b_known_low_goal_allowed),
    ("C. known HIGH goal → DENY",               test_c_known_high_goal_denied),
    ("D. write_outbox writes valid JSON",        test_d_write_outbox_valid_json),
    ("E. checksum matches last_output.md",       test_e_checksum_matches),
    ("F. no SAI import/instantiation",           test_f_no_sai_import),
]


def main() -> int:
    print("=" * 60)
    print("  sai_gateway_adapter — test suite")
    print("=" * 60)
    results = [_run(label, fn) for label, fn in _TESTS]
    print()
    passed = failed = 0
    for status, msg in results:
        icon = "✓" if status == _PASS else "✗"
        print(f"  {icon} {msg}")
        if status == _PASS:
            passed += 1
        else:
            failed += 1
    print()
    print(f"  Results: {passed}/{len(_TESTS)} passed")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
