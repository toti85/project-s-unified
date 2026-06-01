import zipfile
import json
import sys

zip_path = r'C:\ProjectS-Unified\ProjectS-Snapshot-20260601.zip'
results = []

with zipfile.ZipFile(zip_path, 'r') as zf:
    # Test integrity
    bad = zf.testzip()
    results.append('ZIP integrity: ' + ('OK' if bad is None else 'FAILED: ' + str(bad)))
    
    names = zf.namelist()
    results.append('Total entries: ' + str(len(names)))
    
    # Check credential files
    cred = [n for n in names if '.env' in n.lower() or 'credential' in n.lower()]
    results.append('Cred files: ' + ('NONE-OK' if not cred else 'FOUND-BAD: ' + str(cred)))
    
    # Top-level directories
    dirs = sorted(set(n.split('/')[0] for n in names if '/' in n))
    results.append('Dirs: ' + str(dirs))
    
    # self_state.json
    ss = any('self_state.json' in n for n in names)
    results.append('self_state.json present: ' + str(ss))
    if ss:
        try:
            json.loads(zf.read('self_state.json'))
            results.append('self_state.json valid JSON: True')
        except Exception as e:
            results.append('self_state.json valid JSON: False - ' + str(e))
    
    # .git excluded
    results.append('.git present: ' + str(any('.git/' in n for n in names)))
    
    # __pycache__ excluded
    results.append('__pycache__ present: ' + str(any('__pycache__' in n for n in names)))

# Write results to file
with open(r'C:\ProjectS-Unified\zip_integrity_check.txt', 'w') as f:
    f.write('\n'.join(results))

print('\n'.join(results))