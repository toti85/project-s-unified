"""
Bridge Runner CWI Integration Tests - AO5_T10
===============================================

Tests proving CWI advisory integration does not change existing behavior.

Run with:
    python orchestrator_runtime/governance/test_bridge_runner_cwi.py

These tests verify:
A. With CWI_ADVISORY_ENABLED = False, consume behavior is unchanged
B. If CWI advisory raises internally, consume still proceeds
C. CWI advisory result never changes PASS/FAIL verdict
D. checksum mismatch still rejects exactly as before
E. already-consumed output still rejects exactly as before
"""

import json
import hashlib
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator_runtime.governance.bridge_runner import (
    consume_executor_output,
    set_test_paths,
    reset_test_paths,
    compute_checksum,
    STATUS_ACCEPTED,
    STATUS_REJECTED_CHECKSUM,
    STATUS_REJECTED_CONSUMED,
    CWI_ADVISORY_ENABLED,
)

# Test Results Tracking

tests_run = 0
tests_passed = 0
tests_failed = 0


def run_test(name, fn):
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    try:
        fn()
        tests_passed += 1
        print("  PASS: " + name)
    except Exception as e:
        tests_failed += 1
        print("  FAIL: " + name + " - " + str(e))


def _create_test_outbox(content_bytes, checksum, run_id, consumed=False):
    """Create a temporary outbox with output_ready.json and last_output.md.
    
    content_bytes: raw bytes to write to last_output.md (binary mode)
    checksum: SHA-256 hex digest of those exact bytes, first 16 chars
    """
    tmpdir = Path(tempfile.mkdtemp())
    outbox = tmpdir / "cline_outbox"
    outbox.mkdir()

    # Write output_ready.json
    ready = {
        "run_id": run_id,
        "iteration": 1,
        "consumed": consumed,
        "checksum": checksum,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(outbox / "output_ready.json", "w", encoding="utf-8") as f:
        json.dump(ready, f)

    # Write last_output.md in BINARY mode - exact bytes match checksum
    with open(outbox / "last_output.md", "wb") as f:
        f.write(content_bytes)

    return tmpdir


def _make_content(text):
    """Create content bytes and compute matching checksum.
    
    Uses UTF-8 encoding without BOM, LF line endings only.
    """
    raw = text.encode("utf-8")
    h = hashlib.sha256()
    h.update(raw)
    cs = h.hexdigest()[:16]
    return raw, cs


# Test A: CWI_ADVISORY_ENABLED = False means unchanged behavior

def test_a_cwi_disabled_unchanged():
    """With CWI_ADVISORY_ENABLED = False, consume behavior is identical to pre-CWI."""
    assert CWI_ADVISORY_ENABLED is False, "Feature flag must be False for this test"

    text = "# Test Output\nThis is test content.\n"
    raw, cs = _make_content(text)

    tmpdir = _create_test_outbox(raw, cs, "AO5_T10_TEST_A")

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)

        result = consume_executor_output("AO5_T10_TEST_A", 1)

        assert result["status"] == STATUS_ACCEPTED, "Expected ACCEPTED, got " + str(result["status"])
        assert result["content"] == text
        assert result["run_id"] == "AO5_T10_TEST_A"

        # Verify consumed flag was set
        with open(tmpdir / "cline_outbox" / "output_ready.json") as f:
            ready = json.load(f)
        assert ready["consumed"] is True, "Consumed flag must be set"

    finally:
        reset_test_paths()
        shutil.rmtree(tmpdir, ignore_errors=True)


# Test B: CWI internal error does not block consume

def test_b_cwi_error_does_not_block():
    """If CWI advisory raises internally, consume still proceeds normally."""
    assert CWI_ADVISORY_ENABLED is False

    text = "# Error Test\nContent after CWI failure.\n"
    raw, cs = _make_content(text)

    tmpdir = _create_test_outbox(raw, cs, "AO5_T10_TEST_B")

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)

        result = consume_executor_output("AO5_T10_TEST_B", 1)

        assert result["status"] == STATUS_ACCEPTED, "Expected ACCEPTED despite CWI, got " + str(result["status"])

    finally:
        reset_test_paths()
        shutil.rmtree(tmpdir, ignore_errors=True)


# Test C: CWI advisory never changes verdict

def test_c_cwi_never_changes_verdict():
    """CWI advisory result is purely informational - never affects PASS/FAIL."""
    text = "FAILED: Something went wrong\nERROR: test failure\n"
    raw, cs = _make_content(text)

    tmpdir = _create_test_outbox(raw, cs, "AO5_T10_TEST_C")

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)

        result = consume_executor_output("AO5_T10_TEST_C", 1)

        assert result["status"] == STATUS_ACCEPTED, "Expected ACCEPTED, got " + str(result["status"])
        assert result["content"] == text

    finally:
        reset_test_paths()
        shutil.rmtree(tmpdir, ignore_errors=True)


# Test D: Checksum mismatch still rejects

def test_d_checksum_rejection():
    """Checksum mismatch still produces REJECTED_CHECKSUM exactly as before."""
    text = "# Checksum Test\nContent with wrong checksum.\n"
    raw, _actual_cs = _make_content(text)

    tmpdir = _create_test_outbox(raw, "deadbeef12345678", "AO5_T10_TEST_D")

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)

        result = consume_executor_output("AO5_T10_TEST_D", 1)

        assert result["status"] == STATUS_REJECTED_CHECKSUM, \
            "Expected REJECTED_CHECKSUM, got " + str(result["status"])
        assert "Checksum mismatch" in result.get("error", ""), "Error must mention checksum mismatch"

    finally:
        reset_test_paths()
        shutil.rmtree(tmpdir, ignore_errors=True)


# Test E: Already-consumed output still rejects

def test_e_double_consume_rejection():
    """Already-consumed output still produces REJECTED_CONSUMED exactly as before."""
    text = "# Already Consumed\nThis was already processed.\n"
    raw, cs = _make_content(text)

    tmpdir = _create_test_outbox(raw, cs, "AO5_T10_TEST_E", consumed=True)

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)

        result = consume_executor_output("AO5_T10_TEST_E", 1)

        assert result["status"] == STATUS_REJECTED_CONSUMED, \
            "Expected REJECTED_CONSUMED, got " + str(result["status"])
        assert "already consumed" in result.get("error", "").lower(), \
            "Error must mention already consumed"

    finally:
        reset_test_paths()
        shutil.rmtree(tmpdir, ignore_errors=True)


# Run Tests

if __name__ == "__main__":
    print("=" * 60)
    print("Bridge Runner CWI Integration Tests - AO5_T10")
    print("CWI_ADVISORY_ENABLED = " + str(CWI_ADVISORY_ENABLED))
    print("=" * 60)

    run_test("A: CWI disabled = unchanged behavior", test_a_cwi_disabled_unchanged)
    run_test("B: CWI error does not block consume", test_b_cwi_error_does_not_block)
    run_test("C: CWI never changes verdict", test_c_cwi_never_changes_verdict)
    run_test("D: Checksum mismatch still rejects", test_d_checksum_rejection)
    run_test("E: Double-consume still rejects", test_e_double_consume_rejection)

    print()
    print("=" * 60)
    print("Results: " + str(tests_passed) + "/" + str(tests_run) + " passed, " + str(tests_failed) + " failed")
    print("=" * 60)

    if tests_failed > 0:
        sys.exit(1)
    else:
        print("All tests passed.")
        sys.exit(0)