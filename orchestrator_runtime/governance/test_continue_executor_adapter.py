"""
MS-AO8E + AO8I_1 Tests for Continue Executor Adapter.

Tests:
A. simple prompt returns PROJECT_S_CONTINUE_OK
B. file read sandbox works
C. file write sandbox works
D. outbox checksum matches
E. timeout/failure returns structured error
F. AO8I_1: small file allowed (guard passes)
G. AO8I_1: large file blocked (guard rejects)
H. AO8I_1: timeout returns structured TIMEOUT
I. AO8I_1: stale outbox detected
J. AO8I_1: preflight blocks large file before cn runs
"""

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from orchestrator_runtime.governance.continue_executor_adapter import (
    run_continue_prompt,
    write_continue_output_to_outbox,
    compute_checksum,
    run_and_write,
    guard_large_file_in_prompt,
    check_stale_outbox,
    preflight_checks,
    CLINE_OUTBOX,
    _archive_outbox,
)


# ── Test A: simple prompt ──────────────────────────────────────────────

def test_a_simple_prompt():
    """Simple prompt returns PROJECT_S_CONTINUE_OK."""
    result = run_continue_prompt("Reply exactly: PROJECT_S_CONTINUE_OK")
    assert result["status"] == "OK", f"Expected OK, got {result['status']}: {result.get('error')}"
    assert result["exit_code"] == 0
    assert "PROJECT_S_CONTINUE_OK" in result["stdout"], f"Expected phrase in stdout: {result['stdout']}"
    assert result["latency_ms"] > 0
    print(f"[A] PASS | latency={result['latency_ms']:.0f}ms | exit={result['exit_code']}")


# ── Test B: file read sandbox ──────────────────────────────────────────

def test_b_file_read():
    """Read a knowable sandbox file via Continue CLI."""
    result = run_continue_prompt(
        "Read C:\\ProjectS-Server-Live\\orchestrator_runtime\\sandbox\\ao8_continue_input.txt "
        "and reply with exact content only."
    )
    assert result["status"] == "OK", f"Expected OK, got {result['status']}: {result.get('error')}"
    assert "PROJECT_S_CONTINUE_FILE_READ" in result["stdout"]
    print(f"[B] PASS | file read verified")


# ── Test C: file write sandbox ─────────────────────────────────────────

def test_c_file_write():
    """Write a test file via Continue CLI and verify its content."""
    result = run_continue_prompt(
        "Create C:\\ProjectS-Server-Live\\orchestrator_runtime\\sandbox\\test_ao8e_write.txt "
        "with content AO8E_FILE_WRITE_OK"
    )
    assert result["status"] == "OK", f"Expected OK, got {result['status']}"
    # Verify file exists and content matches
    verify_path = Path(r"C:\ProjectS-Server-Live\orchestrator_runtime\sandbox\test_ao8e_write.txt")
    assert verify_path.exists(), "File was not created"
    # Detect encoding (Continue CLI may write UTF-16)
    raw = verify_path.read_bytes()
    if raw[:2] == b'\xff\xfe':
        content = raw.decode('utf-16-le').strip()
    elif raw[:2] == b'\xfe\xff':
        content = raw.decode('utf-16-be').strip()
    else:
        content = raw.decode('utf-8', errors='replace').strip()
    assert "AO8E_FILE_WRITE_OK" in content, f"Expected content not found. Raw bytes: {raw[:40]}"
    print(f"[C] PASS | file write verified: {content}")


# ── Test D: outbox checksum matches ────────────────────────────────────

def test_d_outbox_checksum():
    """RISK_010: write to outbox, checksum must match output_ready.json."""
    test_content = "AO8E_CHECKSUM_TEST_MARKER"
    test_run_id = "AO8E_TEST_CHECKSUM"
    test_iteration = 42

    # Use a temp outbox to avoid polluting real cline_outbox
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Monkey-patch CLINE_OUTBOX temporarily
        import orchestrator_runtime.governance.continue_executor_adapter as cea
        original_outbox = cea.CLINE_OUTBOX
        cea.CLINE_OUTBOX = tmp_path

        try:
            # Write via adapter
            result = write_continue_output_to_outbox(
                run_id=test_run_id,
                content=test_content,
                iteration=test_iteration,
            )
            assert result["status"] == "OK", f"Write failed: {result.get('error')}"
            assert result["output_path"] is not None
            assert result["checksum"] is not None

            # Verify last_output.md content
            output_file = tmp_path / "last_output.md"
            assert output_file.exists(), "last_output.md not created"
            assert output_file.read_text(encoding="utf-8") == test_content

            # Verify output_ready.json
            ready_file = tmp_path / "output_ready.json"
            assert ready_file.exists(), "output_ready.json not created"
            ready = json.loads(ready_file.read_text(encoding="utf-8"))

            # Verify checksum matches
            expected_checksum = compute_checksum(output_file)
            assert ready["checksum"] == expected_checksum, \
                f"Checksum mismatch: ready={ready['checksum']}, computed={expected_checksum}"
            assert ready["run_id"] == test_run_id
            assert ready["iteration"] == test_iteration
            assert ready["consumed"] == False

            print(f"[D] PASS | checksum={expected_checksum} run_id={test_run_id} iter={test_iteration}")
        finally:
            cea.CLINE_OUTBOX = original_outbox


