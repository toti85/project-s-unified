#!/usr/bin/env python3
"""Phase 1 End-to-End Backend Validation Script.

Tests all Phase 1 API endpoints and SQLite persistence.
"""

import json
import pathlib
import sqlite3
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8000"
RESULTS = []


def api(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def record(name, passed, detail):
    RESULTS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}: {detail}")


def main():
    print("=" * 60)
    print("PHASE 1 END-TO-END BACKEND VALIDATION")
    print("=" * 60)

    # 1. Health check
    print("\n=== 1. Health Check ===")
    code, data = api("GET", "/health")
    print(f"  GET /health: {code} -> {data}")
    record("Health check", code == 200, str(data))

    # 2. Create session
    print("\n=== 2. Session Creation ===")
    code, session = api("POST", "/api/sessions", {"user_id": "toti"})
    print(f"  POST /api/sessions: {code}")
    print(json.dumps(session, indent=4))
    sid = session["session_id"]
    uid = session["user_id"]
    record("Session creation", code == 200 and uid == "toti", f"session_id={sid}, user_id={uid}")

    time.sleep(0.1)

    # 3. Create mission
    print("\n=== 3. Mission Creation ===")
    code, mission = api(
        "POST",
        "/api/missions",
        {"user_id": "toti", "session_id": sid, "task": "Phase 1 E2E validation test mission"},
    )
    print(f"  POST /api/missions: {code}")
    print(json.dumps(mission, indent=4))
    mid = mission["mission_id"]
    record(
        "Mission creation",
        code == 200 and mission["state"] == "QUEUED",
        f"mission_id={mid}, state={mission['state']}",
    )

    time.sleep(0.1)

    # 4. Full happy path transitions
    print("\n=== 4. Happy Path State Transitions ===")
    transitions = [
        ("QUEUED", "PLANNING"),
        ("PLANNING", "EXECUTING"),
        ("EXECUTING", "SYNTHESIZING"),
        ("SYNTHESIZING", "WRITING"),
        ("WRITING", "COMPLETE"),
    ]
    for idx, (from_s, to_s) in enumerate(transitions):
        code, result = api("PATCH", f"/api/missions/{mid}/state", {"state": to_s})
        hlen = len(result.get("state_history", []))
        ok = code == 200 and result["state"] == to_s and hlen == idx + 1
        print(f"  {from_s} -> {to_s}: {code}, state_history_len={hlen}")
        record(f"{from_s}->{to_s}", ok, f"state={result['state']}, history_len={hlen}")
        time.sleep(0.05)

    # 5. Query mission
    print("\n=== 5. Mission Query ===")
    code, m = api("GET", f"/api/missions/{mid}")
    print(f"  GET /api/missions/{mid}: {code}, state={m['state']}, history_len={len(m['state_history'])}")
    record(
        "Mission GET",
        code == 200 and m["state"] == "COMPLETE" and len(m["state_history"]) == 5,
        f"state={m['state']}, history_len={len(m['state_history'])}",
    )

    code2, s = api("GET", f"/api/missions/{mid}/status")
    print(f"  GET /api/missions/{mid}/status: {code2}, state={s['state']}")
    record("Mission status", code2 == 200 and s["state"] == "COMPLETE", f"state={s['state']}")

    # 6. List missions
    print("\n=== 6. List Missions ===")
    code, listed = api("GET", "/api/missions")
    print(f"  GET /api/missions: {code}, count={len(listed)}")
    record("List missions", code == 200 and len(listed) >= 1, f"count={len(listed)}")

    # 7. Invalid transition test
    print("\n=== 7. Invalid Transition Test ===")
    code, err = api("PATCH", f"/api/missions/{mid}/state", {"state": "PLANNING"})
    print(f"  COMPLETE -> PLANNING: {code}")
    print(json.dumps(err, indent=4))
    # Verify mission is still COMPLETE
    code2, verify = api("GET", f"/api/missions/{mid}")
    still_complete = verify["state"] == "COMPLETE"
    # Check error message contains "terminal" or "Invalid transition"
    error_detail = err.get("detail", "")
    has_terminal_msg = "terminal" in error_detail.lower() or "Invalid transition" in error_detail
    ok = code == 400 and still_complete and has_terminal_msg
    print(f"  Mission still COMPLETE: {still_complete}")
    print(f"  Error message contains 'terminal': {has_terminal_msg}")
    record("Invalid transition rejected", ok, f"HTTP {code}, terminal state message: {has_terminal_msg}")

    # 8. Session query
    print("\n=== 8. Session Query ===")
    code, sess = api("GET", f"/api/sessions/{sid}")
    print(f"  GET /api/sessions/{sid}: {code}, user_id={sess['user_id']}")
    record("Session query", code == 200 and sess["user_id"] == "toti", f"user_id={sess['user_id']}")

    # 9. SQLite inspection
    print("\n=== 9. SQLite Persistence ===")
    # DB is at project root level (same as database.py DB_PATH calculation)
    db_path = pathlib.Path(__file__).parent.parent / "interactive_layer_data" / "interactive.db"
    if not db_path.exists():
        # Try alternate location
        db_path = pathlib.Path("interactive_layer_data/interactive.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    user = conn.execute("SELECT * FROM users WHERE user_id = ?", ("toti",)).fetchone()
    print(f"  User toti: {'FOUND' if user else 'NOT FOUND'}")
    assert user is not None

    sess_db = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (sid,)).fetchone()
    print(f"  Session: user_id={sess_db['user_id']}, state={sess_db['state']}")
    assert sess_db is not None and sess_db["user_id"] == "toti"

    mission_db = conn.execute("SELECT * FROM missions WHERE mission_id = ?", (mid,)).fetchone()
    print(f"  Mission: state={mission_db['state']}, user_id={mission_db['user_id']}")
    assert mission_db is not None and mission_db["state"] == "COMPLETE" and mission_db["user_id"] == "toti"

    sh = json.loads(mission_db["state_history"])
    print(f"  State history: {len(sh)} entries")
    for h in sh:
        print(f"    {h['state']} at {h['timestamp']}")
    assert len(sh) == 5

    events = conn.execute("SELECT * FROM mission_events WHERE mission_id = ? ORDER BY timestamp", (mid,)).fetchall()
    print(f"  Mission events: {len(events)} entries")
    for e in events:
        print(f"    {e['event_type']} at {e['timestamp']}")
    assert len(events) >= 6  # mission_created + 5 state_transitions

    conn.close()
    record("SQLite persistence", True, "user, session, mission, state_history, events all verified")

    # Summary
    print()
    print("=" * 60)
    print("PHASE 1 E2E VALIDATION SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"Results: {passed}/{total} passed")
    for name, ok, detail in RESULTS:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {detail}")

    verdict = "PASS" if passed == total else "PARTIAL" if passed >= total - 1 else "FAIL"
    print(f"\nVerdict: {verdict}")
    return verdict == "PASS"


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)