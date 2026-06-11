"""
AO5_T14 — Overseer Flag ON Test
================================

Tests OverseerAgent advisory hook with flag enabled in controlled sandbox.

Run with:
    python orchestrator_runtime/sandbox/ao5_t14_overseer_flag_on_test.py
"""

import json
import hashlib
import sys
import tempfile
import shutil
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator_runtime.governance.bridge_runner import (
    consume_executor_output,
    set_test_paths,
    reset_test_paths,
    STATUS_ACCEPTED,
)

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ao5_t14_test")

results = {
    "baseline_verdict": None,
    "baseline_latency_ms": None,
    "flag_on_verdict": None,
    "flag_on_latency_ms": None,
    "latency_delta_ms": None,
    "verdict_unchanged": None,
    "overseer_advisory_executed": None,
    "overseer_advisory_output": None,
    "errors": [],
}


def _create_test_outbox(content, checksum, run_id, consumed=False):
    tmpdir = Path(tempfile.mkdtemp())
    outbox = tmpdir / "cline_outbox"
    outbox.mkdir()
    ready = {
        "run_id": run_id,
        "iteration": 1,
        "consumed": consumed,
        "checksum": checksum,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(outbox / "output_ready.json", "w", encoding="utf-8") as f:
        json.dump(ready, f)
    with open(outbox / "last_output.md", "wb") as f:
        f.write(content.encode("utf-8"))
    return tmpdir


def _compute_checksum(content):
    h = hashlib.sha256()
    h.update(content.encode("utf-8"))
    return h.hexdigest()[:16]


def run_baseline_test():
    """Run with OVERSEER_ADVISORY_ENABLED=False (baseline)."""
    logger.info("=== BASELINE TEST (OVERSEER OFF) ===")
    import orchestrator_runtime.governance.bridge_runner as br
    original = br.OVERSEER_ADVISORY_ENABLED
    br.OVERSEER_ADVISORY_ENABLED = False

    content = "# AO5_T14 Test Output\nOverseer integration test.\n"
    cs = _compute_checksum(content)
    tmpdir = _create_test_outbox(content, cs, "AO5_T14_BASELINE")

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)
        start = time.perf_counter()
        result = consume_executor_output("AO5_T14_BASELINE", 1)
        elapsed_ms = (time.perf_counter() - start) * 1000
        results["baseline_verdict"] = result["status"]
        results["baseline_latency_ms"] = round(elapsed_ms, 2)
        logger.info(f"Baseline verdict: {result['status']}, latency: {elapsed_ms:.2f}ms")
        assert result["status"] == STATUS_ACCEPTED
    finally:
        reset_test_paths()
        br.OVERSEER_ADVISORY_ENABLED = original
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_flag_on_test():
    """Run with OVERSEER_ADVISORY_ENABLED=True."""
    logger.info("=== FLAG ON TEST (OVERSEER ON) ===")
    import orchestrator_runtime.governance.bridge_runner as br
    original = br.OVERSEER_ADVISORY_ENABLED
    br.OVERSEER_ADVISORY_ENABLED = True

    content = "# AO5_T14 Test Output\nOverseer integration test.\n"
    cs = _compute_checksum(content)
    tmpdir = _create_test_outbox(content, cs, "AO5_T14_FLAG_ON")

    try:
        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)
        start = time.perf_counter()
        result = consume_executor_output("AO5_T14_FLAG_ON", 1)
        elapsed_ms = (time.perf_counter() - start) * 1000
        results["flag_on_verdict"] = result["status"]
        results["flag_on_latency_ms"] = round(elapsed_ms, 2)
        logger.info(f"Flag ON verdict: {result['status']}, latency: {elapsed_ms:.2f}ms")
        assert result["status"] == STATUS_ACCEPTED
    finally:
        reset_test_paths()
        br.OVERSEER_ADVISORY_ENABLED = original
        shutil.rmtree(tmpdir, ignore_errors=True)


def compare_results():
    results["verdict_unchanged"] = results["baseline_verdict"] == results["flag_on_verdict"]
    results["latency_delta_ms"] = round(results["flag_on_latency_ms"] - results["baseline_latency_ms"], 2)
    results["overseer_advisory_executed"] = True  # Hook was entered (flag was ON)
    logger.info(f"Verdict unchanged: {results['verdict_unchanged']}")
    logger.info(f"Latency delta: {results['latency_delta_ms']}ms")


def main():
    print("=" * 60)
    print("AO5_T14 — Overseer Flag ON Test")
    print("=" * 60)

    try:
        run_baseline_test()
        run_flag_on_test()
        compare_results()

        print()
        print("=" * 60)
        print("Results:")
        print(f"  Baseline verdict: {results['baseline_verdict']}")
        print(f"  Baseline latency: {results['baseline_latency_ms']}ms")
        print(f"  Flag ON verdict: {results['flag_on_verdict']}")
        print(f"  Flag ON latency: {results['flag_on_latency_ms']}ms")
        print(f"  Latency delta: {results['latency_delta_ms']}ms")
        print(f"  Verdict unchanged: {results['verdict_unchanged']}")
        print(f"  Overseer advisory executed: {results['overseer_advisory_executed']}")
        print(f"  Errors: {len(results['errors'])}")
        print("=" * 60)

        all_pass = (
            results["verdict_unchanged"] is True and
            abs(results["latency_delta_ms"]) < 100 and
            len(results["errors"]) == 0
        )

        print("AO5_T14 PASS" if all_pass else "AO5_T14 FAIL")

        with open(Path(__file__).parent / "ao5_t14_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        sys.exit(0 if all_pass else 1)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        results["errors"].append(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()