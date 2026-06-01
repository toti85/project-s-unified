"""FastAPI application entry point for Project-S Interactive Layer.

Endpoints:
- GET /health — Health check
- GET / — Welcome page
- POST /api/sessions — Create session
- GET /api/sessions — List sessions
- GET /api/sessions/{session_id} — Get session
- DELETE /api/sessions/{session_id} — Delete session
- POST /api/missions — Create mission (QUEUED)
- GET /api/missions/{mission_id} — Get mission
- GET /api/missions — List missions
- PATCH /api/missions/{mission_id}/state — Transition mission state
- GET /api/missions/{mission_id}/status — Mission status
- POST /api/chat — Chat endpoint (Phase 2: SAI mission)
- GET /api/chat/mission/{id}/status — Mission status polling
- GET /api/missions/{id}/stream — SSE stream for mission progress (Phase 3)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db, ensure_default_user, get_or_create_user
from .models import (
    DEFAULT_USER_ID,
    ChatRequest,
    ChatResponse,
    MissionCreate,
    MissionResponse,
    MissionStatusResponse,
    MissionStateUpdate,
    SessionCreate,
    SessionResponse,
)
from .sessions import create_session, get_session, list_sessions, delete_session
from .missions import (
    create_mission,
    get_mission,
    list_missions,
    transition_mission_state,
    get_mission_status,
)
from .sai_runner import _run_sai_mission
from .prompt_router import classify_prompt, RouteType, get_route_handler

# Path to static files directory
STATIC_DIR = Path(__file__).parent / "static"

# =============================================================================
# App Initialization
# =============================================================================

app = FastAPI(
    title="Project-S Interactive Layer",
    description="Minimal interactive operating interface for Project-S",
    version="0.3.0",
)

# Background tasks registry: mission_id → asyncio.Task
_background_tasks: dict[str, asyncio.Task] = {}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    ensure_default_user()


# =============================================================================
# UI Route (Phase 4A)
# =============================================================================

@app.get("/ui", response_class=HTMLResponse)
async def ui_console():
    """Phase 4A: Minimal operator chat UI. Serves static HTML with embedded JS."""
    ui_file = STATIC_DIR / "ui.html"
    if ui_file.exists():
        return ui_file.read_text(encoding="utf-8")
    raise HTTPException(status_code=404, detail="UI file not found")


# =============================================================================
# Health & Welcome
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head><title>Project-S Interactive Layer v0.3</title></head>
        <body>
            <h1>Project-S Interactive Layer</h1>
            <p>Version 0.3.0 (Phase 3: SSE Streaming)</p>
            <p>API endpoints:</p>
            <ul>
                <li><a href="/docs">Swagger UI</a></li>
                <li>GET /health</li>
                <li>POST /api/sessions</li>
                <li>POST /api/missions</li>
                <li>POST /api/chat — Creates real SAI mission</li>
                <li>GET /api/chat/mission/{id}/status — Poll mission status</li>
                <li>GET /api/missions/{id}/stream — SSE stream for mission progress</li>
            </ul>
        </body>
    </html>
    """


# =============================================================================
# Session Endpoints
# =============================================================================

