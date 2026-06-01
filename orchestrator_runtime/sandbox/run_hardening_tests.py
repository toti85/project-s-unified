"""
MS-AO3 Hardening T3-T7 — Negative/edge-case path tests.
Creates intentionally bad fixtures, calls bridge_runner functions directly.
RISK_008: No successful end-to-end flow simulation. Rejection/error paths only.
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

# Add project root to path so orchestrator_runtime is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Import directly (no subprocess needed)
from orchestrator_runtime.governance.bridge_runner import (
    consume_executor_output,
    get_verdict_for_content,
    set_test_paths,
    reset_test_paths,
    STATUS_ACCEPTED,
)

results = {}


def compute_checksum(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_consume(tmp_dir: Path, run_id: str, iteration: int = 1, verdict: bool = False) -> dict:
    """Set test paths, consume, optionally get verdict, reset paths."""
    set_test_paths(tmp_dir / "cline_outbox", tmp_dir / "cycle_log.jsonl")
    try:
        result = consume_executor_output(run_id, iteration)
        if verdict and result["status"] == STATUS_ACCEPTED:
            result["verdict"] = get_verdict_for_content(result["content"], run_id)
        return result
    finally:
        reset_test_paths()


def t3_checksum_mismatch():
    """T3: Valid files but wrong checksum → REJECTED_CHECKSUM"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outbox = Path(tmp_dir) / "cline_outbox"
        outbox.mkdir(parents=True)

        (outbox / "last_output.md").write_text("# T3 Test\nResult: 42\n", encoding="utf-8")
        ready = {
            "run_id": "AO3_T3", "iteration": 1, "status": "ready",
            "checksum": "0000000000000000", "consumed": False,
        }
        (outbox / "output_ready.json").write_text(json.dumps(ready, indent=4), encoding="utf-8")

        result = run_consume(Path(tmp_dir), "AO3_T3")
        results["T3"] = result
        return result["status"] == "REJECTED_CHECKSUM"


def t4_missing_output():
    """T4: Empty outbox → WAITING_FOR_EXECUTOR"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        (Path(tmp_dir) / "cline_outbox").mkdir(parents=True)
        result = run_consume(Path(tmp_dir), "AO3_T4")
        results["T4"] = result
        return result["status"] == "WAITING_FOR_EXECUTOR"


def t5_wrong_run_id():
    """T5: run_id mismatch → REJECTED_RUN_ID"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outbox = Path(tmp_dir) / "cline_outbox"
        outbox.mkdir(parents=True)

        content = "# T5 Test\n"
        (outbox / "last_output.md").write_text(content, encoding="utf-8")
        cs = compute_checksum(outbox / "last_output.md")
        ready = {
            "run_id": "AO3_T5_WRONG", "iteration": 1, "status": "ready",
            "checksum": cs, "consumed": False,
        }
        (outbox / "output_ready.json").write_text(json.dumps(ready, indent=4), encoding="utf-8")

        result = run_consume(Path(tmp_dir), "AO3_T5_RIGHT")
        results["T5"] = result
        return result["status"] == "REJECTED_RUN_ID"


def t6_already_consumed():
    """T6: consumed=true → REJECTED_CONSUMED"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outbox = Path(tmp_dir) / "cline_outbox"
        outbox.mkdir(parents=True)

        content = "# T6 Test\n"
        (outbox / "last_output.md").write_text(content, encoding="utf-8")
        cs = compute_checksum(outbox / "last_output.md")
        ready = {
            "run_id": "AO3_T6", "iteration": 1, "status": "ready",
            "checksum": cs, "consumed": True,
        }
        (outbox / "output_ready.json").write_text(json.dumps(ready, indent=4), encoding="utf-8")

        result = run_consume(Path(tmp_dir), "AO3_T6")
        results["T6"] = result
        return result["status"] == "REJECTED_CONSUMED"


def t7_scl_integration():
    """T7: Valid output + verdict → SCL invoked, no import error"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outbox = Path(tmp_dir) / "cline_outbox"
        outbox.mkdir(parents=True)

        content = "# AO3_T7 Execution Report\n- run_id: AO3_T7\n- result: PASS\n"
        (outbox / "last_output.md").write_text(content, encoding="utf-8")
        cs = compute_checksum(outbox / "last_output.md")
        ready = {
            "run_id": "AO3_T7", "iteration": 1, "status": "ready",
            "checksum": cs, "consumed": False,
        }
        (outbox / "output_ready.json").write_text(json.dumps(ready, indent=4), encoding="utf-8")

        result = run_consume(Path(tmp_dir), "AO3_T7", verdict=True)
        results["T7"] = result
        has_no_import_error = (
            result.get("verdict") is not None and
            "self_correcting_loop not available" not in str(result.get("verdict", ""))
        )
        return has_no_import_error


if __name__ == "__main__":
    tests = [
        ("T3 — Checksum mismatch", t3_checksum_mismatch),
        ("T4 — Missing output", t4_missing_output),
        ("T5 — Wrong run_id", t5_wrong_run_id),
        ("T6 — Already consumed", t6_already_consumed),
        ("T7 — SCL integration", t7_scl_integration),
    ]

    passed = {}
    key_map = {
        "T3 — Checksum mismatch": "T3",
        "T4 — Missing output": "T4",
        "T5 — Wrong run_id": "T5",
        "T6 — Already consumed": "T6",
        "T7 — SCL integration": "T7",
    }
    for name, fn in tests:
        print("=" * 60)
        print(name)
        print("=" * 60)
        p = fn()
        passed[name] = p
        key = key_map[name]
        print(f"PASS: {p}")
        print(f"RAW OUTPUT:\n{json.dumps(results.get(key, {}), indent=4, ensure_ascii=False, default=str)}\n")

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"T3 REJECTED_CHECKSUM: {'YES' if passed.get('T3 — Checksum mismatch') else 'NO'}")
    print(f"T4 WAITING_FOR_EXECUTOR: {'YES' if passed.get('T4 — Missing output') else 'NO'}")
    print(f"T5 run_id mismatch rejected: {'YES' if passed.get('T5 — Wrong run_id') else 'NO'}")
    print(f"T6 REJECTED_CONSUMED: {'YES' if passed.get('T6 — Already consumed') else 'NO'}")
    print(f"T7 SCL invoked (no import error): {'YES' if passed.get('T7 — SCL integration') else 'NO'}")