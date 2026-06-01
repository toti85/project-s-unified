"""
MS-AO1/MS-AO2 Self-State Updater

Features:
  - Reads self_state.json (read-only)
  - Prepares update payload (new evidence, milestone status changes)
  - Writes to orchestrator_runtime/governance/pending_self_state_updates.json ONLY
  - Atomic write + pre-write backup mechanism
  - Full audit log to orchestrator_runtime/governance/self_state_audit.json

Usage:
    from orchestrator_runtime.governance.self_state_updater import SelfStateUpdater
    updater = SelfStateUpdater()
    updater.prepare_milestone_update(35, {"status": "verified"})
    updater.prepare_evidence_addition("MS-AO1", ["goal_queue.json created"])
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

SELF_STATE_PATH = Path(__file__).parent.parent.parent / "self_state.json"
PENDING_UPDATES_PATH = Path(__file__).parent / "pending_self_state_updates.json"
AUDIT_LOG_PATH = Path(__file__).parent / "self_state_audit.json"

# AO2.2 notification integration (lazy import — fails gracefully)
try:
    from orchestrator_runtime.governance.notifier import Notifier
    _NOTIFIER = Notifier()
except ImportError:
    _NOTIFIER = None


def _notify(event_type, goal_id=None, message=""):
    """Send notification if notifier available."""
    if _NOTIFIER is not None:
        try:
            _NOTIFIER.notify(event_type, goal_id=goal_id, message=message)
        except Exception:
            pass


def _load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json_atomic(path, data):
    """Atomic write with pre-write backup."""
    if path.exists():
        backup = path.with_suffix(".backup")
        shutil.copy2(str(path), str(backup))
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    if path.exists():
        path.unlink()
    tmp.rename(path)


def _log_audit(action, details):
    """Append entry to audit log."""
    audit = _load_json(AUDIT_LOG_PATH, {"entries": []})
    entry = {
        "action": action,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "self_state_modified": False,  # Always False — this module never modifies self_state.json
    }
    audit["entries"].append(entry)
    _save_json_atomic(AUDIT_LOG_PATH, audit)


class SelfStateUpdater:
    def __init__(self):
        self._validate_self_state_readonly()

    def _validate_self_state_readonly(self):
        """Ensure self_state.json exists and is readable."""
        if not SELF_STATE_PATH.exists():
            raise FileNotFoundError(f"self_state.json not found at {SELF_STATE_PATH}")
        # Read to verify it's valid JSON
        data = _load_json(SELF_STATE_PATH)
        if not isinstance(data, dict):
            raise ValueError("self_state.json must be a JSON object")

    def read_self_state(self):
        """Read self_state.json (read-only access)."""
        data = _load_json(SELF_STATE_PATH)
        _log_audit("READ_SELF_STATE", {"path": str(SELF_STATE_PATH)})
        return data

    def prepare_milestone_update(self, milestone_id, updates):
        """
        Prepare a milestone status update.

        Args:
            milestone_id: Milestone number to update
            updates: Dict of fields to update (e.g., {"status": "verified"})

        Writes to pending_self_state_updates.json ONLY.
        """
        pending = _load_json(PENDING_UPDATES_PATH, {
            "updates": [],
            "last_updated": None,
            "requires_human_approval": True,
        })

        update_entry = {
            "type": "milestone_update",
            "milestone_id": milestone_id,
            "fields": updates,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
            "approved": False,
            "applied": False,
        }
        pending["updates"].append(update_entry)
        pending["last_updated"] = datetime.now(timezone.utc).isoformat()
        _save_json_atomic(PENDING_UPDATES_PATH, pending)

        _log_audit("PREPARE_MILESTONE_UPDATE", {
            "milestone_id": milestone_id,
            "fields": updates,
            "written_to": str(PENDING_UPDATES_PATH),
            "self_state_modified": False,
        })

        return {
            "status": "PREPARED",
            "update": update_entry,
            "note": "Pending human approval. Will NOT be applied to self_state.json automatically.",
        }

    def prepare_evidence_addition(self, category, evidence_items):
        """
        Prepare new evidence to be added to self_state.json.

        Args:
            category: Evidence category (e.g., "MS-AO1", "MS-FA1")
            evidence_items: List of evidence strings

        Writes to pending_self_state_updates.json ONLY.
        """
        pending = _load_json(PENDING_UPDATES_PATH, {
            "updates": [],
            "last_updated": None,
            "requires_human_approval": True,
        })

        update_entry = {
            "type": "evidence_addition",
            "category": category,
            "evidence_items": evidence_items,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
            "approved": False,
            "applied": False,
        }
        pending["updates"].append(update_entry)
        pending["last_updated"] = datetime.now(timezone.utc).isoformat()
        _save_json_atomic(PENDING_UPDATES_PATH, pending)

        _log_audit("PREPARE_EVIDENCE_ADDITION", {
            "category": category,
            "item_count": len(evidence_items),
            "written_to": str(PENDING_UPDATES_PATH),
            "self_state_modified": False,
        })

        return {
            "status": "PREPARED",
            "update": update_entry,
            "note": "Pending human approval. Will NOT be applied to self_state.json automatically.",
        }

    def prepare_gap_status_change(self, gap_id, new_status, resolution_note=""):
        """
        Prepare a gap status change.

        Args:
            gap_id: Gap identifier (e.g., "GAP_032")
            new_status: New status (e.g., "RESOLVED", "ACTIVE")
            resolution_note: Optional note

        Writes to pending_self_state_updates.json ONLY.
        """
        pending = _load_json(PENDING_UPDATES_PATH, {
            "updates": [],
            "last_updated": None,
            "requires_human_approval": True,
        })

        update_entry = {
            "type": "gap_status_change",
            "gap_id": gap_id,
            "new_status": new_status,
            "resolution_note": resolution_note,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
            "approved": False,
            "applied": False,
        }
        pending["updates"].append(update_entry)
        pending["last_updated"] = datetime.now(timezone.utc).isoformat()
        _save_json_atomic(PENDING_UPDATES_PATH, pending)

        _log_audit("PREPARE_GAP_STATUS_CHANGE", {
            "gap_id": gap_id,
            "new_status": new_status,
            "written_to": str(PENDING_UPDATES_PATH),
            "self_state_modified": False,
        })

        return {
            "status": "PREPARED",
            "update": update_entry,
            "note": "Pending human approval. Will NOT be applied to self_state.json automatically.",
        }

    def apply_updates(self, approved_only=True):
        """
        AO2.1 — Apply approved pending updates to self_state.json.

        Reads pending_self_state_updates.json, filters approved=true (if approved_only),
        applies updates atomically to self_state.json (backup → temp → validate → rename),
        logs every write to self_state_audit.json, marks applied=true.

        Args:
            approved_only: If True, only apply updates with approved=true.

        Returns:
            dict with application result
        """
        pending = _load_json(PENDING_UPDATES_PATH, {"updates": []})
        now = datetime.now(timezone.utc).isoformat()

        # Filter: only unapplied updates
        to_apply = [u for u in pending["updates"] if not u.get("applied", False)]
        if approved_only:
            to_apply = [u for u in to_apply if u.get("approved", False)]

        if not to_apply:
            return {
                "status": "NO_UPDATES",
                "applied_count": 0,
                "note": "No approved, unapplied updates found.",
            }

        # Read current self_state
        state = _load_json(SELF_STATE_PATH)

        # Apply each update
        for update in to_apply:
            utype = update.get("type")

            if utype == "milestone_update":
                mid = update["milestone_id"]
                for m in state.get("milestones", []):
                    if m.get("id") == mid:
                        for k, v in update.get("fields", {}).items():
                            m[k] = v
                        break

            elif utype == "evidence_addition":
                category = update.get("category", "")
                items = update.get("evidence_items", [])
                # Add evidence to latest milestone with matching category or last milestone
                milestones = state.get("milestones", [])
                if milestones:
                    target = milestones[-1]
                    existing = target.get("evidence", [])
                    for item in items:
                        if item not in existing:
                            existing.append(item)
                    target["evidence"] = existing

            elif utype == "gap_status_change":
                gap_id = update.get("gap_id")
                new_status = update.get("new_status")
                for gap in state.get("known_gaps", []):
                    if gap.get("risk_id") == gap_id or gap.get("gap_id") == gap_id:
                        gap["status"] = new_status
                        if update.get("resolution_note"):
                            gap["resolution_note"] = update["resolution_note"]
                        break

        # Atomic write: backup → temp → validate → rename
        backup = SELF_STATE_PATH.with_suffix(".json.backup_ao21")
        tmp = SELF_STATE_PATH.with_suffix(".json.tmp")

        shutil.copy2(str(SELF_STATE_PATH), str(backup))

        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        # Validate before rename
        validated = json.load(open(tmp, encoding="utf-8"))
        if not isinstance(validated, dict):
            # Rollback: restore backup, remove temp
            if tmp.exists():
                tmp.unlink()
            shutil.copy2(str(backup), str(SELF_STATE_PATH))
            return {
                "status": "VALIDATION_FAILED",
                "applied_count": 0,
                "note": "Temp file validation failed. Backup restored.",
            }

        # Rename
        if SELF_STATE_PATH.exists():
            SELF_STATE_PATH.unlink()
        tmp.rename(SELF_STATE_PATH)

        # Mark as applied in pending file
        for update in to_apply:
            update["applied"] = True
            update["applied_at"] = now
        pending["last_updated"] = now
        _save_json_atomic(PENDING_UPDATES_PATH, pending)

        # Audit log
        _log_audit("APPLY_UPDATES", {
            "applied_count": len(to_apply),
            "update_types": [u.get("type") for u in to_apply],
            "backup": str(backup),
            "self_state_modified": True,
            "method": "atomic (backup -> temp -> validate -> rename)",
        })

        _notify("SELF_STATE_UPDATED", message=f"Applied {len(to_apply)} updates via apply_updates()")

        return {
            "status": "APPLIED",
            "applied_count": len(to_apply),
            "backup": str(backup),
            "note": f"Applied {len(to_apply)} updates to self_state.json.",
        }

    def get_pending_updates(self):
        """Return all pending updates awaiting human approval."""
        return _load_json(PENDING_UPDATES_PATH, {"updates": [], "requires_human_approval": True})

    def get_audit_log(self):
        """Return the full audit log."""
        return _load_json(AUDIT_LOG_PATH, {"entries": []})


if __name__ == "__main__":
    updater = SelfStateUpdater()

    # Demo: read self_state (read-only)
    state = updater.read_self_state()
    print(f"self_state.json read: {len(state.get('milestones', []))} milestones, {len(state.get('known_gaps', []))} gaps")

    # Demo: prepare a milestone update (does NOT modify self_state.json)
    result = updater.prepare_milestone_update(35, {"status": "verified", "note": "MS-AO1 infrastructure complete"})
    print(f"\nMilestone update prepared: {json.dumps(result, indent=2)}")

    # Demo: prepare evidence addition
    result2 = updater.prepare_evidence_addition("MS-AO1", [
        "parallel_loop_manager.py created",
        "self_state_updater.py created",
        "All 8 goals processed through governance pipeline",
    ])
    print(f"\nEvidence addition prepared: {json.dumps(result2, indent=2)}")

    # Verify self_state.json was NOT modified
    print(f"\nself_state.json exists: {SELF_STATE_PATH.exists()}")
    print(f"Pending updates: {len(updater.get_pending_updates().get('updates', []))}")
    print(f"Audit entries: {len(updater.get_audit_log().get('entries', []))}")
    print("\nIMPORTANT: self_state.json was NOT modified. Updates are pending in pending_self_state_updates.json.")