# Project-S Interactive Operating Layer — Architecture

**Date:** 2026-05-17
**Type:** Architecture design — Phase 1 Interactive Layer
**Status:** Architecture + execution plan only, NO implementation yet

---

## 1. Current Execution Flow Analysis

### 1.1 Existing Pipeline

```
interactive_task.py (stdin/stdout CLI)
    ↓
SuperIntelligentAI (src/core/super_intelligent_ai.py)
    ↓
MetaController.run_goal() (use_meta_controller=True)
    ↓
SmartToolOrchestrator (tools/tools/registry/smart_orchestrator.py)
    ↓
Tool execution chain:
  - web_search (DDGS)
  - web_scraper
  - browser_automation (Playwright)
  - file_search / file_content_search / file_writer
  - system_tools / pdf_generator
    ↓
LLM Synthesis (Qwen3.6-35B-A3B via OpenRouter)
    ↓
file_writer → output report
    ↓
Witness hook → meta_evidence.jsonl
```

### 1.2 Current I/O Boundaries

| Boundary | Current State | Problem |
|----------|---------------|---------|
| **Input** | stdin text prompt (CLI) | No file upload, no structured input, no conversation history |
| **Output** | stdout text (console) | No streaming, no structured output, no file download |
| **Long-running** | Blocking call, timeout=120s | No progress visibility, no recovery on failure |
| **Evidence** | Append-only JSONL file | No query interface, no real-time visibility |
| **Reports** | Written to disk | No download mechanism, no listing |
| **Sessions** | Stateless (each run is independent) | No conversation continuity, no session persistence |

### 1.3 Key Observations

1. **SAI is the execution engine** — it's a Python class with async methods, takes a `task` string, returns structured output
2. **MetaController is the goal executor** — it runs multi-iteration goal execution with replanning
3. **SmartToolOrchestrator is the tool router** — it selects and chains tools based on the task
4. **Synthesis is a separate step** — Qwen3.6 synthesizes tool output into structured memos
5. **Everything is synchronous/blocking** — no streaming, no async UI feedback
6. **No session model** — each run is independent, no conversation history
7. **Evidence is append-only** — the Witness layer already logs everything, just needs a query interface

---

## 2. Architecture Comparison

### 2.1 Option 1: FastAPI + Minimal HTML/JS

| Aspect | Details |
|--------|---------|
| **Backend** | FastAPI (async, Starlette-based) |
| **Frontend** | Minimal HTML/CSS/JS (vanilla or minimal framework) |
| **Session model** | In-memory dict + SQLite persistence |
| **Streaming** | Server-Sent Events (SSE) via `StreamingResponse` |
| **File handling** | Upload to temp dir, download from output dir |
| **Long-running** | Background tasks via `asyncio.create_task()` |
| **Pros** | Full control, no framework lock-in, production-ready, easy to extend |
| **Cons** | More code to write, manual frontend work, no built-in state management |

### 2.2 Option 2: Gradio

| Aspect | Details |
|--------|---------|
| **Backend** | Gradio (built on FastAPI) |
| **Frontend** | Auto-generated from Python function signatures |
| **Session model** | Built-in `state` parameter |
| **Streaming** | `gr.Textbox(interactive=True)` with generator functions |
| **File handling** | Built-in `gr.File` component |
| **Long-running** | Generator functions with `yield` for streaming |
| **Pros** | Very fast to prototype, built-in streaming, built-in file upload/download |
| **Cons** | Limited customization, Gradio-specific patterns, harder to extend beyond chat UI, framework lock-in |

### 2.3 Option 3: Streamlit

| Aspect | Details |
|--------|---------|
| **Backend** | Streamlit (Python-only framework) |
| **Frontend** | Auto-generated from Python script |
| **Session model** | `st.session_state` |
| **Streaming** | `st.empty()` + `st.delta_generator` |
| **File handling** | `st.file_uploader`, `st.download_button` |
| **Long-running** | `st.spinner` + reruns, or `threading` |
| **Pros** | Python-only, very fast for dashboards, built-in state |
| **Cons** | Full-page rerun model (expensive for SAI calls), not designed for chat UI, hard to customize layout, state management is implicit and fragile |

### 2.4 Comparison Matrix

