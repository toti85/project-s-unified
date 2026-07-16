import json

with open('orchestrator_runtime/sandbox/aider_cloud_trial/chunks/chunk_01.json') as f:
    data = json.load(f)

print("=== TOP-LEVEL KEYS ===")
print(list(data.keys()))
print(f"chunk_id: {data['chunk_id']}")
print(f"start_index: {data['start_index']}")
print(f"end_index: {data['end_index']}")
print(f"finding_count: {data['finding_count']}")
print(f"findings list length: {len(data['findings'])}")

print("\n=== FIRST FINDING ===")
print(json.dumps(data['findings'][0], indent=2))

print("\n=== LAST FINDING ===")
print(json.dumps(data['findings'][-1], indent=2))