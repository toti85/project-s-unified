#!/usr/bin/env python
"""Check TIMEOUT missions in the interactive layer database."""
import sqlite3
import sys
from datetime import datetime

DB_PATH = "interactive_layer_data/interactive.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.execute(
    'SELECT mission_id, created_at, updated_at, state, timeout_seconds, error '
    'FROM missions WHERE state = "TIMEOUT" ORDER BY created_at DESC LIMIT 10'
)
rows = cursor.fetchall()
conn.close()

if not rows:
    print("No TIMEOUT missions found.")
    sys.exit(0)

print(f"{'mission_id':<36} {'created_at':<25} {'updated_at':<25} {'state':<10} {'timeout_seconds':<15} {'error'}")
print("-" * 180)
for r in rows:
    mid, created, updated, state, timeout_sec, error = r
    # Calculate elapsed time
    if created and updated:
        try:
            c = datetime.fromisoformat(str(created))
            u = datetime.fromisoformat(str(updated))
            elapsed = (u - c).total_seconds()
        except Exception:
            elapsed = "N/A"
    else:
        elapsed = "N/A"
    print(f"{str(mid):<36} {str(created):<25} {str(updated):<25} {str(state):<10} {str(timeout_sec):<15} {str(error)[:80]}")
    print(f"  -> Elapsed: {elapsed}s")