| Criterion | FastAPI+HTML | Gradio | Streamlit |
|-----------|-------------|--------|-----------|
| **Chat UI quality** | Full control (best) | Adequate (ok) | Poor (forced) |
| **Streaming support** | SSE (best) | Generator (ok) | Delta gen (ok) |
| **File upload/download** | Manual (flexible) | Built-in (easy) | Built-in (easy) |
| **Long-running tasks** | Background tasks (best) | Generator (ok) | Rerun model (bad) |
| **Session persistence** | Custom (flexible) | Built-in (ok) | st.session_state (fragile) |
| **Progress visibility** | Full control (best) | Limited (ok) | Limited (ok) |
| **Customization** | Unlimited (best) | Limited (bad) | Limited (bad) |
| **Code to prototype** | More (1000+ lines) | Less (50 lines) | Medium (200 lines) |
| **Extendability** | Unlimited (best) | Limited (bad) | Limited (bad) |
| **Framework lock-in** | None (best) | High (bad) | Medium (ok) |
| **Production readiness** | Production-ready (best) | Demo/prototype (ok) | Demo/prototype (ok) |

---

## 3. Recommended Architecture

### 3.1 Choice: **FastAPI + Minimal HTML/JS**

### 3.2 Why This Architecture

For Project-S specifically, FastAPI + minimal HTML/JS is the correct choice because:

1. **Long-running missions need background tasks** — Streamlit's rerun model and Gradio's generator model are both designed for short-lived responses. SAI missions can take 2-10 minutes. FastAPI's `asyncio.create_task()` with background task tracking is the only model that handles this cleanly.

2. **Progress visibility is critical** — The interactive layer needs to show real-time tool execution, synthesis progress, and evidence generation. FastAPI SSE streaming gives full control over what gets streamed and when.

3. **Session persistence matters** — Project-S already has `self_state.json` as a persistent self-model. The interactive layer should build on this, not fight against it. FastAPI gives full control over session storage (SQLite + in-memory).

4. **No framework lock-in** — The SAI core, MetaController, and SmartToolOrchestrator are all stable Python code. The UI layer should be a thin adapter, not a framework that constrains the interaction model.

5. **Extensibility** — Phase 2 will add things like real-time mission monitoring, multi-session support, and possibly WebSocket connections. FastAPI provides the foundation for all of these.

6. **Production readiness** — This is an operational interface, not a demo. FastAPI is used in production systems. Gradio and Streamlit are prototype/demo frameworks.

### 3.3 What This Architecture Is NOT

- It is NOT a polished SaaS product
- It is NOT a multi-tenant system
- It is NOT a real-time collaborative interface
- It is NOT a mobile-first design
- It is NOT a React/Vue/Angular app

---

## 4. Architecture Design

### 4.1 Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (DEV machine)                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Minimal HTML/JS Frontend                 │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │  │
│  │  │  Chat   │ │ Mission  │ │ Evidence │ │Files  │  │  │
│  │  │  Panel  │ │ Progress │ │ Viewer   │ │ Mgr   │  │  │
│  │  └────┬────┘ └────┬─────┘ └────┬─────┘ └──┬────┘  │  │
│  │       │           │           │         │       │  │
│  │       └───────────┴───────────┴─────────┘       │  │
│  │              SSE WebSocket (future)              │  │
│  └──────────────────┬──────────────────────────────┘  │
└─────────────────────┼─────────────────────────────────┘
                      │ HTTP / SSE
                      │
┌─────────────────────┼─────────────────────────────────┐
│              FastAPI Backend                          │
│                      │                                │
│  ┌───────────────────┼───────────────────────────┐   │
│  │          Session Manager                       │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ In-Memory│ │ SQLite   │ │ Conversation │  │   │
│  │  │ Store    │ │ Sessions │ │ History      │  │   │
│  │  └──────────┘ └──────────┘ └──────────────┘  │   │
│  └───────────────────┬───────────────────────────┘   │
│                      │                                │
│  ┌───────────────────┼───────────────────────────┐   │
│  │          Mission Executor                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ asyncio  │ │ Progress │ │ Timeout      │  │   │
│  │  │ create_  │ │ Event    │ │ Handler      │  │   │
│  │  │ task()   │ │ Bus      │ │              │  │   │
│  │  └──────────┘ └──────────┘ └──────────────┘  │   │
│  └───────────────────┬───────────────────────────┘   │
│                      │                                │
│  ┌───────────────────┼───────────────────────────┐   │
│  │          SAI Adapter                             │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ Super    │ │ Meta-    │ │ SmartTool    │  │   │
│  │  │ Intelligent│ │Controller│ │ Orchestrator│  │   │
│  │  │ AI       │ │          │ │              │  │   │
│  │  └──────────┘ └──────────┘ └──────────────┘  │   │
│  └───────────────────┬───────────────────────────┘   │
│                      │                                │
│  ┌───────────────────┼───────────────────────────┐   │
│  │          File Handler                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │
│  │  │ Upload   │ │ Output   │ │ Evidence     │  │   │
│  │  │ Dir      │ │ Dir      │ │ Query        │  │   │
│  │  └──────────┘ └──────────┘ └──────────────┘  │   │
│  └───────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────┘
```

### 4.1 User Model

Every interaction is tied to a user_id. Default: "toti".

```python
class User:
    user_id: str             # "toti" (default), future: unique identifiers
    created_at: datetime
    metadata: dict           # arbitrary user data
