#!/usr/bin/env python3
"""
AO5_T6 Self-State Update Script
Atomic write: backup → temp → validate → rename
"""
import json
import shutil
import sys
import io
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console UTF-8 encoding
if sys.stdout.encoding and 'cp' in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ROOT = Path(r"C:\ProjectS-Unified")
SELF_STATE = ROOT / "self_state.json"
BACKUP = ROOT / "self_state.json.backup_ao5_t6"
PENDING = ROOT / "orchestrator_runtime" / "governance" / "pending_self_state_updates.json"

def main():
    # 1. Read current self_state.json
    if not SELF_STATE.exists():
        print("ERROR: self_state.json not found")
        sys.exit(1)
    
    with open(SELF_STATE, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    # 2. Create backup
    shutil.copy2(SELF_STATE, BACKUP)
    print(f"Backup created: {BACKUP}")
    
    # 3. Apply updates
    # 3a. Add identity fields
    if "identity" in state:
        state["identity"]["name_address"] = "Sz"
        state["identity"]["metaphor_primary"] = "Kognitív Mícelium"
        print("Identity updated: name_address=Sz, metaphor_primary=Kognitív Mícelium")
    
    # 3b. Add milestone
    milestone = {
        "id": 37,
        "date": "2026-06-09",
        "title": "AO5_T6 Ghost Branch v0.1 COMPLETE",
        "description": "Ghost Branch analysis: 93 files scanned, 45 active, 30 ghost candidates, TOP 3 resurrection candidates identified",
        "evidence": {
            "total_py_files": 93,
            "active_files": 45,
            "inactive_files": 30,
            "empty_files": 6,
            "top_candidates": [
                "orchestrator/verdict_evaluator.py (false negative ghost)",
                "core/cognitive_workflow_integration.py (high-value ghost)",
                "core/agents/overseer_agent.py (monitoring ghost)"
            ]
        },
        "achieved_at": "2026-06-09T10:30:00Z"
    }
    if "milestones" not in state:
        state["milestones"] = []
    state["milestones"].append(milestone)
    print(f"Milestone added: AO5_T6 Ghost Branch v0.1 COMPLETE")
    
    # 3c. Update active_focus
    if "current_state" in state:
        state["current_state"]["active_focus"] = "Sz - Ghost Branch v0.2 vagy Compute Arbiter döntés"
        state["current_state"]["next_concrete_step"] = "TOP 3 ghost candidate egyikét bekötni, VAGY Compute Arbiter router"
        state["current_state"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        state["current_state"]["updated_by"] = "AO5_T6 Ghost Branch closeout"
        print("active_focus updated")
        print("next_concrete_step updated")
    
    # 4. Write to temp file
    temp_file = ROOT / "self_state.json.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f"Temp file written: {temp_file}")
    
    # 5. Validate JSON
    with open(temp_file, "r", encoding="utf-8") as f:
        validated = json.load(f)
    print("JSON validation: PASS")
    
    # 6. Atomic rename (delete existing first on Windows)
    if SELF_STATE.exists():
        SELF_STATE.unlink()
    temp_file.rename(SELF_STATE)
    print(f"Atomic rename complete: {SELF_STATE}")
    
    # 7. Verify
    with open(SELF_STATE, "r", encoding="utf-8") as f:
        final = json.load(f)
    
    checks = {
        "name_address": final.get("identity", {}).get("name_address") == "Sz",
        "metaphor_primary": final.get("identity", {}).get("metaphor_primary") == "Kognitív Mícelium",
        "milestone_added": any("AO5_T6" in m.get("title", "") for m in final.get("milestones", [])),
        "active_focus_updated": "Ghost Branch v0.2" in final.get("current_state", {}).get("active_focus", ""),
        "next_step_updated": "TOP 3 ghost" in final.get("current_state", {}).get("next_concrete_step", ""),
        "valid_json": True
    }
    
    print("\n=== VERIFICATION ===")
    all_pass = True
    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        print(f"  {check}: {status}")
        if not result:
            all_pass = False
    
    if all_pass:
        print("\nAll checks PASSED. self_state.json updated successfully.")
    else:
        print("\nSome checks FAILED. Backup available at:", BACKUP)
        sys.exit(1)

if __name__ == "__main__":
    main()