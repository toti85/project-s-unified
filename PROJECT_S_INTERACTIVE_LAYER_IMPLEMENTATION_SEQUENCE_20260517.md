# Project-S Interactive Layer — Implementation Sequence

**Date:** 2026-05-17
**Type:** Implementation sequence and milestones
**Status:** Plan only, NO implementation yet
**Mandatory changes applied:** Mission persistence in Phase 1, user_id field, centralized mission state model

---

## 1. Implementation Philosophy

1. **Build the foundation first, UI last** — Backend must work before frontend
2. **Minimum viable interface** — Each step produces something testable
3. **Mission persistence from Day 1** — Every state transition persists to SQLite immediately
4. **user_id on everything** — Default "toti", future-proof for multi-user
5. **Test with curl/HTTP client first** — Don't tie UI development to API development
6. **Deploy locally after each milestone** — Verify on the actual machine

---

## 2. Implementation Sequence

### Phase 0: Prerequisites (Day 0)

**Goal:** Ensure the dev environment can run FastAPI.

| Step | Action | Verification |
|------|--------|--------------|
| 0.1 | Check Python version (≥3.10) | `python --version` |
| 0.2 | Install FastAPI + uvicorn | `pip install fastapi uvicorn[standard]` |
| 0.3 | Verify import | `python -c "import fastapi; print(fastapi.__version__)"` |
| 0.4 | Create project directory | `mkdir C:\ProjectS-Unified\interactive_layer` |

**Estimated time:** 15 minutes

---

### Phase 1: Backend Core (Day 1-2)

**Goal:** SQLite-backed API with mission state model. Testable with curl.

#### Milestone 1.1: FastAPI App Skeleton

**Files to create:**
```
interactive_layer/
├── __init__.py
├── main.py              # FastAPI app, health endpoint
├── models.py            # Pydantic models + MissionState enum
├── database.py          # SQLite connection + schema init
├── sessions.py          # Session manager (SQLite-backed)
└── missions.py          # Mission CRUD + state transitions
```

**Endpoints:**
- `GET /health` → `{"status": "ok"}`
- `GET /` → Simple HTML with "Project-S Interactive Layer v0.1"

**Verification:**
```bash
uvicorn interactive_layer.main:app --reload --port 8000
# Open http://localhost:8000/health
# Should return: {"status": "ok"}
```

**Estimated time:** 2 hours

#### Milestone 1.2: Database + Mission State Model

**Files to create:**
- `database.py` — SQLite connection, schema initialization
- `models.py` — Pydantic models + mission state enum

**SQLite schema:**
```sql
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
    timeout_seconds INTEGER DEFAULT 600
);

CREATE TABLE IF NOT EXISTS mission_events (
    event_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(mission_id),
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT
);
```

**Mission state enum:**
```python
from enum import Enum

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
```

**Database functions:**
- `init_db()` — Create tables if not exist
- `get_or_create_user(user_id)` — Upsert user
- `create_mission(mission_dict)` — Insert mission, persist immediately
- `update_mission_state(mission_id, new_state, metadata)` — Update state + append to state_history
- `get_mission(mission_id)` — Get mission by ID
- `list_missions(user_id, session_id)` — List missions with filters

**Default user:**
- `DEFAULT_USER_ID = "toti"`
- `ensure_default_user()` — Creates "toti" user on startup

**Verification:**
```python
python -c "
from interactive_layer.database import init_db, ensure_default_user
init_db()
ensure_default_user()
print('DB initialized, default user created')
"
```

**Estimated time:** 4 hours

#### Milestone 1.3: Session Management (SQLite-backed)

**Files to modify:**
- `sessions.py` — Add session CRUD operations

**Features:**
- Create session (returns UUID)
- List sessions
- Get session by ID
- Delete session
- **SQLite persistence** (not in-memory)
- **user_id on every session**

**Models:**
```python
class SessionCreate(BaseModel):
    user_id: str = "toti"

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime
    message_count: int
    state: str

class MessageCreate(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    metadata: dict = {}

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime
    metadata: dict
```

**Verification:**
```bash
# Create session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "toti"}'

# List sessions
curl http://localhost:8000/api/sessions

# Get session
curl http://localhost:8000/api/sessions/{session_id}
```

**Estimated time:** 3 hours

#### Milestone 1.4: Mission CRUD + State Transitions

