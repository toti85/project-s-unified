#!/usr/bin/env python3
"""
AO5_T15 Traffic Generator — Synthetic consume() loop (EventBus feed)
=====================================================================
Generates synthetic consume() events once per hour for 24h observation.
Publishes EventBus events before/after each consume to feed OverseerAgent.

FIXED: RISK_010 checksum sequence + EventBus event publishing.

Usage:
    $env:OVERSEER_ADVISORY='true'; python orchestrator_runtime/sandbox/ao5_t15_traffic_loop.py
    python orchestrator_runtime/sandbox/ao5_t15_traffic_loop.py --once  # single iteration

Interrupt with Ctrl+C.
"""
import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [traffic_loop] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("traffic_loop")

OBS_PATH = Path(__file__).parent.parent / "governance" / "overseer_observation.jsonl"
RUN_HOURS = 24
INTERVAL_SECONDS = 3600


def _compute_checksum(file_path: Path) -> str:
    """SHA-256 of file contents, first 16 hex chars."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _publish_event(event_type: str, data: dict):
    """Publish event to EventBus. Fail-safe: never crashes the loop."""
    try:
        import asyncio
        from core.infrastructure.event_bus import EventBus
        _bus = EventBus()
        asyncio.run(_bus.publish(event_type, data))
        logger.debug(f"Published {event_type}: {json.dumps(data)[:100]}")
    except Exception as e:
        logger.debug(f"EventBus publish failed (non-fatal): {e}")


def _create_sandbox_handoff(run_id: str, tmpdir: Path):
    """
    Create minimal sandbox handoff for synthetic consume().
    RISK_010: write last_output.md FINAL → compute SHA-256 → write output_ready.json LAST
    """
    outbox = tmpdir / "cline_outbox"
    outbox.mkdir(exist_ok=True)

    # Step 1: Write last_output.md FINAL
    content = (
        f"# AO5_T15 Synthetic Output\n"
        f"Run ID: {run_id}\n"
        f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
        f"Synthetic payload for telemetry.\n"
    )
    output_path = outbox / "last_output.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Step 2: Compute SHA-256
    cs = _compute_checksum(output_path)

    # Step 3: Write output_ready.json LAST
    ready = {
        "run_id": run_id,
        "iteration": 1,
        "consumed": False,
        "checksum": cs,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(outbox / "output_ready.json", "w", encoding="utf-8") as f:
        json.dump(ready, f)

    logger.info(f"Handoff: {run_id}, checksum={cs}")
    return tmpdir


def _run_synthetic_consume(hour: int):
    """Run single synthetic consume() with EventBus events."""
    run_id = f"AO5_T15_SYNTH_{hour:02d}"
    tmpdir = Path(tempfile.mkdtemp(prefix=f"synth_{run_id}_"))

    try:
        _create_sandbox_handoff(run_id, tmpdir)

        # Publish workflow.started BEFORE consume
        _publish_event("workflow.started", {
            "id": run_id,
            "type": "synthetic",
            "ts": datetime.now(timezone.utc).isoformat()
        })

        from orchestrator_runtime.governance.bridge_runner import (
            consume_executor_output,
            set_test_paths,
            reset_test_paths,
        )

        cycle_log = tmpdir / "cycle_log.jsonl"
        set_test_paths(tmpdir / "cline_outbox", cycle_log)

        start = time.perf_counter()
        result = consume_executor_output(run_id, 1)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        reset_test_paths()

        verdict = result.get("status", "UNKNOWN")
        logger.info(f"{run_id}: status={verdict}, latency={elapsed_ms}ms")

        # Publish workflow.completed AFTER consume
        _publish_event("workflow.completed", {
            "id": run_id,
            "duration_ms": elapsed_ms,
            "verdict": verdict,
            "ts": datetime.now(timezone.utc).isoformat()
        })

        # Publish performance.metric
        _publish_event("performance.metric", {
            "metric": "consume_latency",
            "value_ms": elapsed_ms,
            "verdict": verdict
        })

        return verdict == "ACCEPTED"

    except Exception as e:
        logger.error(f"{run_id}: EXCEPTION - {e}")
        _publish_event("execution.failed", {
            "id": run_id,
            "error": str(e)[:200]
        })
        return False

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="AO5_T15 Traffic Generator")
    parser.add_argument("--once", action="store_true", help="Run 1 iteration then exit")
    args = parser.parse_args()

    max_iterations = 1 if args.once else RUN_HOURS

    logger.info(f"Starting AO5_T15 traffic generator ({max_iterations} iterations)")
    logger.info(f"OVERSEER_ADVISORY: {os.environ.get('OVERSEER_ADVISORY', 'NOT SET')}")
    logger.info(f"Observation log: {OBS_PATH}")
    logger.info("Press Ctrl+C to stop")

    hour = 0
    try:
        while hour < max_iterations:
            current_hour = int(datetime.now(timezone.utc).hour)
            logger.info(f"[{hour}/{max_iterations}] Synthetic consume at hour {current_hour}Z...")

            success = _run_synthetic_consume(current_hour)
            logger.info(f"[{hour}/{max_iterations}] {'OK' if success else 'FAIL'}")

            if OBS_PATH.exists():
                with open(OBS_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                logger.info(f"Observation log: {len(lines)} entries")

            hour += 1
            if hour < max_iterations:
                logger.info(f"Sleeping {INTERVAL_SECONDS}s...")
                time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("STOPPED_BY_USER")
        sys.exit(0)


if __name__ == "__main__":
    main()