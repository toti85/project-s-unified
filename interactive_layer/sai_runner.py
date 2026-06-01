#!/usr/bin/env python3
"""SAI Runner — Phase 2 SAI Integration.

Orchestrates real Project-S SAI mission execution as a background task.
Connects the Phase 1 mission state machine to the SuperIntelligentAI pipeline.

Truthful state mapping:
  QUEUED → PLANNING (SAI init) → EXECUTING (tool execution) → COMPLETE/FAILED/TIMEOUT

SYNTHESIZING and WRITING are NOT mapped in Phase 2 because the SAI pipeline
does not expose these as distinct, hookable phases. They are reserved for Phase 5+.

REPLAN support:
  If the MetaController replans, we map it back to PLANNING (max 3 replans).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Ensure Project-S root is on sys.path for SAI imports
_REPO_ROOT = str(Path(__file__).parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from interactive_layer.database import (
    append_mission_events as _db_append_events,
    create_mission as _db_create_mission,
    get_mission as _db_get_mission,
    log_mission_event as _db_log_event,
    update_mission_error as _db_update_error,
    update_mission_progress as _db_update_progress,
    update_mission_result as _db_update_result,
    update_mission_state as _db_update_state,
)
from interactive_layer.missions import transition_mission_state
from interactive_layer.models import (
    MissionCreate,
    MissionStateUpdate,
    MissionResponse,
    TERMINAL_STATES,
    validate_transition,
)

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────
# DEFAULT_TIMEOUT was patched to 30 by restart_and_validate.ps1 for GAP_030 DEV validation.
# Restoring to 600 (10 minutes) — this is the correct production value.
DEFAULT_TIMEOUT = 600  # 10 minutes wall-clock (GLOBAL deadline)
MAX_REPLAN_COUNT = 3
# ─────────────────────────────────────────────────────────────────


async def _run_sai_mission(
    mission_id: str,
    session_id: str,
    prompt: str,
    user_id: str = "toti",
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """
    Execute a single SAI mission in the background.

    State flow:
      QUEUED → PLANNING → EXECUTING → COMPLETE (success)
                                    → FAILED (error)
                                    → TIMEOUT (wall-clock exceeded)
      (replan loop: EXECUTING → REPLAN → PLANNING, max 3x)

    GAP_030 FIX:
      - Global deadline established at start using monotonic clock.
      - All replan retries use remaining time (deadline - now).
      - When deadline expires, mission transitions to TIMEOUT immediately.
    """
    replan_count = 0

    # GAP_030: Establish global deadline using monotonic clock
    monotonic_start = time.monotonic()
    deadline = monotonic_start + timeout

    logger.info(
        "SAI mission %s: global deadline established (timeout=%ds)",
        mission_id,
        timeout,
    )

    try:
        # ── Step 1: PLANNING ──────────────────────────────────────
        transition_mission_state(mission_id, MissionStateUpdate(state="PLANNING"))
        _db_log_event(mission_id, "sai_planning", {"prompt": prompt[:200]})

        # Import SAI lazily to avoid startup cost
        from src.core.super_intelligent_ai import SuperIntelligentAI

        ai = SuperIntelligentAI(use_meta_controller=True)

        # ── Step 2: EXECUTING ─────────────────────────────────────
        transition_mission_state(mission_id, MissionStateUpdate(state="EXECUTING"))
        _db_log_event(mission_id, "sai_executing", {
            "prompt": prompt[:200],
            "timeout": timeout,
        })
        _db_update_progress(mission_id, 0.3)

        # Execute with global deadline (GAP_030 fix)
        result = await _execute_with_global_deadline(
            mission_id=mission_id,
            ai=ai,
            prompt=prompt,
            deadline=deadline,
            replan_count=replan_count,
            is_first=True,
        )

        if result is None:
            # Deadline exceeded — mission already terminalized
            return

        # ── Step 3: Process result ────────────────────────────────
        _db_update_progress(mission_id, 0.8)

        if not isinstance(result, dict):
            result = {"output": str(result), "success": True}

        success = result.get("success", False)
        output = result.get("output", "")

        # Check for replan recommendation
        evaluation = result.get("evaluation_result", {})
        if isinstance(evaluation, dict):
            recs = evaluation.get("recommendations", {})
            action = recs.get("action", "") if isinstance(recs, dict) else ""

            if action == "replan" and replan_count < MAX_REPLAN_COUNT:
                replan_count += 1
                _db_log_event(mission_id, "mission_replan", {
                    "replan_count": replan_count,
                    "max_replan": MAX_REPLAN_COUNT,
                    "reason": "Evaluator recommended replan",
                })
                transition_mission_state(mission_id, MissionStateUpdate(state="REPLAN"))
                # Loop back to PLANNING
                transition_mission_state(mission_id, MissionStateUpdate(state="PLANNING"))
                _db_update_progress(mission_id, 0.3)

                # GAP_030: Use remaining time from global deadline
                result = await _execute_with_global_deadline(
                    mission_id=mission_id,
                    ai=ai,
                    prompt=prompt,
                    deadline=deadline,
                    replan_count=replan_count,
                    is_first=False,
                )

                if result is None:
                    # Deadline exceeded during replan
                    return

                success = result.get("success", False)
                output = result.get("output", "")
                if not isinstance(result, dict):
                    result = {"output": str(result), "success": True}

                # Check replan again after retry
                evaluation = result.get("evaluation_result", {})
                if isinstance(evaluation, dict):
                    recs = evaluation.get("recommendations", {})
                    action = recs.get("action", "") if isinstance(recs, dict) else ""
                    if action == "replan" and replan_count >= MAX_REPLAN_COUNT:
                        _db_update_error(mission_id, "max_replan_exceeded")
                        _db_log_event(mission_id, "mission_failed", {
                            "reason": "max_replan_exceeded",
                            "replan_count": replan_count,
                        })
                        transition_mission_state(mission_id, MissionStateUpdate(state="FAILED"))
                        return

        # ── Step 4: COMPLETE or FAILED ────────────────────────────
        _db_update_progress(mission_id, 1.0)

        if success:
            _db_update_result(mission_id, output)
            _db_log_event(mission_id, "mission_complete", {
                "output_length": len(output),
                "replan_count": replan_count,
            })
            transition_mission_state(mission_id, MissionStateUpdate(state="COMPLETE"))
        else:
            error_msg = result.get("error", result.get("output", "Unknown failure"))
            _db_update_error(mission_id, error_msg)
            _db_log_event(mission_id, "mission_failed", {
                "error": error_msg,
                "replan_count": replan_count,
            })
            transition_mission_state(mission_id, MissionStateUpdate(state="FAILED"))

    except Exception as e:
        # Catch-all: don't let exceptions crash the API server
        logger.exception(f"SAI mission {mission_id} crashed: {e}")
        try:
            _db_update_error(mission_id, f"Mission crashed: {e}")
            _db_log_event(mission_id, "mission_failed", {"error": str(e)})
            current = _db_get_mission(mission_id)
            if current and current["state"] not in TERMINAL_STATES:
                transition_mission_state(mission_id, MissionStateUpdate(state="FAILED"))
        except Exception as inner_e:
            logger.error(f"Failed to record error for mission {mission_id}: {inner_e}")


async def _execute_with_global_deadline(
    mission_id: str,
    ai: Any,
    prompt: str,
    deadline: float,
    replan_count: int,
    is_first: bool,
) -> Optional[dict]:
    """
    Execute SAI task with global deadline enforcement.

    GAP_030 FIX:
      - Calculates remaining time from global deadline.
      - If remaining <= 0, transitions mission to TIMEOUT immediately.
      - Uses asyncio.wait_for with remaining time (not full DEFAULT_TIMEOUT).
      - Wraps execution for cancellation reliability.

    Returns:
      dict on success, None if deadline exceeded (mission already terminalized).
    """
    now = time.monotonic()
    remaining = deadline - now

    if remaining <= 0:
        logger.warning(
            "SAI mission %s: global deadline EXCEEDED (remaining=%.1fs, replan=%d/%d)",
            mission_id,
            remaining,
            replan_count,
            MAX_REPLAN_COUNT,
        )
        _db_update_error(
            mission_id,
            f"SAI mission timed out after global deadline exceeded "
            f"(replan={replan_count}/{MAX_REPLAN_COUNT})",
        )
        _db_log_event(mission_id, "mission_timeout", {
            "timeout_seconds": DEFAULT_TIMEOUT,
            "replan_count": replan_count,
            "remaining_at_timeout": remaining,
            "is_first": is_first,
        })
        transition_mission_state(mission_id, MissionStateUpdate(state="TIMEOUT"))
        return None

    logger.info(
        "SAI mission %s: executing with %.1fs remaining (replan=%d/%d, first=%s)",
        mission_id,
        remaining,
        replan_count,
        MAX_REPLAN_COUNT,
        is_first,
    )

    # GAP_030: Wrap execution to ensure asyncio cancellation reliability
    async def _run_task():
        return await ai.execute_intelligent_task(task=prompt)

    try:
        result = await asyncio.wait_for(
            _run_task(),
            timeout=remaining,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(
            "SAI mission %s: execution timed out (remaining=%.1fs, replan=%d/%d)",
            mission_id,
            remaining,
            replan_count,
            MAX_REPLAN_COUNT,
        )
        _db_update_error(
            mission_id,
            f"SAI mission timed out after {remaining:.0f}s remaining "
            f"(replan={replan_count}/{MAX_REPLAN_COUNT})",
        )
        _db_log_event(mission_id, "mission_timeout", {
            "timeout_seconds": DEFAULT_TIMEOUT,
            "replan_count": replan_count,
            "remaining_at_timeout": remaining,
            "is_first": is_first,
        })
        transition_mission_state(mission_id, MissionStateUpdate(state="TIMEOUT"))
        return None