**Files to modify:**
- `missions.py` — Mission CRUD + state transition logic

**Endpoints:**
```
POST /api/missions
Body: { "user_id": "toti", "session_id": "...", "task": "..." }
→ Creates mission in QUEUED state, persists to SQLite
→ Returns { "mission_id": "...", "state": "QUEUED" }

GET /api/missions/{mission_id}
→ Returns full mission object with state_history

GET /api/missions?user_id=toti&session_id=...&state=EXECUTING
→ List missions with filters

PATCH /api/missions/{mission_id}/state
Body: { "state": "PLANNING", "metadata": {} }
→ Updates mission state, appends to state_history, persists immediately
→ Returns updated mission
```

**State transition function:**
```python
def transition_mission_state(mission_id: str, new_state: MissionState, metadata: dict = None) -> Mission:
    """
    Transition mission to new state.
    - Validates transition (only allowed transitions)
    - Updates state field
    - Appends to state_history with timestamp and duration_ms
    - Persists to SQLite immediately
    - Returns updated mission
    """
```

**Allowed transitions (enforced):**
- QUEUED → PLANNING, TIMEOUT, FAILED
- PLANNING → EXECUTING, FAILED, TIMEOUT
- EXECUTING → SYNTHESIZING, REPLAN, FAILED, TIMEOUT
- SYNTHESIZING → WRITING, FAILED, TIMEOUT
- WRITING → COMPLETE, FAILED
- REPLAN → PLANNING

**Verification:**
```bash
# Create mission
curl -X POST http://localhost:8000/api/missions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "toti", "session_id": "...", "task": "Test task"}'

# Check state
curl http://localhost:8000/api/missions/{id}

# Transition state
curl -X PATCH http://localhost:8000/api/missions/{id}/state \
  -H "Content-Type: application/json" \
  -d '{"state": "PLANNING"}'
```

**Estimated time:** 3 hours

#### Milestone 1.5: Chat Endpoint (No SAI Integration)

**Files to modify:**
- `main.py` — Add POST /api/chat endpoint

**Endpoint:**
```
POST /api/chat
Body: { "user_id": "toti", "session_id": "...", "message": "..." }
Response: { "message_id": "...", "response": "Echo: ..." }
```

**Behavior:**
- Store user message in session
- Echo back the message as AI response (no SAI integration yet)
- Store AI response in session
- **user_id on every message**

**Verification:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "toti", "session_id": "...", "message": "Hello"}'
# Should return: {"message_id": "...", "response": "Echo: Hello"}
```

**Estimated time:** 2 hours

---

### Phase 2: SAI Integration (Day 3-4)

**Goal:** Real SAI execution through the API.

#### Milestone 2.1: SAI Adapter

**Files to create:**
- `sai_adapter.py` — Wraps SuperIntelligentAI

**Features:**
- Import SAI from `src/core/super_intelligent_ai.py`
- Wrap `execute_intelligent_task()` method
- Handle async execution
- Return structured results

**Code structure:**
```python
class SAIAdapter:
    def __init__(self):
        self.ai = SuperIntelligentAI()
    
    async def execute_task(self, session_id: str, task: str) -> dict:
        """Execute task via SAI, return structured result."""
        result = await self.ai.execute_intelligent_task(task=task)
        return {
            "success": True,
            "output": result,
            "duration_ms": ...
        }
```

**Verification:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "toti", "session_id": "...", "message": "Summarize Python async"}'
# Should return SAI-generated response
```

**Estimated time:** 4 hours

#### Milestone 2.2: Mission Execution with State Transitions

**Files to modify:**
- `missions.py` — Add mission execution with state transitions

**Features:**
- Create mission from chat message
- State transitions: QUEUED → PLANNING → EXECUTING → SYNTHESIZING → WRITING → COMPLETE
- Each transition persists to SQLite AND streams over SSE
- Handle timeouts

**Mission lifecycle with states:**
```
POST /api/sessions/{session_id}/missions
Body: { "user_id": "toti", "task": "..." }
→ Creates mission in QUEUED state
→ Background task starts: QUEUED → PLANNING → EXECUTING → ...

GET /api/missions/{mission_id}/status
→ Returns { "state": "EXECUTING", "progress": 0.5, "state_history": [...] }
```

