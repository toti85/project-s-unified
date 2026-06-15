"""
t47_sai_controlled_execution.py

T47 execution script:
  1. Gate: sai_pre_execution_gate("GOAL_007")
  2. If ALLOW: execute SuperIntelligentAI with constrained read-only prompt
  3. Write output to outbox via write_sai_output_to_outbox
  4. Print structured evidence for capture

CONSTRAINTS:
  - Read-only prompt only.
  - No filesystem mutations in prompt.
  - No network-wide scans.
  - No code generation affecting production.
  - Timeout: 120 seconds hard limit.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

GOAL_ID = "GOAL_007"
MISSION_ID = "AO5_T47_SAI_CONTROLLED_EXECUTION"
SAI_TIMEOUT = 120  # seconds hard limit

PROMPT = """AO5_T47 — Controlled SAI Execution: Generate MS-AO1 Progress Report

Working directory: C:\\ProjectS-Unified

EXECUTION MODE: READ-ONLY REPORT GENERATION

TASK:
You are executing GOAL_007 — "Generate MS-AO1 Progress Report".

Read self_state.json and list of recent reports to produce a concise report documenting:
1. The current state of Project-S after AO1.1 milestones
2. What has been completed in the AO5 mission series (T31–T46)
3. Key infrastructure built (governance gateway, Continuous Mind v0.1, Taste Model, SAI adapter)
4. The governance chain now in place

CONSTRAINTS (HARD):
- Do NOT modify any files.
- Do NOT execute any code.
- Do NOT make network requests.
- Do NOT scan the entire filesystem.
- Output is a markdown report only.
- Target length: 300-600 words.

OUTPUT:
A markdown report summarizing AO1/AO5 progress. Nothing else.
"""


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run_sai_mission() -> dict:
    """Execute SAI with hard timeout."""
    from orchestrator_runtime.governance.sai_gateway_adapter import (
        sai_pre_execution_gate,
        write_sai_output_to_outbox,
        build_sai_handoff_content,
    )

    evidence: dict = {
        "mission_id": MISSION_ID,
        "goal_id": GOAL_ID,
        "started_at": _ts(),
    }

    # ── Phase 2: Governance Gate ─────────────────────────────────────
    print(f"[T47] Phase 2: governance gate for {GOAL_ID}...")
    gate = sai_pre_execution_gate(MISSION_ID, goal_id=GOAL_ID)
    evidence["gate"] = gate
    print(f"[T47] Gate decision: {gate['gateway_action']} (risk={gate['risk_level']})")
    print(json.dumps(gate, indent=2, ensure_ascii=False))

    if not gate["allowed"]:
        print(f"[T47] STOPPED by gate: {gate['reason']}")
        evidence["stopped"] = True
        evidence["stopped_reason"] = gate["reason"]
        return evidence

    # ── Phase 3: SAI Execution ────────────────────────────────────────
    print(f"\n[T47] Phase 3: executing SAI (timeout={SAI_TIMEOUT}s)...")
    t_start = time.monotonic()

    sai_result: dict = {}
    try:
        from src.core.super_intelligent_ai import SuperIntelligentAI
        ai = SuperIntelligentAI(use_meta_controller=False)

        try:
            sai_result = await asyncio.wait_for(
                ai.execute_intelligent_task(PROMPT),
                timeout=SAI_TIMEOUT,
            )
        except asyncio.TimeoutError:
            sai_result = {
                "success": False,
                "output": "",
                "error": f"SAI execution timed out after {SAI_TIMEOUT}s",
            }
    except Exception as exc:
        sai_result = {
            "success": False,
            "output": "",
            "error": f"SAI execution error: {exc}",
        }

    t_elapsed = time.monotonic() - t_start
    evidence["sai_latency_s"] = round(t_elapsed, 2)
    evidence["sai_result"] = {
        "success": sai_result.get("success"),
        "output_len": len(sai_result.get("output", "")),
        "error": sai_result.get("error"),
    }
    evidence["completed_at"] = _ts()

    print(f"[T47] SAI completed in {t_elapsed:.1f}s — success={sai_result.get('success')}")
    output = sai_result.get("output", "")
    if output:
        print(f"[T47] Output preview (first 500 chars):\n{output[:500]}")
    if sai_result.get("error"):
        print(f"[T47] Error: {sai_result.get('error')}")

    # ── Phase 4: Write to outbox ──────────────────────────────────────
    print(f"\n[T47] Phase 4: writing to outbox...")
    content = build_sai_handoff_content(MISSION_ID, sai_result)
    write_result = write_sai_output_to_outbox(MISSION_ID, content, iteration=1)
    evidence["outbox_write"] = write_result
    print(f"[T47] Outbox write: success={write_result['success']} checksum={write_result.get('checksum')}")

    return evidence


def main() -> int:
    print("=" * 60)
    print(f"  T47 SAI CONTROLLED EXECUTION")
    print(f"  goal_id   : {GOAL_ID}")
    print(f"  mission_id: {MISSION_ID}")
    print(f"  timeout   : {SAI_TIMEOUT}s")
    print("=" * 60)

    evidence = asyncio.run(run_sai_mission())

    print("\n" + "=" * 60)
    print("  EVIDENCE SUMMARY")
    print("=" * 60)
    print(json.dumps(evidence, indent=2, ensure_ascii=False, default=str))

    # Write evidence to sandbox
    sandbox = _ROOT / "orchestrator_runtime" / "sandbox"
    sandbox.mkdir(exist_ok=True)
    ev_path = sandbox / "t47_execution_evidence.json"
    ev_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nEvidence saved: {ev_path}")

    return 0 if evidence.get("outbox_write", {}).get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
