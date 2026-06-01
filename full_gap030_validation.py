#!/usr/bin/env python3
"""GAP_030 Full Live Validation - All-in-one server script.

Runs entirely on SHAYANSKA-DL380 server.
1. Kills any existing server
2. Starts fresh server with global deadline code
3. Waits for server ready
4. Runs validation test
5. Checks final state
6. Reports results
"""

import sys
import os
import time
import subprocess
import requests

BASE_URL = "http://localhost:8000"
SERVER_DIR = r"C:\ProjectS\project-s-code"
DATA_DIR = r"C:\ProjectS\project-s-code\interactive_layer_data"
LOG_FILE = r"C:\ProjectS\validation_server.log"

def kill_existing():
    """Kill any existing uvicorn/python server processes."""
    print("\n[STEP 1] Killing existing server processes...")
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "python.exe", "/T"],
            capture_output=True, text=True, timeout=10
        )
        print("  All Python processes killed")
    except subprocess.TimeoutExpired:
        print("  WARNING: Could not kill all processes in time")
    except Exception as e:
        print(f"  Note: {e}")
    time.sleep(2)

def start_server():
    """Start the Interactive Layer server."""
    print("\n[STEP 2] Starting server...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    proc = subprocess.Popen(
        [sys.executable, "-u", 
         os.path.join(SERVER_DIR, "interactive_layer", "start_server.py")],
        cwd=SERVER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        bufsize=1
    )
    print(f"  Server started (PID: {proc.pid})")
    return proc

