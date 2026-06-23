"""
MS-AO8E Continue Executor Adapter — Project-S headless executor via `cn` CLI.

Wraps Continue CLI (`cn -p <prompt>`) as a subprocess-based executor.
Supports RISK_010-compliant outbox writes with checksum verification.

AO8I_1 additions:
  - Large file guard: rejects prompts referencing files >200 KB
  - Stale outbox preflight: detects unconsumed outbox before new run
  - Timeout clarity: TIMEOUT returns structured FAIL
  - Pre-run validation pipeline

Functions:
    run_continue_prompt(prompt, timeout_sec=180) -> dict
    run_and_write(prompt, run_id, ...) -> dict
    write_continue_output_to_outbox(run_id, content, ...) -> dict
    guard_large_file_in_prompt(prompt) -> dict
    check_stale_outbox() -> dict
    preflight_checks(prompt) -> dict
"""

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLINE_OUTBOX = PROJECT_ROOT / "orchestrator_runtime" / "cline_outbox"
SANDBOX_DIR = PROJECT_ROOT / "orchestrator_runtime" / "sandbox"

# ── Constants ──────────────────────────────────────────────────────────

DEFAULT_TIMEOUT_SEC = 180
MAX_FILE_SIZE_KB = 200            # AO8I_1: max file size for Continue to read
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_KB * 1024

# Full path to cn binary (npm global prefix)
_CN_PATH = Path(os.environ.get("NPM_PREFIX", "")) / "cn"
if _CN_PATH.exists():
    CN_CMD = str(_CN_PATH)
elif Path(r"C:\Users\Administrator\AppData\Roaming\npm\cn.cmd").exists():
    CN_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\cn.cmd"
elif Path(r"C:\Users\Administrator\AppData\Roaming\npm\cn").exists():
    CN_CMD = r"C:\Users\Administrator\AppData\Roaming\npm\cn"
else:
    CN_CMD = "cn"  # Fallback to PATH lookup

# ── File size patterns ─────────────────────────────────────────────────

# Regex to find file paths in prompt text
_FILE_PATH_PATTERN = re.compile(
    r'(?:read|open|load|get|cat|type|dump|show|summarize)\s+(?:file\s+)?'
    r'["\']?([a-zA-Z]:[\\/][^\s"\'<>|]+)["\']?',
    re.IGNORECASE
)

# Known large file extensions that are risky for Continue to process
_RISKY_EXTENSIONS = {'.md', '.txt', '.log', '.json', '.jsonl', '.csv', '.yaml', '.yml', '.xml'}

# ── Guard: Large file detection ────────────────────────────────────────

def guard_large_file_in_prompt(prompt: str) -> dict:
    """
    Scan prompt for referenced file paths and check their size.
    If any file > MAX_FILE_SIZE_KB, the guard rejects the prompt.

    Returns dict:
        allowed: bool
        reason: str | None
        files_checked: list[str]
        large_files: list[dict]  # path + size_kb for each oversized file
    """
    result = {
        "allowed": True,
        "reason": None,
        "files_checked": [],
        "large_files": [],
    }

    matches = _FILE_PATH_PATTERN.findall(prompt)

    for path_str in matches:
        file_path = Path(path_str)

        # If path is not absolute, try relative to PROJECT_ROOT
        if not file_path.is_absolute():
            candidate = PROJECT_ROOT / path_str
            if candidate.exists():
                file_path = candidate
            else:
                continue  # skip unresolvable paths

        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            size_kb = file_path.stat().st_size / 1024.0
        except OSError:
            continue

        result["files_checked"].append(str(file_path))

        if size_kb > MAX_FILE_SIZE_KB and file_path.suffix.lower() in _RISKY_EXTENSIONS:
            result["large_files"].append({
                "path": str(file_path),
                "size_kb": round(size_kb, 1),
                "threshold_kb": MAX_FILE_SIZE_KB,
            })

    if result["large_files"]:
        names = [f"\"{f['path']}\" ({f['size_kb']} KB)" for f in result["large_files"]]
        result["allowed"] = False
        result["reason"] = (
            f"Prompt references {len(result['large_files'])} large file(s) "
            f"exceeding {MAX_FILE_SIZE_KB} KB limit: {'; '.join(names)}. "
            f"Simplify task to use metadata-only summarization or mark NEEDS_HUMAN."
        )

    return result


