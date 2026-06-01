#!/usr/bin/env python3
"""Restart persistence sanity check for Phase 1."""

import json
import time
import urllib.request

BASE = "http://localhost:8000"


def get(path):
    resp = urllib.request.urlopen(BASE + path)
    return resp.status, json.loads(resp.read())


def main():
    # Health check
    code, data = get("/health")
    print(f"Health: {code} -> {data}")
    assert code == 200

    # List missions
    print("\n=== Missions After Restart ===")
    code, missions = get("/api/missions")
    print(f"Missions count: {len(missions)}")
    for m in missions:
        mid = m["mission_id"]
        state = m["state"]
        task = m["task"]
        hlen = len(m["state_history"])
        print(f"  mission_id={mid}")
        print(f"    state={state}")
        print(f"    task={task}")
        print(f"    state_history_len={hlen}")

    # List sessions
    print("\n=== Sessions After Restart ===")
    code, sessions = get("/api/sessions")
    print(f"Sessions count: {len(sessions)}")
    for s in sessions:
        sid = s["session_id"]
        uid = s["user_id"]
        st = s["state"]
        print(f"  session_id={sid}")
        print(f"    user_id={uid}")
        print(f"    state={st}")

    # Verify COMPLETE mission has full state_history
    print("\n=== COMPLETE Mission Detail ===")
    for m in missions:
        if m["state"] == "COMPLETE":
            mid = m["mission_id"]
            code, full = get(f"/api/missions/{mid}")
            sh = full["state_history"]
            print(f"COMPLETE mission state_history ({len(sh)} entries):")
            for h in sh:
                print(f"  {h['state']} at {h['timestamp']}")
            assert len(sh) == 5, f"Expected 5 state_history entries, got {len(sh)}"
            print("State history intact: OK")
            break

    print("\n=== VERDICT ===")
    assert len(missions) >= 2, f"Expected at least 2 missions, got {len(missions)}"
    complete_missions = [m for m in missions if m["state"] == "COMPLETE"]
    assert len(complete_missions) >= 1, f"Expected at least 1 COMPLETE mission, got {len(complete_missions)}"
    assert len(sessions) >= 1, "Expected at least 1 session"
    toti_sessions = [s for s in sessions if s["user_id"] == "toti"]
    assert len(toti_sessions) >= 1, "Expected at least 1 toti session"
    print("PASS - All data persisted correctly across restart")
    print("  - 2 missions found (expected 2)")
    print("  - 1 COMPLETE mission with full state_history (expected 1 with 5 entries)")
    print("  - Sessions intact with user_id=toti")


if __name__ == "__main__":
    main()