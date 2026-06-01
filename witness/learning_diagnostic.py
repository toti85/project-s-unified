"""
witness/learning_diagnostic.py
-------------------------------
Read-only diagnostic scan over memory/intelligence/learning.jsonl.

PURPOSE:
    Understand the nature of any parsing bugs in learning.jsonl.
    Report field inventory, error categories, temporal distribution,
    and sampled records.

WHAT THIS MODULE DOES NOT DO:
    - Does NOT modify learning.jsonl
    - Does NOT modify self_state.json
    - Does NOT call AI or subprocesses

ONLY Python stdlib. Streaming — does not load entire file into memory.
Output: Markdown report in witness/reports/

Usage:
    python -m witness.learning_diagnostic

Exit codes:
    0 — scan complete, report written
    1 — learning.jsonl not found
    2 — unexpected I/O error
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
LEARNING_FILE = REPO_ROOT / "memory" / "intelligence" / "learning.jsonl"
REPORTS_DIR = REPO_ROOT / "witness" / "reports"


# ---------------------------------------------------------------------------
# Core scan
# ---------------------------------------------------------------------------

def run_diagnostic() -> dict:
    """
    Stream-read learning.jsonl, collect stats, return result dict.
    Does not write anything.
    """
    scan_start = time.monotonic()

    # ── Counters ─────────────────────────────────────────────────────────────
    total_lines: int = 0
    empty_lines: int = 0
    ok_records: int = 0
    error_records: int = 0

    # Error categories
    error_categories: dict = {
        "JSONDecodeError_expecting_value": 0,
        "JSONDecodeError_extra_data": 0,
        "JSONDecodeError_other": 0,
        "UnicodeDecodeError": 0,
        "empty_line": 0,
        "concatenated_json": 0,
        "other": 0,
    }

    # Error samples (first 3)
    error_samples: list = []   # [{"line_num": int, "category": str, "raw": str}]

    # OK samples
    ok_samples_first: list = []   # first 3
    ok_last: dict | None = None   # last successful record

    # Field inventory across all OK records
    field_counts: dict = {}    # top-level key -> count

    # Timestamp analysis
    timestamps: list = []      # all valid timestamps

    # Error line numbers
    error_line_nums: list = []

    # ── Streaming read ───────────────────────────────────────────────────────
    with open(LEARNING_FILE, encoding="utf-8", errors="replace") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            total_lines += 1
            line = raw_line.rstrip("\n")

            # Empty line
            if not line.strip():
                empty_lines += 1
                error_records += 1
                error_categories["empty_line"] += 1
                error_line_nums.append(line_num)
                if len(error_samples) < 3:
                    error_samples.append({
                        "line_num": line_num,
                        "category": "empty_line",
                        "raw": "(empty)",
                    })
                continue

            # Detect concatenated JSON heuristic: }{  or }{ with whitespace
            stripped = line.strip()
            if "}{" in stripped or "} {" in stripped:
                error_records += 1
                error_categories["concatenated_json"] += 1
                error_line_nums.append(line_num)
                if len(error_samples) < 3:
                    error_samples.append({
                        "line_num": line_num,
                        "category": "concatenated_json",
                        "raw": stripped[:200],
                    })
                continue

            # JSON parse
            try:
                rec = json.loads(stripped)
            except json.JSONDecodeError as exc:
                error_records += 1
                msg = str(exc).lower()
                if "expecting value" in msg:
                    cat = "JSONDecodeError_expecting_value"
                elif "extra data" in msg:
                    cat = "JSONDecodeError_extra_data"
                else:
                    cat = "JSONDecodeError_other"
                error_categories[cat] += 1
                error_line_nums.append(line_num)
                if len(error_samples) < 3:
                    error_samples.append({
                        "line_num": line_num,
                        "category": cat,
                        "detail": str(exc)[:120],
                        "raw": stripped[:200],
                    })
                continue
            except Exception as exc:
                error_records += 1
                error_categories["other"] += 1
                error_line_nums.append(line_num)
                if len(error_samples) < 3:
                    error_samples.append({
                        "line_num": line_num,
                        "category": "other",
                        "detail": str(exc)[:120],
                        "raw": stripped[:200],
                    })
                continue

            # Successfully parsed
            ok_records += 1

            # Field inventory
            if isinstance(rec, dict):
                for k in rec.keys():
                    field_counts[k] = field_counts.get(k, 0) + 1

            # Timestamp collection
            if isinstance(rec, dict):
                ts = rec.get("timestamp") or rec.get("ts") or rec.get("created_at") or rec.get("time")
                if ts and isinstance(ts, str) and len(ts) >= 10:
                    timestamps.append(ts)

            # Samples
            if len(ok_samples_first) < 3:
                ok_samples_first.append({
                    "line_num": line_num,
                    "rec": _truncate_dict(rec, 200),
                })
            ok_last = {"line_num": line_num, "rec": _truncate_dict(rec, 200)}

    scan_duration = time.monotonic() - scan_start

    # ── Temporal analysis ────────────────────────────────────────────────────
    ts_first: str | None = None
    ts_last: str | None = None
    daily_counts: dict = {}

    if timestamps:
        timestamps_sorted = sorted(timestamps)
        ts_first = timestamps_sorted[0]
        ts_last = timestamps_sorted[-1]
        for ts in timestamps:
            day = ts[:10]
            daily_counts[day] = daily_counts.get(day, 0) + 1

    top_days = sorted(daily_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # ── Field inventory percentages ──────────────────────────────────────────
    field_pct: dict = {}
    if ok_records > 0:
        for k, cnt in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
            field_pct[k] = {"count": cnt, "pct": round(cnt / ok_records * 100, 1)}

    # Rare fields: present in < 50% of records
    rare_fields = {k: v for k, v in field_pct.items() if v["pct"] < 50.0}

    return {
        "scan_duration_seconds": round(scan_duration, 3),
        "total_lines": total_lines,
        "empty_lines": empty_lines,
        "ok_records": ok_records,
        "error_records": error_records,
        "error_rate_pct": round(error_records / total_lines * 100, 2) if total_lines else 0,
        "error_categories": {k: v for k, v in error_categories.items() if v > 0},
        "error_line_nums": error_line_nums,
        "error_samples": error_samples,
        "ok_samples_first": ok_samples_first,
        "ok_last": ok_last,
        "field_pct": field_pct,
        "rare_fields": rare_fields,
        "ts_first": ts_first,
        "ts_last": ts_last,
        "top_days": top_days,
    }


def _truncate_dict(rec, max_chars: int) -> str:
    """Serialize a record to string, truncated."""
    try:
        s = json.dumps(rec, ensure_ascii=False)
    except Exception:
        s = repr(rec)
    return s[:max_chars] + ("…" if len(s) > max_chars else "")


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def build_report(result: dict, today_str: str) -> str:
    """Build markdown report string from scan result."""
    L: list = []

    def h(text: str = "") -> None:
        L.append(text)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total = result["total_lines"]
    ok = result["ok_records"]
    errors = result["error_records"]

    h(f"# Learning Diagnostic Report")
    h()
    h(f"**Generálva:** {now_str}")
    h(f"**Forrás:** `{LEARNING_FILE}`")
    h(f"**Scan idő:** {result['scan_duration_seconds']:.3f} s")
    h()

    h("## Összefoglaló")
    h()
    h(f"| Metrika | Érték |")
    h(f"|---|---|")
    h(f"| Összes sor | {total} |")
    h(f"| Sikeresen parse-olt rekord | {ok} |")
    h(f"| Hibás sor | {errors} |")
    h(f"| Hiba arány | {result['error_rate_pct']:.2f}% |")
    h(f"| Üres sor | {result['empty_lines']} |")
    h()

    # Verdict
    if errors == 0:
        verdict = "**VERDIKT: NINCS AKTÍV BUG** — minden sor sikeresen parse-olható."
    elif result["error_rate_pct"] < 5.0:
        verdict = f"**VERDIKT: RÉSZLEGES BUG** — {errors} hibás sor ({result['error_rate_pct']:.2f}%), de a rekordok többsége rendben."
    else:
        verdict = f"**VERDIKT: AKTÍV BUG** — {result['error_rate_pct']:.2f}% hiba arány ({errors}/{total} sor)."
    h(verdict)
    h()

    h("## Hiba kategóriák")
    h()
    if result["error_categories"]:
        h("| Kategória | Darab |")
        h("|---|---|")
        for cat, cnt in sorted(result["error_categories"].items(), key=lambda x: x[1], reverse=True):
            h(f"| `{cat}` | {cnt} |")
        h()
        if result["error_line_nums"]:
            nums_str = ", ".join(str(n) for n in result["error_line_nums"][:20])
            suffix = f" ... (összesen: {len(result['error_line_nums'])})" if len(result["error_line_nums"]) > 20 else ""
            h(f"**Hibás sor számok:** {nums_str}{suffix}")
    else:
        h("Nincs hibás sor.")
    h()

    h("## Mező inventory (sikeresen parse-olt rekordok)")
    h()
    if result["field_pct"]:
        h("| Mező | Rekordok száma | % arány |")
        h("|---|---|---|")
        for k, v in result["field_pct"].items():
            h(f"| `{k}` | {v['count']} | {v['pct']}% |")
        h()
        if result["rare_fields"]:
            rare_keys = ", ".join(f"`{k}`" for k in result["rare_fields"])
            h(f"**Ritka mezők (<50%):** {rare_keys}")
    else:
        h("Nincs sikeresen parse-olt rekord.")
    h()

    h("## Időbeli eloszlás")
    h()
    if result["ts_first"]:
        h(f"- Első timestamp: `{result['ts_first']}`")
        h(f"- Utolsó timestamp: `{result['ts_last']}`")
        h()
        if result["top_days"]:
            h("**Top napok (rekordszám szerint):**")
            h()
            h("| Nap | Rekord |")
            h("|---|---|")
            for day, cnt in result["top_days"]:
                h(f"| {day} | {cnt} |")
    else:
        h("Nem található timestamp mező a rekordokban.")
    h()

    h("## Mintavétel — első 3 sikeres rekord")
    h()
    for i, s in enumerate(result["ok_samples_first"], 1):
        h(f"**Rekord #{i} (sor {s['line_num']}):**")
        h(f"```json")
        h(s["rec"])
        h(f"```")
        h()

    if result["ok_last"] and (not result["ok_samples_first"] or
                               result["ok_last"]["line_num"] != result["ok_samples_first"][-1]["line_num"]):
        h(f"**Utolsó sikeres rekord (sor {result['ok_last']['line_num']}):**")
        h(f"```json")
        h(result["ok_last"]["rec"])
        h(f"```")
        h()

    h("## Mintavétel — első 3 hibás sor")
    h()
    if result["error_samples"]:
        for i, s in enumerate(result["error_samples"], 1):
            h(f"**Hiba #{i} (sor {s['line_num']}, kategória: `{s['category']}`):**")
            if "detail" in s:
                h(f"- Részlet: `{s['detail']}`")
            h(f"```")
            h(s["raw"])
            h(f"```")
            h()
    else:
        h("Nincs hibás sor — nem volt minta.")
    h()

    return "\n".join(L)


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_summary(result: dict) -> None:
    sep = "=" * 60
    print(sep)
    print("  WITNESS — Learning Diagnostic")
    print(sep)
    print(f"  Fájl:          {LEARNING_FILE}")
    print(f"  Scan idő:      {result['scan_duration_seconds']:.3f}s")
    print(f"  Összes sor:    {result['total_lines']}")
    print(f"  OK rekord:     {result['ok_records']}")
    print(f"  Hibás sor:     {result['error_records']} ({result['error_rate_pct']:.2f}%)")
    print()

    if result["error_categories"]:
        print("  Hiba kategóriák:")
        for cat, cnt in sorted(result["error_categories"].items(), key=lambda x: x[1], reverse=True):
            print(f"    {cat}: {cnt}")
    else:
        print("  Hiba kategóriák: nincs")
    print()

    print("  Mező inventory (top mezők):")
    for k, v in list(result["field_pct"].items())[:10]:
        print(f"    {k}: {v['count']} ({v['pct']}%)")
    print()

    if result["ts_first"]:
        print(f"  Időszak: {result['ts_first'][:10]} → {result['ts_last'][:10]}")
        print()

    # Verdict
    errors = result["error_records"]
    rate = result["error_rate_pct"]
    if errors == 0:
        print("  VERDIKT: NINCS AKTÍV BUG")
    elif rate < 5.0:
        print(f"  VERDIKT: RÉSZLEGES BUG ({errors} hibás sor, {rate:.2f}%)")
    else:
        print(f"  VERDIKT: AKTÍV BUG ({rate:.2f}% hiba arány)")
    print(sep)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not LEARNING_FILE.exists():
        print(f"ERROR: {LEARNING_FILE} not found", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_diagnostic()
    except OSError as exc:
        print(f"ERROR: I/O error reading {LEARNING_FILE}: {exc}", file=sys.stderr)
        sys.exit(2)

    print_summary(result)

    # Build and write markdown report
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_content = build_report(result, today_str)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"learning_diagnostic_{today_str}.md"
    report_path.write_text(report_content, encoding="utf-8")

    print(f"\nJelentés mentve: {report_path}")
    sys.exit(0)
