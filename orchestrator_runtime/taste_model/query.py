"""
query.py — Taste Model query CLI.

Usage:
  python query.py --recent N          # last N missions
  python query.py --pattern X        # missions containing pattern X
  python query.py --model X          # missions using model X
  python query.py --value-min X      # missions with value >= X
  python query.py --value-max X      # missions with value <= X
  python query.py --stats            # summary statistics (text + JSON)
  python query.py --list             # all missions, one line each

Pure Python stdlib — no external dependencies.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

# ── Load data ──────────────────────────────────────────────────────────

_HERE = Path(__file__).parent
_LOG_FILE = _HERE / "mission_outcomes.jsonl"


def _load() -> list[dict]:
    if not _LOG_FILE.exists():
        print(f"[taste_model] No data file found at {_LOG_FILE}", file=sys.stderr)
        return []
    records = []
    with open(_LOG_FILE, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                print(f"[taste_model] WARN: corrupt line {lineno}: {exc}", file=sys.stderr)
    return records


# ── Formatters ─────────────────────────────────────────────────────────

def _fmt_one(r: dict) -> str:
    patterns = ", ".join(r.get("patterns", []))
    rv = r.get("runtime_validated")
    rv_str = "✓" if rv is True else ("~" if rv == "partial" else "✗")
    return (
        f"  {r['mission_id']:<12} {r['date']}  v={r['value_immediate']}  {rv_str}  "
        f"model={r.get('model_used','?')}\n"
        f"    status: {r.get('actual_status','?')}  patterns: [{patterns}]\n"
        f"    notes:  {r.get('notes','')}"
    )


# ── Subcommand handlers ────────────────────────────────────────────────

def cmd_list(records: list[dict]) -> None:
    if not records:
        print("No records.")
        return
    print(f"{'ID':<12} {'Date':<12} {'v':>2}  {'Model':<24} {'Actual Status'}")
    print("-" * 80)
    for r in records:
        print(
            f"{r['mission_id']:<12} {r['date']:<12} {r['value_immediate']:>2}  "
            f"{r.get('model_used','?'):<24} {r.get('actual_status','?')}"
        )
    print(f"\nTotal: {len(records)} records")


def cmd_recent(records: list[dict], n: int) -> None:
    subset = records[-n:]
    if not subset:
        print("No records.")
        return
    print(f"Last {len(subset)} mission(s):\n")
    for r in subset:
        print(_fmt_one(r))
        print()


def cmd_pattern(records: list[dict], pattern: str) -> None:
    matches = [r for r in records if pattern in r.get("patterns", [])]
    if not matches:
        print(f"No missions found with pattern '{pattern}'.")
        return
    print(f"Missions with pattern '{pattern}' ({len(matches)}):\n")
    for r in matches:
        print(_fmt_one(r))
        print()


def cmd_model(records: list[dict], model: str) -> None:
    matches = [r for r in records if r.get("model_used", "") == model]
    if not matches:
        print(f"No missions found for model '{model}'.")
        return
    print(f"Missions using model '{model}' ({len(matches)}):\n")
    for r in matches:
        print(_fmt_one(r))
        print()


def cmd_value_min(records: list[dict], vmin: int) -> None:
    matches = [r for r in records if r.get("value_immediate", 0) >= vmin]
    if not matches:
        print(f"No missions with value >= {vmin}.")
        return
    print(f"Missions with value >= {vmin} ({len(matches)}):\n")
    for r in matches:
        print(_fmt_one(r))
        print()


def cmd_value_max(records: list[dict], vmax: int) -> None:
    matches = [r for r in records if r.get("value_immediate", 99) <= vmax]
    if not matches:
        print(f"No missions with value <= {vmax}.")
        return
    print(f"Missions with value <= {vmax} ({len(matches)}):\n")
    for r in matches:
        print(_fmt_one(r))
        print()


def cmd_stats(records: list[dict]) -> None:
    if not records:
        print("No records.")
        return

    values = [r["value_immediate"] for r in records]
    avg = statistics.mean(values)
    median = statistics.median(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0

    model_counts: Counter = Counter(r.get("model_used", "?") for r in records)
    pattern_counts: Counter = Counter()
    for r in records:
        for p in r.get("patterns", []):
            pattern_counts[p] += 1
    status_counts: Counter = Counter(r.get("actual_status", "?") for r in records)

    by_model: dict[str, list[int]] = {}
    for r in records:
        m = r.get("model_used", "?")
        by_model.setdefault(m, []).append(r["value_immediate"])
    model_avgs = {m: statistics.mean(vs) for m, vs in by_model.items()}

    # ── Text output ──
    print("=" * 60)
    print("  TASTE MODEL — STATISTICS")
    print("=" * 60)
    print(f"  Total missions : {len(records)}")
    print(f"  Value avg      : {avg:.2f}")
    print(f"  Value median   : {median:.1f}")
    print(f"  Value stdev    : {stdev:.2f}")
    print(f"  Value range    : {min(values)} – {max(values)}")
    print()
    print("  Value distribution:")
    for v in range(1, 6):
        count = values.count(v)
        bar = "█" * count
        print(f"    {v}: {bar} ({count})")
    print()
    print("  By model (avg value):")
    for m, mavg in sorted(model_avgs.items(), key=lambda x: -x[1]):
        cnt = model_counts[m]
        print(f"    {m:<28} avg={mavg:.2f}  n={cnt}")
    print()
    print("  Actual status breakdown:")
    for s, cnt in status_counts.most_common():
        print(f"    {s:<32} {cnt}")
    print()
    print("  Top 10 patterns:")
    for p, cnt in pattern_counts.most_common(10):
        print(f"    {p:<36} {cnt}")
    print("=" * 60)
    print()

    # ── JSON output ──
    stats_dict = {
        "total": len(records),
        "value_avg": round(avg, 3),
        "value_median": median,
        "value_stdev": round(stdev, 3),
        "value_min": min(values),
        "value_max": max(values),
        "by_model": {m: {"avg": round(a, 3), "count": model_counts[m]} for m, a in model_avgs.items()},
        "status_breakdown": dict(status_counts.most_common()),
        "top_patterns": dict(pattern_counts.most_common(10)),
    }
    print("JSON:")
    print(json.dumps(stats_dict, indent=2, ensure_ascii=False))


# ── Main ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Taste Model query CLI — query mission_outcomes.jsonl"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--recent", type=int, metavar="N", help="Last N missions")
    g.add_argument("--pattern", metavar="X", help="Missions containing pattern X")
    g.add_argument("--model", metavar="X", help="Missions using model X")
    g.add_argument("--value-min", type=int, metavar="X", help="Missions with value >= X")
    g.add_argument("--value-max", type=int, metavar="X", help="Missions with value <= X")
    g.add_argument("--stats", action="store_true", help="Summary statistics")
    g.add_argument("--list", action="store_true", dest="listall", help="All missions, one line each")

    args = parser.parse_args()
    records = _load()

    if args.recent is not None:
        cmd_recent(records, args.recent)
    elif args.pattern:
        cmd_pattern(records, args.pattern)
    elif args.model:
        cmd_model(records, args.model)
    elif args.value_min is not None:
        cmd_value_min(records, args.value_min)
    elif args.value_max is not None:
        cmd_value_max(records, args.value_max)
    elif args.stats:
        cmd_stats(records)
    elif args.listall:
        cmd_list(records)


if __name__ == "__main__":
    main()
