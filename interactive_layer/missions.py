"""Mission CRUD + state transitions for Project-S Interactive Layer.

Every state transition:
- Validates allowed transitions
- Persists to SQLite immediately
- Returns updated mission
"""

from __future__ import annotations

from typing import Optional

from .database import (
    create_mission as _db_create_mission,
    get_mission as _db_get_mission,
    list_missions as _db_list_missions,
    update_mission_state as _db_update_mission_state,
    update_mission_progress as _db_update_mission_progress,
    update_mission_result as _db_update_mission_result,
    update_mission_error as _db_update_mission_error,
    update_mission_plan as _db_update_mission_plan,
    append_mission_events as _db_append_mission_events,
    log_mission_event as _db_log_mission_event,
    get_mission_events as _db_get_mission_events,
)
from .models import (
    ALLOWED_TRANSITIONS,
    MissionCreate,
    MissionResponse,
    MissionStatusResponse,
    MissionStateUpdate,
    TERMINAL_STATES,
    validate_transition,
)


def create_mission(
    request: MissionCreate,
    route_type: str = "FULL_AGENTIC_META_CONTROLLER",
    route_confidence: float = 0.3,
    route_rationale: str = "",
    route_matched_rules: Optional[list[str]] = None,
    route_llm_used: bool = False,
    route_llm_model: Optional[str] = None,
) -> MissionResponse:
    """Create a mission in QUEUED state, persist immediately.
    
    GAP_031: Accepts optional route metadata for prompt routing persistence.
    """
    data = _db_create_mission(
        mission_id=None,
        user_id=request.user_id,
        session_id=request.session_id,
        task=request.task,
        timeout_seconds=request.timeout_seconds,
        route_type=route_type,
        route_confidence=route_confidence,
        route_rationale=route_rationale,
        route_matched_rules=route_matched_rules,
        route_llm_used=route_llm_used,
        route_llm_model=route_llm_model,
    )
    # Log initial event
    _db_log_mission_event(data["mission_id"], "mission_created", {
        "session_id": request.session_id,
        "task": request.task,
        "route_type": route_type,
    })
    return MissionResponse(**data)


def get_mission(mission_id: str) -> Optional[MissionResponse]:
    """Get a mission by ID."""
    data = _db_get_mission(mission_id)
    if not data:
        return None
    return MissionResponse(**data)


def get_mission_status(mission_id: str) -> Optional[MissionStatusResponse]:
    """Get mission status (lightweight response)."""
    data = _db_get_mission(mission_id)
    if not data:
        return None
    return MissionStatusResponse(
        mission_id=data["mission_id"],
        state=data["state"],
        progress=data["progress"],
        state_history=data["state_history"],
        error=data["error"],
    )


def list_missions(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    state: Optional[str] = None,
) -> list[MissionResponse]:
    """List missions with optional filters."""
    results = _db_list_missions(user_id=user_id, session_id=session_id, state=state)
    return [MissionResponse(**r) for r in results]


def transition_mission_state(
    mission_id: str,
    request: MissionStateUpdate,
) -> MissionResponse:
    """
    Transition mission to new state.
    - Validates transition (only allowed transitions)
    - Updates state field
    - Appends to state_history with timestamp and duration_ms
    - Persists to SQLite immediately
    - Logs event
    - Returns updated mission
    """
    # Validate transition
    current = _db_get_mission(mission_id)
    if not current:
        raise ValueError(f"Mission {mission_id} not found")

    current_state = current["state"]

    # Check terminal states first — provide clear error message
    if current_state in TERMINAL_STATES:
        raise ValueError(
            f"Cannot transition from terminal state '{current_state}'. "
            f"Terminal states (COMPLETE, FAILED, TIMEOUT) cannot be changed. "
            f"Create a new mission instead."
        )

    if not validate_transition(current_state, request.state):
        allowed = ", ".join(ALLOWED_TRANSITIONS.get(current_state, []))
        raise ValueError(
            f"Invalid transition: {current_state} -> {request.state}. "
            f"Allowed from {current_state}: {allowed}"
        )
    
    # Transition
    data = _db_update_mission_state(
        mission_id=mission_id,
        new_state=request.state,
        metadata=request.metadata,
    )
    
    # Log event
    _db_log_mission_event(mission_id, "state_transition", {
        "from_state": current["state"],
        "to_state": request.state,
        "metadata": request.metadata,
    })
    
    return MissionResponse(**data)


def update_mission_progress(mission_id: str, progress: float) -> None:
    """Update mission progress."""
    _db_update_mission_progress(mission_id, progress)


def complete_mission(mission_id: str, result: str, output_path: Optional[str] = None) -> MissionResponse:
    """Mark mission as complete. Sets state=COMPLETE and persists result."""
    # Transition state first so polling loops see COMPLETE atomically
    _db_update_mission_state(mission_id, "COMPLETE")
    _db_update_mission_result(mission_id, result, output_path)
    _db_log_mission_event(mission_id, "mission_complete", {
        "output_path": output_path,
    })
    return get_mission(mission_id)


def fail_mission(mission_id: str, error: str) -> MissionResponse:
    """Mark mission as failed."""
    _db_update_mission_error(mission_id, error)
    _db_log_mission_event(mission_id, "mission_failed", {
        "error": error,
    })
    return get_mission(mission_id)


def set_mission_plan(mission_id: str, plan: dict) -> None:
    """Set mission plan."""
    _db_update_mission_plan(mission_id, plan)
    _db_log_mission_event(mission_id, "plan_set", {
        "plan": plan,
    })


def append_events(mission_id: str, events: list[dict]) -> None:
    """Append events to mission."""
    _db_append_mission_events(mission_id, events)
    _db_log_mission_event(mission_id, "events_appended", {
        "event_count": len(events),
    })


def get_mission_events(mission_id: str, limit: int = 100) -> list[dict]:
    """Get mission events."""
    return _db_get_mission_events(mission_id, limit)