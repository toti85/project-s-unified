#!/usr/bin/env python3
"""Phase 2.1 tests - State integrity + input validation."""

import json
import sys
import time
import urllib.request
import urllib.error

# Set stdout to UTF-8 to avoid cp1251 encoding errors
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"


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


def main():
    print("=" * 60)
    print("PHASE 2.1 TESTS - State Integrity + Input Validation")
    print("=" * 60)

    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            print("  [PASS] " + name + ": " + str(detail))
            passed += 1
        else:
            print("  [FAIL] " + name + ": " + str(detail))
            failed += 1

    # Issue 2: Empty/whitespace prompt validation
    print("\n=== Issue 2: Empty Prompt Validation ===")

    code, session = api("POST", "/api/sessions", {"user_id": "toti"})
    sid = session["session_id"]
    check("Session creation", code == 200, "session_id=" + sid)

    code, missions_before = api("GET", "/api/missions")
    count_before = len(missions_before)

    code, err = api("POST", "/api/chat", {"session_id": sid, "message": ""})
    check("Empty prompt -> 400", code == 400, "HTTP " + str(code) + " detail=" + str(err.get("detail", "")))

    code, err = api("POST", "/api/chat", {"session_id": sid, "message": "   "})
    check("Whitespace prompt -> 400", code == 400, "HTTP " + str(code))

    code, err = api("POST", "/api/chat", {"session_id": sid, "message": "\n"})
    check("Newline prompt -> 400", code == 400, "HTTP " + str(code))

    code, err = api("POST", "/api/chat", {"session_id": sid, "message": "\t"})
    check("Tab prompt -> 400", code == 400, "HTTP " + str(code))

    code, missions_after = api("GET", "/api/missions")
    count_after = len(missions_after)
    check("Mission count unchanged", count_after == count_before,
          "before=" + str(count_before) + " after=" + str(count_after))

    # Issue 1: State transition integrity
    print("\n=== Issue 1: State Transition Integrity ===")

    smoke_prompt = "List 3 bullet points about Project-S. Simple synthesis only."
    code, chat = api("POST", "/api/chat", {"session_id": sid, "message": smoke_prompt})
    mid = chat["mission_id"]
    check("Real mission created", code == 200 and mid is not None, "mission_id=" + str(mid))

    print("\n  Polling for mission completion...")
    for i in range(60):
        time.sleep(3)
        code, status = api("GET", "/api/chat/mission/" + mid + "/status")
        if status["task_complete"]:
            break

    code, mission = api("GET", "/api/missions/" + mid)

    check("Final state is COMPLETE", mission["state"] == "COMPLETE", "state=" + mission["state"])

    sh = mission["state_history"]
    sh_states = [h["state"] for h in sh]
    check("state_history has 3 entries", len(sh) == 3, "states=" + str(sh_states))
    check("state_history has PLANNING", "PLANNING" in sh_states)
    check("state_history has EXECUTING", "EXECUTING" in sh_states)
    check("state_history has COMPLETE", "COMPLETE" in sh_states)

    check("state_history contains COMPLETE entry",
          any(h["state"] == "COMPLETE" for h in sh),
          "sh_states=" + str(sh_states))

    check("Result is non-empty", bool(mission.get("result")),
          "result_length=" + str(len(mission.get("result", ""))))

    check("Error is None", mission.get("error") is None,
          "error=" + str(mission.get("error")))

    # Regression: validate_phase1.py still passes
    print("\n=== Regression: Phase 1 Full Path ===")
    code, mission2 = api("POST", "/api/missions", {
        "user_id": "toti",
        "session_id": sid,
        "task": "Phase 2.1 regression test",
    })
    mid2 = mission2["mission_id"]
    check("Regression mission created", code == 200, "state=" + mission2["state"])

    transitions = [
        ("QUEUED", "PLANNING"),
        ("PLANNING", "EXECUTING"),
        ("EXECUTING", "SYNTHESIZING"),
        ("SYNTHESIZING", "WRITING"),
        ("WRITING", "COMPLETE"),
    ]
    for from_s, to_s in transitions:
        code, result = api("PATCH", "/api/missions/" + mid2 + "/state", {"state": to_s})
        ok = code == 200 and result["state"] == to_s
        check(from_s + " -> " + to_s, ok, "HTTP " + str(code))

    print("\n" + "=" * 60)
    print("PHASE 2.1 TESTS: " + str(passed) + " PASS, " + str(failed) + " FAIL")
    print("=" * 60)

    if failed == 0:
        print("\n  VERDICT: ALL PASS")
    else:
        print("\n  VERDICT: " + str(failed) + " TESTS FAILED")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)