```

### 4.2 Session Model

```python
# Session structure
class Session:
    session_id: str          # UUID
    user_id: str             # FK to User (default "toti")
    created_at: datetime
    updated_at: datetime
    messages: list[Message]  # conversation history
    current_mission: Mission | None  # active long-running task
    state: str               # "idle" | "running" | "paused" | "error"
    metadata: dict           # arbitrary session data

class Message:
    role: str                # "user" | "assistant" | "system"
    content: str             # message text
    timestamp: datetime
    metadata: dict           # tool calls, evidence refs, etc.
```

### 4.3 Centralized Mission State Model

**Mission states (immutable enum):**

```
QUEUED → PLANNING → EXECUTING → SYNTHESIZING → WRITING → COMPLETE
   │         │          │           │           │
   │         │          │           │           └→ FAILED (write error)
   │         │          │           │
   │         │          │           └→ FAILED (synthesis error)
   │         │          │
   │         │          └→ FAILED (tool error) / REPLAN
   │         │
   │         └→ FAILED (planning error) / TIMEOUT
   │
   └→ FAILED (queue error) / TIMEOUT
```

**State transitions (all persist to SQLite, all stream over SSE):**

| Transition | Trigger | SSE Event |
|------------|---------|-----------|
| QUEUED → PLANNING | Mission dequeued | `mission_planning` |
| PLANNING → EXECUTING | Plan generated | `mission_executing` |
| PLANNING → FAILED | Planning error | `mission_failed` |
| PLANNING → TIMEOUT | Planning timeout | `mission_timeout` |
| EXECUTING → SYNTHESIZING | All tools complete | `mission_synthesizing` |
| EXECUTING → REPLAN | Replan needed | `mission_replan` |
| EXECUTING → FAILED | Tool error | `mission_failed` |
| EXECUTING → TIMEOUT | Execution timeout | `mission_timeout` |
| SYNTHESIZING → WRITING | Synthesis complete | `mission_writing` |
| SYNTHESIZING → FAILED | Synthesis error | `mission_failed` |
| SYNTHESIZING → TIMEOUT | Synthesis timeout | `mission_timeout` |
| WRITING → COMPLETE | Report written | `mission_complete` |
| WRITING → FAILED | Write error | `mission_failed` |
| REPLAN → PLANNING | Replan triggered | `mission_replan` |

**Mission model (SQLite-persisted):**

```python
class Mission:
    mission_id: str              # UUID
    user_id: str                 # FK to User (default "toti")
    session_id: str              # FK to Session
    created_at: datetime
    updated_at: datetime
    task: str                    # original task string
    state: str                   # one of the 9 states above
    state_history: list[dict]    # [{state, timestamp, duration_ms, metadata}]
    progress: float              # 0.0 - 1.0
    plan: dict | None            # generated plan (tools, order)
    events: list[dict]           # tool execution events
    result: str | None           # final output text
    output_path: str | None      # path to written report
    error: str | None            # error message if failed
    timeout_seconds: int         # per-mission timeout (default 600)
```

**SQLite schema:**

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    state TEXT DEFAULT 'idle',
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE missions (
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

CREATE TABLE mission_events (
    event_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(mission_id),
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT
);
```

### 4.3 Streaming Mechanism