@app.post("/api/sessions", response_model=SessionResponse)
async def api_create_session(request: SessionCreate):
    """Create a new session for a user."""
    try:
        return create_session(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def api_list_sessions(user_id: Optional[str] = None):
    """List sessions, optionally filtered by user_id."""
    return list_sessions(user_id=user_id)


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def api_get_session(session_id: str):
    """Get a session by ID."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/sessions/{session_id}")
async def api_delete_session(session_id: str):
    """Delete a session and its missions."""
    delete_session(session_id)
    return {"deleted": True, "session_id": session_id}


# =============================================================================
# Mission Endpoints
# =============================================================================

@app.post("/api/missions", response_model=MissionResponse)
async def api_create_mission(request: MissionCreate):
    """Create a mission in QUEUED state, persist immediately."""
    try:
        return create_mission(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/missions/{mission_id}", response_model=MissionResponse)
async def api_get_mission(mission_id: str):
    """Get a mission by ID."""
    mission = get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@app.get("/api/missions/{mission_id}/status", response_model=MissionStatusResponse)
async def api_get_mission_status(mission_id: str):
    """Get mission status (lightweight)."""
    status = get_mission_status(mission_id)
    if not status:
        raise HTTPException(status_code=404, detail="Mission not found")
    return status


@app.get("/api/missions")
async def api_list_missions(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    state: Optional[str] = None,
):
    """List missions with optional filters."""
    return list_missions(user_id=user_id, session_id=session_id, state=state)


@app.patch("/api/missions/{mission_id}/state", response_model=MissionResponse)
async def api_transition_mission_state(mission_id: str, request: MissionStateUpdate):
    """Transition mission to a new state. Validates allowed transitions."""
    try:
        return transition_mission_state(mission_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SSE Streaming Endpoint (Phase 3)
# =============================================================================

@app.get("/api/missions/{mission_id}/stream")
async def api_sse_stream(mission_id: str):
    """
    Phase 3: SSE stream for real-time mission progress.

    Returns text/event-stream with:
    - mission_state events on every state transition
    - mission_terminal event when mission completes
    - heartbeat events every ~10s while mission is non-terminal

    Event format:
      event: mission_state
      data: {"mission_id": "...", "state": "PLANNING", ...}

      event: mission_terminal
      data: {"mission_id": "...", "state": "COMPLETE", ...}

      event: heartbeat
      data: {"mission_id": "...", "state": "EXECUTING", ...}
    """
    from .sse_stream import _sse_stream_generator

    return StreamingResponse(
        _sse_stream_generator(mission_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# Chat Endpoint (Phase 2: SAI Integration)
# =============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(request: ChatRequest):
    """
    Phase 2.1: Chat endpoint creates a real SAI mission and returns immediately.

    Flow:
      1. Validate prompt is non-empty (400 if empty/whitespace)
      2. Validate session exists (404 if not)
      3. Create mission in QUEUED state
      4. Launch background task -> sai_runner._run_sai_mission()
      5. Return immediately with mission_id

    The SAI mission runs asynchronously in the background.
    State transitions: QUEUED -> PLANNING -> EXECUTING -> COMPLETE/FAILED/TIMEOUT
    """
    # 1. Validate prompt is not empty or whitespace-only
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty or whitespace-only",
        )

    # 2. Validate session
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")

    # 3. Ensure user exists (FK constraint: missions.user_id -> users.user_id)
    get_or_create_user(request.user_id)

    # 4. Classify prompt via GAP_031 router
    route_decision = classify_prompt(request.message)

    # 5. Create mission in QUEUED state with route metadata
    mission_req = MissionCreate(
        user_id=request.user_id,
        session_id=request.session_id,
        task=request.message,
        selected_route=route_decision.route_type,
        route_confidence=route_decision.confidence,
        route_rationale=route_decision.rationale,
        route_matched_rules=route_decision.matched_rules,
    )
    mission = create_mission(
        mission_req,
        route_type=route_decision.route_type,
        route_confidence=route_decision.confidence,
        route_rationale=route_decision.rationale,
        route_matched_rules=route_decision.matched_rules,
        route_llm_used=route_decision.llm_used,
        route_llm_model=route_decision.llm_model,
    )
    mission_id = mission.mission_id

    # 6. Route dispatch: Phase 1 handlers
    handler = get_route_handler(route_decision.route_type)
    if handler is not None:
        # Phase 1: Lightweight route — execute immediately, store result
        try:
            handler_result = handler(
                prompt=request.message,
                decision=route_decision,
                mission_id=mission_id,
            )
            # Store the lightweight result directly
            from .missions import complete_mission
            complete_mission(mission_id, handler_result["result"])
            # Log the route decision as a mission event
            from .database import log_mission_event
            log_mission_event(mission_id, "route_dispatched", {
                "route_type": route_decision.route_type,
                "confidence": route_decision.confidence,
                "handler": "lightweight",
            })
            response_text = f"Route: {route_decision.route_type}\n\n{handler_result['result']}"
            # Return immediately with the lightweight handler result
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                response=response_text,
                mission_id=mission_id,
            )
        except Exception as e:
            # If handler fails, fall through to SAI
            logger.warning("Route handler failed for %s: %s — falling back to SAI",
                           route_decision.route_type, e)
            task = asyncio.create_task(
                _run_sai_mission(
                    mission_id=mission_id,
                    session_id=request.session_id,
                    prompt=request.message,
                    user_id=request.user_id,
                )
            )
            _background_tasks[mission_id] = task
            return ChatResponse(
                message_id=str(uuid.uuid4()),
                response=f"Route {route_decision.route_type} fell back to SAI: {str(e)}",
                mission_id=mission_id,
            )
    else:
        # No handler yet — fall back to existing SAI path
        task = asyncio.create_task(
            _run_sai_mission(
                mission_id=mission_id,
                session_id=request.session_id,
                prompt=request.message,
                user_id=request.user_id,
            )
        )
        _background_tasks[mission_id] = task

    # 7. Return immediately
    return ChatResponse(
        message_id=str(uuid.uuid4()),
        response=f"Mission queued ({route_decision.route_type})",
        mission_id=mission_id,
    )


# =============================================================================
# Mission Status Polling Endpoint (Phase 2 convenience)
# =============================================================================

@app.get("/api/chat/mission/{mission_id}/status")
async def api_get_chat_mission_status(mission_id: str):
    """
    Convenience endpoint to poll mission status from a chat-initiated mission.
    Returns the current state, progress, and state_history.
    """
    mission = get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {
        "mission_id": mission.mission_id,
        "state": mission.state,
        "progress": mission.progress,
        "state_history": mission.state_history,
        "result": mission.result,
        "error": mission.error,
        "task_complete": mission.state in ("COMPLETE", "FAILED", "TIMEOUT"),
    }


# =============================================================================
# Run with:
# uvicorn interactive_layer.main:app --reload --port 8000
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)