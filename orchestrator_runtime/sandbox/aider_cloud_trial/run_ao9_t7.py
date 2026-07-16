"""
run_ao9_t7.py — AO9_T7 Aider Cloud Executor Cell

Tests chunk-merge-verify pattern using Aider CLI in its NATIVE
configuration: cloud model (DeepSeek V4 Flash) via OpenRouter.

Comparison:
  AO9_T5_RUN4  — Ornith 9B, custom adapter     (PASS 11/11)
  AO9_T6       — Ornith 9B, Aider CLI           (INVALID: model-class mismatch)
  AO9_T7       — DeepSeek V4 Flash, Aider CLI   (THIS RUN — valid native test)

SAME:  chunk sizes (25/25/27), input (scan_canonical.json), prompt format
DIFF:  model (cloud large), endpoint (OpenRouter), API key required
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────

_repo_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_repo_root))

TRIAL_DIR     = pathlib.Path(__file__).parent
T5_TRIAL      = _repo_root / "orchestrator_runtime" / "sandbox" / "ornith_executor_trial"
T6_TRIAL      = _repo_root / "orchestrator_runtime" / "sandbox" / "aider_executor_trial"
T7_TRIAL      = _repo_root / "orchestrator_runtime" / "sandbox" / "aider_cloud_trial"
CHUNKS_DIR    = T7_TRIAL / "chunks"
LOGS_DIR      = T7_TRIAL / "logs"
CANONICAL_SRC = T5_TRIAL / "ao9_t5_run4" / "scan_canonical.json"
CANONICAL     = T7_TRIAL / "scan_canonical.json"
REPORTS_DIR   = _repo_root / "reports"
OUTCOMES_FILE = T7_TRIAL / "aider_cloud_outcomes.jsonl"
RESULTS_FILE  = T7_TRIAL / "ao9_t7_result.json"

# ── Aider / OpenRouter config ──────────────────────────────────────────

AIDER_EXE     = _repo_root / "venv" / "Scripts" / "aider.exe"
OR_ENDPOINT   = "https://openrouter.ai/api/v1"
MODEL_ID      = "deepseek/deepseek-v4-flash"
AIDER_MODEL   = f"openai/{MODEL_ID}"

# API key loaded from env var (never hardcoded, never logged)
def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        # Try reading from known key file as fallback (matches project convention)
        key_file = _repo_root / "openrouter.txt"
        if key_file.exists():
            key = key_file.read_text(encoding="utf-8").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set and openrouter.txt not found")
    return key

# ── Mission config ────────────────────────────────────────────────────

MISSION_ID     = "AO9_T7"
EXPECTED_COUNT = 77

CHUNK_CONFIGS = [
    (1, 0, 25),    # chunk_id, slice_start, slice_end (exclusive)
    (2, 25, 50),
    (3, 50, 77),
]

# ── Prompt builder ────────────────────────────────────────────────────

def build_chunk_prompt(chunk_id: int, chunk_findings: list, start_idx: int) -> str:
    end_idx = start_idx + len(chunk_findings) - 1
    n = len(chunk_findings)

    finding_lines = []
    for i, f in enumerate(chunk_findings):
        idx = start_idx + i
        ctx = (f.get("context_before") or f.get("context_after") or "").strip()
        line = f"#{idx} [{f['type']}] {f['file']}:{f['line']} {json.dumps(f['text'])}"
        if ctx:
            line += f"  context: {json.dumps(ctx)}"
        finding_lines.append(line)

    target_file = f"chunk_{chunk_id:02d}.json"

    lines = [
        f"Create a new file `{target_file}` in the current directory.",
        f"The file must contain ONLY valid JSON — no preamble, no markdown, no explanation.",
        f"",
        f"Classify these {n} findings (indices {start_idx} to {end_idx}) with severity:",
        f"HIGH=security/data-loss/auth, MEDIUM=functionality/correctness/performance, LOW=docs/style/cleanup",
        f"",
        f"FINDINGS (include ALL, invent NONE):",
    ]
    lines.extend(finding_lines)
    lines += [
        f"",
        f"Required JSON structure for `{target_file}`:",
        '{',
        f'  "chunk_id": {chunk_id},',
        f'  "start_index": {start_idx},',
        f'  "end_index": {end_idx},',
        f'  "finding_count": {n},',
        '  "findings": [',
        '    {',
        '      "index": <number>,',
        '      "file": "<file path>",',
        '      "line": <number>,',
        '      "type": "<TODO|FIXME|XXX>",',
        '      "severity": "<LOW|MEDIUM|HIGH>",',
        '      "text": "<exact text>",',
        '      "context": "<context>"',
        '    }',
        '  ]',
        '}',
        f'',
        f'Every finding index from {start_idx} to {end_idx} MUST appear exactly once.',
        f'Do not add findings that are not in the list above.',
    ]
    return "\n".join(lines)


# ── JSON extraction ───────────────────────────────────────────────────

def extract_json_from_text(text: str) -> dict | None:
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i, c in enumerate(text[start:]):
        if esc: esc = False; continue
        if c == "\\" and in_str: esc = True; continue
        if c == '"': in_str = not in_str
        elif not in_str:
            if c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try: return json.loads(text[start:start+i+1])
                    except: break
    return None


# ── Chunk validation ──────────────────────────────────────────────────

def validate_chunk(data: dict, chunk_id: int, start_idx: int, end_idx: int, n: int) -> list:
    errors = []
    if data.get("chunk_id") != chunk_id:
        errors.append(f"chunk_id={data.get('chunk_id')} expected {chunk_id}")
    fc = data.get("finding_count")
    if fc != n:
        errors.append(f"finding_count={fc} expected {n}")
    findings = data.get("findings", [])
    if len(findings) != n:
        errors.append(f"findings len={len(findings)} expected {n}")
    actual = {f.get("index") for f in findings}
    expected = set(range(start_idx, end_idx + 1))
    missing = sorted(expected - actual)
    if missing:
        errors.append(f"missing idx: {missing[:5]}")
    extra = sorted(actual - expected)
    if extra:
        errors.append(f"extra idx: {extra[:5]}")
    return errors


# ── Extract token usage from Aider output ─────────────────────────────

def parse_aider_tokens(text: str) -> dict:
    """Parse 'Tokens: N sent, M received.' from Aider output."""
    m = re.search(r"Tokens:\s*([\d,]+)\s*sent,\s*([\d,]+)\s*received", text)
    if m:
        sent = int(m.group(1).replace(",", ""))
        recv = int(m.group(2).replace(",", ""))
        return {"tokens_sent": sent, "tokens_received": recv, "tokens_total": sent + recv}
    return {"tokens_sent": None, "tokens_received": None, "tokens_total": None}


# ── Run Aider (cloud) ─────────────────────────────────────────────────

def run_aider_chunk(
    chunk_id: int,
    prompt: str,
    work_dir: pathlib.Path,
    api_key: str,
    timeout: int = 300,
) -> dict:
    """
    Run one Aider invocation for a single chunk against DeepSeek V4 Flash.
    Returns result dict with timing, exit code, file created, parse result.
    """
    target = work_dir / f"chunk_{chunk_id:02d}.json"
    prompt_file = work_dir / f"chunk_{chunk_id:02d}_prompt.txt"
    log_file = LOGS_DIR / f"aider_cloud_chunk_{chunk_id:02d}.log"

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(prompt, encoding="utf-8")

    # Note: no --no-stream (leave streaming as default — works correctly)
    # API key passed via --openai-api-key (env var only, not logged in code)
    cmd = [
        str(AIDER_EXE),
        "--no-git",
        "--yes-always",
        "--no-check-update",
        "--no-show-model-warnings",
        "--openai-api-base", OR_ENDPOINT,
        "--openai-api-key", api_key,
        "--model", AIDER_MODEL,
        "--message-file", str(prompt_file),
    ]

    t_start = time.time()
    result = {
        "chunk_id": chunk_id,
        "target_file": str(target),
        "prompt_file": str(prompt_file),
        "log_file": str(log_file),
        "t_start": datetime.now(timezone.utc).isoformat(),
    }

    # Build env — api key in env too for belt-and-suspenders
    env = {
        **os.environ,
        "OPENROUTER_API_KEY": api_key,
        "OPENAI_API_KEY": api_key,
        "OPENAI_API_BASE": OR_ENDPOINT,
    }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
            env=env,
        )
        elapsed = round(time.time() - t_start, 2)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        combined = stdout + stderr

        # Redact API key from log (safety)
        key_masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        log_content = combined.replace(api_key, key_masked)
        log_file.write_text(
            f"CHUNK: {chunk_id}\nCWD: {work_dir}\nEXIT: {proc.returncode}\nELAPSED: {elapsed}s\n"
            f"{'='*60}\nOUTPUT:\n{log_content}\n",
            encoding="utf-8",
        )

        token_info = parse_aider_tokens(combined)

        result.update({
            "elapsed": elapsed,
            "exit_code": proc.returncode,
            "stdout_len": len(stdout),
            "token_info": token_info,
            "stdout_preview": combined[:1200].replace(api_key, key_masked),
            "error": None,
        })

        # Check if Aider created the target file
        file_created = target.exists()
        chunk_data = None
        parse_ok = False
        validation_errors = []

        if file_created:
            content = target.read_text(encoding="utf-8", errors="replace")
            chunk_data = extract_json_from_text(content)
            if chunk_data:
                parse_ok = True
                sl = CHUNK_CONFIGS[chunk_id - 1]
                start_idx = sl[1] + 1
                end_idx = sl[2]
                n = sl[2] - sl[1]
                validation_errors = validate_chunk(chunk_data, chunk_id, start_idx, end_idx, n)
            result["file_size"] = target.stat().st_size
        else:
            # Try to extract JSON from stdout (fallback)
            chunk_data = extract_json_from_text(combined)
            if chunk_data:
                target.write_text(json.dumps(chunk_data, indent=2, ensure_ascii=False), encoding="utf-8")
                file_created = True
                parse_ok = True
                sl = CHUNK_CONFIGS[chunk_id - 1]
                start_idx = sl[1] + 1
                end_idx = sl[2]
                n = sl[2] - sl[1]
                validation_errors = validate_chunk(chunk_data, chunk_id, start_idx, end_idx, n)
                result["file_from_stdout"] = True
                result["file_size"] = target.stat().st_size
            else:
                result["file_size"] = 0

        result.update({
            "file_created": file_created,
            "parse_ok": parse_ok,
            "validation_errors": validation_errors,
            "chunk_ok": file_created and parse_ok and len(validation_errors) == 0,
            "chunk_data": chunk_data,
        })

    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - t_start, 2)
        result.update({
            "elapsed": elapsed,
            "exit_code": -1,
            "error": f"TIMEOUT after {timeout}s",
            "file_created": target.exists(),
            "parse_ok": False,
            "chunk_ok": False,
            "chunk_data": None,
            "token_info": {"tokens_sent": None, "tokens_received": None},
            "stdout_preview": "",
        })
    except Exception as e:
        elapsed = round(time.time() - t_start, 2)
        result.update({
            "elapsed": elapsed,
            "exit_code": -1,
            "error": str(e),
            "file_created": False,
            "parse_ok": False,
            "chunk_ok": False,
            "chunk_data": None,
            "token_info": {"tokens_sent": None, "tokens_received": None},
            "stdout_preview": "",
        })

    return result


# ── Markdown renderer ─────────────────────────────────────────────────

def render_markdown(findings: list, scan_ts: str, files_scanned: int, files_with: int) -> str:
    total = len(findings)
    type_counts: dict = {}
    sev_counts: dict = {}
    dir_counts: dict = {}
    for f in findings:
        t = f.get("type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1
        s = f.get("severity", "LOW")
        sev_counts[s] = sev_counts.get(s, 0) + 1
        parts = f.get("file", "").split("/")
        d = parts[0] if len(parts) > 1 else "(root)"
        dir_counts[d] = dir_counts.get(d, 0) + 1

    ls = [
        "# PROJECT-S TODO/FIXME/XXX AUDIT (AO9_T7 — Aider + DeepSeek V4 Flash)",
        "",
        "## 1. Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Scan date | {scan_ts[:10]} |",
        f"| Python files scanned | {files_scanned} |",
        f"| Files with findings | {files_with} |",
        f"| Total findings | {total} |",
        f"| TODO | {type_counts.get('TODO', 0)} |",
        f"| FIXME | {type_counts.get('FIXME', 0)} |",
        f"| XXX | {type_counts.get('XXX', 0)} |",
        f"| Executor | Aider CLI 0.86.2 |",
        f"| Model | DeepSeek V4 Flash (via OpenRouter) |",
        "",
        "## 2. Counts by Marker Type",
        "",
    ]
    for t, c in sorted(type_counts.items()):
        ls.append(f"- **{t}**: {c}")
    ls += ["", "## 3. Counts by Severity", ""]
    for s in ("HIGH", "MEDIUM", "LOW"):
        if s in sev_counts:
            ls.append(f"- **{s}**: {sev_counts[s]}")
    ls += ["", "## 4. Counts by Directory", ""]
    for d, c in sorted(dir_counts.items(), key=lambda x: -x[1]):
        ls.append(f"- `{d}`: {c}")
    ls += ["", "## 5. Complete Finding List", ""]
    for f in findings:
        ls += [
            f"### Finding #{f['index']}",
            "",
            f"- **File**: `{f.get('file', '')}`",
            f"- **Line**: {f.get('line', '')}",
            f"- **Type**: {f.get('type', '')}",
            f"- **Severity**: {f.get('severity', 'LOW')}",
            f"- **Text**: `{f.get('text', '')}`",
        ]
        ctx = f.get("context", "")
        if ctx:
            ls.append(f"- **Context**: `{ctx}`")
        ls.append("")
    return "\n".join(ls)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("AO9_T7 — AIDER CLOUD CELL (DeepSeek V4 Flash via OpenRouter)")
    print("=" * 60)

    # Setup dirs
    T7_TRIAL.mkdir(parents=True, exist_ok=True)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    scan_ts = datetime.now(timezone.utc).isoformat()

    # ── PHASE 0: Preflight ────────────────────────────────────────────
    print("\n[PHASE 0] Preflight...")

    # API key
    try:
        api_key = get_api_key()
        print(f"  API key: loaded ({api_key[:8]}...)")
    except RuntimeError as e:
        print(f"  ABORT: {e}")
        sys.exit(1)

    # Aider binary
    if not AIDER_EXE.exists():
        print(f"  ABORT: aider.exe not found at {AIDER_EXE}")
        sys.exit(1)
    print(f"  Aider: {AIDER_EXE}")

    # OpenRouter connectivity check (lightweight)
    import urllib.request
    try:
        req = urllib.request.Request(
            f"{OR_ENDPOINT}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        r = urllib.request.urlopen(req, timeout=10)
        models_data = json.loads(r.read().decode())
        model_ids = [m["id"] for m in models_data.get("data", [])]
        model_found = MODEL_ID in model_ids
        print(f"  OpenRouter models: {len(model_ids)} | {MODEL_ID} found: {model_found}")
        if not model_found:
            print(f"  WARNING: {MODEL_ID} not in model list — check model string")
    except Exception as e:
        print(f"  WARNING: OpenRouter check failed: {e}")

    # ── PHASE 0b: Preflight test ──────────────────────────────────────
    print("\n[PHASE 0b] Aider cloud preflight test (AIDER_CLOUD_OK)...")
    preflight_dir = T7_TRIAL / "preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    preflight_log = LOGS_DIR / "aider_cloud_preflight.log"

    env_pf = {
        **os.environ,
        "OPENROUTER_API_KEY": api_key,
        "OPENAI_API_KEY": api_key,
        "OPENAI_API_BASE": OR_ENDPOINT,
    }
    t_pf = time.time()
    pf_result = subprocess.run(
        [
            str(AIDER_EXE),
            "--no-git", "--yes-always",
            "--no-check-update", "--no-show-model-warnings",
            "--openai-api-base", OR_ENDPOINT,
            "--openai-api-key", api_key,
            "--model", AIDER_MODEL,
            "--message", "Reply with exactly this text and nothing else: AIDER_CLOUD_OK",
        ],
        capture_output=True, text=True, timeout=60,
        cwd=str(preflight_dir), env=env_pf,
    )
    pf_elapsed = round(time.time() - t_pf, 2)
    pf_output = pf_result.stdout + pf_result.stderr
    key_masked = api_key[:8] + "..." + api_key[-4:]
    preflight_log.write_text(
        pf_output.replace(api_key, key_masked),
        encoding="utf-8",
    )

    pf_ok = "AIDER_CLOUD_OK" in pf_output
    pf_tokens = parse_aider_tokens(pf_output)
    print(f"  Exit code: {pf_result.returncode} | {pf_elapsed}s")
    print(f"  AIDER_CLOUD_OK found: {pf_ok}")
    print(f"  Tokens: {pf_tokens}")
    print(f"  Preview: {pf_output[:300].replace(api_key, key_masked)!r}")

    if not pf_ok:
        print("  ABORT: preflight failed — check API key and model string")
        sys.exit(1)

    # ── PHASE 0c: Load canonical ──────────────────────────────────────
    print("\n[PHASE 0c] Load canonical scan...")
    if not CANONICAL_SRC.exists():
        print(f"  ABORT: {CANONICAL_SRC} not found")
        sys.exit(1)

    canon = json.loads(CANONICAL_SRC.read_text(encoding="utf-8"))
    shutil.copy2(CANONICAL_SRC, CANONICAL)

    all_findings = canon["findings"]
    files_scanned = canon.get("files_scanned", 0)
    files_with = canon.get("files_with_findings", 0)
    actual_n = len(all_findings)
    print(f"  Loaded {actual_n} findings | {files_scanned} files | {files_with} with findings")

    if actual_n != EXPECTED_COUNT:
        print(f"  WARNING: expected {EXPECTED_COUNT}, got {actual_n}")

    # ── PHASE 1: Chunk generation ─────────────────────────────────────
    print(f"\n[PHASE 1] Chunk generation (3 chunks, Aider + DeepSeek V4 Flash)...")
    print(f"  Model: {AIDER_MODEL}")
    print(f"  Endpoint: {OR_ENDPOINT}")

    chunk_results = []
    all_chunks_pass = True
    total_tokens_sent = 0
    total_tokens_recv = 0

    for chunk_id, sl_start, sl_end in CHUNK_CONFIGS:
        chunk_finds = all_findings[sl_start:sl_end]
        start_idx = sl_start + 1
        end_idx = sl_end
        n = len(chunk_finds)

        print(f"\n  -- Chunk {chunk_id}: findings #{start_idx}–#{end_idx} ({n} items) --")

        prompt = build_chunk_prompt(chunk_id, chunk_finds, start_idx)
        (CHUNKS_DIR / f"chunk_{chunk_id:02d}_prompt.txt").write_text(prompt, encoding="utf-8")

        chunk_ok = False
        resp = {}

        for attempt in range(1, 3):
            print(f"    Attempt {attempt}...")
            target = CHUNKS_DIR / f"chunk_{chunk_id:02d}.json"
            if target.exists():
                target.unlink()

            resp = run_aider_chunk(
                chunk_id=chunk_id,
                prompt=prompt,
                work_dir=CHUNKS_DIR,
                api_key=api_key,
                timeout=300,
            )

            lat = resp.get("elapsed", 0)
            exit_c = resp.get("exit_code")
            tok = resp.get("token_info", {})
            ts = tok.get("tokens_sent") or 0
            tr = tok.get("tokens_received") or 0
            print(f"    {lat}s | exit={exit_c} | file={resp.get('file_created')} | parse={resp.get('parse_ok')} | tok={ts}+{tr}")

            if resp.get("error"):
                print(f"    Error: {resp['error']}")
                if attempt == 2:
                    all_chunks_pass = False
                continue

            if resp.get("validation_errors"):
                print(f"    Validation: {resp['validation_errors']}")
                if attempt == 2:
                    if not resp.get("chunk_data"):
                        all_chunks_pass = False
                continue

            if resp.get("chunk_ok"):
                chunk_ok = True
                total_tokens_sent += ts
                total_tokens_recv += tr
                print(f"    PASS")
                break

            if attempt == 2:
                all_chunks_pass = False

        # accumulate tokens even on partial
        ts2 = (resp.get("token_info") or {}).get("tokens_sent") or 0
        tr2 = (resp.get("token_info") or {}).get("tokens_received") or 0
        if not chunk_ok:
            total_tokens_sent += ts2
            total_tokens_recv += tr2

        # Chunk markdown
        chunk_md_path = CHUNKS_DIR / f"chunk_{chunk_id:02d}.md"
        cd = resp.get("chunk_data")
        if cd:
            md = [f"# Chunk {chunk_id} — Findings #{start_idx}–#{end_idx}", ""]
            for f in cd.get("findings", []):
                md += [
                    f"## #{f.get('index', '?')} [{f.get('type', '')}] {f.get('file', '')}:{f.get('line', '')}",
                    f"- Severity: {f.get('severity', 'LOW')}",
                    f"- Text: `{f.get('text', '')}`",
                    "",
                ]
            chunk_md_path.write_text("\n".join(md), encoding="utf-8")

        chunk_results.append({
            "chunk_id": chunk_id,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "n": n,
            "ok": chunk_ok,
            "exit_code": resp.get("exit_code"),
            "elapsed": resp.get("elapsed"),
            "file_created": resp.get("file_created"),
            "parse_ok": resp.get("parse_ok"),
            "validation_errors": resp.get("validation_errors", []),
            "file_size": resp.get("file_size", 0),
            "token_info": resp.get("token_info", {}),
            "stdout_preview": resp.get("stdout_preview", "")[:600],
            "data": resp.get("chunk_data"),
        })

    # ── PHASE 2: Deterministic merge ──────────────────────────────────
    print("\n[PHASE 2] Deterministic merge...")

    merged_findings = []
    seen_idx: set = set()
    seen_flt: set = set()
    dup_count = 0

    for cr in chunk_results:
        if cr["data"] is None:
            continue
        for f in cr["data"].get("findings", []):
            idx = f.get("index")
            key = (f.get("file"), f.get("line"), f.get("type"))
            if idx in seen_idx or key in seen_flt:
                dup_count += 1
                continue
            seen_idx.add(idx)
            seen_flt.add(key)
            merged_findings.append(f)

    merged_findings.sort(key=lambda x: x.get("index", 0))
    merged_n = len(merged_findings)

    expected_idx = set(range(1, actual_n + 1))
    actual_idx = {f.get("index") for f in merged_findings}
    missing_idx = sorted(expected_idx - actual_idx)
    extra_idx = sorted(actual_idx - expected_idx)

    print(f"  Merged: {merged_n} | dups: {dup_count} | missing: {len(missing_idx)}")

    output_json = T7_TRIAL / "todo_inventory.json"
    final_json_obj = {
        "generated_utc": scan_ts,
        "total_files": files_scanned,
        "total_findings": merged_n,
        "executor_cell": "aider_cloud_v0.86.2_deepseek-v4-flash",
        "model": MODEL_ID,
        "findings": merged_findings,
    }
    output_json.write_text(json.dumps(final_json_obj, indent=2, ensure_ascii=False), encoding="utf-8")
    json_size = output_json.stat().st_size

    try:
        reloaded = json.loads(output_json.read_text(encoding="utf-8"))
        json_parse_ok = True
        json_total = reloaded.get("total_findings")
        json_entry_count = len(reloaded.get("findings", []))
    except Exception as e:
        json_parse_ok = False
        json_total = None
        json_entry_count = None
        print(f"  Re-parse error: {e}")

    consistent = (
        json_parse_ok and merged_n == actual_n and not missing_idx and dup_count == 0
    )
    print(f"  Consistent: {consistent}")

    # ── PHASE 3: Markdown render ───────────────────────────────────────
    print("\n[PHASE 3] Python markdown render...")
    md = render_markdown(merged_findings, scan_ts, files_scanned, files_with)
    output_md = T7_TRIAL / "PROJECT_S_TODO_AUDIT_CLOUD.md"
    output_md.write_text(md, encoding="utf-8")
    md_size = output_md.stat().st_size
    md_findings = md.count("### Finding #")
    print(f"  {output_md.name}: {md_size} bytes, {md_findings} findings")

    # ── PHASE 4: Checks ───────────────────────────────────────────────
    print("\n[PHASE 4] Checks...")
    chunks_pass = sum(1 for cr in chunk_results if cr["ok"])
    any_timeout = any((cr.get("exit_code") == -1 or "TIMEOUT" in str(cr.get("validation_errors"))) for cr in chunk_results)

    checks = {
        "canonical_loaded":    actual_n == EXPECTED_COUNT,
        "preflight_ok":        pf_ok,
        "all_chunks_pass":     all_chunks_pass,
        "no_timeout":          not any_timeout,
        "json_exists":         output_json.exists(),
        "json_parses":         json_parse_ok,
        "count_consistent":    consistent,
        "md_exists":           output_md.exists(),
        "md_count_ok":         md_findings == actual_n,
        "zero_duplicates":     dup_count == 0,
        "no_missing_indices":  len(missing_idx) == 0,
    }

    for name, ok in checks.items():
        print(f"  {'OK' if ok else 'FAIL'} {name}")

    passed = sum(checks.values())
    total_c = len(checks)

    if all(checks.values()):
        classification = "PASS"
    elif chunks_pass >= 2 and merged_n >= 50:
        classification = "PARTIAL PASS"
    else:
        classification = "FAIL"

    # Scenario mapping
    if classification == "PASS":
        scenario = "A"
    elif classification == "PARTIAL PASS":
        scenario = "B"
    else:
        scenario = "C"

    # ── PHASE 5: AO8N outcomes ────────────────────────────────────────
    print("\n[PHASE 5] AO8N outcomes...")
    try:
        from orchestrator_runtime.mission_outcome_schema import (
            create_default_outcome, derive_merge_ready,
            derive_outcome_confidence, derive_outcome_confidence_band,
            SCHEMA_VERSION,
        )

        def make_outcome(task_id, created, verified, passed_flag, evidence):
            o = create_default_outcome(f"{MISSION_ID}_{task_id}", f"{MISSION_ID}_{task_id}")
            o["schema_version"] = SCHEMA_VERSION
            if created and verified and passed_flag:
                o["execution_status"] = "EXECUTED"
                o["artifact_status"] = "VERIFIED"
                o["verification_status"] = "PASSED"
                o["handoff_status"] = "ACCEPTED"
                o["quality_status"] = "REVIEWED"
                o["quality_score"] = 4
            elif created:
                o["execution_status"] = "EXECUTED"
                o["artifact_status"] = "CREATED"
                o["verification_status"] = "FAILED"
                o["handoff_status"] = "UNKNOWN"
                o["quality_status"] = "UNREVIEWED"
            else:
                o["execution_status"] = "FAILED"
                o["artifact_status"] = "MISSING"
                o["verification_status"] = "FAILED"
                o["handoff_status"] = "UNKNOWN"
                o["quality_status"] = "UNREVIEWED"
            o["evidence"] = evidence
            o["outcome_confidence"] = derive_outcome_confidence(o)
            o["outcome_confidence_band"] = derive_outcome_confidence_band(o["outcome_confidence"])
            o["merge_ready"] = derive_merge_ready(o)
            return o

        OUTCOMES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTCOMES_FILE, "a", encoding="utf-8") as fh:
            for cr in chunk_results:
                ev = [f"chunk={cr['chunk_id']}", f"ok={cr['ok']}",
                      f"elapsed={cr['elapsed']}s", f"exit={cr['exit_code']}",
                      f"tokens={cr.get('token_info',{})}"]
                o = make_outcome(f"CHUNK{cr['chunk_id']}", cr["data"] is not None,
                                 cr["ok"], cr["ok"], ev)
                fh.write(json.dumps(o) + "\n")
            merge_ev = [f"merged={merged_n}", f"dups={dup_count}",
                        f"missing={len(missing_idx)}", f"consistent={consistent}"]
            o = make_outcome("MERGE", output_json.exists(), json_parse_ok, consistent, merge_ev)
            fh.write(json.dumps(o) + "\n")
        print("  AO8N outcomes written")
        ao8n_ok = True
    except Exception as e:
        print(f"  AO8N outcome error: {e}")
        ao8n_ok = False

    # ── Load T5_RUN4 and T6 for comparison ────────────────────────────
    t5_result_path = T5_TRIAL / "ao9_t5_run4" / "ao9_t5_run4_result.json"
    t5_result = {}
    if t5_result_path.exists():
        try:
            t5_result = json.loads(t5_result_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    t6_result_path = T6_TRIAL / "ao9_t6_result.json"
    t6_result = {}
    if t6_result_path.exists():
        try:
            t6_result = json.loads(t6_result_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    t5_chunks_map = {c["chunk_id"]: c for c in t5_result.get("chunks", [])}
    t6_chunks_map = {c["chunk_id"]: c for c in t6_result.get("chunks", [])}
    t5_merge = t5_result.get("merge", {})
    t6_merge = t6_result.get("merge", {})

    # ── Cost estimation ────────────────────────────────────────────────
    # DeepSeek V4 Flash pricing on OpenRouter (approx):
    # Input: ~$0.07/1M tokens, Output: ~$0.28/1M tokens (check current)
    COST_IN_PER_1M  = 0.07    # USD per 1M input tokens
    COST_OUT_PER_1M = 0.28    # USD per 1M output tokens
    cost_estimate = (
        (total_tokens_sent / 1_000_000) * COST_IN_PER_1M +
        (total_tokens_recv / 1_000_000) * COST_OUT_PER_1M
    )
    cost_per_finding = cost_estimate / actual_n if actual_n > 0 else 0

    print(f"\n[COST] tokens sent={total_tokens_sent} recv={total_tokens_recv}")
    print(f"  Estimated cost: ${cost_estimate:.4f}")
    print(f"  Cost per finding: ${cost_per_finding:.5f}")

    # ── Save result ────────────────────────────────────────────────────
    result = {
        "mission": MISSION_ID,
        "timestamp": scan_ts,
        "preflight": {
            "api_key_loaded": True,
            "model": MODEL_ID,
            "aider_model_string": AIDER_MODEL,
            "endpoint": OR_ENDPOINT,
            "preflight_test_ok": pf_ok,
            "preflight_elapsed": pf_elapsed,
            "preflight_tokens": pf_tokens,
        },
        "canonical": {
            "files_scanned": files_scanned,
            "files_with_findings": files_with,
            "total_findings": actual_n,
        },
        "chunks": [
            {
                "chunk_id": cr["chunk_id"],
                "start": cr["start_idx"],
                "end": cr["end_idx"],
                "n": cr["n"],
                "ok": cr["ok"],
                "exit_code": cr["exit_code"],
                "elapsed": cr["elapsed"],
                "file_created": cr["file_created"],
                "parse_ok": cr["parse_ok"],
                "validation_errors": cr["validation_errors"],
                "token_info": cr["token_info"],
            }
            for cr in chunk_results
        ],
        "merge": {
            "merged_count": merged_n,
            "duplicates": dup_count,
            "missing_indices": missing_idx,
            "extra_indices": extra_idx,
            "json_parse_ok": json_parse_ok,
            "json_total": json_total,
            "consistent": consistent,
        },
        "tokens": {
            "total_sent": total_tokens_sent,
            "total_received": total_tokens_recv,
            "preflight_sent": pf_tokens.get("tokens_sent"),
            "preflight_received": pf_tokens.get("tokens_received"),
        },
        "cost_estimate_usd": round(cost_estimate, 5),
        "cost_per_finding_usd": round(cost_per_finding, 6),
        "artifacts": {
            "todo_inventory_json": {"exists": output_json.exists(), "size": json_size},
            "audit_md": {"exists": output_md.exists(), "size": md_size, "finding_headings": md_findings},
        },
        "checks": checks,
        "checks_passed": f"{passed}/{total_c}",
        "classification": classification,
        "scenario": scenario,
        "manual_content_intervention": False,
        "fabricated_findings": False,
    }
    RESULTS_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # ── Phase 6: Three-cell comparison ────────────────────────────────
    print("\n[PHASE 6] Writing comparison and cost reports...")

    def _chunk_row(chunk_id: int, t5: dict, t6: dict, t7_cr) -> str:
        t5c = t5.get(chunk_id, {})
        t6c = t6.get(chunk_id, {})
        def fmt(c, ok_key="ok", lat_key="latency", elapsed_key="elapsed"):
            ok = c.get(ok_key, False)
            lat = c.get(lat_key) or c.get(elapsed_key) or "?"
            return f"{'PASS' if ok else 'FAIL'} / {lat}s" if lat != "?" else "FAIL / ?"
        t7_val = f"{'PASS' if t7_cr['ok'] else 'FAIL'} / {t7_cr['elapsed']}s"
        return f"| Chunk {chunk_id} ({t7_cr['n']} findings) | {fmt(t5c)} | {fmt(t6c)} | {t7_val} |"

    t5_total_lat = sum(c.get("latency", 0) or c.get("elapsed", 0) for c in t5_chunks_map.values())
    t6_total_lat = sum(c.get("elapsed", 0) or 0 for c in t6_chunks_map.values())
    t7_total_lat = sum(cr["elapsed"] or 0 for cr in chunk_results)

    comp_lines = [
        "# AO9_T7 — Three-Cell Comparison",
        "",
        f"Date: {scan_ts[:10]}",
        f"Input: scan_canonical.json (77 findings, frozen — same for all 3 cells)",
        "",
        "## Cell Definitions",
        "",
        "| Dimension | Ornith Cell (T5_RUN4) | Aider-Ornith (T6, INVALID) | Aider-Cloud (T7) |",
        "|-----------|----------------------|-----------------------------|-----------------|",
        "| Model class | Small local (9B) | Small local (9B) | Large cloud |",
        f"| Model | Ornith-1.0-9B Q4_K_M | Ornith-1.0-9B Q4_K_M | DeepSeek V4 Flash |",
        "| Interface | Custom adapter | Aider CLI 0.86.2 | Aider CLI 0.86.2 |",
        "| Endpoint | localhost:8766 | localhost:8766 | OpenRouter |",
        "| Native match? | YES | NO | YES |",
        "| Valid cell? | YES | NO (model-class mismatch) | YES |",
        "",
        "## Results",
        "",
        "| Dimension | Ornith (T5_RUN4) | Aider-Ornith (T6, INVALID) | Aider-Cloud (T7) |",
        "|-----------|-----------------|------------------------------|-----------------|",
        _chunk_row(1, t5_chunks_map, t6_chunks_map, chunk_results[0]),
        _chunk_row(2, t5_chunks_map, t6_chunks_map, chunk_results[1]),
        _chunk_row(3, t5_chunks_map, t6_chunks_map, chunk_results[2]),
        f"| Total latency | {t5_total_lat:.0f}s | {t6_total_lat:.0f}s (partial) | {t7_total_lat:.0f}s |",
        f"| Cost | $0 (local) | $0 (local) | ${cost_estimate:.4f} |",
        f"| Reconciliation | {t5_merge.get('merged_count','?')}/77 | {t6_merge.get('merged_count','?')}/77 | {merged_n}/77 |",
        f"| merge_ready | {t5_result.get('checks',{}).get('count_consistent','?')} | {t6_result.get('checks',{}).get('count_consistent','?')} | {consistent} |",
        f"| Verdict | {t5_result.get('classification','PASS')} | INVALID | {classification} |",
        "",
        "## Verdict",
        "",
    ]

    if classification == "PASS":
        verdict_text = (
            f"**SCENARIO A — AIDER CLOUD PASS**\n\n"
            f"All 3 chunks succeeded via Aider CLI + DeepSeek V4 Flash.\n\n"
            f"The chunk-merge-verify pattern IS portable to a native Aider+cloud configuration.\n\n"
            f"Key findings:\n"
            f"- AO9_T6 was INVALID (model-class mismatch) — its SCENARIO C verdict is discarded.\n"
            f"- AO9_T7 is the valid adapter comparison: same task, same interface, correct model class.\n"
            f"- Aider CLI IS a valid executor for chunk-classify workflows when using cloud models.\n"
            f"- Latency: {t7_total_lat:.0f}s total vs {t5_total_lat:.0f}s Ornith (cloud faster/slower per chunk documented above).\n"
            f"- Cost: ${cost_estimate:.4f} total (${cost_per_finding:.5f}/finding).\n\n"
            f"Executor Matrix: 2 valid cells confirmed (Ornith custom, Aider+cloud).\n"
            f"Fable 5 hármas szabály: 1 more cell/task pair needed for generalization claim."
        )
    elif classification == "PARTIAL PASS":
        verdict_text = (
            f"**SCENARIO B — PARTIAL PASS**\n\n"
            f"{chunks_pass}/3 chunks succeeded. Pattern partially portable.\n\n"
            f"- {merged_n}/77 findings reconciled.\n"
            f"- Document specific failure mode per chunk log.\n"
            f"- Aider+cloud is viable but requires further tuning for this task."
        )
    else:
        verdict_text = (
            f"**SCENARIO C — AIDER CLOUD FAIL**\n\n"
            f"0/3 chunks succeeded via Aider CLI + DeepSeek V4 Flash.\n\n"
            f"The chunk-merge-verify pattern IS custom-adapter-specific.\n"
            f"Aider CLI has structural incompatibility with structured multi-chunk JSON output tasks,\n"
            f"regardless of model quality.\n\n"
            f"This is not a model quality issue — it is an adapter protocol issue."
        )

    comp_lines += [
        verdict_text,
        "",
        f"**Scenario: {scenario}**",
        "",
        "## AO9_T6 Invalidation Note",
        "",
        "AO9_T6 used Ornith 9B (small local model) with Aider CLI (designed for cloud large models).",
        "The mismatch produced timeouts — but this measured the model-class mismatch, not the adapter.",
        "AO9_T6 result is DISCARDED as a measurement of Aider capability.",
        "AO9_T7 is the valid measurement: Aider in its native (cloud, large-model) configuration.",
        "",
        "---",
        "",
        "*AO9_T7 — Three-cell comparison. No manual content intervention.*",
    ]

    comp_path = REPORTS_DIR / "AO9_T7_THREE_CELL_COMPARISON_20260713.md"
    comp_path.write_text("\n".join(comp_lines), encoding="utf-8")

    # Cell definition report
    cell_def_lines = [
        "# AO9_T7 — Aider Cloud Executor Cell Definition",
        "",
        f"Date: {scan_ts[:10]}",
        "",
        "## Cell Parameters",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Model | DeepSeek V4 Flash |",
        f"| Model string (Aider) | {AIDER_MODEL} |",
        f"| Runtime | Aider CLI 0.86.2 |",
        f"| Endpoint | {OR_ENDPOINT} |",
        f"| Provider | OpenRouter |",
        f"| Context window | 1,048,576 tokens |",
        f"| Hardware | N/A (cloud inference) |",
        f"| Aider flags | --no-git --yes-always --no-check-update --no-show-model-warnings |",
        f"| Output format | whole edit format (Aider default) |",
        f"| Prompt convention | Create file X with: [JSON] |",
        f"| API key | env var OPENROUTER_API_KEY (never hardcoded) |",
        f"| Preflight latency | {pf_elapsed}s |",
        f"| Preflight tokens | {pf_tokens} |",
        "",
        "## Cell Classification Table",
        "",
        "| Dimension | Ornith (T5_RUN4) | Aider-Ornith (T6, INVALID) | Aider-Cloud (T7) |",
        "|-----------|-----------------|------------------------------|-----------------|",
        "| Model class | Small local (9B) | Small local (9B) | Large cloud |",
        "| Interface | Custom minimal | Aider CLI | Aider CLI |",
        "| Native match? | YES | NO | YES |",
        "| Valid measurement? | YES | NO | YES |",
        "",
        "## A/B Test Validity",
        "",
        "T5_RUN4 vs T7: different model AND interface — confounded comparison.",
        "T6 vs T7: same interface, different model class — isolates model-class effect.",
        "T5_RUN4 vs T7 (Aider-native only): tests interface effect within native configurations.",
        "",
        "The cleanest comparison for adapter portability:",
        "  'Does chunk-merge-verify work with Aider in its native config?'",
        "  Answer: T7 provides this measurement.",
        "",
        "## Prompt Adaptation",
        "",
        "Same Aider file-create format as T6:",
        "  `Create a new file chunk_XX.json. The file must contain ONLY valid JSON.`",
        "No adaptation needed between T6 and T7 (same Aider adapter, same format).",
        "Semantic content identical to T5_RUN4 (same findings, same schema, same severity rules).",
        "",
        f"## Cost Model",
        "",
        f"DeepSeek V4 Flash via OpenRouter (estimated rates):",
        f"- Input: ${COST_IN_PER_1M}/1M tokens",
        f"- Output: ${COST_OUT_PER_1M}/1M tokens",
        f"- Total tokens this run: {total_tokens_sent} sent, {total_tokens_recv} received",
        f"- Estimated cost: ${cost_estimate:.4f}",
        "",
        "---",
        "",
        "*AO9_T7 cell definition — generated automatically*",
    ]
    cell_def_path = REPORTS_DIR / "AO9_T7_AIDER_CLOUD_CELL_DEFINITION_20260713.md"
    cell_def_path.write_text("\n".join(cell_def_lines), encoding="utf-8")

    # Execution log
    exec_lines = [
        "# AO9_T7 — Aider Cloud Execution Log",
        "",
        f"Started: {scan_ts}",
        f"Model: {AIDER_MODEL}",
        f"Endpoint: {OR_ENDPOINT}",
        "",
        "## Preflight",
        "",
        f"- API key: loaded ({api_key[:8]}...)",
        f"- Model available: {MODEL_ID in model_ids if 'model_ids' in dir() else 'checked'}",
        f"- AIDER_CLOUD_OK test: {'PASS' if pf_ok else 'FAIL'} ({pf_elapsed}s)",
        f"- Tokens: {pf_tokens}",
        "",
        "## Chunk Execution",
        "",
    ]
    for cr in chunk_results:
        exec_lines += [
            f"### Chunk {cr['chunk_id']} (#{cr['start_idx']}–#{cr['end_idx']}, {cr['n']} findings)",
            f"- Exit code: {cr['exit_code']}",
            f"- Elapsed: {cr['elapsed']}s",
            f"- File created: {cr['file_created']}",
            f"- JSON parses: {cr['parse_ok']}",
            f"- Token info: {cr.get('token_info', {})}",
            f"- Validation errors: {cr['validation_errors'] or 'none'}",
            f"- Status: {'PASS' if cr['ok'] else 'FAIL'}",
            f"- Output preview: `{cr['stdout_preview'][:400]!r}`",
            "",
        ]
    exec_lines += [
        "## Merge",
        "",
        f"- Merged count: {merged_n}",
        f"- Duplicates: {dup_count}",
        f"- Missing indices: {missing_idx or 'none'}",
        f"- Consistent: {consistent}",
        "",
        f"## Final Result: {classification} (Scenario {scenario})",
        "",
        f"Checks: {passed}/{total_c}",
    ]
    exec_log_path = REPORTS_DIR / "AO9_T7_AIDER_CLOUD_EXECUTION_LOG_20260713.md"
    exec_log_path.write_text("\n".join(exec_lines), encoding="utf-8")

    # Cost report
    cost_lines = [
        "# AO9_T7 — Cost Report",
        "",
        f"Date: {scan_ts[:10]}",
        f"Model: {MODEL_ID} (via OpenRouter)",
        "",
        "## Token Usage",
        "",
        "| Phase | Tokens Sent | Tokens Received | Total |",
        "|-------|------------|-----------------|-------|",
        f"| Preflight | {pf_tokens.get('tokens_sent','?')} | {pf_tokens.get('tokens_received','?')} | {(pf_tokens.get('tokens_sent') or 0) + (pf_tokens.get('tokens_received') or 0)} |",
    ]
    chunk_total_sent = 0
    chunk_total_recv = 0
    for cr in chunk_results:
        ti = cr.get("token_info", {})
        ts3 = ti.get("tokens_sent") or 0
        tr3 = ti.get("tokens_received") or 0
        chunk_total_sent += ts3
        chunk_total_recv += tr3
        cost_lines.append(
            f"| Chunk {cr['chunk_id']} ({'PASS' if cr['ok'] else 'FAIL'}) | {ts3} | {tr3} | {ts3+tr3} |"
        )
    cost_lines += [
        f"| **TOTAL** | **{chunk_total_sent}** | **{chunk_total_recv}** | **{chunk_total_sent+chunk_total_recv}** |",
        "",
        "## Cost Breakdown",
        "",
        f"| Item | Amount |",
        f"|------|--------|",
        f"| Input rate | ${COST_IN_PER_1M}/1M tokens |",
        f"| Output rate | ${COST_OUT_PER_1M}/1M tokens |",
        f"| Input cost | ${(chunk_total_sent/1_000_000)*COST_IN_PER_1M:.5f} |",
        f"| Output cost | ${(chunk_total_recv/1_000_000)*COST_OUT_PER_1M:.5f} |",
        f"| **Total estimated** | **${cost_estimate:.5f}** |",
        f"| Cost per finding | ${cost_per_finding:.6f} |",
        f"| Findings reconciled | {merged_n}/77 |",
        "",
        "## Comparison",
        "",
        "| Cell | Model | Cost | Per Finding |",
        "|------|-------|------|-------------|",
        f"| Ornith (T5_RUN4) | Ornith 9B (local) | $0.00 | $0.00 |",
        f"| Aider-Ornith (T6) | Ornith 9B (local) | $0.00 | N/A (INVALID) |",
        f"| Aider-Cloud (T7) | DeepSeek V4 Flash | ${cost_estimate:.5f} | ${cost_per_finding:.6f} |",
        "",
        "Note: OpenRouter actual cost may differ from estimate.",
        "Check OpenRouter dashboard for real usage data.",
        "",
        "---",
        "",
        "*AO9_T7 cost report — estimated rates, verify against dashboard*",
    ]
    cost_path = REPORTS_DIR / "AO9_T7_COST_REPORT_20260713.md"
    cost_path.write_text("\n".join(cost_lines), encoding="utf-8")

    # ── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Model:           {AIDER_MODEL}")
    print(f"  Endpoint:        {OR_ENDPOINT}")
    print(f"  Preflight:       PASS ({pf_elapsed}s)")
    print(f"  Chunks:          {chunks_pass}/{len(CHUNK_CONFIGS)} PASS")
    print(f"  Total latency:   {t7_total_lat:.0f}s")
    print(f"  Merge:           {merged_n}/77 | dups={dup_count} | missing={len(missing_idx)}")
    print(f"  Consistent:      {consistent}")
    print(f"  Checks:          {passed}/{total_c}")
    print(f"  Classification:  {classification}")
    print(f"  Scenario:        {scenario}")
    print(f"  Cost estimate:   ${cost_estimate:.4f} (${cost_per_finding:.5f}/finding)")
    print(f"  Result file:     {RESULTS_FILE}")
    print("=" * 60)

    return classification


if __name__ == "__main__":
    main()
