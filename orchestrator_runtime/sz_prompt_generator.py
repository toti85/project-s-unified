from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKING_DIRECTORY = r"C:\ProjectS-Unified"
ROOT = Path(WORKING_DIRECTORY)
SELF_STATE_PATH = ROOT / "self_state.json"
REPORTS_DIR = ROOT / "reports"
GOAL_QUEUE_PATH = ROOT / "orchestrator_runtime" / "goal_queue.json"
OUTBOX_LAST_OUTPUT_PATH = ROOT / "orchestrator_runtime" / "cline_outbox" / "last_output.md"
MISSION_DIR = ROOT / "orchestrator_runtime" / "sz_proposed_missions"
MISSION_ID_PATTERN = re.compile(r"AO5_T(\d+)", re.IGNORECASE)
HIGH_PRIORITY_MARKERS = {"HIGH", "URGENT", "CRITICAL", "P0", "P1"}
DONE_MARKERS = {"DONE", "COMPLETED", "CLOSED", "RESOLVED"}
TASTE_MODEL_LOG = ROOT / "orchestrator_runtime" / "taste_model" / "mission_outcomes.jsonl"

try:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from orchestrator_runtime.taste_model.mission_outcome_logger import log_outcome as _log_outcome
except Exception:
    _log_outcome = None  # type: ignore[assignment]


def slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug.upper() or "MISSION"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_head(path: Path, max_lines: int) -> str:
    if not path.exists():
        return "(missing)"
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        lines = []
        for _, line in zip(range(max_lines), handle):
            lines.append(line.rstrip("\n"))
    return "\n".join(lines).strip() or "(empty)"


def compact(text: str, limit: int = 240) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def get_nested(mapping: dict[str, Any], key: str, default: Any = "") -> Any:
    value = mapping.get(key, default)
    return value if value not in (None, "") else default


def parse_self_state() -> dict[str, Any]:
    data = read_json(SELF_STATE_PATH)
    milestones = data.get("milestones") or []
    key_realizations = data.get("key_realizations") or []
    return {
        "last_updated": get_nested(data, "last_updated", "unknown"),
        "active_focus": get_nested(data, "active_focus", "unknown"),
        "next_concrete_step": get_nested(data, "next_concrete_step", "unknown"),
        "milestones": milestones[-5:],
        "key_realizations": key_realizations[-3:],
    }


def read_last_output_head() -> str:
    return read_head(OUTBOX_LAST_OUTPUT_PATH, 50)


def recent_reports(limit: int = 5) -> list[dict[str, Any]]:
    excluded_tokens = ("SZ_PROMPT_GENERATOR",)
    reports = []
    for path in REPORTS_DIR.glob("*.md"):
        if any(token in path.name for token in excluded_tokens):
            continue
        reports.append(
            {
                "path": path,
                "mtime": path.stat().st_mtime,
                "head": read_head(path, 30),
            }
        )
    reports.sort(key=lambda item: item["mtime"], reverse=True)
    return reports[:limit]


def parse_goal_queue() -> list[dict[str, Any]]:
    data = read_json(GOAL_QUEUE_PATH)
    if isinstance(data, dict):
        goals = data.get("goals") or data.get("pending_goals") or []
    elif isinstance(data, list):
        goals = data
    else:
        goals = []

    pending = []
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        status = str(goal.get("status", "PENDING")).strip().upper()
        rationale = str(goal.get("rationale", "")).strip().lower()
        if status in DONE_MARKERS:
            continue
        if "already completed" in rationale:
            continue
        pending.append(goal)
    return pending