```
Client                          Server
  │                               │
  │  POST /api/chat              │
  │  { "session_id": "...",      │
  │    "message": "..." }        │
  │─────────────────────────────>│
  │                               │  asyncio.create_task(run_mission())
  │  202 Accepted                 │
  │  { "mission_id": "..." }     │
  │<─────────────────────────────│
  │                               │
  │  GET /api/stream/{mission_id} │
  │─────────────────────────────>│
  │                               │  SSE stream:
  │  event: progress             │  data: {"type":"progress","msg":"..."}
  │  data: {...}                 │  data: {"type":"tool","name":"web_search",...}
  │  event: tool                 │  data: {"type":"tool","name":"synthesis",...}
  │  data: {...}                 │  data: {"type":"complete","result":"..."}
  │  event: complete             │
  │  data: {...}                 │
  │<─────────────────────────────│
```

### 4.4 File Handling Model

```
Upload directory:  C:\ProjectS-Unified\uploads\{session_id}\
Output directory:  C:\ProjectS-Unified\outputs\{session_id}\
Evidence directory: C:\ProjectS-Unified\memory\intelligence\meta_evidence.jsonl

API endpoints:
  POST /api/files/upload     → uploads/{session_id}/{filename}
  GET  /api/files/list        → list files in session
  GET  /api/files/download/{filename} → stream file download
  GET  /api/outputs/list      → list generated reports
  GET  /api/outputs/download/{filename} → stream report download
```

### 4.5 Mission Execution Model

```python
# Mission lifecycle
PENDING → RUNNING → SYNTHESIZING → COMPLETE
   │         │          │
   │         └──────────┼──→ FAILED (error)
   │                    │
   └────────────────────┼──→ FAILED (timeout)
                        │
                        └──→ PAUSED (manual)
```

- **PENDING**: Mission queued, not yet started
- **RUNNING**: Tool execution in progress, streaming events
- **SYNTHESIZING**: Tools complete, LLM synthesis in progress
- **COMPLETE**: Mission finished successfully
- **FAILED**: Mission failed (error or timeout)
- **PAUSED**: Mission paused by user (future feature)

### 4.6 Logging Visibility

```
Real-time events (SSE stream):
  - tool_start: { "tool": "web_search", "params": {...} }
  - tool_complete: { "tool": "web_search", "duration_ms": 1234 }
  - tool_error: { "tool": "web_search", "error": "..." }
  - synthesis_start: { "model": "qwen/qwen3.6-35b-a3b" }
  - synthesis_chunk: { "tokens": 123 }
  - mission_complete: { "duration_ms": 45678, "output_bytes": 3456 }

Evidence (append-only):
  - meta_evidence.jsonl already logs every tool execution
  - New endpoint: GET /api/evidence?session_id=...&limit=50
  - Returns recent evidence entries for the session
```

---

## 5. Synchronous vs Asynchronous Boundaries

### 5.1 What Should Stay Synchronous

| Operation | Reason |
|-----------|--------|
| **Chat message submission** | User expects immediate response (202 Accepted) |
| **Session creation** | Fast, no blocking |
| **File upload** | Small files, fast operation |
| **Mission status query** | Fast lookup |
| **Evidence query** | Fast SQLite/JSONL read |

### 5.2 What Should Be Asynchronous

| Operation | Reason |
|-----------|--------|
| **SAI task execution** | 2-10 minutes, needs streaming |
| **MetaController goal execution** | Multi-iteration, needs progress events |
| **LLM synthesis** | 10-60 seconds, needs streaming |
| **Browser automation** | 30-120 seconds, needs progress events |
| **File download** | Can be large, needs streaming |

### 5.3 Timeout Policy

| Operation | Timeout |
|-----------|---------|
| **SAI task** | 600 seconds (10 minutes) |
| **LLM synthesis** | 120 seconds |
| **Browser automation** | 180 seconds |
| **File upload** | 30 seconds |
| **File download** | No timeout (streaming) |

---

## 6. Long-Running Mission Behavior

### 6.1 In the UI

1. User sends a message → mission starts
2. UI shows "Mission running..." with progress indicator
3. Real-time tool execution events appear in the chat stream
4. When synthesis starts, a "Synthesizing..." indicator appears
5. When complete, the result appears as a message with a "Download report" link
6. If failed, the error message appears with a "Retry" button

### 6.2 On Page Refresh

1. UI loads session from SQLite
2. Checks for any missions with status "running" or "pending"
3. If a mission was running when page closed:
   - Show "Previous mission was running" with status
   - Option to check status or start a new mission
4. Conversation history loads from SQLite

### 6.3 On Browser Close

1. No immediate action (no heartbeat mechanism in v1)
2. Next page load checks for stale running missions
3. User is informed and can check status or start fresh

---

## 7. Metrics/Status Always Visible

### 7.1 Header Bar

