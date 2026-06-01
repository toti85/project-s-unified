"""
Unit tests for bridge_runner.py — component-level only, NO end-to-end simulation.

Each test writes real fixture files to a temp directory on disk, then calls
bridge_runner functions in isolation. No executor is faked, no full pipeline
is run. This is the RISK_008 mitigation: test parts, not the whole flow.

Run:
    python -m pytest orchestrator_runtime/sandbox/test_bridge_runner.py -v
"""

import json
import hashlib
import shutil
import tempfile
from pathlib import Path

import pytest

from orchestrator_runtime.governance.bridge_runner import (
    consume_executor_output,
    compute_checksum,
    set_test_paths,
    reset_test_paths,
    STATUS_ACCEPTED,
    STATUS_WAITING_FOR_EXECUTOR,
    STATUS_REJECTED_CHECKSUM,
    STATUS_REJECTED_RUN_ID,
    STATUS_REJECTED_CONSUMED,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_outbox(tmp_path: Path):
    """Create a temp outbox dir with cycle_log.jsonl target."""
    outbox = tmp_path / "cline_outbox"
    outbox.mkdir(parents=True)
    cycle_log = tmp_path / "cycle_log.jsonl"
    set_test_paths(outbox, cycle_log)
    yield outbox
    reset_test_paths()


def _write_ready(outbox: Path, run_id: str, iteration: int, checksum: str,
                 consumed: bool = False):
    """Write output_ready.json with given params."""
    data = {
        "run_id": run_id,
        "iteration": iteration,
        "timestamp": "2026-05-30T04:52:54.3923550Z",
        "status": "ready",
        "checksum": checksum,
    }
    if consumed:
        data["consumed"] = True
    (outbox / "output_ready.json").write_text(json.dumps(data, indent=4), encoding="utf-8")


def _write_output(outbox: Path, content: str):
    """Write last_output.md with given content."""
    (outbox / "last_output.md").write_text(content, encoding="utf-8")


def _real_checksum(content: str) -> str:
    """Compute what compute_checksum() would return for this content."""
    h = hashlib.sha256(content.encode("utf-8"))
    return h.hexdigest()[:16]


# ── Tests ─────────────────────────────────────────────────────────────

class TestChecksumMatch:
    """Valid output with correct checksum → ACCEPTED."""

    def test_accepts_valid_output(self, tmp_outbox: Path):
        content = "# Test Report\nHello world\n"
        _write_output(tmp_outbox, content)
        # Use actual file checksum (write_text may convert line endings on Windows)
        cs = compute_checksum(tmp_outbox / "last_output.md")
        _write_ready(tmp_outbox, "TEST_001", 1, cs)

        result = consume_executor_output("TEST_001", 1)

        assert result["status"] == STATUS_ACCEPTED
        assert result["run_id"] == "TEST_001"
        assert result["iteration"] == 1

    def test_marks_consumed_after_accept(self, tmp_outbox: Path):
        content = "data"
        _write_output(tmp_outbox, content)
        cs = compute_checksum(tmp_outbox / "last_output.md")
        _write_ready(tmp_outbox, "TEST_002", 1, cs)

        consume_executor_output("TEST_002", 1)

        # Verify consumed=True was written atomically
        ready = json.loads((tmp_outbox / "output_ready.json").read_text(encoding="utf-8"))
        assert ready["consumed"] is True
        assert "consumed_at" in ready


class TestChecksumMismatch:
    """Wrong checksum → REJECTED_CHECKSUM, content NOT consumed."""

    def test_rejects_bad_checksum(self, tmp_outbox: Path):
        content = "# Real content"
        _write_ready(tmp_outbox, "TEST_003", 1, "0000000000000000")  # wrong
        _write_output(tmp_outbox, content)

        result = consume_executor_output("TEST_003", 1)

        assert result["status"] == STATUS_REJECTED_CHECKSUM
        assert result["content"] is None
        assert "Checksum mismatch" in result["error"]

    def test_does_not_mark_consumed_on_mismatch(self, tmp_outbox: Path):
        content = "data"
        _write_ready(tmp_outbox, "TEST_004", 1, "badchecksum00000")
        _write_output(tmp_outbox, content)

        consume_executor_output("TEST_004", 1)

        ready = json.loads((tmp_outbox / "output_ready.json").read_text(encoding="utf-8"))
        assert ready.get("consumed", False) is False


class TestRunIdMismatch:
    """run_id or iteration doesn't match → REJECTED_RUN_ID."""

    def test_rejects_wrong_run_id(self, tmp_outbox: Path):
        content = "x"
        _write_output(tmp_outbox, content)
        cs = compute_checksum(tmp_outbox / "last_output.md")
        _write_ready(tmp_outbox, "WRONG_ID", 1, cs)

        result = consume_executor_output("EXPECTED_ID", 1)

        assert result["status"] == STATUS_REJECTED_RUN_ID
        assert "run_id mismatch" in result["error"]

    def test_rejects_wrong_iteration(self, tmp_outbox: Path):
        content = "x"
        _write_output(tmp_outbox, content)
        cs = compute_checksum(tmp_outbox / "last_output.md")
        _write_ready(tmp_outbox, "TEST_005", 99, cs)  # iter 99

        result = consume_executor_output("TEST_005", 1)  # expect iter 1

        assert result["status"] == STATUS_REJECTED_RUN_ID
        assert "iteration mismatch" in result["error"]


class TestWaitingForExecutor:
    """Missing files → WAITING_FOR_EXECUTOR, NOT a false PASS."""

    def test_no_output_ready_json(self, tmp_outbox: Path):
        # Don't write output_ready.json at all
        result = consume_executor_output("NOPE", 1)

        assert result["status"] == STATUS_WAITING_FOR_EXECUTOR
        assert result["content"] is None

    def test_no_last_output_md(self, tmp_outbox: Path):
        content_placeholder = "ignored"
        cs = _real_checksum(content_placeholder)
        _write_ready(tmp_outbox, "TEST_006", 1, cs)
        # Don't write last_output.md

        result = consume_executor_output("TEST_006", 1)

        assert result["status"] == STATUS_WAITING_FOR_EXECUTOR
        assert "last_output.md not found" in result["error"]

    def test_empty_outbox_returns_waiting(self, tmp_outbox: Path):
        # Fresh empty dir — no files at all
        result = consume_executor_output("EMPTY", 1)

        assert result["status"] == STATUS_WAITING_FOR_EXECUTOR
        # Critical: must NOT be ACCEPTED (RISK_008 check)
        assert result["status"] != STATUS_ACCEPTED


class TestAlreadyConsumed:
    """consumed=True → REJECTED_CONSUMED (no double-consume)."""

    def test_rejects_double_consume(self, tmp_outbox: Path):
        content = "already taken"
        _write_output(tmp_outbox, content)
        cs = compute_checksum(tmp_outbox / "last_output.md")
        _write_ready(tmp_outbox, "TEST_007", 1, cs, consumed=True)

        result = consume_executor_output("TEST_007", 1)

        assert result["status"] == STATUS_REJECTED_CONSUMED
        assert "already consumed" in result["error"]


class TestComputeChecksum:
    """compute_checksum helper works correctly."""

    def test_deterministic(self, tmp_path: Path):
        f = tmp_path / "data.txt"
        f.write_text("hello", encoding="utf-8")
        cs1 = compute_checksum(f)
        cs2 = compute_checksum(f)
        assert cs1 == cs2
        assert len(cs1) == 16

    def test_different_content_different_checksum(self, tmp_path: Path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("aaa", encoding="utf-8")
        f2.write_text("bbb", encoding="utf-8")
        assert compute_checksum(f1) != compute_checksum(f2)


class TestCycleLog:
    """cycle_log.jsonl gets written on each call."""

    def test_logs_consumed_event(self, tmp_outbox: Path, tmp_path: Path):
        content = "logged"
        _write_output(tmp_outbox, content)
        cs = compute_checksum(tmp_outbox / "last_output.md")
        _write_ready(tmp_outbox, "TEST_LOG", 1, cs)

        consume_executor_output("TEST_LOG", 1)

        cycle_log = tmp_path / "cycle_log.jsonl"
        assert cycle_log.exists()
        lines = cycle_log.read_text(encoding="utf-8").strip().split("\n")
        # Last line should be bridge_consumed
        last = json.loads(lines[-1])
        assert last["event"] == "bridge_consumed"
        assert last["run_id"] == "TEST_LOG"