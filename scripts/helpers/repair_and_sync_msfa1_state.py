"""
repair_and_sync_msfa1_state.py

Safely repairs self_state.json and adds MS-FA1 milestone.
Usage: python scripts/helpers/repair_and_sync_msfa1_state.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # c:\ProjectS-Unified
STATE_FILE = ROOT / "self_state.json"
TMP_FILE = ROOT / "self_state.json.tmp"

MSFA1_MILESTONE = {
    "id": 34,
    "date": "2026-05-24",
    "title": "MS-FA1 Filesystem Automation Pipeline v1 completed through Phase 1.5",
    "status": "completed",
    "summary": "Project-S can now coordinate Cline through a controlled filesystem handoff protocol. FA1.1 manual loop, FA1.2 semi-automated loop, FA1.2H hardening, FA1.3 AI prompt/evaluator, FA1.4 controlled multi-iteration, and FA1.5 file-based handoff polling all passed.",
    "evidence": [
        "FA1_001 manual loop PASS",
        "FA1_002 semi-auto JSON validator PASS",
        "FA1_003 hardening CSV row counter PASS",
        "FA1_004 AI prompt/evaluator INI parser PASS",
        "FA1_005 multi-iteration TXT word counter PASS",
        "FA1_006 handoff polling YAML key counter PASS",
        "25/25 tests PASS",
        "0 safety violations"
    ],
    "classification": "controlled_orchestration_not_full_autonomy"
}


def main():
    print("=== MS-FA1 self_state.json repair & sync ===")

    # 1. Load and validate JSON
    print(f"[1] Loading {STATE_FILE} ...")
    try:
        text = STATE_FILE.read_text(encoding="utf-8")
        data = json.loads(text)
        print("    JSON valid.")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"    FATAL: Cannot load JSON: {e}")
        sys.exit(1)

    # 2. Validate top-level keys
    print("[2] Validating top-level keys ...")
    for key in ("milestones",):
        if key not in data:
            print(f"    FATAL: Missing key: {key}")
            sys.exit(1)
    # known_risks may have been lost during prior corruption — restore from backup
    BACKUP_FILE = ROOT / "self_state.json.bak_before_msfa1_sync_20260524"
    if "known_risks" not in data:
        print("    WARNING: known_risks missing (lost during prior corruption). Attempting backup restore...")
        if BACKUP_FILE.exists():
            try:
                backup_data = json.loads(BACKUP_FILE.read_text(encoding="utf-8"))
                if "known_risks" in backup_data and isinstance(backup_data["known_risks"], list):
                    data["known_risks"] = backup_data["known_risks"]
                    print(f"    Restored {len(data['known_risks'])} known_risks from backup.")
                else:
                    data["known_risks"] = []
                    print("    Backup also missing known_risks. Initialized empty list.")
            except Exception as e:
                print(f"    Backup restore failed: {e}. Initialized empty list.")
                data["known_risks"] = []
        else:
            data["known_risks"] = []
            print("    No backup found. Initialized empty list.")
    print("    OK.")

    # 3. Validate milestones is a list
    milestones = data["milestones"]
    if not isinstance(milestones, list):
        print(f"    FATAL: milestones is not a list (type={type(milestones).__name__})")
        sys.exit(1)
    print(f"    milestones: list with {len(milestones)} items.")

    # 4. Remove malformed entries (non-dict items)
    original_len = len(milestones)
    milestones = [m for m in milestones if isinstance(m, dict)]
    if len(milestones) < original_len:
        print(f"    WARNING: Removed {original_len - len(milestones)} malformed milestone entries.")
    data["milestones"] = milestones

    # 5. Check if MS-FA1 milestone already exists
    existing_ids = {m.get("id") for m in milestones if "id" in m}
    if MSFA1_MILESTONE["id"] in existing_ids:
        # Find next available ID
        next_id = max(existing_ids) + 1
        MSFA1_MILESTONE["id"] = next_id
        print(f"    ID {next_id - 1} exists, using {next_id}.")

    # Check by title too
    titles = {m.get("title", "") for m in milestones}
    if MSFA1_MILESTONE["title"] in titles:
        print("    MS-FA1 milestone already present. Skipping add.")
    else:
        milestones.append(MSFA1_MILESTONE)
        data["milestones"] = milestones
        print(f"    Added MS-FA1 milestone (id={MSFA1_MILESTONE['id']}).")

    # 6. Preserve gap counts
    gaps_summary = data.get("gaps_summary", {})
    print(f"    gaps_summary preserved: {gaps_summary}")

    # 7. Preserve known_risks
    known_risks = data.get("known_risks", [])
    if isinstance(known_risks, list):
        print(f"    known_risks: {len(known_risks)} items preserved.")
    else:
        print(f"    WARNING: known_risks is not a list (type={type(known_risks).__name__})")

    # 8. Extract risk entries that got merged into milestones array (corruption repair)
    risk_ids_in_milestones = [m for m in milestones if m.get("risk_id")]
    if risk_ids_in_milestones:
        print(f"    REPAIR: Extracting {len(risk_ids_in_milestones)} risk entries from milestones array...")
        milestones = [m for m in milestones if not m.get("risk_id")]
        data["milestones"] = milestones
        # Merge with existing known_risks
        existing_risks = data.get("known_risks", [])
        data["known_risks"] = list(existing_risks) + risk_ids_in_milestones
        print(f"    Restored {len(data['known_risks'])} known_risks. Milestones now {len(milestones)}.")

    # 9. Update active_focus / next_concrete_step if fields exist
    current_state = data.get("current_state", {})
    if isinstance(current_state, dict):
        current_state.setdefault("active_focus", "")
        current_state["active_focus"] = (
            "MS-FA1 controlled filesystem orchestration completed through Phase 1.5; "
            "docs/self_state sync and next-step decision pending."
        )
        current_state["next_concrete_step"] = (
            "Decide whether to pause after MS-FA1 Phase 1.5 for review, "
            "proceed to FA1.6, or begin MS-AO1 planning. "
            "Do not claim full autonomy yet."
        )
        data["current_state"] = current_state
        print("    Updated active_focus and next_concrete_step.")

    # 10. Update metadata
    data["last_updated"] = "2026-05-25T19:30:00Z"
    data["updated_by"] = "repair_and_sync_msfa1_state.py — MS-FA1 docs sync"

    # 11. Atomic write
    print(f"[3] Atomic write: {STATE_FILE} ...")
    try:
        TMP_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        # Validate the temp file
        json.loads(TMP_FILE.read_text(encoding="utf-8"))
        # Windows: rename fails if target exists
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        TMP_FILE.rename(STATE_FILE)
        print("    Write + rename OK.")
    except Exception as e:
        import sys
        sys.stderr.write(f"    FATAL: Write failed: {e!s}\n")
        if TMP_FILE.exists():
            TMP_FILE.unlink()
        sys.exit(1)

    # 12. Re-load and validate
    print("[4] Re-loading written file ...")
    try:
        reloaded = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        assert isinstance(reloaded["milestones"], list)
        assert isinstance(reloaded["known_risks"], list)
        msfa1_count = sum(1 for m in reloaded["milestones"] if m.get("title", "").startswith("MS-FA1"))
        assert msfa1_count == 1, f"Expected 1 MS-FA1 milestone, got {msfa1_count}"
        print(f"    Validation PASSED (milestones={len(reloaded['milestones'])}, "
              f"known_risks={len(reloaded['known_risks'])}, MS-FA1={msfa1_count})")
    except Exception as e:
        print(f"    FATAL: Post-write validation failed: {e}")
        sys.exit(1)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()