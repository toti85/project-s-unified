#!/usr/bin/env python
"""Query interactive.db for mission details to build iteration-level timelines."""

import sqlite3
import json
import sys

DB_PATH = "interactive_layer_data/interactive.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r["name"] for r in cur.fetchall()]
    print("Tables:", tables)

    # Mission IDs from the test run
    mission_ids = {
        "TEST_1": "abcf445c-2528-4018-bbbf-7003b0574e86",
        "TEST_2": None,  # 404 - may have been cleaned up
        "TEST_3": None,  # 404
        "TEST_4": None,  # unknown full ID
        "TEST_5": None,  # unknown full ID
        "TEST_6": None,  # unknown full ID
        "TEST_7": None,  # unknown full ID
        "TEST_8": "5272befc-b854-40a6-83d1-639bf8a5a1b9",
    }

    # Get all missions to find the ones we need
    cur.execute("SELECT mission_id, state, error, result, plan, task, state_history, created_at, updated_at FROM missions ORDER BY created_at DESC LIMIT 20")
    rows = cur.fetchall()
    print(f"\nFound {len(rows)} recent missions:")
    for r in rows:
        print(f"  {r['mission_id'][:36]} state={r['state']} error={str(r['error'])[:80]}")

    # Query specific missions
    for test_name, mid in mission_ids.items():
        if mid is None:
            continue
        cur.execute(
            "SELECT * FROM missions WHERE mission_id = ?",
            (mid,)
        )
        row = cur.fetchone()
        if row:
            print(f"\n=== {test_name} Mission ===")
            for k in row.keys():
                v = row[k]
                if k in ("result", "error", "plan"):
                    v = str(v)[:1000] if v else None
                elif k == "state_history":
                    try:
                        sh = json.loads(v) if isinstance(v, str) else v
                        v = json.dumps(sh, indent=2, ensure_ascii=False)[:2000]
                    except:
                        v = str(v)[:500]
                print(f"  {k}: {v}")
        else:
            print(f"\n=== {test_name} Mission: NOT FOUND ({mid}) ===")

    conn.close()

if __name__ == "__main__":
    main()