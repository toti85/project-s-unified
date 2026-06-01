#!/usr/bin/env python3
"""Real SAI+SSE smoke mission test.

Creates a mission via /api/chat, subscribes to SSE stream,
and verifies the full lifecycle.
"""

import json
import sys
import time
import urllib.request
import urllib.error

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


def open_sse_stream(mission_id, timeout=120):
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
    print("REAL SAI + SSE SMOKE MISSION")
    print("=" * 60)

    # 1. Create session
    print("\n=== 1. Create Session ===")
    code, session = api("POST", "/api/sessions", {"user_id": "toti"})
    sid = session["session_id"]
    print("  Session: " + sid)
    assert code == 200

    # 2. Create SAI mission via /api/chat
    print("\n=== 2. Create SAI Mission via /api/chat ===")
    prompt = "Write 3 short bullet points about Project-S. Simple synthesis only."
    print("  Prompt: " + prompt)

    start_time = time.time()
    code, chat = api("POST", "/api/chat", {"session_id": sid, "message": prompt})
    elapsed = time.time() - start_time

    mid = chat["mission_id"]
    print("  Response: " + str(chat["response"]))
    print("  Mission ID: " + mid)
    print("  Time to return: " + str(round(elapsed, 2)) + "s")
    assert code == 200
    assert mid is not None

    # 3. Open SSE stream
    print("\n=== 3. Open SSE Stream ===")
    events = open_sse_stream(mid, timeout=120)
    stream_duration = time.time() - start_time

    print("  Total events received: " + str(len(events)))
    event_types = [e["event"] for e in events]
    states = [e["data"].get("state") for e in events if e["event"] == "mission_state"]

    print("  Event types: " + str(event_types))
    print("  States seen: " + str(states))
    print("  Stream duration: " + str(round(stream_duration, 2)) + "s")

    # 4. Check final mission state
    print("\n=== 4. Final Mission State ===")
    code, mission = api("GET", "/api/missions/" + mid)
    print("  State: " + mission["state"])
    print("  Progress: " + str(mission.get("progress")))
    print("  Has result: " + str(bool(mission.get("result"))))
    print("  Error: " + str(mission.get("error")))

    if mission.get("result"):
        result_preview = mission["result"][:300]
        print("  Result preview: " + result_preview)

    # 5. Summary
    print("\n" + "=" * 60)
    print("SAI+SSE SMOKE MISSION SUMMARY")
    print("=" * 60)
    print("  Mission ID: " + mid)
    print("  Final state: " + mission["state"])
    print("  Total duration: " + str(round(time.time() - start_time, 2)) + "s")
    print("  SSE events: " + str(len(events)))
    print("  Has terminal event: " + str("mission_terminal" in event_types))
    print("  Has result: " + str(bool(mission.get("result"))))

    if mission["state"] == "COMPLETE" and mission.get("result"):
        print("\n  VERDICT: SAI+SSE SMOKE MISSION PASSED")
        return True
    else:
        print("\n  VERDICT: SAI+SSE SMOKE MISSION INCOMPLETE")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)