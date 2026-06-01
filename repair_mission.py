import sqlite3
from datetime import datetime

db = r"C:\ProjectS\project-s-code\interactive_layer_data\interactive.db"

conn = sqlite3.connect(db)

# Repair stuck mission
conn.execute("""
    UPDATE missions 
    SET state='TIMEOUT', 
        error='GAP_030 manual repair: prior timeout did not terminalize mission.', 
        updated_at=datetime('now') 
    WHERE mission_id='07ee2be9-1bf5-40a0-bae9-ff99f249c6d4'
""")
conn.commit()

# Verify
r = conn.execute("""
    SELECT mission_id, state, error, updated_at 
    FROM missions 
    WHERE mission_id='07ee2be9-1bf5-40a0-bae9-ff99f249c6d4'
""").fetchone()
print("Repaired mission:", r)

# Also check all missions
rows = conn.execute("SELECT mission_id, state, progress FROM missions").fetchall()
print("All missions:")
for row in rows:
    print(f"  {row[0]} | {row[1]} | {row[2]}")

conn.close()