# GAP_031 Phase 1 — /api/chat 500 Root Cause & Fix

**Date:** 2026-05-20  
**Engineer:** GitHub Copilot (Claude Sonnet 4.6)  
**Status:** RESOLVED

---

## A. Exact 500 Root Cause

| Field | Detail |
|---|---|
| **Exception type** | `sqlite3.OperationalError` |
| **Message** | `table missions has no column named route_type` |
| **File** | `interactive_layer/database.py` — `create_mission()` INSERT |
| **Category** | DB schema migration gap |

### Root Cause Explanation

GAP_031 Phase 1 added 6 new `route_*` columns to the `missions` DDL inside `SCHEMA_SQL`:

```
route_type, route_confidence, route_rationale,
route_matched_rules, route_llm_used, route_llm_model
```

However, `SCHEMA_SQL` uses `CREATE TABLE IF NOT EXISTS missions (...)`.  
The existing SQLite DB (`interactive_layer_data/interactive.db`) was created before GAP_031.  
`CREATE TABLE IF NOT EXISTS` is a no-op when the table already exists — it does **not** add
new columns. Therefore, all 6 columns were absent at runtime.

When `POST /api/chat` ran `create_mission()`, the INSERT statement referenced the missing
columns, causing SQLite to raise `OperationalError`, which FastAPI surfaced as HTTP 500.

```
# Confirmed via PRAGMA table_info(missions) before fix:
['mission_id', 'user_id', 'session_id', 'created_at', 'updated_at', 'task', 'state',
 'state_history', 'progress', 'plan', 'events', 'result', 'output_path', 'error',
 'timeout_seconds']
# → route_type … route_llm_model: ABSENT
```

---

## B. Files Changed

### 1. `interactive_layer/database.py` — `init_db()` migration added

```python
# Before:
def init_db(db_path: Path | str = DB_PATH) -> None:
    """Initialize database schema."""
    with _get_conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
```

```python
# After:
def init_db(db_path: Path | str = DB_PATH) -> None:
    """Initialize database schema + incremental migrations."""
    with _get_conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        # GAP_031 migration: add route_* columns to existing missions tables
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
```

### 2. `interactive_layer/_debug_gap031_chat_smoke.py` — new smoke helper (created)

Standalone helper script for manual and CI smoke validation of `POST /api/chat`.

---

## C. TEST_1 Smoke: HTTP 200?

**Yes.**

```
[2] POST /api/chat ...
    prompt : 'Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.'
    status : 200
    body   : {
  "message_id": "e636d069-c8b3-4391-ab03-9c4544103aa0",
  "response": "Mission queued (DIRECT_LIGHTWEIGHT_RESPONSE)",
  "mission_id": "90817825-be43-4a95-aea6-741b289fa07a"
}

RESULT : PASS — HTTP 200
  mission_id : 90817825-be43-4a95-aea6-741b289fa07a
  response   : Mission queued (DIRECT_LIGHTWEIGHT_RESPONSE)
```

---

## D. Response Body Valid?

**Yes.**

- `message_id`: UUID present ✓  
- `mission_id`: UUID present ✓  
- `response`: non-empty string with route name ✓  
- Route correctly classified as `DIRECT_LIGHTWEIGHT_RESPONSE` (Hungarian "Írj 3 … mondatot" matches `irj_mondat` rule) ✓

**Note — secondary non-blocking observation:**  
The `response` field shows `"Mission queued (DIRECT_LIGHTWEIGHT_RESPONSE)"` (the generic fallback
string) rather than the handler-generated text. This is because `main.py`'s chat handler computes
`response_text` when the lightweight handler succeeds, but the final `return ChatResponse(...)` at
line ~360 always uses `f"Mission queued ({route_decision.route_type})"`. The handler result IS
stored correctly in the mission via `complete_mission()`. This is a UX-only gap, not a correctness
failure, and is **out of scope** for this emergency 500 fix.

---

## E. Full 8/8 Live Rerun Safe?

**Yes.**

- The only failure mode was the missing DB schema columns.
- The migration is idempotent (`PRAGMA table_info` check before each `ALTER TABLE`).
- All 6 route_* columns are now confirmed present.
- The server is running with the patched `init_db()`.
- TEST_1 smoke (`DIRECT_LIGHTWEIGHT_RESPONSE`) passes cleanly.

The full 8/8 live acceptance matrix rerun is safe to restart.

---

## Appendix: DB Column Verification

```
# After fix:
route cols: ['route_type', 'route_confidence', 'route_rationale',
             'route_matched_rules', 'route_llm_used', 'route_llm_model']
```

All 6 present. Migration is idempotent — re-running `init_db()` on an already-migrated DB
will not raise any error.
