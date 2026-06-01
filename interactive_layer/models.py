"""Pydantic models + MissionState enum for Project-S Interactive Layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Mission State Enum
# =============================================================================

class MissionState(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    SYNTHESIZING = "SYNTHESIZING"
    WRITING = "WRITING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    REPLAN = "REPLAN"
    TIMEOUT = "TIMEOUT"


# Terminal states — no outgoing transitions allowed
TERMINAL_STATES = {"COMPLETE", "FAILED", "TIMEOUT"}

# Phase 2 truthful coarse-grained transition graph:
# SAI does NOT expose SYNTHESIZING/WRITING as separate hookable phases,
# so we add EXECUTING → COMPLETE as an official direct transition.
# Phase 5+: when SAI exposes these as distinct phases, remove this
# direct transition and restore the full QUEUED→PLANNING→EXECUTING→
# SYNTHESIZING→WRITING→COMPLETE path.
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "QUEUED": ["PLANNING", "FAILED", "TIMEOUT"],
    "PLANNING": ["EXECUTING", "FAILED", "TIMEOUT"],
    "EXECUTING": ["SYNTHESIZING", "COMPLETE", "REPLAN", "FAILED", "TIMEOUT"],
    "SYNTHESIZING": ["WRITING", "FAILED", "TIMEOUT"],
    "WRITING": ["COMPLETE", "FAILED"],
    "REPLAN": ["PLANNING"],
}


def validate_transition(from_state: str, to_state: str) -> bool:
    """Validate whether a state transition is allowed."""
    allowed = ALLOWED_TRANSITIONS.get(from_state, [])
    return to_state in allowed


# =============================================================================
# User Models
# =============================================================================

DEFAULT_USER_ID = "toti"


class UserCreate(BaseModel):
    user_id: str = DEFAULT_USER_ID
    metadata: dict[str, Any] = {}


class UserResponse(BaseModel):
    user_id: str
    created_at: datetime
    metadata: dict[str, Any] = {}


# =============================================================================
# Session Models
# =============================================================================

class SessionCreate(BaseModel):
    user_id: str = DEFAULT_USER_ID


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    state: str = "idle"


class MessageCreate(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    metadata: dict[str, Any] = {}


class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = {}


# =============================================================================
# Mission Models
# =============================================================================

class MissionCreate(BaseModel):
    user_id: str = DEFAULT_USER_ID
    session_id: str
    task: str
    timeout_seconds: int = 600
    # GAP_031 Route metadata fields
    selected_route: str = "FULL_AGENTIC_META_CONTROLLER"
    route_confidence: float = 0.3
    route_rationale: str = ""
    route_matched_rules: list[str] = []


class MissionStateUpdate(BaseModel):
    state: str  # MissionState value
    metadata: dict[str, Any] = {}


class MissionResponse(BaseModel):
    mission_id: str
    user_id: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    task: str
    state: str
    state_history: list[dict[str, Any]]
    progress: float = 0.0
    plan: Optional[dict[str, Any]] = None
    events: list[dict[str, Any]]
    result: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None
    timeout_seconds: int = 600
    # GAP_031 route metadata — persisted columns exposed in API response
    route_type: str = "FULL_AGENTIC_META_CONTROLLER"
    route_confidence: float = 0.3
    route_rationale: str = ""
    route_matched_rules: Any = []
    route_llm_used: int = 0
    route_llm_model: str = ""


class MissionStatusResponse(BaseModel):
    mission_id: str
    state: str
    progress: float
    state_history: list[dict[str, Any]]
    error: Optional[str] = None


# =============================================================================
# Chat Models
# =============================================================================

class ChatRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    session_id: str
    message: str


class ChatResponse(BaseModel):
    message_id: str
    response: str
    mission_id: Optional[str] = None


# =============================================================================
# Evidence Models
# =============================================================================

class EvidenceQuery(BaseModel):
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = None
    limit: int = 50
    source: Optional[str] = None
    success: Optional[bool] = None


class EvidenceEntry(BaseModel):
    timestamp: str
    source: str
    tool: str
    success: bool
    duration_ms: int
    params: dict[str, Any] = {}
    result_summary: str = ""


class EvidenceResponse(BaseModel):
    total: int
    entries: list[EvidenceEntry]


# =============================================================================
# File Models
# =============================================================================

class FileUploadResponse(BaseModel):
    filename: str
    size: int


class FileInfo(BaseModel):
    filename: str
    size: int
    uploaded: str  # ISO datetime string


class FileListResponse(BaseModel):
    files: list[FileInfo]