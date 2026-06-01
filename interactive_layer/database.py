"""SQLite database layer for Project-S Interactive Layer.

Handles:
- Database initialization
- User CRUD
- Session CRUD
- Mission CRUD with state persistence
- Mission event logging
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

DB_PATH = Path(__file__).parent.parent / "interactive_layer_data" / "interactive.db"

# SQL schema
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state TEXT DEFAULT 'idle',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    task TEXT NOT NULL,
    state TEXT NOT NULL,
    state_history TEXT NOT NULL,
    progress REAL DEFAULT 0.0,
    plan TEXT,
    events TEXT DEFAULT '[]',
    result TEXT,
    output_path TEXT,
    error TEXT,
    timeout_seconds INTEGER DEFAULT 600,
    -- GAP_031 Route metadata columns
    route_type TEXT DEFAULT 'FULL_AGENTIC_META_CONTROLLER',
    route_confidence REAL DEFAULT 0.3,
    route_rationale TEXT DEFAULT '',
    route_matched_rules TEXT DEFAULT '[]',
    route_llm_used INTEGER DEFAULT 0,
    route_llm_model TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS mission_events (
    event_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(mission_id),
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT
);

CREATE INDEX IF NOT EXISTS idx_missions_user_id ON missions(user_id);
CREATE INDEX IF NOT EXISTS idx_missions_session_id ON missions(session_id);
CREATE INDEX IF NOT EXISTS idx_missions_state ON missions(state);
CREATE INDEX IF NOT EXISTS idx_mission_events_mission_id ON mission_events(mission_id);
"""


def _get_conn(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Get a database connection."""
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    """Initialize database schema + incremental migrations."""
    with _get_conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        # GAP_031 migration: add route_* columns to existing missions tables
        # SQLite does not support ADD COLUMN IF NOT EXISTS, so we check PRAGMA.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(missions)")}
        _ROUTE_COLUMN_DEFAULTS: list[tuple[str, str]] = [
            ("route_type",          "TEXT DEFAULT 'FULL_AGENTIC_META_CONTROLLER'"),
            ("route_confidence",    "REAL DEFAULT 0.3"),
            ("route_rationale",     "TEXT DEFAULT ''"),
            ("route_matched_rules", "TEXT DEFAULT '[]'"),
            ("route_llm_used",      "INTEGER DEFAULT 0"),
            ("route_llm_model",     "TEXT DEFAULT ''"),
        ]
        for col_name, col_def in _ROUTE_COLUMN_DEFAULTS:
            if col_name not in existing:
                conn.execute(f"ALTER TABLE missions ADD COLUMN {col_name} {col_def}")
        conn.commit()


def _now() -> str:
    return datetime.utcnow().isoformat()


# =============================================================================
# User Operations
# =============================================================================

def get_or_create_user(user_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get or create a user. Returns user dict."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        
        meta_json = json.dumps(metadata or {})
        created_at = _now()
        conn.execute(
            "INSERT INTO users (user_id, created_at, metadata) VALUES (?, ?, ?)",
            (user_id, created_at, meta_json)
        )
        conn.commit()
        return {"user_id": user_id, "created_at": created_at, "metadata": json.loads(meta_json)}


def ensure_default_user(db_path: Path | str = DB_PATH) -> dict[str, Any]:
    """Ensure the default user 'toti' exists."""
    try:
        from .models import DEFAULT_USER_ID
    except ImportError:
        DEFAULT_USER_ID = "toti"
    return get_or_create_user(DEFAULT_USER_ID)


# =============================================================================
# Session Operations
# =============================================================================

def create_session(session_id: Optional[str], user_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a session. Returns session dict."""
    sid = session_id or str(uuid4())
    now = _now()
    meta_json = json.dumps(metadata or {})
    
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?)",
            (sid, user_id, now, now, meta_json)
        )
        conn.commit()
    
    return {
        "session_id": sid,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
        "state": "idle",
    }


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    """Get a session by ID."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        # Count messages (from mission results)
        msg_count = conn.execute(
            "SELECT COUNT(*) FROM missions WHERE session_id = ? AND result IS NOT NULL",
            (session_id,)
        ).fetchone()[0]
        result["message_count"] = msg_count
        return result


def list_sessions(user_id: Optional[str] = None) -> list[dict[str, Any]]:
    """List sessions, optionally filtered by user_id."""
    with _get_conn() as conn:
        if user_id:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def delete_session(session_id: str) -> bool:
    """Delete a session and its missions."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM missions WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        return True


