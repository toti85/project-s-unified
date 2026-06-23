"""
Test suite for continue_watchdog.py — 4 tests.

1. allow on healthy AO8G history
2. block on synthetic 3 FAIL
3. block on synthetic low average
4. kill switch block
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SCORE = 0
MAX = 5

def _test(name: str, result: dict, expect_allow: bool):
    global SCORE
    ok = result["allow_continue"] == expect_allow
    marker = "PASS" if ok else "FAIL"
    SCORE += 1 if ok else 0
    print(f"  [{marker}] {name}: allow_continue={result['allow_continue']} reason={result['reason']}")
    if not ok:
        print(f"        evidence={result.get('evidence', [])}")
    return ok

def test_1_healthy_allow():
    """Watchdog should ALLOW on healthy AO8G history (all completed, avg=3.0)."""
    print("[1] healthy state — should ALLOW")
    from orchestrator_runtime.governance.continue_watchdog import decide
    result = decide()
    return _test("healthy allow", result, expect_allow=True)

def test_2_synthetic_3_fail():
    """Watchdog should BLOCK when we inject 3 consecutive FAIL entries."""
    print("[2] synthetic 3 consecutive FAIL — should BLOCK")
    tm_path = ROOT / "orchestrator_runtime" / "taste_model" / "mission_outcomes.jsonl"
    backup = tm_path.read_text(encoding="utf-8-sig") if tm_path.exists() else ""
    try:
        # Append 3 synthetic FAIL entries for continue_cli
        for i in range(3):
            entry = {
                "mission_id": f"SYNTH_FAIL_{i}",
                "date": "2026-06-19",
                "claimed_status": "failed",
                "actual_status": "failed",
                "model_used": "continue_cli_qwen3.6",
                "runtime_validated": False,
                "value_immediate": 1,
                "patterns": ["cm_continue", "cm_failed"],
                "notes": f"Synthetic fail {i}",
                "logged_at": "2026-06-19T23:59:00+00:00",
            }
            with open(tm_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

        from orchestrator_runtime.governance.continue_watchdog import decide
        result = decide()
        passed = _test("3 fail block", result, expect_allow=False)
        return passed
    finally:
        tm_path.write_text(backup, encoding="utf-8")

def test_3_synthetic_low_average():
    """Watchdog should BLOCK when last 5 values avg < 3.0."""
    print("[3] synthetic low average (5 values avg=2.0) — should BLOCK")
    tm_path = ROOT / "orchestrator_runtime" / "taste_model" / "mission_outcomes.jsonl"
    backup = tm_path.read_text(encoding="utf-8-sig") if tm_path.exists() else ""
    try:
        # Write 5 entries with value_immediate=2
        for i in range(5):
            entry = {
                "mission_id": f"SYNTH_LOW_{i}",
                "date": "2026-06-19",
                "claimed_status": "completed",
                "actual_status": "completed",
                "model_used": "continue_cli_qwen3.6",
                "runtime_validated": True,
                "value_immediate": 2,
                "patterns": ["cm_continue"],
                "notes": f"Synthetic low {i}",
                "logged_at": "2026-06-19T23:59:00+00:00",
            }
            with open(tm_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

        from orchestrator_runtime.governance.continue_watchdog import decide
        result = decide()
        passed = _test("low avg block", result, expect_allow=False)
        return passed
    finally:
        tm_path.write_text(backup, encoding="utf-8")

def test_4_kill_switch():
    """Watchdog should BLOCK when kill_switch env var is set."""
    print("[4] kill switch env — should BLOCK")
    os.environ["CM_KILL_SWITCH"] = "1"
    try:
        from orchestrator_runtime.governance.continue_watchdog import decide
        result = decide()
        return _test("kill switch block", result, expect_allow=False)
    finally:
        del os.environ["CM_KILL_SWITCH"]

def test_5_stale_outbox_archived():
    """Watchdog should NOT block when stale outbox is older than 5 min (AO8J_3)."""
    global SCORE
    print("[5] stale outbox older than 5 min — should ALLOW (archive + skip)")
    import tempfile
    from orchestrator_runtime.governance.continue_watchdog import _recent_outbox_errors

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a stale output_ready.json with consumed=false, mtime > 5 min ago
        ready = tmp_path / "output_ready.json"
        stale_data = {
            "run_id": "AO8J_STALE_TEST",
            "checksum": "abc123",
            "consumed": False,
            "timestamp": "2026-06-22T10:00:00+00:00",
        }
        ready.write_text(json.dumps(stale_data), encoding="utf-8")

        # Set mtime to 10 minutes ago
        old_time = time.time() - 600
        os.utime(ready, (old_time, old_time))

        # Also create last_output.md
        last = tmp_path / "last_output.md"
        last.write_text("stale content")

        errors = _recent_outbox_errors(tmp_path)

        # Should have NO errors — stale outbox was archived
        passed = len(errors) == 0
        marker = "PASS" if passed else "FAIL"
        SCORE += 1 if passed else 0
        print(f"  [{marker}] stale outbox archived: errors={errors}")

        # Verify archive was created
        archive_dir = tmp_path / "archive"
        if archive_dir.exists():
            archived_files = list(archive_dir.iterdir())
            print(f"        archived files: {[f.name for f in archived_files]}")
        else:
            print(f"        WARNING: archive dir not created")

        return passed

def run_all():
    global SCORE
    SCORE = 0
    print("=" * 60)
    print("Continue Watchdog — Test Suite")
    print("=" * 60)
    tests = [test_1_healthy_allow, test_2_synthetic_3_fail, test_3_synthetic_low_average, test_4_kill_switch, test_5_stale_outbox_archived]
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {e}")
    print()
    print(f"Results: {SCORE} passed, {MAX - SCORE} failed out of {MAX}")
    print()

if __name__ == "__main__":
    run_all()