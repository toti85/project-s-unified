import json

with open('orchestrator_runtime/sandbox/aider_cloud_single_prompt_trial/single_prompt_output.json', encoding='utf-8') as f:
    data = json.load(f)

print("=== TOP-LEVEL KEYS ===")
print(list(data.keys()))

print(f"\nprompt_id: {data.get('prompt_id')}")
print(f"start_index: {data.get('start_index')}")
print(f"end_index: {data.get('end_index')}")
print(f"finding_count: {data.get('finding_count')}")

findings = data.get('findings', [])
print(f"\nfindings list length: {len(findings)}")

if len(findings) == 0:
    print("NO FINDINGS IN OUTPUT")
else:
    print(f"\n=== FIRST FINDING ===")
    print(json.dumps(findings[0], indent=2))
    print(f"\n=== LAST FINDING ===")
    print(json.dumps(findings[-1], indent=2))

    # Check indices
    indices = [f.get('index') for f in findings]
    unique = set(indices)
    print(f"\n=== INDEX VALIDATION ===")
    print(f"Total entries: {len(indices)}")
    print(f"Unique indices: {len(unique)}")
    
    if len(indices) != len(unique):
        print("WARNING: DUPLICATE INDICES!")
        from collections import Counter
        dupes = [i for i, c in Counter(indices).items() if c > 1]
        print(f"Duplicated indices: {dupes}")
    
    expected = set(range(1, 78))
    missing = expected - unique
    extra = unique - expected
    
    if missing:
        print(f"Missing indices: {sorted(missing)}")
    else:
        print("No missing indices: ALL 77 present ✅")
    
    if extra:
        print(f"Extra indices: {sorted(extra)}")
    else:
        print("No extra indices ✅")
    
    # Check all required fields per finding
    required_fields = {'index', 'file', 'line', 'type', 'severity', 'text', 'context'}
    all_ok = True
    for i, f in enumerate(findings):
        missing_fields = required_fields - set(f.keys())
        if missing_fields:
            print(f"Finding {i}: missing fields: {missing_fields}")
            all_ok = False
    if all_ok:
        print("\nAll findings have all required fields ✅")
    
    # Severity breakdown
    from collections import Counter
    sev = Counter(f.get('severity') for f in findings)
    print(f"\n=== SEVERITY BREAKDOWN ===")
    for s, c in sev.most_common():
        print(f"  {s}: {c}")
    
    # Type breakdown
    types = Counter(f.get('type') for f in findings)
    print(f"\n=== TYPE BREAKDOWN ===")
    for t, c in types.most_common():
        print(f"  {t}: {c}")

print("\n=== VALIDATION SUMMARY ===")
print(f"JSON parseable: YES")
print(f"Finding count: {len(findings)}")
print(f"All 77 present: {len(missing) == 0}")
print(f"No duplicates: {len(indices) == len(unique)}")
print(f"All required fields: {all_ok}")