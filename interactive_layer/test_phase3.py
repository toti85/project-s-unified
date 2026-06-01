#!/usr/bin/env python3
"""Phase 3 tests - SSE streaming for mission progress.

Tests:
A. SSE route validation: nonexistent mission -> error event
B. Initial snapshot: create mission, connect stream, first event has state
C. Live transition stream: manual transitions -> stream emits each state
D. Terminal completion: stream emits terminal marker and closes
E. Already-terminal mission: stream immediately emits terminal info
F. Heartbeat test
"""

import json
import sys
import time
import threading
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


def open_sse_stream(mission_id, timeout=15):
    """Open SSE stream and read events until timeout or stream closes."""
    url = BASE + "/api/missions/" + mission_id + "/stream"
    req = urllib.request.Request(url)
    events = []
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        buffer = b""
        while True:
            chunk = resp.read(1)
            if not chunk:
                break
            buffer += chunk
            while b"\n\n" in buffer:
                event_str, buffer = buffer.split(b"\n\n", 1)
                event_str = event_str.decode("utf-8", errors="replace")
                event_type = None
                data_obj = None
                for line in event_str.split("\n"):
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        try:
                            data_obj = json.loads(line[6:])
                        except json.JSONDecodeError:
                            data_obj = {"raw": line[6:]}
                if event_type and data_obj:
                    events.append({"event": event_type, "data": data_obj})
    except urllib.error.HTTPError as e:
        events.append({"event": "error", "data": {"http_status": e.code}})
    except Exception:
        pass
    return events


def main():
    print("=" * 60)
    print("PHASE 3 TESTS - SSE Streaming")
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

    # A. SSE route validation
    print("\n=== A. SSE Route Validation ===")
    events = open_sse_stream("nonexistent-mission-id", timeout=5)
    has_error = any(e["event"] == "error" for e in events)
    check("Nonexistent mission -> error event", has_error,
          "events=" + str([e["event"] for e in events]))

    # B. Initial snapshot
    print("\n=== B. Initial Snapshot ===")
    code, session = api("POST", "/api/sessions", {"user_id": "toti"})
    sid = session["session_id"]
    code, mission = api("POST", "/api/missions", {
        "user_id": "toti",
        "session_id": sid,
        "task": "Phase 3 SSE test - initial snapshot",
    })
    mid = mission["mission_id"]
    check("Mission created", code == 200, "state=" + mission["state"])

    events = open_sse_stream(mid, timeout=8)
    check("SSE stream received events", len(events) > 0, "event_count=" + str(len(events)))

    if events:
        first_event = events[0]
        check("First event is mission_state", first_event["event"] == "mission_state",
              "event=" + first_event["event"])
        check("First event has QUEUED state",
              first_event["data"].get("state") == "QUEUED",
              "state=" + str(first_event["data"].get("state")))
        check("First event has is_initial=True",
              first_event["data"].get("is_initial") == True,
              "is_initial=" + str(first_event["data"].get("is_initial")))

    # C. Live transition stream
    print("\n=== C. Live Transition Stream ===")
    code, mission2 = api("POST", "/api/missions", {
        "user_id": "toti",
        "session_id": sid,
        "task": "Phase 3 SSE test - live transitions",
    })
    mid2 = mission2["mission_id"]
    check("Live transition mission created", code == 200, "state=" + mission2["state"])

    stream_events = []
    stream_lock = threading.Lock()

    def stream_worker():
        evts = open_sse_stream(mid2, timeout=20)
        with stream_lock:
            stream_events.extend(evts)

    t = threading.Thread(target=stream_worker, daemon=True)
    t.start()
    time.sleep(2)

    for state in ["PLANNING", "EXECUTING", "SYNTHESIZING", "WRITING", "COMPLETE"]:
        code, result = api("PATCH", "/api/missions/" + mid2 + "/state", {"state": state})
        if code == 200:
            time.sleep(1.5)

    t.join(timeout=25)

    with stream_lock:
        all_events = stream_events[:]

    event_types = [e["event"] for e in all_events]
    states_seen = [e["data"].get("state") for e in all_events if e["event"] == "mission_state"]

    check("Stream received events", len(all_events) > 0, "event_count=" + str(len(all_events)))
    check("Stream has PLANNING", "PLANNING" in states_seen, "states=" + str(states_seen))
    check("Stream has EXECUTING", "EXECUTING" in states_seen, "states=" + str(states_seen))
    check("Stream has COMPLETE", "COMPLETE" in states_seen, "states=" + str(states_seen))
    check("Stream has terminal event", "mission_terminal" in event_types,
          "events=" + str(event_types))

    # D. Already-terminal mission
    print("\n=== D. Already-Terminal Mission ===")
    code, mission3 = api("POST", "/api/missions", {
        "user_id": "toti",
        "session_id": sid,
        "task": "Phase 3 SSE test - already terminal",
    })
    mid3 = mission3["mission_id"]

    for s in ["PLANNING", "EXECUTING", "SYNTHESIZING", "WRITING", "COMPLETE"]:
        api("PATCH", "/api/missions/" + mid3 + "/state", {"state": s})

    events = open_sse_stream(mid3, timeout=8)
    event_types = [e["event"] for e in events]
    states = [e["data"].get("state") for e in events if e["event"] == "mission_state"]

    check("Terminal mission stream has events", len(events) > 0, "event_count=" + str(len(events)))
    check("Terminal mission has COMPLETE snapshot", "COMPLETE" in states, "states=" + str(states))
    check("Terminal mission has terminal event", "mission_terminal" in event_types,
          "events=" + str(event_types))

    terminal_events = [e for e in events if e["event"] == "mission_terminal"]
    if terminal_events:
        te = terminal_events[0]
        check("Terminal event has success=True", te["data"].get("success") == True,
              "success=" + str(te["data"].get("success")))
        check("Terminal event has final_output_available",
              te["data"].get("final_output_available") == False,
              "final_output_available=" + str(te["data"].get("final_output_available")))

    # E. Heartbeat test
    print("\n=== E. Heartbeat Test ===")
    code, mission4 = api("POST", "/api/missions", {
        "user_id": "toti",
        "session_id": sid,
        "task": "Phase 3 SSE test - heartbeat",
    })
    mid4 = mission4["mission_id"]

    api("PATCH", "/api/missions/" + mid4 + "/state", {"state": "PLANNING"})
    api("PATCH", "/api/missions/" + mid4 + "/state", {"state": "EXECUTING"})

    events = open_sse_stream(mid4, timeout=18)
    event_types = [e["event"] for e in events]

    check("Stream has heartbeat", "heartbeat" in event_types,
          "events=" + str(event_types))

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 3 TESTS: " + str(passed) + " PASS, " + str(failed) + " FAIL")
    print("=" * 60)

    if failed == 0:
        print("\n  VERDICT: ALL PASS")
    else:
        print("\n  VERDICT: " + str(failed) + " TESTS FAILED")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)