# ── Guard: Stale outbox detection ──────────────────────────────────────

def check_stale_outbox() -> dict:
    """
    Check if cline_outbox/ has an unconsumed output_ready.json from a prior run.
    If stale, archive it and return a warning.

    Returns dict:
        stale: bool
        run_id: str | None
        timestamp: str | None
        action: str  # "none" | "archived" | "blocked"
        reason: str | None
    """
    result = {
        "stale": False,
        "run_id": None,
        "timestamp": None,
        "action": "none",
        "reason": None,
    }

    ready_path = CLINE_OUTBOX / "output_ready.json"
    if not ready_path.exists():
        return result

    try:
        with open(ready_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        result["stale"] = True
        result["action"] = "archived"
        result["reason"] = "output_ready.json exists but is unreadable — archived"
        _archive_outbox("unreadable_stale")
        return result

    consumed = data.get("consumed", False)
    run_id = data.get("run_id", "unknown")

    if not consumed:
        result["stale"] = True
        result["run_id"] = run_id
        result["timestamp"] = data.get("timestamp")
        result["action"] = "archived"
        result["reason"] = (
            f"Stale unconsumed outbox from run_id={run_id} "
            f"at {result['timestamp']}. Archived automatically."
        )
        _archive_outbox(run_id)
        return result

    # Already consumed — that's fine, no action needed
    return result


def _archive_outbox(label: str) -> None:
    """Move stale outbox files to a timestamped archive."""
    archive_dir = CLINE_OUTBOX / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    for fname in ["last_output.md", "output_ready.json"]:
        src = CLINE_OUTBOX / fname
        if src.exists():
            dst = archive_dir / f"{ts}_{label}_{fname}"
            src.rename(dst)
            logger.info("Archived stale outbox %s -> %s", src.name, dst.name)


# ── Preflight pipeline ─────────────────────────────────────────────────

def preflight_checks(prompt: str) -> dict:
    """
    Run all preflight checks before executing a Continue prompt.

    Returns dict:
        allowed: bool
        reason: str | None
        large_file_check: dict
        stale_outbox_check: dict
    """
    large_file_result = guard_large_file_in_prompt(prompt)
    stale_outbox_result = check_stale_outbox()

    if not large_file_result["allowed"]:
        return {
            "allowed": False,
            "reason": large_file_result["reason"],
            "large_file_check": large_file_result,
            "stale_outbox_check": stale_outbox_result,
        }

    if stale_outbox_result["stale"]:
        return {
            "allowed": True,
            "reason": stale_outbox_result["reason"] + " (archived, continuing)",
            "large_file_check": large_file_result,
            "stale_outbox_check": stale_outbox_result,
        }

    return {
        "allowed": True,
        "reason": None,
        "large_file_check": large_file_result,
        "stale_outbox_check": stale_outbox_result,
    }


# ── Core function: run Continue prompt ─────────────────────────────────

def run_continue_prompt(prompt: str, timeout_sec: int = DEFAULT_TIMEOUT_SEC) -> dict:
    """
    Execute a prompt via `cn -p <prompt>` and return structured result.

    AO8I_1: Runs preflight checks before executing.
    If preflight blocks, returns structured ERROR without running cn.

    Returns dict with keys:
        status: "OK" | "TIMEOUT" | "ERROR" | "PREFLIGHT_BLOCKED"
        stdout: str
        stderr: str
        exit_code: int | None
        latency_ms: float
        error: str | None
        preflight: dict | None
    """
    # ── Preflight ──────────────────────────────────────────────────────
    preflight = preflight_checks(prompt)
    if not preflight["allowed"]:
        return {
            "status": "PREFLIGHT_BLOCKED",
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "latency_ms": 0.0,
            "error": preflight["reason"],
            "preflight": preflight,
        }

    # ── Execute ────────────────────────────────────────────────────────
    start = time.perf_counter()
    result = {
        "status": None,
        "stdout": "",
        "stderr": "",
        "exit_code": None,
        "latency_ms": 0.0,
        "error": None,
        "preflight": preflight,
    }

    try:
        proc = subprocess.run(
            [CN_CMD, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace",
        )
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["exit_code"] = proc.returncode
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)

        if proc.returncode == 0:
            result["status"] = "OK"
        else:
            result["status"] = "ERROR"
            result["error"] = f"Exit code {proc.returncode}: {proc.stderr[:500]}"

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["error"] = f"Process timed out after {timeout_sec}s"
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
    except FileNotFoundError:
        result["status"] = "ERROR"
        result["error"] = f"'{CN_CMD}' not found on PATH. Is Continue CLI installed?"
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)

    # Sanitize: mask any API key patterns in output
    result["stdout"] = _sanitize_output(result["stdout"])
    result["stderr"] = _sanitize_output(result["stderr"])

    return result