| Item | Source |
|------|--------|
| **Session ID** | Session model |
| **Mission status** | Current mission status |
| **Elapsed time** | Mission start time |
| **Model** | Model policy (from self_state.json) |
| **Connection** | SSE connection status |

### 7.2 Mission Progress Panel

| Item | Source |
|------|--------|
| **Current tool** | Last tool_start event |
| **Tools executed** | Tool execution events count |
| **Progress bar** | Mission progress (0-100%) |
| **Estimated time** | Based on average tool durations |

### 7.3 Evidence Panel (collapsible)

| Item | Source |
|------|--------|
| **Total evidence entries** | meta_evidence.jsonl line count |
| **Recent entries** | Last 10 evidence entries |
| **Session evidence count** | Evidence entries for current session |

---

## 8. Anti-Patterns — What NOT to Build

### 8.1 Do NOT Build Yet

1. **React/Vue/Angular frontend** — Overkill for v1. Vanilla HTML/JS is sufficient.
2. **WebSocket connections** — SSE is sufficient for v1. WebSockets add complexity.
3. **Multi-tenant support** — This is a single-user operational interface.
4. **Authentication/authorization** — Local dev machine, no security boundary needed.
5. **Mobile responsive design** — Desktop-only for v1.
6. **Real-time collaboration** — Single user only.
7. **Plugin system** — Tools are already registered in the orchestrator.
8. **Custom theme system** — Use a simple dark theme, no customization needed.
9. **Database migrations** — SQLite with simple schema, no migrations needed.
10. **Containerization** — Local dev machine, no deployment needed yet.

### 8.2 Do NOT Over-Engineer

1. **No microservices** — Single FastAPI process.
2. **No message queues** — asyncio.create_task() is sufficient.
3. **No caching layer** — SQLite is fast enough for session data.
4. **No CDN** — Local dev machine.
5. **No CI/CD** — Manual deployment to local machine.

---

## 9. What Can Wait Until Phase 2

1. **WebSocket upgrade** — SSE is sufficient for v1
2. **Real-time mission monitoring dashboard** — Basic progress in chat is enough
3. **Multi-session support** — Single session for v1
4. **File diff viewer** — Basic download is enough
5. **Evidence search/query UI** — Basic evidence panel is enough
6. **Mission templates** — User types tasks manually
7. **Scheduled missions** — No scheduling needed
8. **API key management** — Local dev, no auth needed
9. **Usage analytics** — Not a product
10. **Mobile support** — Desktop only

---

## 10. Technology Stack Summary

| Component | Technology | Version | Reason |
|-----------|-----------|---------|--------|
| **Backend** | FastAPI | latest | Async, SSE support, production-ready |
| **Frontend** | Vanilla HTML/JS/CSS | — | Minimal, no framework overhead |
| **Database** | SQLite | — | Simple, file-based, no server |
| **Streaming** | Server-Sent Events | — | Built into FastAPI |
| **Task queue** | asyncio.create_task() | — | Built into Python |
| **File storage** | Filesystem | — | Simple, no blob storage needed |
| **Evidence** | JSONL file | — | Already exists, append-only |

---

## 11. File Structure

```
C:\ProjectS-Unified\
├── interactive_layer\
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── sessions.py              # Session manager
│   ├── missions.py              # Mission executor
│   ├── files.py                 # File handler
│   ├── evidence.py              # Evidence query
│   ├── models.py                # Pydantic models
│   ├── templates\
│   │   └── index.html           # Main UI
│   └── static\
│       ├── style.css            # Styles
│       └── app.js               # Frontend logic
├── uploads\                     # Upload directory
├── outputs\                     # Output directory
└── PROJECT_S_INTERACTIVE_LAYER_*.md  # Architecture docs
```

---

## 12. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **SAI timeout kills mission** | Medium | Increase timeout, add retry logic |
| **SSE connection drops** | Low | Auto-reconnect on page refresh |
| **SQLite concurrent writes** | Low | Single-writer model (asyncio) |
| **Large file uploads** | Low | Size limit (10MB) in v1 |
| **Memory leak in session storage** | Medium | Session TTL (24 hours) |
| **LLM API rate limiting** | Medium | Queue missions, show wait time |
| **Browser automation hangs** | High | Strict timeout (180s), kill on timeout |

---

*End of architecture document.*
*Next: V1 screen plan (PROJECT_S_INTERACTIVE_LAYER_V1_SCREEN_PLAN_20260517.md)*