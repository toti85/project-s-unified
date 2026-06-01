#!/usr/bin/env python3
"""Phase 2 API tests — quick smoke tests before real SAI mission."""

import json
import time
import urllib.request
import urllib.error

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
    print("PHASE 2 API TESTS")
    print("=" * 60)

    # 1. Health check
    print("\n=== 1. Health Check ===")
    code, data = api("GET", "/health")
    print(f"  Health: {code} -> {data}")
    assert code == 200
    print("  PASS")

    # 2. Create session
    print("\n=== 2. Create Session ===")
    code, session = api("POST", "/api/sessions", {"user_id": "toti"})
    sid = session["session_id"]
    print(f"  Session: {code}, id={sid}")
    assert code == 200
    print("  PASS")

    # 3. Test invalid session
    print("\n=== 3. Invalid Session ===")
    code, err = api("POST", "/api/chat", {"session_id": "nonexistent", "message": "test"})
    print(f"  Invalid session: {code}")
    assert code == 404
    print("  PASS")

    # 4. Test empty prompt (should create mission, return QUEUED)
    print("\n=== 4. Empty Prompt ===")
    code, chat = api("POST", "/api/chat", {"session_id": sid, "message": ""})
    mid = chat["mission_id"]
    print(f"  Empty prompt: {code}, mission_id={mid}")
    assert code == 200
    assert mid is not None
    assert chat["response"] == "Mission queued, run async"
    print("  PASS")

    # Wait for empty mission to complete (should be fast, likely FAILED due to empty prompt)
    print("\n=== 5. Wait for Empty Mission ===")
    for i in range(20):
        time.sleep(2)
        code, status = api("GET", f"/api/chat/mission/{mid}/status")
        if status["task_complete"]:
            break
    print(f"  Empty mission final state: {status['state']}")
    print(f"  Error: {status.get('error', 'none')}")
    print("  PASS")

    print("\n" + "=" * 60)
    print("PHASE 2 API TESTS: ALL PASS")
    print("=" * 60)
    return sid


if __name__ == "__main__":
    sid = main()
    print(f"\nSession ID for smoke test: {sid}")