**Verification:**
```bash
# Start mission
curl -X POST http://localhost:8000/api/sessions/{id}/missions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "toti", "task": "Research local LLMs"}'

# Check status
curl http://localhost:8000/api/missions/{id}/status
```

**Estimated time:** 4 hours

---

### Phase 3: Streaming (Day 5)

**Goal:** Real-time progress via SSE.

#### Milestone 3.1: SSE Stream

**Files to create:**
- `stream.py` — SSE event generator

**Endpoint:**
```
GET /api/stream/{mission_id}
Content-Type: text/event-stream
```

**Event types:**
```
event: mission_planning
data: {"mission_id": "...", "state": "PLANNING", "timestamp": "..."}

event: mission_executing
data: {"mission_id": "...", "state": "EXECUTING", "timestamp": "..."}

event: tool_start
data: {"type": "tool_start", "tool": "web_search", "params": {...}}

event: tool_complete
data: {"type": "tool_complete", "tool": "web_search", "duration_ms": 1234}

event: mission_synthesizing
data: {"mission_id": "...", "state": "SYNTHESIZING", "timestamp": "..."}

event: mission_writing
data: {"mission_id": "...", "state": "WRITING", "timestamp": "..."}

event: mission_complete
data: {"type": "mission_complete", "output": "...", "duration_ms": 45678}

event: mission_failed
data: {"type": "mission_failed", "error": "..."}

event: mission_timeout
data: {"type": "mission_timeout", "timeout_seconds": 600}

event: mission_replan
data: {"type": "mission_replan", "reason": "..."}
```

**Verification:**
```bash
curl http://localhost:8000/api/stream/{mission_id}
# Should stream events in real-time
```

**Estimated time:** 3 hours

---

### Phase 4: File Handling (Day 6)

**Goal:** Upload and download support.

#### Milestone 4.1: File Endpoints

**Files to modify:**
- `main.py` — Add file routes
- New file: `files.py` — File handler

**Endpoints:**
```
POST /api/files/upload
  → Multipart upload, saves to uploads/{session_id}/{filename}
  → Returns { "filename": "...", "size": 1234 }

GET /api/files/list
  → Lists files in uploads/{session_id}/
  → Returns [{ "filename": "...", "size": 1234, "uploaded": "..." }]

GET /api/files/download/{filename}
  → Streams file download

GET /api/outputs/list
  → Lists generated reports
  → Returns [{ "filename": "...", "size": 1234, "generated": "..." }]

GET /api/outputs/download/{filename}
  → Streams report download
```

**Verification:**
```bash
# Upload
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@research.txt"

# List
curl http://localhost:8000/api/files/list

# Download
curl -O http://localhost:8000/api/files/download/research.txt
```

**Estimated time:** 3 hours

---

### Phase 5: Evidence Query (Day 7)

**Goal:** Query the Witness layer.

#### Milestone 5.1: Evidence Endpoint

**Files to create:**
- `evidence.py` — Evidence query handler

**Endpoint:**
```
GET /api/evidence?user_id=toti&session_id=...&limit=50&source=...&success=true
```

**Response:**
```json
{
  "total": 403000,
  "entries": [
    {
      "timestamp": "2026-05-17T21:30:15.123Z",
      "source": "super_intelligent_ai",
      "tool": "web_search",
      "success": true,
      "duration_ms": 14234,
      "params": {"query": "..."},
      "result_summary": "Found 10 results"
    }
  ]
}
```

**Implementation:**
- Read meta_evidence.jsonl
- Filter by user_id, session_id, query parameters
- Return most recent entries
- Limit max 1000 entries per query

**Estimated time:** 2 hours

---

### Phase 6: Frontend (Day 8-10)

**Goal:** Working UI that connects to the API.

#### Milestone 6.1: Static HTML

**Files to create:**
```
interactive_layer/
├── templates/
│   └── index.html       # Main UI
└── static/
    ├── style.css        # Dark theme styles
    └── app.js           # Frontend logic
```

**index.html structure:**
- Header bar (user_id, session, mission status, elapsed time)
- Tab navigation (Chat, Mission, Evidence, Files, Reports)
- Chat panel (message list + input)
- Mission panel (progress, tool events, state history)
- Evidence panel (table + detail view)
- File panel (upload area + file lists)

**Estimated time:** 6 hours

#### Milestone 6.2: Chat Functionality

