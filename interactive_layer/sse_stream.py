"""SSE (Server-Sent Events) streaming for mission progress.

Phase 3: Real-time mission state streaming via SSE.

Design:
- Lightweight polling of persisted mission_events / mission current_state from SQLite
- No Redis, no external queue, no new infra
- SQLite remains the source of truth
- Single operator v1

Event types:
- mission_state: emitted on every state transition (including initial snapshot)
- mission_terminal: emitted when mission reaches COMPLETE/FAILED/TIMEOUT
- heartbeat: emitted every ~10s while mission is non-terminal

Stream lifecycle:
- Client opens GET /api/missions/{mission_id}/stream
- Server emits initial snapshot immediately
- Server polls SQLite every 2s for state changes
- Server emits terminal event and closes when mission completes
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import HTTPException

from .database import get_mission, get_mission_events
from .missions import get_mission_status

logger = logging.getLogger(__name__)

# Poll interval for checking state changes (seconds)
POLL_INTERVAL = 2.0

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 10.0

# Terminal states
TERMINAL_STATES = {"COMPLETE", "FAILED", "TIMEOUT"}


def _now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _format_sse(
    event_type: str,
    data: dict,
    retry: int = 3000,
) -> str:
    """Format an SSE event string."""
    lines = []
    if event_type:
        lines.append(f"event: {event_type}")
    lines.append(f"data: {json.dumps(data, default=str)}")
    lines.append(f"retry: {retry}")
    lines.append("")  # Empty line terminates SSE event
    lines.append("")  # Extra newline for safety
    return "\n".join(lines)


async def _poll_mission_state(
    mission_id: str,
    last_state: str,
) -> tuple[str | None, dict]:
    """Poll SQLite for mission state changes.

    Returns:
        (new_state, mission_dict) if state changed, or (None, mission_dict) if unchanged.
    """
    mission = get_mission(mission_id)
    if not mission:
        return None, {}

    current_state = mission.get("state", "UNKNOWN")
    if current_state != last_state:
        return current_state, mission

    return None, mission


async def _sse_stream_generator(
    mission_id: str,
) -> AsyncIterator[str]:
    """Generator that yields SSE events for a mission.

    This is the core SSE stream logic:
    1. Validate mission exists
    2. Emit initial snapshot
    3. Poll for state changes
    4. Emit heartbeat while waiting
    5. Emit terminal event when done
    6. Close stream
    """
    # Validate mission exists
    mission = get_mission(mission_id)
    if not mission:
        # Cannot raise HTTPException inside generator — yield error event instead
        error_data = {
            "mission_id": mission_id,
            "error": "Mission not found",
            "timestamp": _now_iso(),
        }
        yield _format_sse("error", error_data)
        return

    # Track last known state
    last_state = mission.get("state", "UNKNOWN")
    last_event_time = time.monotonic()

    # Emit initial snapshot
    initial_data = {
        "mission_id": mission_id,
        "state": last_state,
        "previous_state": None,
        "timestamp": _now_iso(),
        "progress": mission.get("progress", 0.0),
        "is_initial": True,
    }
    yield _format_sse("mission_state", initial_data)

    # If already terminal, emit terminal event and close
    if last_state in TERMINAL_STATES:
        terminal_data = {
            "mission_id": mission_id,
            "state": last_state,
            "success": last_state == "COMPLETE",
            "final_output_available": bool(mission.get("result")),
            "timestamp": _now_iso(),
        }
        yield _format_sse("mission_terminal", terminal_data)
        return

    # Main polling loop
    try:
        while True:
            await asyncio.sleep(POLL_INTERVAL)

            # Check for state change
            new_state, mission = await _poll_mission_state(mission_id, last_state)

            if new_state is not None:
                last_state = new_state
                last_event_time = time.monotonic()

                # Emit state transition event
                state_data = {
                    "mission_id": mission_id,
                    "state": new_state,
                    "previous_state": mission.get("state", "UNKNOWN"),
                    "timestamp": _now_iso(),
                    "progress": mission.get("progress", 0.0),
                }
                yield _format_sse("mission_state", state_data)

                # Check if terminal
                if new_state in TERMINAL_STATES:
                    terminal_data = {
                        "mission_id": mission_id,
                        "state": new_state,
                        "success": new_state == "COMPLETE",
                        "final_output_available": bool(mission.get("result")),
                        "timestamp": _now_iso(),
                    }
                    yield _format_sse("mission_terminal", terminal_data)
                    return

            # Emit heartbeat if needed
            elapsed = time.monotonic() - last_event_time
            if elapsed >= HEARTBEAT_INTERVAL:
                last_event_time = time.monotonic()
                heartbeat_data = {
                    "mission_id": mission_id,
                    "state": last_state,
                    "timestamp": _now_iso(),
                    "is_heartbeat": True,
                }
                yield _format_sse("heartbeat", heartbeat_data)

    except asyncio.CancelledError:
        # Client disconnected — clean exit
        logger.info(f"SSE stream cancelled for mission {mission_id}")
        return
    except Exception as e:
        logger.error(f"SSE stream error for mission {mission_id}: {e}")
        error_data = {
            "mission_id": mission_id,
            "error": str(e),
            "timestamp": _now_iso(),
        }
        yield _format_sse("error", error_data)
        return


async def sse_stream(mission_id: str) -> tuple[AsyncIterator[str], dict]:
    """Create an SSE stream for a mission.

    Returns:
        Tuple of (generator, headers) for FastAPI StreamingResponse.
    """
    generator = _sse_stream_generator(mission_id)
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable nginx buffering
        "Content-Type": "text/event-stream",
    }
    return generator, headers