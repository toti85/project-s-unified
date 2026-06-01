"""
witness/evidence_reader.py
--------------------------
Witness layer — első modulja.

Feladat: Olvassa a meta_evidence.jsonl-t streaming módon,
összesít statisztikákat, és frissíti a self_state.json-t.

Korlátok (Foundation.md — Governance First):
  - NEM ír a meta_evidence.jsonl-be
  - NEM hív AI modellt
  - NEM indít másik folyamatot
  - Csak Python stdlib
  - Atomikus írás (tmp + os.replace)

Futtatás:
  python -m witness.evidence_reader
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Útvonalak ---
REPO_ROOT = Path(__file__).parent.parent
META_EVIDENCE_PATH = REPO_ROOT / "memory" / "intelligence" / "meta_evidence.jsonl"
SELF_STATE_PATH = REPO_ROOT / "self_state.json"
SELF_STATE_TMP = REPO_ROOT / "self_state.json.tmp"

# Ismert event típusok (dinamikusan is gyűjtjük az egyébieket)
KNOWN_EVENTS = [
    "goal_started",
    "plan_selected",
    "execution_done",
    "validation_done",
    "replan_triggered",
    "goal_completed",
]


def scan_evidence(evidence_path: Path) -> dict:
    """
    Streameli a meta_evidence.jsonl-t, statisztikákat gyűjt.
    Nem tölti be egyszerre a memóriába.

    Returns:
        dict: scan eredménye
    """
    event_counts: dict[str, int] = {}
    unique_goal_ids: set[str] = set()
    total_records = 0
    parse_errors = 0
    first_timestamp = None
    last_timestamp = None
    last_goal_completed = None
    last_goal_started = None

    with open(evidence_path, encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            total_records += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue

            # --- Timestamp ---
            ts = record.get("timestamp")
            if ts:
                if first_timestamp is None:
                    first_timestamp = ts
                last_timestamp = ts

            # --- Event type ---
            event_type = record.get("event_type", "<missing_event_type>")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # --- Goal ID ---
            data = record.get("data", {})
            goal_id = data.get("goal_id") if isinstance(data, dict) else None
            if goal_id:
                unique_goal_ids.add(goal_id)

            # --- Utolsó goal_completed ---
            if event_type == "goal_completed":
                last_goal_completed = {
                    "goal_id": goal_id,
                    "timestamp": ts,
                    "iterations": data.get("iterations") if isinstance(data, dict) else None,
                }

            # --- Utolsó goal_started ---
            if event_type == "goal_started":
                last_goal_started = {
                    "goal_id": goal_id,
                    "timestamp": ts,
                    "goal": data.get("goal", "<unknown>") if isinstance(data, dict) else "<unknown>",
                }

    # Rendezett event_counts: ismert sorrendben elöl, többi mögötte
    ordered_counts: dict[str, int] = {}
    for key in KNOWN_EVENTS:
        ordered_counts[key] = event_counts.get(key, 0)
    for key, val in event_counts.items():
        if key not in ordered_counts:
            ordered_counts[key] = val

    return {
        "total_records": total_records,
        "first_record_time": first_timestamp,
        "last_record_time": last_timestamp,
        "event_counts": ordered_counts,
        "unique_goal_ids": len(unique_goal_ids),
        "last_completed_goal": last_goal_completed,
        "last_started_goal": last_goal_started,
        "parse_errors": parse_errors,
    }


def update_self_state(scan_result: dict, duration_seconds: float) -> None:
    """
    Frissíti a self_state.json-t az evidence_summary blokkal.
    Atomikus: tmp fájlba ír, majd os.replace().
    A többi mezőt NEM módosítja (kivéve last_updated).
    """
    # Beolvasás
    with open(SELF_STATE_PATH, encoding="utf-8") as f:
        state = json.load(f)

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # evidence_summary blokk összeállítása
    state["evidence_summary"] = {
        "last_scanned_at": now_utc,
        "scanner": "witness/evidence_reader.py",
        "scan_duration_seconds": round(duration_seconds, 3),
        "total_records": scan_result["total_records"],
        "first_record_time": scan_result["first_record_time"],
        "last_record_time": scan_result["last_record_time"],
        "event_counts": scan_result["event_counts"],
        "unique_goal_ids": scan_result["unique_goal_ids"],
        "last_completed_goal": scan_result["last_completed_goal"],
        "last_started_goal": scan_result["last_started_goal"],
        "parse_errors": scan_result["parse_errors"],
    }

    # last_updated frissítése a gyökérben
    state["last_updated"] = now_utc

    # Atomikus írás: tmp → os.replace
    tmp_path = SELF_STATE_TMP
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")

    os.replace(tmp_path, SELF_STATE_PATH)


def print_summary(scan_result: dict, duration: float) -> None:
    """Human-readable konzol kimenet."""
    sep = "=" * 60
    print(sep)
    print("  WITNESS — Evidence Reader")
    print(sep)
    print(f"  Fájl:           {META_EVIDENCE_PATH}")
    print(f"  Scan idő:       {duration:.2f}s")
    print(f"  Összes rekord:  {scan_result['total_records']:,}")
    print(f"  Parse hibák:    {scan_result['parse_errors']}")
    print(f"  Egyedi goal_id: {scan_result['unique_goal_ids']:,}")
    print(f"  Első rekord:    {scan_result['first_record_time']}")
    print(f"  Utolsó rekord:  {scan_result['last_record_time']}")
    print()
    print("  Event counts:")
    for event_type, count in scan_result["event_counts"].items():
        print(f"    {event_type:<30} {count:>8,}")
    print()
    if scan_result["last_completed_goal"]:
        lg = scan_result["last_completed_goal"]
        print(f"  Utolsó goal_completed:")
        print(f"    goal_id:    {lg.get('goal_id')}")
        print(f"    timestamp:  {lg.get('timestamp')}")
        print(f"    iterations: {lg.get('iterations')}")
    else:
        print("  Utolsó goal_completed: (nincs)")
    print(sep)
    print(f"  self_state.json frissítve: {SELF_STATE_PATH}")
    print(sep)


def main() -> int:
    """
    Fő belépési pont.
    Return: 0 ha sikeres, 1 ha hiba.
    """
    if not META_EVIDENCE_PATH.exists():
        print(f"[HIBA] Nem található: {META_EVIDENCE_PATH}", file=sys.stderr)
        return 1

    if not SELF_STATE_PATH.exists():
        print(f"[HIBA] Nem található: {SELF_STATE_PATH}", file=sys.stderr)
        return 1

    print(f"[WITNESS] Scan indul: {META_EVIDENCE_PATH}")
    print(f"[WITNESS] Fájl mérete: {META_EVIDENCE_PATH.stat().st_size / 1_048_576:.1f} MB")

    t0 = time.monotonic()
    try:
        scan_result = scan_evidence(META_EVIDENCE_PATH)
    except Exception as e:
        print(f"[HIBA] Scan közben: {e}", file=sys.stderr)
        return 1
    duration = time.monotonic() - t0

    print_summary(scan_result, duration)

    try:
        update_self_state(scan_result, duration)
    except Exception as e:
        print(f"[HIBA] self_state.json frissítés közben: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
