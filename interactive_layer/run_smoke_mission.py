#!/usr/bin/env python3
"""Phase 2 real SAI smoke mission test."""

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
    print("PHASE 2 REAL SAI SMOKE MISSION")
    print("=" * 60)

    # Create session
    print("\n=== 1. Create Session ===")
    code, session = api("POST", "/api/sessions", {"user_id": "toti"})
    sid = session["session_id"]
    print(f"  Session: {code}, id={sid}")
    assert code == 200

    # Smoke mission prompt
    smoke_prompt = (
        "Sorold fel 5 pontban röviden mit csinal a Project-S rendszer, "
        "csak a mar birtokodban eso tudas alapjan. Ne keress weben, "
        "ne hasznalj browser_automation-t. Egyszeru synthesis."
    )

    # Send chat request
    print("\n=== 2. Send Smoke Mission ===")
    print(f"  Prompt: {smoke_prompt[:80]}...")
    code, chat = api("POST", "/api/chat", {"session_id": sid, "message": smoke_prompt})
    mid = chat["mission_id"]
    print(f"  Response: {code}, mission_id={mid}")
    print(f"  Message: {chat['response']}")
    assert code == 200
    assert mid is not None
    start_time = time.time()

    # Poll for completion
    print("\n=== 3. Poll Mission Status ===")
    max_wait = 300  # 5 minutes max
    poll_interval = 5
    last_state = None

    while time.time() - start_time < max_wait:
        time.sleep(poll_interval)
        code, status = api("GET", f"/api/chat/mission/{mid}/status")
        current_state = status["state"]

        if current_state != last_state:
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] State: {current_state}, progress: {status['progress']}")
            last_state = current_state

        if status["task_complete"]:
            elapsed = int(time.time() - start_time)
            print(f"\n  Mission completed in {elapsed}s")
            break
    else:
        print("\n  TIMEOUT: Mission did not complete within 5 minutes")

    # Final status
    print("\n=== 4. Final Status ===")
    code, status = api("GET", f"/api/chat/mission/{mid}/status")
    print(f"  State: {status['state']}")
    print(f"  Progress: {status['progress']}")
    print(f"  Error: {status.get('error', 'none')}")

    # Get full mission detail
    print("\n=== 5. Full Mission Detail ===")
    code, mission = api("GET", f"/api/missions/{mid}")
    print(f"  Mission state: {mission['state']}")
    print(f"  Task: {mission['task'][:60]}...")
    print(f"  Progress: {mission['progress']}")
    print(f"  Result preview: {str(mission.get('result', '')[:300])}...")
    print(f"  Error: {mission.get('error', 'none')}")
    print(f"  State history ({len(mission['state_history'])} entries):")
    for h in mission["state_history"]:
        print(f"    {h['state']} at {h['timestamp']}")

    # Summary
    print("\n" + "=" * 60)
    print("SMOKE MISSION SUMMARY")
    print("=" * 60)
    print(f"  Mission ID: {mid}")
    print(f"  Final state: {status['state']}")
    print(f"  Duration: ~{int(time.time() - start_time)}s")
    print(f"  Has result: {bool(mission.get('result'))}")
    print(f"  Has error: {bool(mission.get('error'))}")

    if status["state"] == "COMPLETE":
        print("\n  VERDICT: SMOKE MISSION PASSED")
    elif status["state"] == "FAILED":
        print(f"\n  VERDICT: SMOKE MISSION FAILED - {mission.get('error', 'unknown')}")
    else:
        print(f"\n  VERDICT: SMOKE MISSION INCOMPLETE (state={status['state']})")

    print("=" * 60)
    return mid, status["state"]


if __name__ == "__main__":
    mid, state = main()