import json

for i in [1, 2, 3]:
    path = f'orchestrator_runtime/sandbox/aider_cloud_trial/chunks/chunk_0{i}.json'
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        print(f'chunk_0{i}.json: {len(data)} items, valid JSON array')
        if len(data) > 0:
            first = data[0]
            last = data[-1]
            print(f'  First item keys: {list(first.keys())}')
            idx_key = 'index' if 'index' in first else 'finding_id'
            print(f'  First item {idx_key}: {first.get(idx_key)}')
            print(f'  Last item {idx_key}: {last.get(idx_key)}')
    else:
        print(f'chunk_0{i}.json: {type(data).__name__}, keys: {list(data.keys())[:5]}')