# ── Test E: timeout/failure returns structured error ───────────────────

def test_e_timeout_error():
    """Timeout/failure returns structured error dict."""
    # Test with empty prompt simulates error
    result = run_continue_prompt("", timeout_sec=5)
    assert result["status"] in ("ERROR", "TIMEOUT"), \
        f"Expected ERROR or TIMEOUT, got {result['status']}"
    assert result["error"] is not None or result["stderr"] != ""
    assert "latency_ms" in result
    print(f"[E] PASS | status={result['status']} error={result.get('error')}")


# ══════════════════════════════════════════════════════════════════════
# AO8I_1 Tests (new)
# ══════════════════════════════════════════════════════════════════════

# ── Test F: small file allowed ─────────────────────────────────────────

def test_f_small_file_allowed():
    """AO8I_1: prompt referencing a small file should pass guard."""
    # Create a small temp file (< 200 KB)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        small_file = tmp_path / "small_test.txt"
        small_file.write_text("small content " * 100)  # ~1.3 KB

        prompt = f"Read file {small_file} and summarize"
        result = guard_large_file_in_prompt(prompt)

        assert result["allowed"] is True, f"Small file should be allowed, got: {result}"
        assert len(result["large_files"]) == 0, "Should have no large files"
        assert str(small_file) in result["files_checked"], f"Should have checked {small_file}"
        print(f"[F] PASS | small file allowed: {small_file}")


# ── Test G: large file blocked ─────────────────────────────────────────

def test_g_large_file_blocked():
    """AO8I_1: prompt referencing a large file (>200 KB) should be blocked."""
    # Create a temp file > 200 KB
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        large_file = tmp_path / "large_report.md"
        # Write 250 KB of data
        with open(large_file, "w") as f:
            f.write("x" * (250 * 1024))  # 250 KB

        prompt = f"Read file {large_file} and summarize the key points"
        result = guard_large_file_in_prompt(prompt)

        assert result["allowed"] is False, f"Large file should be blocked, got: {result}"
        assert len(result["large_files"]) == 1, f"Should have 1 large file, got: {result['large_files']}"
        assert result["large_files"][0]["size_kb"] > 200, "Size should exceed 200 KB"
        assert "exceeding" in result["reason"].lower() or "200" in result["reason"], \
            f"Reason should mention threshold: {result['reason']}"
        print(f"[G] PASS | large file blocked: {result['large_files'][0]['path']} ({result['large_files'][0]['size_kb']} KB)")


# ── Test H: timeout returns structured TIMEOUT ─────────────────────────

def test_h_timeout_returns_structured_timeout():
    """AO8I_1: Very short timeout should return structured TIMEOUT, not a hang."""
    result = run_continue_prompt(
        "Reply with a very long essay about everything you know",
        timeout_sec=5,  # Very short timeout
    )

    assert result["status"] == "TIMEOUT", \
        f"Expected TIMEOUT status, got {result['status']}: {result}"
    assert "timed out" in result["error"].lower(), \
        f"Error should mention timeout: {result.get('error')}"
    assert result["latency_ms"] < 15_000, \
        f"Latency should indicate timeout (< 15s): {result['latency_ms']:.0f}ms"
    print(f"[H] PASS | timeout={result['latency_ms']:.0f}ms status={result['status']}")


# ── Test I: stale outbox detected ──────────────────────────────────────

def test_i_stale_outbox_detected():
    """AO8I_1: Unconsumed output_ready.json should be detected as stale."""
    # Use temp dir to simulate stale outbox
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        import orchestrator_runtime.governance.continue_executor_adapter as cea
        original_outbox = cea.CLINE_OUTBOX
        cea.CLINE_OUTBOX = tmp_path

        try:
            # Write an unconsumed output_ready.json
            ready_path = tmp_path / "output_ready.json"
            stale_data = {
                "run_id": "TEST_STALE_RUN",
                "iteration": 1,
                "checksum": "abc123",
                "consumed": False,
                "timestamp": "2026-06-20T21:30:00+00:00",
            }
            with open(ready_path, "w", encoding="utf-8") as f:
                json.dump(stale_data, f, indent=4)

            # Also write a dummy last_output.md
            last_output = tmp_path / "last_output.md"
            last_output.write_text("stale content", encoding="utf-8")

            result = check_stale_outbox()

            assert result["stale"] is True, f"Should detect stale outbox: {result}"
            assert result["run_id"] == "TEST_STALE_RUN", f"Should report run_id: {result}"
            assert result["action"] == "archived" or result["action"] == "blocked", \
                f"Action should be archived or blocked: {result}"

            # Verify files were archived (moved to archive/)
            archive_dir = tmp_path / "archive"
            assert archive_dir.exists(), "Archive dir should exist after archiving"
            archive_files = list(archive_dir.iterdir())
            assert len(archive_files) >= 1, f"Archive should contain files: {archive_files}"

            print(f"[I] PASS | stale outbox detected for run_id={result['run_id']} action={result['action']}")
        finally:
            cea.CLINE_OUTBOX = original_outbox


