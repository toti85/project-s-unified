#!/usr/bin/env python
"""Check authoritative rerun missions from 2026-05-20."""
import sqlite3
import sys
from datetime import datetime

DB_PATH = "interactive_layer_data/interactive.db"

conn = sqlite3.connect(DB_PATH)
# Get all missions from 2026-05-20
cursor = conn.execute(
    'SELECT mission_id, created_at, updated_at, state, timeout_seconds, error, result '
    'FROM missions WHERE created_at LIKE "2026-05-20%" ORDER BY created_at DESC LIMIT 20'
)
rows = cursor.fetchall()
conn.close()

if not rows:
    print("No missions found from 2026-05-20.")
    sys.exit(0)

print(f"{'mission_id':<36} {'created_at':<25} {'updated_at':<25} {'state':<12} {'timeout':<8} {'error'[:60]}")
print("-" * 160)
for r in rows:
    mid, created, updated, state, timeout_sec, error, result = r
    if created and updated:
        try:
            c = datetime.fromisoformat(str(created))
            u = datetime.fromisoformat(str(updated))
            elapsed = (u - c).total_seconds()
        except Exception:
            elapsed = "N/A"
    else:
        elapsed = "N/A"
    err_str = str(error or "")[:60]
    print(f"{str(mid):<36} {str(created):<25} {str(updated):<25} {str(state):<12} {str(timeout_sec):<8} {err_str}")
    print(f"  -> Elapsed: {elapsed}s")
    if result and len(str(result)) > 0:
        print(f"  -> Result preview: {str(result)[:100]}")