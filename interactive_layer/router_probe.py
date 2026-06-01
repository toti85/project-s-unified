#!/usr/bin/env python3
"""GAP_031 Logging-Only Router Probe — DESIGN PHASE ONLY.

This module does NOT change any execution behavior.
It only classifies prompts according to proposed deterministic rules
and prints the classification for diagnostic reporting.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List


class RouteType:
    DIRECT_TEXT_RESPONSE = "DIRECT_TEXT_RESPONSE"
    TRUTHFUL_UNCERTAINTY_RESPONSE = "TRUTHFUL_UNCERTAINTY_RESPONSE"
    INTERNAL_PROJECT_DOC_REASONING = "INTERNAL_PROJECT_DOC_REASONING"
    EXTERNAL_RESEARCH_SYNTHESIS = "EXTERNAL_RESEARCH_SYNTHESIS"
    FULL_AGENTIC_META_CONTROLLER = "FULL_AGENTIC_META_CONTROLLER"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"


@dataclass
class RouteDecision:
    prompt: str
    route_type: str
    confidence: float
    rationale: str
    matched_rules: List[str] = field(default_factory=list)
    requires_tools: bool = False
    requires_internal_docs: bool = False
    requires_external_web: bool = False
    allow_meta_controller: bool = True


def _normalize_hungarian(text: str) -> str:
    """Normalize Hungarian accented characters to ASCII equivalents for regex matching."""
    # Map Hungarian special chars to ASCII equivalents
    mapping = {
        'á': 'a', 'Á': 'A',
        'é': 'e', 'É': 'E',
        'í': 'i', 'Í': 'I',
        'ó': 'o', 'Ó': 'O',
        'ö': 'o', 'Ö': 'O',
        'ő': 'o', 'Ő': 'O',
        'ú': 'u', 'Ú': 'U',
        'ü': 'u', 'Ü': 'U',
        'ű': 'u', 'Ű': 'U',
    }
    result = []
    for ch in text:
        result.append(mapping.get(ch, ch.lower()))
    return ''.join(result)


# --- Deterministic Rule Sets ---

TRUTHINESS_PATTERNS = [
    r"biztosan\s",
    r"garant",
    r"pontosan\s+mennyi",
    r"pontos\s+bevete",
    r"holnap\s+pontosan",
    r"bekövetkezik",
    r"garantaltan",
    r"100%\s",
]

DIRECT_TEXT_PATTERNS = [
    r"irj\s+\d+\s+mondat",
    r"irj\s+\d+\s+sort",
    r"fogalmazd\s+meg",
    r"summazd\s+röviden",
    r"summazd\s+roviden",
    r"adj\s+rövid\s+valasz",
    r"adj\s+rovid\s+valasz",
    r"roviden\s+irj",
    r"valaszolj\s+röviden",
    r"valaszolj\s+roviden",
    r"adj\s+pontosan\s+\d+\s+soros",
]

INTERNAL_DOC_PATTERNS = [
    r"self_state",
    r"PROJECT_S_OVERVIEW",
    r"STATUS_AND_JOURNAL",
    r"GAP_0\d\d",
    r"project-s\s+jelenlegi\s+allapot",
    r"project-s\s+jelenlegi\s+dokumentum",
    r"project-s\s+következo\s+fejlesztesi",
    r"project-s\s+kovetkezo\s+fejlesztesi",
    r"project-s\s+statusza",
    r"project-s\s+statusz",
    r"project-s\s+fejlesztesi\s+irany",
    r"project-s\s+mi\s+a\s+kovetkezo",
    r"project-s\s+mi\s+kovetkezo",
    r"project-s\s+mi\s+a\s+kovetkezo\s+legyszerubb",
    r"project-s\s+jelenlegi\s+dokumentumai\s+alapjan",
]

EXTERNAL_RESEARCH_PATTERNS = [
    r"keress",
    r"keres",
    r"talald\s+meg",
    r"aktualis",
    r"legfrissebb",
    r"jelenlegi\s+piaci",
    r"milyen\s+uj",
    r"nezze\s+utana",
    r"nez\s+utana",
    r"piaci\s+ar",
    r"piaci\s+arat",
    r"osszehasonlitsd",
    r"osszehasonlitas",
]

FULL_AGENTIC_PATTERNS = [
    r"elemzend\s+es\s+hasonlitsd",
    r"elemzend\s+es\s+keszits",
    r"iteral",
    r"keszits\s+tervet",
    r"tobb\s+szempont\s+szerint",
    r"komplex\s+strategiai",
    r"tobb\s+lepeses",
    r"strukturalt\s+jelentes",
    r"dontesi\s+memo",
]


def classify_prompt(prompt: str) -> RouteDecision:
    """Classify a prompt using deterministic rules. Returns RouteDecision."""
    # Normalize Hungarian characters for matching
    prompt_norm = _normalize_hungarian(prompt)
    scores = {}

    # Score each route
    for pattern in TRUTHINESS_PATTERNS:
        if re.search(pattern, prompt_norm):
            scores.setdefault(RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE, []).append(pattern)

    for pattern in DIRECT_TEXT_PATTERNS:
        if re.search(pattern, prompt_norm):
            scores.setdefault(RouteType.DIRECT_TEXT_RESPONSE, []).append(pattern)

    for pattern in INTERNAL_DOC_PATTERNS:
        if re.search(pattern, prompt_norm):
            scores.setdefault(RouteType.INTERNAL_PROJECT_DOC_REASONING, []).append(pattern)

    for pattern in EXTERNAL_RESEARCH_PATTERNS:
        if re.search(pattern, prompt_norm):
            scores.setdefault(RouteType.EXTERNAL_RESEARCH_SYNTHESIS, []).append(pattern)

    for pattern in FULL_AGENTIC_PATTERNS:
        if re.search(pattern, prompt_norm):
            scores.setdefault(RouteType.FULL_AGENTIC_META_CONTROLLER, []).append(pattern)

    # Determine winner
    if not scores:
        return RouteDecision(
            prompt=prompt,
            route_type=RouteType.FULL_AGENTIC_META_CONTROLLER,
            confidence=0.3,
            rationale="No rules matched - defaults to full agentic (conservative)",
            matched_rules=[],
        )

    # Sort by number of matched rules (descending)
    best_route = max(scores.keys(), key=lambda r: len(scores[r]))
    matched = scores[best_route]

    # Confidence based on rule count and specificity
    confidence = min(0.95, 0.5 + 0.15 * len(matched))

    # Build decision metadata
    requires_tools = best_route in (
        RouteType.EXTERNAL_RESEARCH_SYNTHESIS,
        RouteType.FULL_AGENTIC_META_CONTROLLER,
    )
    requires_internal_docs = best_route == RouteType.INTERNAL_PROJECT_DOC_REASONING
    requires_external_web = best_route == RouteType.EXTERNAL_RESEARCH_SYNTHESIS
    allow_meta_controller = best_route == RouteType.FULL_AGENTIC_META_CONTROLLER

    return RouteDecision(
        prompt=prompt,
        route_type=best_route,
        confidence=confidence,
        rationale=f"Matched {len(matched)} rules: {', '.join(matched[:3])}",
        matched_rules=matched,
        requires_tools=requires_tools,
        requires_internal_docs=requires_internal_docs,
        requires_external_web=requires_external_web,
        allow_meta_controller=allow_meta_controller,
    )


def probe_results(probes: List[str]) -> List[RouteDecision]:
    """Run classification on a list of prompts."""
    return [classify_prompt(p) for p in probes]


if __name__ == "__main__":
    # 8-test acceptance matrix prompts
    prompts = [
        # TEST_1: Direct simple answer
        "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
        # TEST_2: Self-state retrieval
        "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
        # TEST_3: Strategic recommendation
        "Készíts rövid döntési memót: a Project-S következő UI-fejlesztése inkább file upload/download legyen, vagy mission history? Adj egy konkrét ajánlást.",
        # TEST_4: Diagnostic-style operator request
        "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
        # TEST_5: External research task
        "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM egy saját AI-infrastruktúrában, és foglald össze 5 pontban.",
        # TEST_6: Internal-doc reasoning
        "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.",
        # TEST_7: Output-format compliance
        "Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel. Téma: mi működik most jól a Project-S-ben.",
        # TEST_8: Truthfulness / impossible prediction
        "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
    ]

    results = probe_results(prompts)

    print("=" * 80)
    print("GAP_031 ROUTER PROBE - DESIGN PHASE ONLY")
    print("=" * 80)

    for i, r in enumerate(results, 1):
        print(f"\nTEST_{i}: {r.route_type}")
        print(f"  Confidence: {r.confidence:.2f}")
        print(f"  Rationale: {r.rationale}")
        print(f"  Matched rules: {len(r.matched_rules)}")
        print(f"  Requires tools: {r.requires_tools}")
        print(f"  Requires internal docs: {r.requires_internal_docs}")
        print(f"  Requires external web: {r.requires_external_web}")
        print(f"  Allow MetaController: {r.allow_meta_controller}")
        print(f"  Prompt: {prompts[i-1][:80]}...")

    print("\n" + "=" * 80)
    print("PROBE SUMMARY")
    print("=" * 80)

    route_counts = {}
    for r in results:
        route_counts[r.route_type] = route_counts.get(r.route_type, 0) + 1

    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")

    # Check for misclassifications
    expected = {
        1: RouteType.DIRECT_TEXT_RESPONSE,
        2: RouteType.INTERNAL_PROJECT_DOC_REASONING,
        3: RouteType.FULL_AGENTIC_META_CONTROLLER,
        4: RouteType.DIRECT_TEXT_RESPONSE,
        5: RouteType.EXTERNAL_RESEARCH_SYNTHESIS,
        6: RouteType.INTERNAL_PROJECT_DOC_REASONING,
        7: RouteType.DIRECT_TEXT_RESPONSE,
        8: RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
    }

    print("\nMISCLASSIFICATION CHECK:")
    for i, r in enumerate(results, 1):
        exp = expected.get(i)
        if exp and r.route_type != exp:
            print(f"  TEST_{i}: MISMATCH - expected {exp}, got {r.route_type}")
        elif exp:
            print(f"  TEST_{i}: OK - {r.route_type}")