# =============================================================================
# Mission Operations
# =============================================================================

def create_mission(
    mission_id: Optional[str],
    user_id: str,
    session_id: str,
    task: str,
    timeout_seconds: int = 600,
    route_type: str = "FULL_AGENTIC_META_CONTROLLER",
    route_confidence: float = 0.3,
    route_rationale: str = "",
    route_matched_rules: Optional[list[str]] = None,
    route_llm_used: bool = False,
    route_llm_model: Optional[str] = None,
) -> dict[str, Any]:
    """Create a mission in QUEUED state. Returns mission dict.
    
    GAP_031: Accepts route metadata for prompt routing persistence.
    """
    mid = mission_id or str(uuid4())
    now = _now()
    matched_rules_json = json.dumps(route_matched_rules or [])
    llm_model_str = route_llm_model or ""
    
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO missions 
               (mission_id, user_id, session_id, created_at, updated_at, task, state, state_history, progress, events, timeout_seconds,
                route_type, route_confidence, route_rationale, route_matched_rules, route_llm_used, route_llm_model)
               VALUES (?, ?, ?, ?, ?, ?, 'QUEUED', '[]', 0.0, '[]', ?,
                       ?, ?, ?, ?, ?, ?)""",
            (
                mid, user_id, session_id, now, now, task, timeout_seconds,
                route_type, route_confidence, route_rationale, matched_rules_json,
                1 if route_llm_used else 0, llm_model_str,
            )
        )
        conn.commit()
    
    return {
        "mission_id": mid,
        "user_id": user_id,
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "task": task,
        "state": "QUEUED",
        "state_history": [],
        "progress": 0.0,
        "plan": None,
        "events": [],
        "result": None,
        "output_path": None,
        "error": None,
        "timeout_seconds": timeout_seconds,
        "route_type": route_type,
        "route_confidence": route_confidence,
        "route_rationale": route_rationale,
        "route_matched_rules": route_matched_rules or [],
        "route_llm_used": route_llm_used,
        "route_llm_model": route_llm_model or "",
    }


def get_mission(mission_id: str) -> Optional[dict[str, Any]]:
    """Get a mission by ID."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        # Parse JSON fields
        result["state_history"] = json.loads(result["state_history"] or "[]")
        result["events"] = json.loads(result["events"] or "[]")
        result["plan"] = json.loads(result["plan"]) if result.get("plan") else None
        # GAP_031: parse route_matched_rules from JSON string to list
        if "route_matched_rules" in result and isinstance(result["route_matched_rules"], str):
            try:
                result["route_matched_rules"] = json.loads(result["route_matched_rules"] or "[]")
            except (json.JSONDecodeError, TypeError):
                result["route_matched_rules"] = []
        # Coerce nullable string columns to empty string for Pydantic
        result["route_llm_model"] = result.get("route_llm_model") or ""
        result["route_rationale"] = result.get("route_rationale") or ""
        result["route_type"] = result.get("route_type") or "FULL_AGENTIC_META_CONTROLLER"
        return result


def list_missions(user_id: Optional[str] = None, session_id: Optional[str] = None, state: Optional[str] = None) -> list[dict[str, Any]]:
    """List missions with optional filters."""
    conditions = []
    params = []
    
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    if session_id:
        conditions.append("session_id = ?")
        params.append(session_id)
    if state:
        conditions.append("state = ?")
        params.append(state)
    
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    with _get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM missions{where} ORDER BY created_at DESC",
            params
        ).fetchall()
        results = []
        for row in rows:
            result = dict(row)
            result["state_history"] = json.loads(result["state_history"] or "[]")
            result["events"] = json.loads(result["events"] or "[]")
            result["plan"] = json.loads(result["plan"]) if result.get("plan") else None
            if "route_matched_rules" in result and isinstance(result["route_matched_rules"], str):
                try:
                    result["route_matched_rules"] = json.loads(result["route_matched_rules"] or "[]")
                except (json.JSONDecodeError, TypeError):
                    result["route_matched_rules"] = []
            results.append(result)
        return results