def _sanitize_output(text: str) -> str:
    """Mask potential API key leaks in output."""
    # Mask sk-or-v1-... patterns
    text = re.sub(r'sk-or-v1-[a-zA-Z0-9]{32,64}', 'sk-or-v1-***MASKED***', text)
    # Mask sk-... patterns
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-***MASKED***', text)
    return text


# ── Checksum helper ────────────────────────────────────────────────────

def compute_checksum(file_path: Path) -> str:
    """SHA-256 of file contents, first 16 hex chars."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ── RISK_010-compliant outbox write ────────────────────────────────────

def write_continue_output_to_outbox(
    run_id: str,
    content: str,
    iteration: int = 1,
    metadata: dict | None = None,
) -> dict:
    """
    Write executor output to cline_outbox/ following RISK_010 protocol.

    RISK_010 mandatory order:
        1. Write last_output.md (FINAL — no more edits)
        2. Compute checksum from file bytes
        3. Write output_ready.json LAST
        4. STOP — never touch last_output.md after step 3

    Returns dict with keys:
        status: "OK" | "ERROR"
        output_path: str | None
        checksum: str | None
        error: str | None
    """
    result = {
        "status": None,
        "output_path": None,
        "checksum": None,
        "error": None,
    }

    # ── AO8J_2: Empty output guard ──
    if not content or not content.strip():
        logger.warning(f"Empty output for run_id={run_id} — not writing outbox")
        result["status"] = "EMPTY_OUTPUT"
        result["error"] = "Continue produced empty output"
        return result

    try:
        # Ensure outbox directory exists
        CLINE_OUTBOX.mkdir(parents=True, exist_ok=True)

        # ── Step 1: Write last_output.md (FINAL) ──
        # AO8J_4: Prepend Run ID / Goal ID header so CM can verify identity
        goal_id = (metadata or {}).get("goal_id", "unknown")
        header = f"Run ID: {run_id}\nGoal ID: {goal_id}\n\n"
        output_path = CLINE_OUTBOX / "last_output.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header + content)

        result["output_path"] = str(output_path)

        # ── Step 2: Compute checksum from file bytes ──
        checksum = compute_checksum(output_path)
        result["checksum"] = checksum

        # ── Step 3: Write output_ready.json LAST ──
        ready_data = {
            "run_id": run_id,
            "iteration": iteration,
            "checksum": checksum,
            "consumed": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            ready_data["metadata"] = metadata

        ready_path = CLINE_OUTBOX / "output_ready.json"
        tmp = ready_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ready_data, f, indent=4, ensure_ascii=False)
        tmp.replace(ready_path)

        # ── Step 4: STOP — never touch last_output.md again ──
        result["status"] = "OK"

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        logger.error(f"write_continue_output_to_outbox failed: {e}")

    return result


# ── Convenience: run prompt + write to outbox ──────────────────────────

def run_and_write(
    prompt: str,
    run_id: str,
    iteration: int = 1,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    metadata: dict | None = None,
) -> dict:
    """
    Run a Continue prompt and write result to outbox in one call.

    Returns combined dict with keys:
        run: result from run_continue_prompt
        outbox: result from write_continue_output_to_outbox
        overall: "OK" | "ERROR" | "PREFLIGHT_BLOCKED"
    """
    run_result = run_continue_prompt(prompt, timeout_sec=timeout_sec)

    if run_result["status"] == "PREFLIGHT_BLOCKED":
        # Preflight blocked: write a minimal outbox explaining why,
        # return structured PREFLIGHT_BLOCKED so CM can handle it
        block_msg = (
            f"🚫 PREFLIGHT BLOCK: {run_result.get('error', 'Unknown reason')}\n\n"
            f"Run {run_id} was not executed.\n"
        )
        outbox_result = write_continue_output_to_outbox(
            run_id=run_id,
            content=block_msg,
            iteration=iteration,
            metadata={**({"preflight": run_result.get("preflight", {})} if metadata is None else metadata), "blocked": True},
        )
        return {
            "run": run_result,
            "outbox": outbox_result,
            "overall": "PREFLIGHT_BLOCKED",
        }

    if run_result["status"] != "OK":
        return {
            "run": run_result,
            "outbox": None,
            "overall": "ERROR",
        }

    outbox_result = write_continue_output_to_outbox(
        run_id=run_id,
        content=run_result.get("stdout", ""),
        iteration=iteration,
        metadata=metadata,
    )

    # ── AO8J_2: empty output detected — return structured FAIL ──
    if outbox_result.get("status") == "EMPTY_OUTPUT":
        return {
            "run": run_result,
            "outbox": None,
            "overall": "EMPTY_OUTPUT",
            "reason": outbox_result.get("error", "Continue produced empty output"),
        }

    overall = "OK" if outbox_result["status"] == "OK" else "ERROR"

    return {
        "run": run_result,
        "outbox": outbox_result,
        "overall": overall,
    }


# ── CLI Entry Point ────────────────────────────────────────────────────

def _cli():
    """CLI wrapper for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Continue Executor Adapter CLI")
    sub = parser.add_subparsers(dest="command")

    # run
    run_p = sub.add_parser("run", help="Run a Continue prompt")
    run_p.add_argument("--prompt", required=True, help="Prompt to execute")
    run_p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC)

    # guard
    guard_p = sub.add_parser("guard", help="Test large file guard")
    guard_p.add_argument("--prompt", required=True)

    # stale
    stale_p = sub.add_parser("stale", help="Check stale outbox")
    stale_p.add_argument("--force-archive", action="store_true", help="Archive stale outbox")

    # write
    write_p = sub.add_parser("write", help="Write output to outbox")
    write_p.add_argument("--run-id", required=True)
    write_p.add_argument("--content", required=True)
    write_p.add_argument("--iteration", type=int, default=1)

    # run-and-write
    rw_p = sub.add_parser("run-and-write", help="Run prompt + write to outbox")
    rw_p.add_argument("--prompt", required=True)
    rw_p.add_argument("--run-id", required=True)
    rw_p.add_argument("--iteration", type=int, default=1)
    rw_p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC)

    args = parser.parse_args()

    if args.command == "run":
        result = run_continue_prompt(args.prompt, timeout_sec=args.timeout)
    elif args.command == "guard":
        result = guard_large_file_in_prompt(args.prompt)
    elif args.command == "stale":
        result = check_stale_outbox()
    elif args.command == "write":
        result = write_continue_output_to_outbox(
            run_id=args.run_id,
            content=args.content,
            iteration=args.iteration,
        )
    elif args.command == "run-and-write":
        result = run_and_write(
            prompt=args.prompt,
            run_id=args.run_id,
            iteration=args.iteration,
            timeout_sec=args.timeout,
        )
    else:
        parser.print_help()
        sys.exit(1)

    output = json.dumps(result, indent=4, ensure_ascii=False, default=str) + "\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.exit(0 if result.get("status") == "OK" or result.get("overall") == "OK" else 1)


if __name__ == "__main__":
    _cli()