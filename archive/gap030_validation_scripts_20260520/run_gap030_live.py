#!/usr/bin/env python3
"""GAP_030 DEV Live Global Timeout Validation Script."""

import asyncio
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = "C:\\ProjectS-Unified\\interactive_layer_data\\interactive.db"
TIMEOUT_OVERRIDE = 30  # seconds

def api_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read().decode())

def api_post(path, data):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, json.loads(resp.read().decode())

def patch_default_timeout():
    """Patch DEFAULT_TIMEOUT in sai_runner.py to 30s."""
    sai_path = Path("C:\\ProjectS-Unified\\interactive_layer\\sai_runner.py")
    content = sai_path.read_text()
    content = content.replace("DEFAULT_TIMEOUT = 600", "DEFAULT_TIMEOUT = 30")
    sai_path.write_text(content)
    print(f"  Patched DEFAULT_TIMEOUT to 30 in sai_runner.py")

async def poll_mission(mission_id, max_seconds=90):
    """Poll mission status until terminal or max_seconds."""
    poll_start = time.monotonic()
    count = 0
    state_history = []

    while (time.monotonic() - poll_start) < max_seconds:
        await asyncio.sleep(3)
        count += 1
        try:
            status, data = api_get(f"/api/chat/mission/{mission_id}/status")
            state = data["state"]
            progress = data["progress"]
            elapsed = int(time.monotonic() - poll_start)
            print(f"  [{count}] [{elapsed}s] {state} (progress: {progress})")
            state_history.append(f"{state}|{progress}|{elapsed}")

            if state in ("COMPLETE", "FAILED", "TIMEOUT"):
                print(f"  -> Terminal state reached: {state} at {elapsed}s")
                return state, state_history
        except Exception as e:
            print(f"  Poll error: {e}")

    return "EXECUTING", state_history

def check_sqlite(mission_id):
    """Query SQLite for mission state."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT mission_id, state, progress, error FROM missions WHERE mission_id=?",
        (mission_id,)
    ).fetchall()
    if rows:
        for r in rows:
            print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3] or '(none)'}")
    else:
        print("  Mission not found in DB")

    rows = conn.execute(
        "SELECT mission_id, state, progress FROM missions ORDER BY updated_at DESC LIMIT 5"
    ).fetchall()
    print("  Last 5 missions:")
    for r in rows:
        print(f"    {r[0]} | {r[1]} | {r[2]}")
    conn.close()

async def main():
    print("=" * 60)
    print("  GAP_030 DEV LIVE GLOBAL TIMEOUT VALIDATION")
    print(f"  Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 0: Patch DEFAULT_TIMEOUT
    print(f"\n[0/7] Patching DEFAULT_TIMEOUT to {TIMEOUT_OVERRIDE}s...")
    patch_default_timeout()

    # Step 1: Health check before
    print("\n[1/7] Health check BEFORE test...")
    try:
        status, data = api_get("/health")
        health_before = (status == 200)
        print(f"  Health: PASS ({status})")
    except Exception as e:
        print(f"  Health: FAIL — {e}")
        health_before = False

    # Step 2: Create session + mission
    print(f"\n[2/7] Creating test mission (timeout={TIMEOUT_OVERRIDE}s)...")
    try:
        status, sessions = api_get("/api/sessions")
        session = None
        for s in sessions:
            if s.get("user_id") == "toti":
                session = s
                break
        if not session:
            status, session = api_post("/api/sessions", {
                "user_id": "toti",
                "metadata": {"name": "GAP_030_live_test"}
            })
        session_id = session["session_id"]
        print(f"  Session: {session_id}")
    except Exception as e:
        print(f"  Session creation FAIL: {e}")
        session_id = None

    if session_id:
        prompt = ("Write a very detailed and comprehensive analysis of the history "
                  "of mathematics from ancient times to the modern era. Include at least "
                  "20 paragraphs covering every major discovery, mathematician, and concept. "
                  "Each paragraph should be detailed and thorough, including specific dates, "
                  "names, and mathematical concepts. Be extremely verbose and detailed in your response.")

        try:
            status, result = api_post("/api/chat", {
                "session_id": session_id,
                "message": prompt,
                "user_id": "toti"
            })
            mission_id = result["mission_id"]
            print(f"  Mission: {mission_id}")
        except Exception as e:
            print(f"  Mission creation FAIL: {e}")
            mission_id = None

        if mission_id:
            # Step 3: Poll
            print(f"\n[3/7] Polling mission status (max 90s, timeout={TIMEOUT_OVERRIDE}s)...")
            final_state, state_history = await poll_mission(mission_id, max_seconds=90)

            # Step 4: SQLite
            print("\n[4/7] Checking SQLite DB...")
            check_sqlite(mission_id)

            # Step 5: Stuck check
            print(f"\n[5/7] Stuck EXECUTING check...")
            remained_executing = (final_state == "EXECUTING")
            if remained_executing:
                print("  REMAINED EXECUTING: YES (timeout may not have fired within 90s)")
            else:
                print(f"  REMAINED EXECUTING: NO (reached terminal state: {final_state})")

            # Step 6: Health after
            print(f"\n[6/7] Health check AFTER test...")
            try:
                status, data = api_get("/health")
                health_after = (status == 200)
                print(f"  Health: PASS ({status})")
            except Exception as e:
                print(f"  Health: FAIL")
                health_after = False

            # Step 7: Summary
            print(f"\n[7/7] Summary:")
            print(f"  Mission ID:         {mission_id}")
            print(f"  Timeout override:   {TIMEOUT_OVERRIDE}s")
            print(f"  Final state:        {final_state}")
            print(f"  Health before:      {health_before}")
            print(f"  Health after:       {health_after}")
            print(f"  Remained EXECUTING: {remained_executing}")

            # Determine GAP_030 status
            gap030_status = "ACTIVE"
            if final_state == "TIMEOUT" and health_after and not remained_executing:
                gap030_status = "RESOLVED"
            elif final_state == "TIMEOUT":
                gap030_status = "PARTIAL"

            print(f"  GAP_030 status:     {gap030_status}")

            # Save results
            results = {
                "health_before": health_before,
                "timeout_override": TIMEOUT_OVERRIDE,
                "prompt_used": prompt[:100] + "...",
                "mission_id": mission_id,
                "final_state": final_state,
                "state_history": state_history,
                "remained_executing": remained_executing,
                "health_after": health_after,
                "gap030_status": gap030_status,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open("C:\\ProjectS-Unified\\.gap030_live_results.json", "w") as f:
                json.dump(results, f, indent=2)

            print("\n" + "=" * 60)
            print(f"  VALIDATION COMPLETE — Status: {gap030_status}")
            print("=" * 60)
        else:
            print("  No mission created — validation skipped")
    else:
        print("  No session created — validation skipped")

if __name__ == "__main__":
    asyncio.run(main())