def is_high_priority(goal: dict[str, Any]) -> bool:
    numeric_priority = goal.get("priority")
    if isinstance(numeric_priority, int) and numeric_priority <= 3:
        return True

    candidates = [
        goal.get("priority"),
        goal.get("priority_level"),
        goal.get("priority_class"),
        goal.get("urgency"),
        goal.get("risk"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip().upper() in HIGH_PRIORITY_MARKERS:
            return True
    return False


def materialize_template(template: str, mission_number: int, mission_slug: str) -> str:
    return (
        template.replace("<N>", str(mission_number))
        .replace("<mission_id>", f"AO5_T{mission_number}")
        .replace("<slug>", mission_slug)
        .replace("<date>", datetime.now(timezone.utc).strftime("%Y%m%d"))
    )


def finalize_mission(mission: dict[str, Any], mission_number: int) -> dict[str, Any]:
    mission_slug = slugify(str(mission.get("title", "MISSION")))
    return {
        **mission,
        "mission_slug": mission_slug,
        "outputs": [materialize_template(item, mission_number, mission_slug) for item in mission["outputs"]],
    }


def next_mission_number() -> int:
    max_seen = 0
    scan_paths = [REPORTS_DIR, MISSION_DIR]
    for base in scan_paths:
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            for match in MISSION_ID_PATTERN.finditer(path.name):
                max_seen = max(max_seen, int(match.group(1)))
    return max_seen + 1


def choose_mission(state: dict[str, Any], goals: list[dict[str, Any]], reports: list[dict[str, Any]]) -> dict[str, Any]:
    high_priority_goals = [goal for goal in goals if is_high_priority(goal)]
    if high_priority_goals:
        goal = sorted(high_priority_goals, key=lambda item: int(item.get("priority", 9999)) if str(item.get("priority", "")).isdigit() else 9999)[0]
        title = str(goal.get("title") or goal.get("id") or "Unnamed high-priority goal")
        title_lower = title.lower()

        if "auto-approval gateway" in title_lower or "risk-classified" in title_lower:
            return {
                "reason": "goal_queue_high_priority",
                "title": title,
                "execution_mode": "SURGICAL",
                "summary": "Implement the risk-classified auto-approval gateway with explicit allow, pause, and deny behavior, then validate the classification flow end to end.",
                "phases": [
                    "Phase 1 — Locate the current approval, orchestration, and governance decision points, then identify the exact file where a risk classifier should intercept execution requests.",
                    "Phase 2 — Implement the smallest viable gateway that classifies actions into auto-approve, manual approval required, or blocked, without changing unrelated orchestration behavior.",
                    "Phase 3 — Run focused validation on representative low, medium, and high-risk cases, then document the final policy and any unresolved edge cases.",
                ],
                "outputs": [
                    "reports/MS_AO5_T<N>_<slug>_<date>.md",
                    "orchestrator_runtime/cline_outbox/last_output.md",
                    "orchestrator_runtime/cline_outbox/output_ready.json",
                ],
                "return_values": [
                    "Exact interception point and changed files",
                    "Classification policy summary",
                    "Validation results for low, medium, and high-risk examples",
                ],
            }

        return {
            "reason": "goal_queue_high_priority",
            "title": title,
            "execution_mode": "SURGICAL",
            "summary": f"Advance the queued high-priority goal: {title}.",
            "phases": [
                f"Phase 1 — Inspect the existing implementation surface for '{title}', identify the exact owning files, and restate the smallest valid scope before editing.",
                "Phase 2 — Execute the task with the minimum necessary file changes, preserving current behavior outside the requested slice.",
                "Phase 3 — Run the narrowest available validation, then write a closeout report with changed files, evidence, and unresolved risks.",
            ],
            "outputs": [
                "reports/MS_AO5_T<N>_<slug>_<date>.md",
                "orchestrator_runtime/cline_outbox/last_output.md",
                "orchestrator_runtime/cline_outbox/output_ready.json",
            ],
            "return_values": [
                "What changed and why",
                "Validation results",
                "Open risks or blockers",
            ],
        }

    next_step = state["next_concrete_step"]
    next_step_lower = next_step.lower()
    if "verdict_evaluator" in next_step_lower:
        return {
            "reason": "next_concrete_step_specific_action",
            "title": "Verdict Evaluator Ghost Candidate Deep Dive",
            "execution_mode": "READ-ONLY",
            "summary": "Map the real verdict_evaluator execution path, compare it to the untouched ghost candidate, and produce a concrete keep, revive, or archive recommendation.",
            "phases": [
                "Phase 1 — Find every verdict_evaluator candidate, list each file path, and capture imports, exports, and real call sites with exact references.",
                "Phase 2 — Identify which candidate is live, which one is ghost or dead code, and what concrete behavior difference exists between them.",
                "Phase 3 — Write a decisive report: keep as-is, revive with a future integration plan, or archive as misleading residue, backed by proof excerpts.",
            ],
            "outputs": [
                "reports/MS_<mission_id>_VERDICT_EVALUATOR_DEEP_DIVE_<date>.md",
                "orchestrator_runtime/sandbox/<slug>_notes.md",
                "orchestrator_runtime/cline_outbox/last_output.md",
                "orchestrator_runtime/cline_outbox/output_ready.json",
            ],
            "return_values": [
                "Live execution path with exact file references",
                "Ghost candidate verdict with proof",
                "Specific recommended next mission",
            ],
        }

    if "cm v0.1" in next_step_lower or "continuous mind" in next_step_lower:
        return {
            "reason": "next_concrete_step_specific_action",
            "title": "Continuous Mind v0.1 Phase 1 Planning Packet",
            "execution_mode": "READ-ONLY",
            "summary": "Produce a concrete implementation packet for Continuous Mind v0.1 Phase 1 with file targets, interfaces, and validation steps, but no production edits.",
            "phases": [
                "Phase 1 — Map the current heartbeat path, git observer path, and CWI entry surfaces with exact owning files and known constraints.",
                "Phase 2 — Define the minimal Phase 1 architecture: new or touched files, data flow, interface contracts, and validation points.",
                "Phase 3 — Save a build-ready planning packet plus an operator handoff that names the first edit slice and its acceptance criteria.",
            ],
            "outputs": [
                "reports/MS_AO5_T<N>_CM_V01_PHASE1_PLAN_<date>.md",
                "orchestrator_runtime/sandbox/ao5_cm_v01_phase1_plan.md",
                "orchestrator_runtime/cline_outbox/last_output.md",
                "orchestrator_runtime/cline_outbox/output_ready.json",
            ],
            "return_values": [
                "Phase 1 scope",
                "File targets and risks",
                "Validation plan",
            ],
        }

    last_report_name = reports[0]["path"].name if reports else "no recent report"
    return {
        "reason": "fallback_recent_reports_and_focus",
        "title": "Recent Report Synthesis and Next Mission Proposal",
        "execution_mode": "READ-ONLY",
        "summary": f"Analyze {last_report_name} plus the current active focus and propose the next safe mission.",
        "phases": [
            "Phase 1 — Summarize the latest report evidence and unresolved questions.",
            "Phase 2 — Correlate that evidence with active_focus and next_concrete_step.",
            "Phase 3 — Write a single next-mission proposal with constraints and proof references.",
        ],
        "outputs": [
            "reports/MS_AO5_T<N>_NEXT_MISSION_SYNTHESIS_<date>.md",
            "orchestrator_runtime/cline_outbox/last_output.md",
            "orchestrator_runtime/cline_outbox/output_ready.json",
        ],
        "return_values": [
            "Proposed next mission",
            "Supporting evidence",
            "Risk notes",
        ],
    }


def load_taste_model_summary() -> str:
    """
    Read mission_outcomes.jsonl and return a compact advisory string.
    Advisory-only: NEVER raises — returns a fallback string on any error.
    Max 12 lines. Does not block prompt generation.
    """
    try:
        if not TASTE_MODEL_LOG.exists():
            return "Taste Model unavailable; continuing."

        records: list[dict[str, Any]] = []
        with TASTE_MODEL_LOG.open(encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if raw:
                    try:
                        records.append(json.loads(raw))
                    except json.JSONDecodeError:
                        continue

        if not records:
            return "Taste Model unavailable; continuing."

        total = len(records)
        values = [r["value_immediate"] for r in records if isinstance(r.get("value_immediate"), int)]
        avg = sum(values) / len(values) if values else 0.0

        by_model: dict[str, list[int]] = {}
        for r in records:
            m = r.get("model_used", "?")
            v = r.get("value_immediate")
            if isinstance(v, int):
                by_model.setdefault(m, []).append(v)
        if by_model:
            top_model = max(by_model, key=lambda m: sum(by_model[m]) / len(by_model[m]))
            top_avg = sum(by_model[top_model]) / len(by_model[top_model])
        else:
            top_model, top_avg = "?", 0.0

        recent = records[-3:]
        recent_lines = [
            f"  {r['mission_id']} v={r.get('value_immediate','?')} "
            f"{r.get('actual_status','?')} [{r.get('model_used','?')}]"
            for r in recent
        ]

        last = records[-1]
        last_status = last.get("actual_status", "")
        warning = ""
        if last_status in ("false_declaration", "partial_pass"):
            warning = (
                f"WARNING: last mission ({last['mission_id']}) "
                f"status={last_status} — verify before trusting continuation."
            )

        hv_patterns: dict[str, int] = {}
        for r in records:
            if r.get("value_immediate", 0) >= 5:
                for p in r.get("patterns", []):
                    hv_patterns[p] = hv_patterns.get(p, 0) + 1
        top_hv = sorted(hv_patterns, key=lambda p: -hv_patterns[p])[:4]

        lines = [
            f"total={total}  avg_value={avg:.2f}  top_model={top_model} (avg={top_avg:.2f})",
            "recent missions:",
            *recent_lines,
        ]
        if warning:
            lines.append(warning)
        if top_hv:
            lines.append(f"high-value patterns (v>=5): {', '.join(top_hv)}")

        return "\n".join(lines)

    except Exception as exc:  # advisory must never block
        return f"Taste Model unavailable; continuing. (error: {exc})"


def build_context(state: dict[str, Any], reports: list[dict[str, Any]], last_output_head: str) -> list[str]:
    milestone_lines = []
    for item in state["milestones"]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "untitled milestone"))
        date = str(item.get("date") or item.get("completed_at") or item.get("created_at") or "unknown date")
        status = str(item.get("status", "unknown"))
        milestone_lines.append(f"{title} ({date}, {status})")

    realization_lines = []
    for item in state["key_realizations"]:
        if not isinstance(item, dict):
            continue
        realization_lines.append(compact(str(item.get("realization", "")), 180))

    recent_report = reports[0] if reports else None
    recent_report_summary = compact(recent_report["head"], 220) if recent_report else "No recent report head available."
    recent_report_name = recent_report["path"].name if recent_report else "no report"

    sentences = [
        f"self_state.json last_updated is {state['last_updated']} and the active focus is {state['active_focus']}.",
        f"The recorded next concrete step is: {state['next_concrete_step']}.",
        f"Latest milestones include: {'; '.join(milestone_lines) if milestone_lines else 'no milestone data available'}.",
        f"Recent key realizations: {'; '.join(realization_lines) if realization_lines else 'none recorded'}.",
        f"The latest Cline outbox result begins with: {compact(last_output_head, 220)}",
        f"The newest usable report is {recent_report_name}; first-lines summary: {recent_report_summary}",
    ]
    return sentences


def format_block(title: str, lines: list[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines)
    return f"{title}\n{body}"


def render_prompt(
    mission_number: int,
    mission: dict[str, Any],
    state: dict[str, Any],
    reports: list[dict[str, Any]],
    last_output_head: str,
) -> str:
    mission_id = f"AO5_T{mission_number}"
    mission = finalize_mission(mission, mission_number)
    context_sentences = build_context(state, reports, last_output_head)
    taste_advisory = load_taste_model_summary()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    lines = [
        mission_id,
        "",
        f"Working directory: {WORKING_DIRECTORY}",
        "",
        f"EXECUTION MODE: {mission['execution_mode']}",
        "",
        "CONTEXT:",
        *context_sentences,
        "",
        "TASK:",
        f"Mission objective: {mission['summary']}",
        *mission["phases"],
        "",
        format_block("OUTPUT FILES EXPECTED:", mission["outputs"]).rstrip(),
        "",
        format_block("RETURN VALUES:", mission["return_values"]).rstrip(),
        "",
        "## Taste Model Advisory",
        taste_advisory,
        "",
        "CRITICAL CONSTRAINTS:",
        "- No src/ modifications without Toti approval",
        "- No git push without Toti approval",
        "- All file ops in sandbox/ + reports/ + cline_outbox/",
        "",
        "RISK_010 REMINDER:",
        "- last_output.md FINAL first",
        "- checksum computed",
        "- output_ready.json LAST",
        "",
        "PROOF NOT JUST CODE:",
        "- Show evidence, not just intent",
        "- Prefer verification artifacts and concrete file references",
        "",
        f"GENERATOR META: reason={mission['reason']} generated_utc={timestamp}",
        f"GENERATOR META: proposal={mission['summary']}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def save_prompt(prompt_text: str, mission_number: int) -> Path:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = MISSION_DIR / f"MS_AO5_T{mission_number}_DRAFT_{timestamp}.md"
    path.write_text(prompt_text, encoding="utf-8")
    if _log_outcome:
        try:
            _log_outcome(
                mission_id=f"AO5_T{mission_number}_DRAFT",
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                claimed_status="draft_only",
                actual_status="draft_only",
                model_used="sz_prompt_generator",
                runtime_validated=False,
                value_immediate=3,
                patterns=["sz_auto_draft", "draft_generated"],
                notes=f"Auto-generated draft {len(prompt_text)} chars",
            )
        except Exception:
            pass  # logging must never break draft generation
    return path


def main() -> int:
    state = parse_self_state()
    reports = recent_reports()
    goals = parse_goal_queue()
    last_output_head = read_last_output_head()
    mission_number = next_mission_number()
    mission = choose_mission(state, goals, reports)
    prompt_text = render_prompt(mission_number, mission, state, reports, last_output_head)
    saved_path = save_prompt(prompt_text, mission_number)
    sys.stdout.write(prompt_text)
    sys.stdout.write(f"\nSAVED TO: {saved_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())