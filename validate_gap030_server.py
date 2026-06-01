0#!/usr/bin/env python3
"""GAP_030 Live Validation - Server-side runner.

Runs from C:\ProjectS\project-s-code directory.
Patches DEFAULT_TIMEOUT to 30s, launches a mission, polls until terminal.
"""

import sys
import os
import time

os.chdir(r"C:\ProjectS\project-s-code")
sys.path.insert(0, r"C:\ProjectS\project-s-code")

import requests

BASE_URL = "http://localhost:8000"

def main():
    print("=" * 60)
    print("  GAP_030 LIVE VALIDATION")
    print("  Testing: Global deadline enforcement with 30s timeout")
    print("=" * 60)

    # Patch timeout
    import interactive_layer.sai_runner as sr
    original_timeout = sr.DEFAULT_TIMEOUT
    sr.DEFAULT_TIMEOUT = 30
    print(f"\nPatched DEFAULT_TIMEOUT: {original_timeout} -> 30")

    try:
        # Create session
        print("\n[1] Creating session...")
        resp = requests.post(f"{BASE_URL}/api/sessions", json={
            "user_id": "gap030_test",
            "metadata": {"test": "gap030_validation"}
        }, timeout=10)
        resp.raise_for_status()
        session_id = resp.json()['session_id']
        print(f"  Session: {session_id}")

        # Launch mission
        print("\n[2] Launching mission...")
        resp = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Write 3 short sentences about why documentation is important.",
            "user_id": "gap030_test"
        }, timeout=10)
        resp.raise_for_status()
        mission_id = resp.json()['mission_id']
        print(f"  Mission: {mission_id}")

        # Poll
        print("\n[3] Polling (max 120s)...")
        start = time.time()
        states = []
        while time.time() - start < 120:
            try:
                resp = requests.get(
                    f"{BASE_URL}/api/chat/mission/{mission_id}/status",
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    state = data.get('state', 'UNKNOWN')
                    progress = data.get('progress', 0)
                    states.append((state, progress, int(time.time()-start)))
                    print(f"  [{int(time.time()-start)}s] {state} (progress: {progress})")
                    if state in ('COMPLETE', 'FAILED', 'TIMEOUT'):
                        break
            except requests.exceptions.RequestException:
                pass
            time.sleep(5)

        # Results
        print("\n[4] RESULTS:")
        if states:
            final = states[-1]
            final_state = final[0]
            elapsed = final[2]
            print(f"  Final state: {final_state}")
            print(f"  Elapsed: ~{elapsed}s")
            print(f"  Total observations: {len(states)}")

            replan_count = sum(1 for s, _, _ in states if s == 'REPLAN')
            print(f"  Replan transitions: {replan_count}")

            if final_state == 'TIMEOUT':
                print("\n  *** SUCCESS: TIMEOUT reached ***")
                if 20 <= elapsed <= 90:
                    print("  *** SUCCESS: Within expected 30s window ***")
                else:
                    print("  WARNING: Outside expected window")
            elif final_state == 'EXECUTING':
                print("\n  *** FAILURE: Stuck in EXECUTING ***")
            else:
                print(f"\n  State: {final_state}")
        else:
            print("  No states observed")

        # State history
        print("\n[5] State history:")
        for i, (s, p, e) in enumerate(states):
            print(f"  {i+1}. [{e}s] {s} (progress: {p})")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sr.DEFAULT_TIMEOUT = original_timeout
        print(f"\nRestored DEFAULT_TIMEOUT: 30 -> {original_timeout}")

    print("\n" + "=" * 60)
    print("  VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()