**Features:**
- Send message → POST /api/chat
- Receive response → append to message list
- Display conversation history from session
- Auto-scroll to bottom on new message

**Estimated time:** 4 hours

#### Milestone 6.3: Mission Progress

**Features:**
- Connect to SSE stream
- Display state transitions in mission panel
- Update progress bar
- Show current tool
- Handle mission complete/fail

**Estimated time:** 4 hours

#### Milestone 6.4: File Manager

**Features:**
- Drag-and-drop upload
- File list display
- Download buttons
- Report list with download

**Estimated time:** 3 hours

#### Milestone 6.5: Evidence Viewer

**Features:**
- Query evidence endpoint
- Display in table
- Click to view detail JSON
- Filter by user_id, source, success

**Estimated time:** 3 hours

---

### Phase 7: Polish (Day 11-12)

**Goal:** Make it usable.

#### Milestone 7.1: Error Handling

**Features:**
- Show error messages in chat
- Retry button on failed missions
- Timeout handling
- Connection lost detection

**Estimated time:** 3 hours

#### Milestone 7.2: Startup Script

**Files to create:**
- `start.bat` — Windows startup script
- `requirements.txt` — Python dependencies

**start.bat content:**
```batch
@echo off
cd /d C:\ProjectS-Unified
python -m uvicorn interactive_layer.main:app --reload --port 8000
echo Open http://localhost:8000 in your browser
pause
```

**requirements.txt:**
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
aiofiles>=23.2.1
```

**Estimated time:** 1 hour

---

## 3. Updated Estimated Timeline

| Phase | Days | Hours | Cumulative |
|-------|------|-------|------------|
| 0. Prerequisites | 0.25 | 1.5 | 1.5 |
| 1. Backend Core (with DB + missions) | 2.5 | 14 | 15.5 |
| 2. SAI Integration | 2 | 8 | 23.5 |
| 3. Streaming | 1 | 3 | 26.5 |
| 4. File Handling | 1 | 3 | 29.5 |
| 5. Evidence Query | 1 | 2 | 31.5 |
| 6. Frontend | 3 | 18 | 49.5 |
| 7. Polish | 1 | 4 | 53.5 |

**Total estimated effort:** ~54 hours (7 working days at 7-8 hours/day)

---

## 4. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **SAI import fails** | Use relative import with sys.path manipulation |
| **SAI timeout kills mission** | Set 600s timeout, show error in UI |
| **SSE connection drops** | Auto-reconnect on page refresh |
| **Large synthesis output** | Stream in chunks, not all at once |
| **Browser automation hangs** | Strict 180s timeout, kill process |
| **SQLite concurrent writes** | Single-writer model (asyncio) |

---

## 5. What NOT to Implement Yet

1. **Authentication** — Local dev, no security boundary
2. **Docker/containerization** — Local dev only
3. **CI/CD pipeline** — Manual deployment
4. **Database migrations** — SQLite, simple schema
5. **API versioning** — Single version for v1
6. **Load testing** — Single user
7. **Monitoring/alerting** — Local dev
8. **Logging framework** — Console output is enough
9. **Configuration management** — Hardcoded is fine
10. **Test suite** — Manual testing with curl/browser is enough for v1

---

## 6. Deployment Checklist

After implementation:

- [ ] `pip install -r requirements.txt`
- [ ] `python -m uvicorn interactive_layer.main:app --port 8000`
- [ ] Open http://localhost:8000/health → returns `{"status": "ok"}`
- [ ] Open http://localhost:8000/ → shows UI
- [ ] Send a test message → SAI responds
- [ ] Start a mission → progress streams
- [ ] Upload a file → file appears in list
- [ ] Download a report → file saved
- [ ] Query evidence → entries returned
- [ ] Refresh page → session restored

---

## 7. Success Criteria for V1

The v1 is considered complete when:

1. ✅ User can send a task via chat
2. ✅ SAI executes the task
3. ✅ Progress streams in real-time
4. ✅ Result appears in chat with download link
5. ✅ User can upload files
6. ✅ User can download reports
7. ✅ User can view evidence entries
8. ✅ Session persists across page refresh
9. ✅ Error messages are clear
10. ✅ Mission timeout is handled gracefully
11. ✅ Mission state persists to SQLite on every transition
12. ✅ user_id is present on all entities

---

*End of implementation sequence document.*
*All three architecture documents are complete.*