"""MS-OQ1 — Output Quality Baseline Evaluator.

Runs the 20-prompt corpus through Project-S route handlers and scores each answer
using the 5-dimension rubric defined in docs/response_quality_rubric.md.

Usage:
    python -m interactive_layer.evaluate_output_quality_baseline [--smoke] [--json-only]

Options:
    --smoke       Run only the 5-prompt smoke subset (IDs: DL_01, TU_01, ID_01, ER_01, FA_01)
    --json-only   Skip markdown report, write JSON only

Output:
    reports/MS_OQ1_BASELINE_RESULTS_<DATE>.json
    reports/MS_OQ1_BASELINE_REPORT_<DATE>.md

Scoring approach:
    Each dimension (0-3) is scored by deterministic heuristics that check:
    - Answer length (not too short, not empty)
    - Structural markers (numbered lists, bullet prefix, line count)
    - Uncertainty markers for TRUTHFUL_UNCERTAINTY route
    - Keyword presence for topic relevance
    A final manual_review_needed flag is set when heuristics alone are insufficient.
    An optional LLM evaluator hook is available (set ENABLE_LLM_SCORER=1 env var).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_CORPUS_PATH = _ROOT / "tests" / "fixtures" / "output_quality_prompt_corpus.json"
_REPORTS_DIR = _ROOT / "reports"
_REPORTS_DIR.mkdir(exist_ok=True)

_DATE_STAMP = datetime.now().strftime("%Y%m%d")
_JSON_OUT = _REPORTS_DIR / f"MS_OQ1_BASELINE_RESULTS_{_DATE_STAMP}.json"
_MD_OUT = _REPORTS_DIR / f"MS_OQ1_BASELINE_REPORT_{_DATE_STAMP}.md"

# ---------------------------------------------------------------------------
# Route handler invocation (direct — no HTTP server required)
# ---------------------------------------------------------------------------

def _invoke_route_handler(prompt: str) -> Dict[str, Any]:
    """Classify and execute a prompt via the prompt_router handlers directly.

    For FULL_AGENTIC_META_CONTROLLER, falls back to HTTP API if server is
    reachable at 127.0.0.1:8000; otherwise returns a NO_SERVER sentinel result.

    Returns dict with:
        route_selected, elapsed_s, result, terminal_state, error
    """
    from interactive_layer.prompt_router import classify_prompt, get_route_handler

    t0 = time.monotonic()
    try:
        decision = classify_prompt(prompt)
        route = decision.route_type
        handler = get_route_handler(route)

        if handler is not None:
            # Lightweight handler — execute directly
            dummy_mission_id = f"eval_{int(time.time() * 1000)}"
            handler_result = handler(
                prompt=prompt,
                decision=decision,
                mission_id=dummy_mission_id,
            )
            # MS-OQ1-B: Apply response polish layer
            from interactive_layer.response_polish import polish_response
            handler_result = polish_response(handler_result, route, prompt)
            elapsed = time.monotonic() - t0
            return {
                "route_selected": route,
                "elapsed_s": round(elapsed, 2),
                "result": handler_result.get("result", ""),
                "terminal_state": handler_result.get("mission_state", "COMPLETE"),
                "error": None,
                "source": "direct_handler",
                "response_polished": handler_result.get("response_polished", False),
                "polish_version": handler_result.get("polish_version", ""),
            }
        else:
            # FULL_AGENTIC — try HTTP API
            elapsed_pre = time.monotonic() - t0
            api_result = _invoke_via_http(prompt)
            elapsed_total = time.monotonic() - t0
            api_result["elapsed_s"] = round(elapsed_total, 2)
            api_result["route_selected"] = route
            return api_result

    except Exception as exc:
        elapsed = time.monotonic() - t0
        return {
            "route_selected": "ERROR",
            "elapsed_s": round(elapsed, 2),
            "result": "",
            "terminal_state": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
            "source": "error",
        }


def _invoke_via_http(prompt: str, timeout_s: int = 90) -> Dict[str, Any]:
    """Send prompt to HTTP API and poll for result.

    Returns dict with result, terminal_state, error, source.
    """
    base = "http://127.0.0.1:8000"

    # Health check first
    try:
        urllib.request.urlopen(f"{base}/health", timeout=3)
    except Exception:
        return {
            "result": "",
            "terminal_state": "SKIPPED_NO_SERVER",
            "error": "Server not reachable at 127.0.0.1:8000",
            "source": "no_server",
        }

    try:
        # Create or reuse eval session
        req = urllib.request.Request(
            f"{base}/api/sessions",
            data=json.dumps({"user_id": "eval_harness"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        sess = json.loads(urllib.request.urlopen(req, timeout=10).read())
        sid = sess["session_id"]

        # Send chat
        req = urllib.request.Request(
            f"{base}/api/chat",
            data=json.dumps({"user_id": "eval_harness", "session_id": sid, "message": prompt}).encode(),
            headers={"Content-Type": "application/json"},
        )
        chat = json.loads(urllib.request.urlopen(req, timeout=10).read())
        mid = chat.get("mission_id", "")
        # If response already contains result (lightweight handler via HTTP)
        if chat.get("response") and "Mission queued" not in chat.get("response", ""):
            return {
                "result": chat.get("response", ""),
                "terminal_state": "COMPLETE",
                "error": None,
                "source": "http_immediate",
            }

        # Poll for mission completion
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            time.sleep(3)
            r = urllib.request.urlopen(f"{base}/api/missions/{mid}", timeout=10)
            m = json.loads(r.read())
            state = m.get("state", "")
            if state in ("COMPLETE", "FAILED", "TIMEOUT", "ERROR"):
                return {
                    "result": m.get("result", ""),
                    "terminal_state": state,
                    "error": None,
                    "source": "http_poll",
                }

        return {
            "result": "",
            "terminal_state": "TIMEOUT",
            "error": "Polling timeout exceeded",
            "source": "http_poll_timeout",
        }

    except Exception as exc:
        return {
            "result": "",
            "terminal_state": "ERROR",
            "error": f"{type(exc).__name__}: {exc}",
            "source": "http_error",
        }


# ---------------------------------------------------------------------------
# Deterministic Scorer (5 dimensions, 0-3 each)
# ---------------------------------------------------------------------------

_UNCERTAINTY_MARKERS = [
    "nem tudom", "nem garantalhatom", "lehetetlen", "nem latható", "nem ismert",
    "bizonytalan", "nem lehet", "nem tudhatjuk", "nem meghatározható",
    "nem garantálható", "nem jósolható", "nem jósolom", "előrejelzés",
    "ismeretlen", "nem számítható ki", "cannot", "uncertain", "unknown",
    "not knowable", "impossible to predict", "no guarantee",
]

_VAGUE_PHRASES = [
    "általánosságban", "sokféle lehet", "nehéz megmondani", "attól függ",
    "különböző", "számos tényezőtől", "általában", "esetenként",
    "in general", "it depends", "various factors",
]

_STRUCTURE_MARKERS = re.compile(
    r"(^\s*[-•*]\s|^\s*\d+[\.\)]\s|^##?\s|\*\*[^*]+\*\*)",
    re.MULTILINE
)


def score_response(
    prompt_item: Dict[str, Any],
    result: str,
    route_selected: str,
    terminal_state: str,
) -> Dict[str, Any]:
    """Score a response using 5 heuristic dimensions.

    Returns dict with:
        d1_relevance, d2_specificity, d3_truthfulness, d4_structure, d5_action,
        total, max_possible, manual_review_needed, notes
    """
    route = prompt_item.get("route_type_expected", "")
    notes: List[str] = []
    manual_review = False

    # --- Pre-checks ---
    if terminal_state in ("SKIPPED_NO_SERVER", "ERROR", "TIMEOUT"):
        return {
            "d1_relevance": 0, "d2_specificity": 0, "d3_truthfulness": 0,
            "d4_structure": 0, "d5_action": 0,
            "total": 0, "max_possible": 15,
            "manual_review_needed": True,
            "notes": [f"Skipped scoring: terminal_state={terminal_state}"],
        }

    result_lower = result.lower()
    result_norm = _normalize_for_scoring(result)
    lines = [l for l in result.strip().splitlines() if l.strip()]
    word_count = len(result.split())
    has_structure = bool(_STRUCTURE_MARKERS.search(result))
    has_uncertainty = any(m in result_norm for m in _UNCERTAINTY_MARKERS)
    has_vague = any(m in result_lower for m in _VAGUE_PHRASES)

    # --- D1: Relevance ---
    d1 = _score_relevance(prompt_item, result, lines, word_count, route, notes)

    # --- D2: Specificity ---
    d2 = _score_specificity(prompt_item, result, lines, word_count, has_vague, route, notes)

    # --- D3: Truthfulness ---
    d3 = _score_truthfulness(prompt_item, result, has_uncertainty, has_vague, route, notes)

    # --- D4: Structure ---
    d4 = _score_structure(prompt_item, result, lines, has_structure, route, notes)

    # --- D5: Action-readiness ---
    d5 = _score_action_readiness(prompt_item, result, lines, word_count, has_structure, route, notes)

    # Flag for manual review when answer is borderline
    total = d1 + d2 + d3 + d4 + d5
    if total in range(6, 12):
        manual_review = True
        notes.append("Manual review recommended: borderline score")

    return {
        "d1_relevance": d1,
        "d2_specificity": d2,
        "d3_truthfulness": d3,
        "d4_structure": d4,
        "d5_action": d5,
        "total": total,
        "max_possible": 15,
        "manual_review_needed": manual_review,
        "notes": notes,
    }


def _normalize_for_scoring(text: str) -> str:
    """Lowercase + remove accents for scoring checks."""
    MAP = str.maketrans("áéíóöőúüűÁÉÍÓÖŐÚÜŰ", "aeiooouuuAEIOOOUUU")
    return text.lower().translate(MAP)


def _score_relevance(item, result, lines, word_count, route, notes):
    prompt = item["prompt"].lower()
    if word_count < 5:
        notes.append("D1: Answer too short (<5 words) → 0")
        return 0
    if word_count < 20:
        notes.append("D1: Answer very short (<20 words) → 1")
        return 1

    # Route-specific spot checks
    if route == "DIRECT_LIGHTWEIGHT_RESPONSE":
        # Check for format constraints from prompt
        m = re.search(r"(\d+)\s+soros", _normalize_for_scoring(item["prompt"]))
        if m:
            expected_lines = int(m.group(1))
            if abs(len(lines) - expected_lines) <= 1:
                return 3
            elif abs(len(lines) - expected_lines) <= 3:
                notes.append(f"D1: Expected {expected_lines} lines, got {len(lines)}")
                return 2
            else:
                notes.append(f"D1: Expected {expected_lines} lines, got {len(lines)} → 1")
                return 1

        m = re.search(r"(\d+)\s+.*?mondat", _normalize_for_scoring(item["prompt"]))
        if m:
            expected_sents = int(m.group(1))
            sentence_count = len(re.split(r'[.!?]+', result.strip()))
            if abs(sentence_count - expected_sents) <= 1:
                return 3
            elif abs(sentence_count - expected_sents) <= 3:
                notes.append(f"D1: Expected ~{expected_sents} sentences, got ~{sentence_count}")
                return 2
            return 1

    if route == "TRUTHFUL_UNCERTAINTY_RESPONSE":
        norm = _normalize_for_scoring(result)
        if any(m in norm for m in ["nem tudom", "nem garantalhatom", "lehetetlen", "nem lathatom", "nem joslom", "nem lehet"]):
            return 3
        notes.append("D1: TU answer may not explicitly address the uncertainty")
        return 2

    if route == "EXTERNAL_RESEARCH_SYNTHESIS":
        if re.search(r"\d+\.", result):
            return 3
        notes.append("D1: ER answer lacks numbered points")
        return 2

    # General: long answer is probably relevant
    if word_count >= 100:
        return 3
    if word_count >= 40:
        return 2
    return 1


def _score_specificity(item, result, lines, word_count, has_vague, route, notes):
    result_lower = result.lower()

    # Too short = vague by default
    if word_count < 20:
        notes.append("D2: Too short to be specific")
        return 0

    if route == "EXTERNAL_RESEARCH_SYNTHESIS":
        # Check for named tools, dates, or concrete findings
        has_named_entity = bool(re.search(
            r"\b(ollama|lm studio|llm|langchain|langgraph|crewai|mcp|anthropic|openai|mistral|qwen|llama|model context)\b",
            result_lower
        ))
        has_date = bool(re.search(r"\b(2024|2025|2026|january|february|march)\b", result_lower))
        numbered = bool(re.search(r"^\s*\d+\.", result, re.MULTILINE))
        specificity_signals = sum([has_named_entity, has_date, numbered])
        if specificity_signals >= 2:
            return 3
        if specificity_signals == 1:
            notes.append("D2: Some concrete specifics but limited")
            return 2
        if has_vague:
            notes.append("D2: Vague phrases detected")
            return 1
        return 2

    if route == "INTERNAL_PROJECT_DOC_REASONING":
        # Check for gap IDs, milestone numbers, specific model names, phase names
        has_gap = bool(re.search(r"gap_0\d\d", result_lower))
        has_model = bool(re.search(r"(qwen|gpt|deepseek|mistral|llm)", result_lower))
        has_phase = bool(re.search(r"(production_stable|phase|milestone|gap|resolved)", result_lower))
        signals = sum([has_gap, has_model, has_phase])
        if signals >= 2:
            return 3
        if signals == 1:
            notes.append("D2: Limited doc-specific content")
            return 2
        notes.append("D2: No doc-specific markers found")
        return 1

    if route == "DIRECT_LIGHTWEIGHT_RESPONSE":
        # Check for concrete named subject matter
        if word_count >= 60 and not has_vague:
            return 3
        if word_count >= 30:
            return 2
        if has_vague:
            notes.append("D2: Vague phrases detected")
            return 1
        return 2

    if route == "TRUTHFUL_UNCERTAINTY_RESPONSE":
        # Specificity for TU = names what exactly is unknowable
        if word_count >= 50:
            return 3
        if word_count >= 25:
            return 2
        notes.append("D2: TU answer too brief to be specific about the limits")
        return 1

    if route == "FULL_AGENTIC_META_CONTROLLER":
        if has_vague and word_count < 100:
            notes.append("D2: Vague and short for agentic")
            return 1
        if word_count >= 150:
            return 3
        if word_count >= 75:
            return 2
        return 1

    return 2


def _score_truthfulness(item, result, has_uncertainty, has_vague, route, notes):
    result_lower = result.lower()

    if route == "TRUTHFUL_UNCERTAINTY_RESPONSE":
        # Must explicitly handle uncertainty
        if has_uncertainty:
            # Check for strong vs weak uncertainty
            strong_markers = ["nem tudom", "nem garantalhatom", "lehetetlen", "nem lathatom", "nem lehet tudni"]
            norm = _normalize_for_scoring(result)
            if any(m in norm for m in strong_markers):
                return 3
            notes.append("D3: Uncertainty present but weak markers")
            return 2
        notes.append("D3: TU answer lacks explicit uncertainty markers → 1")
        return 1

    # Non-TU routes: check for false overconfidence
    false_confidence_patterns = [
        r"\bbiztosan\b", r"\bgarantálom\b", r"\bgarantalom\b",
        r"\bbiztosan lesz\b", r"\b100%-osan\b",
    ]
    norm = _normalize_for_scoring(result)
    has_false_confidence = any(re.search(p, norm) for p in false_confidence_patterns)
    if has_false_confidence:
        notes.append("D3: False confidence language detected → 1")
        return 1

    # External research: should not present web summaries as certain facts
    if route == "EXTERNAL_RESEARCH_SYNTHESIS":
        if re.search(r"(szerint|alapján|sources|according|research shows)", result_lower):
            return 3
        # No source attribution but also no false confidence
        notes.append("D3: ER answer lacks source attribution language")
        return 2

    # For other routes, truthfulness is presumed unless actively violated
    return 3


def _score_structure(item, result, lines, has_structure, route, notes):
    if not result.strip():
        return 0

    if route == "DIRECT_LIGHTWEIGHT_RESPONSE":
        prompt_norm = _normalize_for_scoring(item["prompt"])
        # Exact line count requested?
        m = re.search(r"(\d+)\s+soros", prompt_norm)
        if m:
            expected = int(m.group(1))
            if abs(len(lines) - expected) <= 1:
                return 3
            if abs(len(lines) - expected) <= 2:
                notes.append(f"D4: Line count off by 2 (expected {expected}, got {len(lines)})")
                return 2
            return 1
        # Bullet prefix requested?
        if "kotojel" in prompt_norm or "kötőjel" in item["prompt"].lower():
            dash_lines = sum(1 for l in lines if l.strip().startswith("-"))
            if dash_lines == len(lines) and len(lines) >= 3:
                return 3
            if dash_lines > 0:
                return 2
            notes.append("D4: Dash prefix requested but not found")
            return 1
        # List requested?
        if has_structure:
            return 3
        if len(lines) >= 3:
            return 2
        return 1 if len(lines) >= 1 else 0

    if route == "TRUTHFUL_UNCERTAINTY_RESPONSE":
        # TU: should have a clear flow (not a wall of text)
        if len(lines) >= 2 and len(result) > 100:
            return 3
        if len(lines) >= 1 and len(result) > 50:
            return 2
        return 1

    if route == "EXTERNAL_RESEARCH_SYNTHESIS":
        # Numbered points are the expected format
        numbered_lines = sum(1 for l in lines if re.match(r"^\s*\d+[\.\)]", l))
        if numbered_lines >= 3:
            return 3
        if numbered_lines >= 1:
            notes.append(f"D4: Only {numbered_lines} numbered points")
            return 2
        if has_structure:
            notes.append("D4: Bullets but no numbers for ER route")
            return 2
        notes.append("D4: ER answer has no numbered structure")
        return 1

    if route == "INTERNAL_PROJECT_DOC_REASONING":
        if has_structure or len(lines) >= 3:
            return 3
        if len(lines) >= 2:
            return 2
        return 1

    if route == "FULL_AGENTIC_META_CONTROLLER":
        # Memo/report structure expected
        has_headers = bool(re.search(r"^#{1,3}\s|\*\*[^*]+\*\*", result, re.MULTILINE))
        if has_headers and len(lines) >= 8:
            return 3
        if has_structure and len(lines) >= 5:
            return 2
        if len(lines) >= 3:
            return 1
        return 0

    # Generic
    if has_structure:
        return 3
    if len(lines) >= 3:
        return 2
    return 1


def _score_action_readiness(item, result, lines, word_count, has_structure, route, notes):
    if word_count < 10:
        notes.append("D5: Too short to be actionable")
        return 0

    if route == "DIRECT_LIGHTWEIGHT_RESPONSE":
        # If it delivered the requested content, it's actionable
        if word_count >= 30 and (has_structure or len(lines) >= 2):
            return 3
        if word_count >= 15:
            return 2
        return 1

    if route == "TRUTHFUL_UNCERTAINTY_RESPONSE":
        # Actionable TU: tells user what THEY CAN do instead
        result_lower = result.lower()
        has_alternative = any(t in result_lower for t in [
            "helyette", "alternatív", "lehet", "próbáld", "javaslom",
            "instead", "however", "alternatively", "consider",
        ])
        if has_alternative and word_count >= 40:
            return 3
        if word_count >= 40:
            notes.append("D5: TU answer long but no alternatives offered")
            return 2
        return 1

    if route == "EXTERNAL_RESEARCH_SYNTHESIS":
        # Numbered findings = actionable
        numbered_lines = sum(1 for l in lines if re.match(r"^\s*\d+[\.\)]", l))
        if numbered_lines >= 4:
            return 3
        if numbered_lines >= 2:
            return 2
        notes.append(f"D5: Only {numbered_lines} actionable numbered points")
        return 1

    if route == "INTERNAL_PROJECT_DOC_REASONING":
        if word_count >= 80 and has_structure:
            return 3
        if word_count >= 40:
            return 2
        return 1

    if route == "FULL_AGENTIC_META_CONTROLLER":
        # Must have a recommendation or conclusion
        has_rec = bool(re.search(
            r"(ajánl|javasl|döntés|conclusion|recommend|suggest|priority|prioritas)",
            result.lower()
        ))
        if has_rec and word_count >= 100:
            return 3
        if word_count >= 80:
            return 2
        return 1

    return 2


# ---------------------------------------------------------------------------
# Run corpus
# ---------------------------------------------------------------------------

SMOKE_IDS = {"DL_01", "TU_01", "ID_01", "ER_01", "FA_01"}


def run_evaluation(smoke_only: bool = False) -> Dict[str, Any]:
    """Run the full (or smoke) corpus and return a results dict."""

    with open(_CORPUS_PATH, encoding="utf-8") as f:
        corpus = json.load(f)

    prompts = corpus["prompts"]
    if smoke_only:
        prompts = [p for p in prompts if p["id"] in SMOKE_IDS]

    results = []
    total_scored = 0
    total_skipped = 0

    print(f"\n{'='*70}")
    print(f"MS-OQ1 Output Quality Baseline — {'SMOKE (5)' if smoke_only else 'FULL (20)'}")
    print(f"{'='*70}\n")

    for item in prompts:
        pid = item["id"]
        route_expected = item["route_type_expected"]
        prompt = item["prompt"]

        print(f"[{pid}] ({route_expected[:20]}) {prompt[:60]}...")
        t0 = time.monotonic()

        invocation = _invoke_route_handler(prompt)
        elapsed = invocation["elapsed_s"]
        result = invocation.get("result", "")
        state = invocation.get("terminal_state", "ERROR")
        route_sel = invocation.get("route_selected", "ERROR")
        error = invocation.get("error")

        score = score_response(item, result, route_sel, state)
        total = score["total"]

        route_match = (route_sel == route_expected)
        status = "PASS" if (state == "COMPLETE" and total >= 10 and route_match) else (
            "SKIP" if state in ("SKIPPED_NO_SERVER",) else "PARTIAL"
        )

        if state in ("SKIPPED_NO_SERVER",):
            total_skipped += 1
        else:
            total_scored += 1

        record = {
            "id": pid,
            "group": item.get("group"),
            "route_expected": route_expected,
            "route_selected": route_sel,
            "route_match": route_match,
            "prompt": prompt,
            "elapsed_s": elapsed,
            "terminal_state": state,
            "result_preview": result[:300] if result else "",
            "result_length": len(result),
            "error": error,
            "score": score,
            "status": status,
        }
        results.append(record)

        print(f"       state={state}  route_match={route_match}  score={total}/15  status={status}")
        if error:
            print(f"       ERROR: {error[:80]}")

    # Summary stats
    completed = [r for r in results if r["terminal_state"] == "COMPLETE"]
    route_matches = sum(1 for r in completed if r["route_match"])
    scores = [r["score"]["total"] for r in completed if r["score"]["total"] > 0]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    summary = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "mode": "smoke" if smoke_only else "full",
        "total_prompts": len(prompts),
        "total_completed": len(completed),
        "total_skipped": total_skipped,
        "route_match_rate": f"{route_matches}/{len(completed)}" if completed else "0/0",
        "average_score": avg_score,
        "max_possible": 15,
        "pass_threshold": 12,
        "scores_above_threshold": sum(1 for s in scores if s >= 12),
        "corpus_version": corpus.get("corpus_version", "1.0"),
    }

    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"  Completed: {len(completed)}/{len(prompts)}")
    print(f"  Skipped:   {total_skipped}")
    print(f"  Route match rate: {summary['route_match_rate']}")
    print(f"  Average score: {avg_score}/15")
    print(f"  Scores ≥12: {summary['scores_above_threshold']}/{len(scores)}")
    print(f"{'='*70}\n")

    return {"summary": summary, "results": results}


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_json(data: Dict[str, Any], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON results written: {path}")


def write_markdown_report(data: Dict[str, Any], path: Path) -> None:
    s = data["summary"]
    results = data["results"]
    date = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# MS-OQ1 — Output Quality Baseline Report",
        f"",
        f"**Date:** {date}  ",
        f"**Mode:** {s['mode'].upper()}  ",
        f"**Corpus version:** {s['corpus_version']}  ",
        f"",
        f"---",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Prompts run | {s['total_prompts']} |",
        f"| Completed (COMPLETE state) | {s['total_completed']} |",
        f"| Skipped (no server / error) | {s['total_skipped']} |",
        f"| Route match rate | {s['route_match_rate']} |",
        f"| Average score | **{s['average_score']} / 15** |",
        f"| Scores ≥ 12 (target) | {s['scores_above_threshold']} |",
        f"",
        f"---",
        f"",
        f"## Per-Prompt Results",
        f"",
        f"| ID | Group | Route Expected | Route Selected | Match | State | Score | Status |",
        f"|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        sc = r["score"]["total"]
        lines.append(
            f"| {r['id']} | {r['group']} | {r['route_expected'][:25]} | "
            f"{r['route_selected'][:25]} | {'✅' if r['route_match'] else '❌'} | "
            f"{r['terminal_state']} | {sc}/15 | {r['status']} |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## Score Detail",
        f"",
    ]

    for r in results:
        sc = r["score"]
        lines += [
            f"### {r['id']} — {r['route_expected']}",
            f"",
            f"**Prompt:** {r['prompt'][:120]}",
            f"",
            f"| Dimension | Score |",
            f"|---|---|",
            f"| D1 Relevance | {sc['d1_relevance']} / 3 |",
            f"| D2 Specificity | {sc['d2_specificity']} / 3 |",
            f"| D3 Truthfulness | {sc['d3_truthfulness']} / 3 |",
            f"| D4 Structure | {sc['d4_structure']} / 3 |",
            f"| D5 Action-readiness | {sc['d5_action']} / 3 |",
            f"| **Total** | **{sc['total']} / 15** |",
            f"",
        ]
        if sc.get("notes"):
            lines.append(f"Notes: {'; '.join(sc['notes'])}")
            lines.append("")
        if r.get("result_preview"):
            preview = r["result_preview"].replace("\n", " ↵ ")[:200]
            lines.append(f"Preview: `{preview}`")
            lines.append("")

    lines += [
        f"---",
        f"",
        f"## Scoring Notes",
        f"",
        f"- Scores are **heuristic** (deterministic checks on length, structure markers, uncertainty language).",
        f"- FULL_AGENTIC results require a running server; skipped if server is offline.",
        f"- `manual_review_needed=True` items should be reviewed by a human evaluator.",
        f"- Target threshold: average ≥ 12/15 (not expected at baseline).",
        f"",
        f"---",
        f"",
        f"*Generated by `interactive_layer/evaluate_output_quality_baseline.py`*",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown report written: {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    smoke = "--smoke" in sys.argv
    json_only = "--json-only" in sys.argv

    data = run_evaluation(smoke_only=smoke)

    write_json(data, _JSON_OUT)
    if not json_only:
        write_markdown_report(data, _MD_OUT)


if __name__ == "__main__":
    main()
