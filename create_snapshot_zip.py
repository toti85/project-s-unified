import zipfile
import os
import sys

stage = r'C:\ProjectS-Snapshot-Staging'
zip_path = r'C:\ProjectS-Unified\ProjectS-Snapshot-20260601.zip'

print(f'Stage exists: {os.path.exists(stage)}', flush=True)
if not os.path.exists(stage):
    print('ERROR: Staging directory does not exist!', flush=True)
    sys.exit(1)

print(f'Stage contents: {os.listdir(stage)[:10]}', flush=True)

# Count files first
count = 0
for root, dirs, files in os.walk(stage):
    count += len(files)
print(f'Total files to zip: {count}', flush=True)

# Create zip
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    added = 0
    for root, dirs, files in os.walk(stage):
        for f in files:
            fp = os.path.join(root, f)
            arc = os.path.relpath(fp, stage)
            try:
                zf.write(fp, arc)
                added += 1
            except Exception as e:
                print(f'ERROR adding {fp}: {e}', flush=True)
    print(f'Files added to zip: {added}', flush=True)

# Verify
if os.path.exists(zip_path):
    size_mb = round(os.path.getsize(zip_path) / 1048576, 2)
    print(f'ZIP created successfully: {zip_path}', flush=True)
    print(f'Size: {size_mb} MB', flush=True)
else:
    print('ERROR: ZIP file was not created!', flush=True)
    sys.exit(1)