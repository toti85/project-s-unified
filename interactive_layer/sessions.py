"""Session management for Project-S Interactive Layer.

SQLite-backed session CRUD with user_id on every session.
"""

from __future__ import annotations

from typing import Optional

from .database import create_session as _db_create_session
from .database import get_session as _db_get_session
from .database import list_sessions as _db_list_sessions
from .database import delete_session as _db_delete_session
from .database import get_or_create_user
from .models import SessionCreate, SessionResponse


def create_session(request: SessionCreate) -> SessionResponse:
    """Create a new session for a user.

    Auto-creates the user if they don't exist (avoids FK constraint failure).
    """
    # Auto-create user to avoid FK constraint failure
    get_or_create_user(request.user_id)

    data = _db_create_session(
        session_id=None,
        user_id=request.user_id,
    )
    return SessionResponse(**data)


def get_session(session_id: str) -> Optional[SessionResponse]:
    """Get a session by ID."""
    data = _db_get_session(session_id)
    if not data:
        return None
    return SessionResponse(**data)


def list_sessions(user_id: Optional[str] = None) -> list[SessionResponse]:
    """List sessions, optionally filtered by user_id."""
    results = _db_list_sessions(user_id=user_id)
    return [SessionResponse(**r) for r in results]


def delete_session(session_id: str) -> bool:
    """Delete a session and its missions."""
    return _db_delete_session(session_id)