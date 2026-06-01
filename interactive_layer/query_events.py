#!/usr/bin/env python
"""Query mission_events table for evaluator responses."""

import sqlite3
import json

DB_PATH = "interactive_layer_data/interactive.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Mission IDs
    test_missions = {
        "TEST_1": "abcf445c-2528-4018-bbbf-7003b0574e86",
        "TEST_8": "5272befc-b854-40a6-83d1-639bf8a5a1b9",
        "TEST_4": "6c0e8e28-ca36-465b-89e4-3f30da77a682",
        "TEST_5": "59c5d35f-6aab-4026-beb7-1952de223c78",
        "TEST_6": "2dcbcd89-2d6a-4167-b0ca-312ef61f833a",
    }

    for test_name, mid in test_missions.items():
        cur.execute(
            "SELECT event_id, event_type, data, timestamp FROM mission_events WHERE mission_id = ? ORDER BY event_id",
            (mid,)
        )
        rows = cur.fetchall()
        print(f"\n{'='*70}")
        print(f"{test_name} ({mid[:36]}): {len(rows)} events")
        print(f"{'='*70}")
        for r in rows:
            data_str = str(r["data"])[:500]
            print(f"  eid={r['event_id']} type={r['event_type']} ts={r['timestamp']}")
            print(f"    data: {data_str}")

    conn.close()

if __name__ == "__main__":
    main()