# ── Test J: preflight blocks large file before cn runs ─────────────────

def test_j_preflight_blocks_large_file():
    """AO8I_1: preflight_checks should reject prompt referencing a large file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        large_file = tmp_path / "big_data.json"
        with open(large_file, "w") as f:
            f.write("[" + ", ".join('"x" * 100' for _ in range(5000)) + "]")  # ~250 KB

        prompt = f"Read {large_file} and summarize the contents"
        preflight = preflight_checks(prompt)

        assert preflight["allowed"] is False, \
            f"Preflight should block large file: {preflight}"
        assert preflight["reason"] is not None
        assert preflight["large_file_check"]["allowed"] is False
        assert len(preflight["large_file_check"]["large_files"]) == 1
        print(f"[J] PASS | preflight blocked: {preflight['reason'][:80]}...")


# ── AO8J_1: None-safe outbox regression ─────────────────────────────────
# Simulates continue_result = {"status":"FAIL","outbox":None}
# The CM patch uses: outbox = continue_result.get("outbox") or {}
# Then outbox.get("status") must not crash.

def test_k_continue_result_outbox_none():
    """Continue result with outbox=None must not crash when extracting fields."""
    import hashlib

    # Simulate the exact patched logic from continuous_mind.py
    continue_result = {"status": "FAIL", "outbox": None, "run": None}

    run = continue_result.get("run") or {}
    outbox = continue_result.get("outbox") or {}
    outbox_status = outbox.get("status", "MISSING")
    checksum = outbox.get("checksum", "MISSING")
    run_status = run.get("status", "MISSING")
    run_error = run.get("error", "(no error field)")

    # These must NOT crash and must return meaningful fallback values
    assert outbox_status == "MISSING", f"Expected MISSING, got {outbox_status}"
    assert checksum == "MISSING", f"Expected MISSING, got {checksum}"
    assert run_status == "MISSING", f"Expected MISSING, got {run_status}"
    assert run_error == "(no error field)", f"Expected (no error field), got {run_error}"

    print(f"[K] PASS | outbox=None handled: status={outbox_status} checksum={checksum} run={run_status}")

def test_l_continue_result_outbox_none_overall_ok():
    """Continue result with overall=OK but outbox=None must log error but not crash."""
    continue_result = {"overall": "OK", "outbox": None, "run": {"status": "OK"}}

    run = continue_result.get("run") or {}
    outbox = continue_result.get("outbox") or {}
    run_ok = continue_result.get("overall") == "OK" and run.get("status") == "OK"
    outbox_status = outbox.get("status", "MISSING")
    checksum = outbox.get("checksum", "MISSING")

    assert run_ok is True, f"run_ok must be True, got {run_ok}"
    assert outbox_status == "MISSING", f"outbox must be Missing, got {outbox_status}"
    assert checksum == "MISSING", f"checksum must be Missing, got {checksum}"
    print(f"[L] PASS | outbox=None with run_ok=True: status={outbox_status} checksum={checksum}")


# ── Run all tests ──────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("A: simple prompt", test_a_simple_prompt),
        ("B: file read sandbox", test_b_file_read),
        ("C: file write sandbox", test_c_file_write),
        ("D: outbox checksum matches", test_d_outbox_checksum),
        ("E: timeout/failure error", test_e_timeout_error),
        ("F: small file allowed (AO8I_1)", test_f_small_file_allowed),
        ("G: large file blocked (AO8I_1)", test_g_large_file_blocked),
        ("H: timeout returns TIMEOUT (AO8I_1)", test_h_timeout_returns_structured_timeout),
        ("I: stale outbox detected (AO8I_1)", test_i_stale_outbox_detected),
        ("J: preflight blocks large file (AO8I_1)", test_j_preflight_blocks_large_file),
        ("K: outbox=None no crash (AO8J_1)", test_k_continue_result_outbox_none),
        ("L: outbox=None + run_ok=True (AO8J_1)", test_l_continue_result_outbox_none_overall_ok),
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("MS-AO8E + AO8I_1 Continue Executor Adapter - Test Suite")
    print("=" * 60)

    for name, testfn in tests:
        try:
            testfn()
            passed += 1
            print(f"  OK {name}")
        except Exception as e:
            failed += 1
            import traceback
            print(f"  FAIL {name}: {e}")
            traceback.print_exc()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)