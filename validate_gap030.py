#!/usr/bin/env python3
"""GAP_030 Live Validation Script.

Runs from the Project-S root directory, patches DEFAULT_TIMEOUT to 30s,
then runs a mission that triggers replan cycles to verify global deadline.
"""

import sys
import os
import time

# Ensure Project-S root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

BASE_URL = "http://localhost:8000"

def patch_timeout():
    """Patch DEFAULT_TIMEOUT to 30s for testing."""
    import interactive_layer.sai_runner as sr
    original_timeout = sr.DEFAULT_TIMEOUT
    sr.DEFAULT_TIMEOUT = 30
    print(f"Patched DEFAULT_TIMEOUT: {original_timeout} -> 30")
    return original_timeout

def restore_timeout(original):
    """Restore original DEFAULT_TIMEOUT."""
    import interactive_layer.sai_runner as sr
    sr.DEFAULT_TIMEOUT = original
    print(f"Restored DEFAULT_TIMEOUT: 30 -> {original}")

def create_session():
    """Create a test session."""
    resp = requests.post(f"{BASE_URL}/api/sessions", json={
        "user_id": "gap030_test",
        "metadata": {"test": "gap030_validation"}
    })
    resp.raise_for_status()
    data = resp.json()
    print(f"Session created: {data['session_id']}")
    return data['session_id']

def chat_mission(session_id, prompt):
    """Launch a SAI mission via /api/chat."""
    resp = requests.post(f"{BASE_URL}/api/chat", json={
        "session_id": session_id,
        "message": prompt,
        "user_id": "gap030_test"
    })
    resp.raise_for_status()
    data = resp.json()
    print(f"Mission launched: {data['mission_id']}")
    return data['mission_id']

def poll_mission(mission_id, max_wait=120):
    """Poll mission until terminal or timeout."""
    start = time.time()
    states = []
    while time.time() - start < max_wait:
        try:
            resp = requests.get(
                f"{BASE_URL}/api/chat/mission/{mission_id}/status",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                state = data.get('state', 'UNKNOWN')
                progress = data.get('progress', 0)
                states.append((state, progress))
                print(f"  [{int(time.time()-start)}s] State: {state}, Progress: {progress}")
                if state in ('COMPLETE', 'FAILED', 'TIMEOUT'):
                    return data, states
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)
    return None, states

def main():
    print("=" * 60)
    print("  GAP_030 LIVE VALIDATION")
    print("  Testing: Global deadline enforcement with 30s timeout")
    print("=" * 60)

    # Patch timeout
    original_timeout = patch_timeout()

    try:
        # Create session
        print("\n[1] Creating session...")
        session_id = create_session()

        # Launch mission with a prompt likely to trigger replans
        print("\n[2] Launching mission (prompt triggers replan cycles)...")
        mission_id = chat_mission(session_id,
            "Write 3 short sentences about why documentation is important.")

        # Poll mission
        print("\n[3] Polling mission status (max 120s)...")
        result, states = poll_mission(mission_id, max_wait=120)

        # Check result
        print("\n[4] Results:")
        if result:
            final_state = result.get('state', 'UNKNOWN')
            error = result.get('error', '')
            print(f"  Final state: {final_state}")
            print(f"  Error: {error[:100] if error else 'None'}")
            print(f"  Total states observed: {len(states)}")

            # Check for replan cycles
            replan_count = sum(1 for s, _ in states if s == 'REPLAN')
            print(f"  Replan transitions observed: {replan_count}")

            # Verify global deadline behavior
            if final_state == 'TIMEOUT':
                print("\n  *** SUCCESS: Mission reached TIMEOUT terminal state ***")
                elapsed = len(states) * 5  # approximate
                print(f"  Timeout occurred after ~{elapsed}s (expected ~30s)")
                if 20 <= elapsed <= 90:
                    print("  *** SUCCESS: Timeout occurred within expected window ***")
                else:
                    print("  WARNING: Timeout outside expected window")
            elif final_state == 'EXECUTING':
                print("\n  *** FAILURE: Mission stuck in EXECUTING ***")
            else:
                print(f"\n  State: {final_state} (not TIMEOUT)")
        else:
            print("  Mission did not reach terminal state within 120s")
            print("  *** FAILURE: Mission may be stuck ***")

        # Print state history
        print("\n[5] State transition history:")
        for i, (state, progress) in enumerate(states):
            print(f"  {i+1}. {state} (progress: {progress})")

    finally:
        restore_timeout(original_timeout)

    print("\n" + "=" * 60)
    print("  VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()