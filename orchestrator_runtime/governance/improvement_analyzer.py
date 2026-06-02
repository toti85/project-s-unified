"""
MS-AO4 AO4.3 — Improvement Analyzer (Self-Improvement Suggestion Loop)

Reads escalation_queue.json and cycle_log.jsonl to analyze failed goals.
Generates structured improvement suggestions. NEVER auto-applies.

Rules:
  - auto_apply: always false
  - requires_human_approval: always true
  - Suggestions only — human approves before any change

Usage:
  from orchestrator_runtime.governance.improvement_analyzer import analyze_failures
  suggestions = analyze_failures()
  # or
  python orchestrator_runtime/governance/improvement_analyzer.py analyze
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ESCALATION_QUEUE_PATH = Path(__file__).parent / "escalation_queue.json"
CYCLE_LOG_PATH = Path(__file__).parent / "cycle_log.jsonl"
SUGGESTIONS_PATH = Path(__file__).parent / "improvement_suggestions.json"


def _load_json(path, default=None):
    if default is None:
        default = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    if path.exists():
        path.unlink()
    tmp.rename(path)


def _read_cycle_log():
    """Read cycle_log.jsonl and return list of entries."""
    entries = []
    if CYCLE_LOG_PATH.exists():
        with open(CYCLE_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


def _analyze_failure_pattern(goal_id, cycle_entries):
    """Analyze failure pattern for a specific goal. Returns (pattern, suggestion, confidence)."""
    # Get all verdict entries for this goal
    goal_verdicts = []
    for entry in cycle_entries:
        if entry.get("event") == "verdict" and entry.get("result", {}).get("goal_id") == goal_id:
            goal_verdicts.append(entry.get("result", {}))

    if not goal_verdicts:
        return None, None, 0.0

    # Check for retry_strategy pattern: same approach repeated
    retry_count = sum(1 for v in goal_verdicts if v.get("action") == "RETRY")
    if retry_count >= 2:
        return (
            "retry_strategy",
            f"Goal {goal_id} retried {retry_count} times with same approach. Consider: (1) revising the prompt to be more specific, (2) breaking into sub-goals, (3) adding explicit dependency prerequisites before execution.",
            0.8,
        )

    # Check for prompt_quality pattern: vague/ambiguous prompt
    for v in goal_verdicts:
        feedback = v.get("reason", "") + " " + v.get("feedback", "")
        vague_indicators = ["vague", "ambiguous", "unclear", "missing", "incomplete", "dependencies still missing"]
        if any(ind in feedback.lower() for ind in vague_indicators):
            return (
                "prompt_quality",
                f"Goal {goal_id} failed due to prompt quality issues. The prompt may have been too vague or missing critical context. Suggestion: rewrite prompt with explicit success criteria, list required dependencies, and specify expected output format.",
                0.75,
            )

    # Check for risk_misclassification: HIGH risk goal that should have been caught earlier
    for v in goal_verdicts:
        if v.get("action") == "ESCALATED":
            return (
                "risk_misclassification",
                f"Goal {goal_id} was escalated after max retries. The initial risk classification may have been too optimistic. Suggestion: review risk classifier thresholds for similar goal patterns. Consider raising the threshold for goals with similar characteristics.",
                0.7,
            )

    # Default: generic suggestion
    return (
        "retry_strategy",
        f"Goal {goal_id} failed after {len(goal_verdicts)} attempts. Suggestion: analyze the failure chain manually and consider whether the goal needs decomposition into smaller, more testable sub-goals.",
        0.6,
    )


def analyze_failures():
    """
    Analyze escalated goals and generate improvement suggestions.
    Returns list of suggestion dicts. NEVER auto-applies.
    """
    # Read escalation queue
    escalation_data = _load_json(ESCALATION_QUEUE_PATH, {"entries": []})
    escalated = escalation_data.get("entries", [])

    # Read cycle log
    cycle_entries = _read_cycle_log()

    # Load existing suggestions to avoid duplicates
    existing = _load_json(SUGGESTIONS_PATH, {"suggestions": []})
    existing_ids = {s.get("goal_id") for s in existing.get("suggestions", [])}

    suggestions = existing.get("suggestions", [])

    for entry in escalated:
        goal_id = entry.get("goal_id", "")
        if goal_id in existing_ids:
            continue

        pattern, suggestion, confidence = _analyze_failure_pattern(goal_id, cycle_entries)
        if pattern is None:
            continue

        suggestion_entry = {
            "goal_id": goal_id,
            "failure_pattern": pattern,
            "suggestion": suggestion,
            "confidence": confidence,
            "auto_apply": False,
            "requires_human_approval": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "PENDING_HUMAN_REVIEW",
        }
        suggestions.append(suggestion_entry)

    # Save suggestions
    _save_json(SUGGESTIONS_PATH, {"suggestions": suggestions})

    return suggestions


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        suggestions = analyze_failures()
        print(f"Analysis complete: {len(suggestions)} suggestion(s) generated")
        for s in suggestions:
            print(f"  - {s['goal_id']}: {s['failure_pattern']} (confidence: {s['confidence']})")
            print(f"    Suggestion: {s['suggestion'][:120]}...")
            print(f"    auto_apply: {s['auto_apply']}, requires_human_approval: {s['requires_human_approval']}")
    else:
        print("Usage: python improvement_analyzer.py analyze")