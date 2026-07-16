"""
run_t7b.py — AO9_T7B Single-Prompt Aider Cloud Execution
"""

import json
import os
import pathlib
import subprocess
import sys
import time

# Paths
_repo_root = pathlib.Path(__file__).parent.parent.parent.parent
TRIAL_DIR = pathlib.Path(__file__).parent
AIDER_EXE = _repo_root / "venv" / "Scripts" / "aider.exe"
OR_ENDPOINT = "https://openrouter.ai/api/v1"
MODEL_ID = "deepseek/deepseek-v4-flash"
AIDER_MODEL = f"openai/{MODEL_ID}"

# API key
api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not set")

# Environment with encoding fixes
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "TERM": "dumb"}

# Base args
BASE_ARGS = [
    str(AIDER_EXE),
    "--no-git", "--yes-always", "--no-check-update",
    "--no-show-model-warnings", "--no-stream", "--no-pretty",
    "--openai-api-base", OR_ENDPOINT,
    "--openai-api-key", api_key,
    "--model", AIDER_MODEL,
]

# Preflight
print("=== PREFLIGHT ===")
t0 = time.time()
try:
    preflight_result = subprocess.run(
        BASE_ARGS + ["--message", "Reply with exactly: AIDER_CLOUD_OK"],
        capture_output=True, text=True, timeout=30,
        cwd=str(TRIAL_DIR), env=env
    )
    pf_elapsed = time.time() - t0
    print(f"Preflight exit: {preflight_result.returncode}")
    print(f"Preflight elapsed: {pf_elapsed:.2f}s")
    print(f"Stdout (last 500 chars): {preflight_result.stdout[-500:]}")
    print(f"Stderr (last 500 chars): {preflight_result.stderr[-500:]}")
    
    # Check if AIDER_CLOUD_OK is in output
    preflight_ok = "AIDER_CLOUD_OK" in preflight_result.stdout or "AIDER_CLOUD_OK" in preflight_result.stderr
    print(f"Preflight AIDER_CLOUD_OK found: {preflight_ok}")
    if not preflight_ok and preflight_result.returncode != 0:
        raise RuntimeError(f"Preflight FAILED: {preflight_result.stderr[-300:]}")
except subprocess.TimeoutExpired:
    print("Preflight TIMEOUT (continuing anyway)")
    pf_elapsed = time.time() - t0
    preflight_ok = False

# Single-prompt execution
print("\n=== SINGLE PROMPT EXECUTION ===")
prompt_file = TRIAL_DIR / "single_prompt_instruction.txt"
if not prompt_file.exists():
    raise RuntimeError(f"Prompt file not found: {prompt_file}")

print(f"Prompt file: {prompt_file}")
print(f"Prompt size: {prompt_file.stat().st_size} bytes")
print(f"Starting Aider invocation (timeout: 600s)...")

t1 = time.time()
try:
    result = subprocess.run(
        BASE_ARGS + ["--message-file", str(prompt_file)],
        capture_output=True, text=True, timeout=600,
        cwd=str(TRIAL_DIR), env=env
    )
    elapsed = time.time() - t1
    exit_code = result.returncode
    print(f"Exit code: {exit_code}")
    print(f"Elapsed: {elapsed:.2f}s")
except subprocess.TimeoutExpired:
    elapsed = time.time() - t1
    print(f"TIMEOUT after {elapsed:.2f}s")
    result = None
    exit_code = -1

# Save full log
log_path = TRIAL_DIR / "aider_single_prompt_response.log"
with open(log_path, 'w', encoding='utf-8') as f:
    f.write(f"EXIT: {exit_code}\n")
    f.write(f"ELAPSED: {elapsed:.2f}s\n")
    f.write("=" * 60 + "\n")
    if result:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\n" + "=" * 60 + "\n")
        f.write("STDERR:\n")
        f.write(result.stderr)
    else:
        f.write("TIMEOUT - no output captured\n")
print(f"Log saved to: {log_path}")

# Check for output file
output_path = TRIAL_DIR / "single_prompt_output.json"
if output_path.exists():
    print(f"\nOutput file exists: {output_path}")
    print(f"Size: {output_path.stat().st_size} bytes")
    try:
        with open(output_path, encoding='utf-8') as f:
            output_data = json.load(f)
        print(f"JSON parseable: YES")
        if isinstance(output_data, dict):
            print(f"Top-level keys: {list(output_data.keys())}")
            findings = output_data.get('findings', [])
            print(f"Findings count: {len(findings)}")
            if len(findings) > 0:
                print(f"First finding index: {findings[0].get('index')}")
                print(f"Last finding index: {findings[-1].get('index')}")
                indices = [f.get('index') for f in findings]
                unique = set(indices)
                print(f"Unique indices: {len(unique)}")
                if len(indices) != len(unique):
                    print("WARNING: DUPLICATE INDICES FOUND!")
                expected = set(range(1, 78))
                missing = expected - unique
                if missing:
                    print(f"Missing indices: {sorted(missing)}")
                else:
                    print("No missing indices: ALL 77 present")
        elif isinstance(output_data, list):
            print(f"List with {len(output_data)} items")
            if len(output_data) > 0:
                print(f"First item keys: {list(output_data[0].keys())}")
        else:
            print(f"Unexpected type: {type(output_data).__name__}")
    except json.JSONDecodeError as e:
        print(f"JSON parseable: NO — {e}")
else:
    print(f"\nOutput file NOT FOUND at: {output_path}")
    for f in sorted(TRIAL_DIR.iterdir()):
        if f.suffix == '.json' and f.name != 'scan_canonical.json':
            print(f"  Found JSON file: {f.name} ({f.stat().st_size} bytes)")

# Token info
print("\n=== TOKEN INFO ===")
if result:
    for line in result.stdout.split('\n'):
        if 'Tokens:' in line:
            print(f"  {line.strip()}")
    for line in result.stderr.split('\n'):
        if 'Tokens:' in line:
            print(f"  {line.strip()}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Model:           {AIDER_MODEL}")
print(f"  Endpoint:        {OR_ENDPOINT}")
print(f"  Preflight:       {'PASS' if preflight_ok else 'FAIL'} ({pf_elapsed:.2f}s)")
print(f"  Exit code:       {exit_code}")
print(f"  Elapsed:         {elapsed:.2f}s")
print(f"  Output file:     {'EXISTS' if output_path.exists() else 'NOT FOUND'}")
print("=" * 60)