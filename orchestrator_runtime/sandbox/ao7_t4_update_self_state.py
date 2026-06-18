#!/usr/bin/env python
"""AO7_T4: Honest state capture — update self_state.json with AO7_T1-T3.5 findings."""

import json
import shutil
from datetime import datetime
from pathlib import Path

SELF_STATE_PATH = Path("self_state.json")
BACKUP_PATH = Path(f"self_state.json.backup.{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
TMP_PATH = Path("self_state.json.tmp")

# 1. Backup
shutil.copy2(SELF_STATE_PATH, BACKUP_PATH)
print(f"Backup: {BACKUP_PATH}")

# 2. Read
with open(SELF_STATE_PATH, "r", encoding="utf-8") as f:
    state = json.load(f)

# 3. Verify current counts
milestones_before = len(state.get("milestones", []))
kr_before = len(state.get("key_realizations", []))
gaps_before = len(state.get("identity", {}).get("known_gaps", []))
print(f"Before: milestones={milestones_before}, KR={kr_before}, gaps={gaps_before}")

# 4. Add milestone 62
state["milestones"].append({
    "id": 62,
    "date": "2026-06-18",
    "title": "AO7_T1-T3.5 SAI Pipeline Multi-Layer Regression Recovery — PARTIAL",
    "status": "partial_pass",
    "summary": "Multi-layer regression diagnosed by DeepSeek V4 Flash (5 root cause layers identified, DEV deep analysis). 3 fixes applied server-side (FIX 1: use_orchestration kw-based override, FIX 2: ExecutionValidator 0 val → unanimous_pass, FIX 3 revised: honest tool_result inspection). Dispatch chain restored. Still blocked: DDGS environment issue + smart_orchestrator error-wrapping regression (Layer B). 2 time bombs documented for future fixes.",
    "evidence": [
        "Commits: TBD (this one)",
        "DEV deep analysis identified 5 layers (DeepSeek V4 Flash)",
        "Server FIX applied, dispatch restored, but end-to-end blocked"
    ],
    "classification": "honest_partial_recovery"
})

# 5. Add TIME_BOMB_002 to known_gaps
state["identity"]["known_gaps"].append({
    "gap_id": "TIME_BOMB_002",
    "discovered": "2026-06-18",
    "discovered_by": "DeepSeek V4 Flash AO7_T3.5",
    "title": "smart_orchestrator wraps DDGS exception as success",
    "status": "DOCUMENTED_NOT_FIXED",
    "context": "When DDGS raises exception, smart_orchestrator wraps it as orchestration success at higher level than _ExecutorAdapter. AO7_T3 FIX 3 revision catches some cases but not all. Real fix needed at smart_orchestrator level.",
    "discovered_evidence": "AO7_T3.5: DDGS test returned 0 results without exception, but orchestrator-level result reported success",
    "deferred_fix": "Inspect smart_orchestrator.orchestrate_task error handling. Identify where DDGS exception is caught and silently wrapped. Replace with explicit error propagation."
})

# 6. Add WORKAROUND_001 to known_gaps
state["identity"]["known_gaps"].append({
    "gap_id": "WORKAROUND_001",
    "discovered": "2026-06-18",
    "title": "AO7_T3 FIX 1: use_orchestration kw-based override (temporary)",
    "status": "WORKAROUND_ACTIVE",
    "context": "use_orchestration heuristic upstream is unreliable. FIX 1 forces True when task contains keywords (research, memo, report, file, etc.). This works but is brittle to phrasing changes.",
    "deferred_fix": "Replace with: use_orchestration=True if Phase 1 strategic_plan returned recommended_tools list (regardless of task wording)",
    "rationale_for_workaround": "Quick restoration of pipeline. Proper upstream fix in separate mission after DDGS + Layer B resolved."
})

# 7. Add KR_017
state["key_realizations"].append({
    "id": "KR_017",
    "date": "2026-06-18",
    "realization": "Multi-layer regression detected by DeepSeek V4 Flash with explicit 'go deeper' instruction. Cline-Qwen single-pass diagnosis was incomplete (3 of 5 layers missed). DeepSeek V4 Flash also caught FIX 3's fake success regression (Scenario GAMMA) where Cline-Qwen previously reported PARTIAL SUCCESS. Model-task fit matters: deep diagnosis and honest fake-success detection are DeepSeek V4 Flash strengths.",
    "context": "AO7_T1_DEV deep + AO7_T3.5 evaluations"
})

# 8. Update top-level fields
state["last_updated"] = "2026-06-18T09:18:00Z"
state["updated_by"] = "AO7_T4 self_state update — AO7_T1-T3.5 honest partial recovery documentation"
state["active_focus"] = "SAI pipeline partial recovery (AO7_T1-T3.5). Dispatch chain restored. DDGS env issue + Layer B orchestrator wrapping deferred. TIME_BOMB_001 (GAP_029) + TIME_BOMB_002 documented."
state["current_state"]["active_focus"] = "SAI pipeline partial recovery (AO7_T1-T3.5). Dispatch chain restored. DDGS env issue + Layer B orchestrator wrapping deferred. TIME_BOMB_001 (GAP_029) + TIME_BOMB_002 documented."
state["next_concrete_step"] = "AO7_T5 — DDGS investigation and resolution (env issue, not code). After: AO7_T6 — Layer B fix in smart_orchestrator.py."
state["current_state"]["next_concrete_step"] = "AO7_T5 — DDGS investigation and resolution (env issue, not code). After: AO7_T6 — Layer B fix in smart_orchestrator.py."
state["current_state"]["last_updated"] = "2026-06-18T09:18:00.000000+00:00"
state["current_state"]["updated_by"] = "AO7_T4 self_state update"

# Update known_gaps summary in gaps_summary
gaps = state["identity"]["known_gaps"]
resolved = sum(1 for g in gaps if g["status"] == "RESOLVED")
active = sum(1 for g in gaps if g["status"] not in ("RESOLVED", "ACCEPTED", "open_measured_not_fixed"))
accepted = sum(1 for g in gaps if g["status"] == "ACCEPTED")
open_measured = sum(1 for g in gaps if g["status"] == "open_measured_not_fixed")
state["current_state"]["gaps_summary"]["total"] = len(gaps)
state["current_state"]["gaps_summary"]["resolved"] = resolved
state["current_state"]["gaps_summary"]["active"] = active
state["current_state"]["gaps_summary"]["accepted"] = accepted
state["current_state"]["gaps_summary"]["open_measured_not_fixed"] = open_measured

# 9. Verify counts
milestones_after = len(state["milestones"])
kr_after = len(state["key_realizations"])
gaps_after = len(state["identity"]["known_gaps"])
print(f"After: milestones={milestones_after}, KR={kr_after}, gaps={gaps_after}")
assert milestones_after == milestones_before + 1, f"Milestones: {milestones_before} → {milestones_after}"
assert kr_after == kr_before + 1, f"KR: {kr_before} → {kr_after}"
assert gaps_after == gaps_before + 2, f"Gaps: {gaps_before} → {gaps_after}"

# 10. Atomic write to tmp → rename
with open(TMP_PATH, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

# Validate by re-reading
with open(TMP_PATH, "r", encoding="utf-8") as f:
    validated = json.load(f)
    assert len(validated["milestones"]) == milestones_after
    assert len(validated["key_realizations"]) == kr_after
    assert len(validated["identity"]["known_gaps"]) == gaps_after
    assert validated["last_updated"] == "2026-06-18T09:18:00Z"
    print("Validation PASSED")

# Rename tmp → actual
TMP_PATH.replace(SELF_STATE_PATH)
print(f"Written: {SELF_STATE_PATH}")
print("Done.")