def update_mission_state(mission_id: str, new_state: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Update mission state. Appends to state_history, persists immediately.
    Returns updated mission.
    """
    now = _now()
    
    with _get_conn() as conn:
        # Get current mission
        row = conn.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,)).fetchone()
        if not row:
            raise ValueError(f"Mission {mission_id} not found")
        
        current = dict(row)
        state_history = json.loads(current["state_history"] or "[]")
        
        # Append state transition
        transition = {
            "state": new_state,
            "timestamp": now,
            "metadata": metadata or {},
        }
        if state_history:
            prev_state = state_history[-1]
            prev_ts = datetime.fromisoformat(prev_state.get("timestamp", now))
            curr_ts = datetime.fromisoformat(now)
            duration_ms = int((curr_ts - prev_ts).total_seconds() * 1000)
            transition["duration_ms"] = duration_ms
        
        state_history.append(transition)
        
        conn.execute(
            """UPDATE missions 
               SET state = ?, state_history = ?, updated_at = ?
               WHERE mission_id = ?""",
            (new_state, json.dumps(state_history), now, mission_id)
        )
        conn.commit()
    
    return get_mission(mission_id)


def update_mission_progress(mission_id: str, progress: float) -> None:
    """Update mission progress."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE missions SET progress = ?, updated_at = ? WHERE mission_id = ?",
            (progress, _now(), mission_id)
        )
        conn.commit()


def update_mission_result(mission_id: str, result: str, output_path: Optional[str] = None) -> None:
    """Update mission result and output path."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE missions SET result = ?, output_path = ?, updated_at = ? WHERE mission_id = ?",
            (result, output_path, _now(), mission_id)
        )
        conn.commit()


def update_mission_error(mission_id: str, error: str) -> None:
    """Update mission error."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE missions SET error = ?, updated_at = ? WHERE mission_id = ?",
            (error, _now(), mission_id)
        )
        conn.commit()


def update_mission_plan(mission_id: str, plan: dict[str, Any]) -> None:
    """Update mission plan."""
    with _get_conn() as conn:
        conn.execute(
            "UPDATE missions SET plan = ?, updated_at = ? WHERE mission_id = ?",
            (json.dumps(plan), _now(), mission_id)
        )
        conn.commit()


def append_mission_events(mission_id: str, events: list[dict[str, Any]]) -> None:
    """Append events to mission events list."""
    with _get_conn() as conn:
        row = conn.execute("SELECT events FROM missions WHERE mission_id = ?", (mission_id,)).fetchone()
        if not row:
            raise ValueError(f"Mission {mission_id} not found")
        
        existing = json.loads(row["events"] or "[]")
        existing.extend(events)
        
        conn.execute(
            "UPDATE missions SET events = ?, updated_at = ? WHERE mission_id = ?",
            (json.dumps(existing), _now(), mission_id)
        )
        conn.commit()


# =============================================================================
# Mission Event Operations
# =============================================================================

def log_mission_event(mission_id: str, event_type: str, data: dict[str, Any] | None = None) -> None:
    """Log a mission event."""
    event_id = str(uuid4())
    now = _now()
    
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO mission_events (event_id, mission_id, event_type, timestamp, data) VALUES (?, ?, ?, ?, ?)",
            (event_id, mission_id, event_type, now, json.dumps(data or {}))
        )
        conn.commit()


def get_mission_events(mission_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Get mission events."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM mission_events WHERE mission_id = ? ORDER BY timestamp DESC LIMIT ?",
            (mission_id, limit)
        ).fetchall()
        results = []
        for row in rows:
            r = dict(row)
            r["data"] = json.loads(r["data"]) if r.get("data") else {}
            results.append(r)
        return results