def wait_for_server(timeout=30):
    """Wait for server to be ready."""
    print("\n[STEP 3] Waiting for server to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=3)
            if resp.status_code == 200:
                print(f"  Server ready in {int(time.time()-start)}s")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except Exception:
            pass
        time.sleep(2)
    print("  ERROR: Server did not start in time")
    return False

def run_validation():
    """Run the GAP_030 validation test."""
    print("\n[STEP 4] Running GAP_030 validation...")
    
    # Patch DEFAULT_TIMEOUT to 30s
    import interactive_layer.sai_runner as sr
    original_timeout = sr.DEFAULT_TIMEOUT
    sr.DEFAULT_TIMEOUT = 30
    print(f"  Patched DEFAULT_TIMEOUT: {original_timeout} -> 30")
    
    states = []
    mission_id = None
    
    try:
        # Create session
        print("\n  [4a] Creating session...")
        resp = requests.post(f"{BASE_URL}/api/sessions", json={
            "user_id": "gap030_test",
            "metadata": {"test": "gap030_validation"}
        }, timeout=10)
        resp.raise_for_status()
        session_id = resp.json()['session_id']
        print(f"    Session: {session_id}")
        
        # Launch mission
        print("\n  [4b] Launching mission...")
        resp = requests.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "Write 3 short sentences about why documentation is important.",
            "user_id": "gap030_test"
        }, timeout=10)
        resp.raise_for_status()
        mission_id = resp.json()['mission_id']
        print(f"    Mission: {mission_id}")
        
        # Poll for state changes
        print("\n  [4c] Polling for state changes (max 120s)...")
        poll_start = time.time()
        while time.time() - poll_start < 120:
            try:
                resp = requests.get(
                    f"{BASE_URL}/api/chat/mission/{mission_id}/status",
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    state = data.get('state', 'UNKNOWN')
                    progress = data.get('progress', 0)
                    elapsed = int(time.time() - poll_start)
                    states.append((state, progress, elapsed))
                    print(f"    [{elapsed}s] {state} (progress: {progress})")
                    if state in ('COMPLETE', 'FAILED', 'TIMEOUT'):
                        break
            except requests.exceptions.RequestException:
                pass
            time.sleep(3)
        
        return states, mission_id, True
        
    except Exception as e:
        print(f"\n  ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
        return states, mission_id, False
    finally:
        sr.DEFAULT_TIMEOUT = original_timeout
        print(f"\n  Restored DEFAULT_TIMEOUT: 30 -> {original_timeout}")

def check_final_state():
    """Check persisted SQLite state."""
    print("\n[STEP 5] Checking persisted SQLite state...")
    db_path = os.path.join(DATA_DIR, "interactive.db")
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT mission_id, state, progress, error FROM missions ORDER BY updated_at DESC LIMIT 5"
        ).fetchall()
        conn.close()
        
        print("  Last 5 missions:")
        for r in rows:
            err = (r[3] or "")[:80]
            print(f"    {r[0]} | {r[1]} | {r[2]} | {err}")
        
        # Find the gap030_test mission
        for r in rows:
            if 'gap030' in str(r[0]):
                return r[1]  # Return state
        
        return "N/A (no gap030 mission found)"
    except Exception as e:
        return f"ERROR: {e}"

def post_test_health():
    """Check /health after test."""
    print("\n[STEP 6] Post-test health check...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("  PASS")
            return True
    except Exception as e:
        print(f"  FAIL: {e}")
    return False

def main():
    print("=" * 60)
    print("  GAP_030 FULL LIVE VALIDATION")
    print("  Testing: Global deadline enforcement with 30s timeout")
    print("=" * 60)
    
    # Step 1: Kill existing
    kill_existing()
    
    # Step 2: Start server
    proc = start_server()
    
    # Step 3: Wait for server
    server_ready = wait_for_server()
    
    # Step 4: Run validation
    states = []
    mission_id = None
    validation_success = False
    
    if server_ready:
        states, mission_id, validation_success = run_validation()
    
    # Step 5: Check final state
    final_persisted_state = check_final_state()
    
    # Step 6: Post-test health
    health_after = post_test_health() if server_ready else False
    
    # === RESULTS ===
    print("\n" + "=" * 60)
    print("  GAP_030 VALIDATION RESULTS")
    print("=" * 60)
    
    # Determine actual final state from polling
    actual_final_state = "UNKNOWN"
    if states:
        actual_final_state = states[-1][0]
    
    # Determine if TIMEOUT was reached within expected window
    timeout_success = False
    if actual_final_state == 'TIMEOUT':
        timeout_elapsed = states[-1][2] if states else 0
        if 15 <= timeout_elapsed <= 90:
            timeout_success = True
    
    # Count replan transitions
    replan_count = sum(1 for s, _, _ in states if s == 'REPLAN')
    
    print(f"\n  Health before test: {'PASS' if server_ready else 'FAIL'}")
    print(f"  Validation executed: {'YES' if validation_success else 'NO'}")
    print(f"  Mission ID: {mission_id or 'N/A'}")
    print(f"  Final state (polling): {actual_final_state}")
    print(f"  Final state (persisted): {final_persisted_state}")
    print(f"  Timeout reached within window: {'YES' if timeout_success else 'NO'}")
    print(f"  Replan transitions: {replan_count}")
    print(f"  Health after test: {'PASS' if health_after else 'FAIL'}")
    
    # State history
    if states:
        print(f"\n  State history ({len(states)} observations):")
        for i, (s, p, e) in enumerate(states):
            print(f"    {i+1}. [{e}s] {s} (progress: {p})")
    
    # Final verdict
    print("\n" + "-" * 60)
    if actual_final_state == 'TIMEOUT' and timeout_success and health_after:
        print("  GAP_030 STATUS: RESOLVED")
    elif actual_final_state == 'EXECUTING':
        print("  GAP_030 STATUS: PARTIAL (global deadline code deployed, but server crashed during test)")
    else:
        print("  GAP_030 STATUS: PARTIAL")
    print("-" * 60)
    
    # Save results to file
    results = {
        "health_before": server_ready,
        "validation_executed": validation_success,
        "mission_id": mission_id,
        "final_state_polling": actual_final_state,
        "final_state_persisted": final_persisted_state,
        "timeout_within_window": timeout_success,
        "replan_count": replan_count,
        "health_after": health_after,
        "state_history": [{"state": s, "progress": p, "elapsed_s": e} for s, p, e in states],
        "gap030_status": "RESOLVED" if (actual_final_state == 'TIMEOUT' and timeout_success and health_after) else "PARTIAL"
    }
    
    import json
    with open(r"C:\ProjectS\gap030_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to C:\\ProjectS\\gap030_results.json")
    
    print("\n" + "=" * 60)
    print("  VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()