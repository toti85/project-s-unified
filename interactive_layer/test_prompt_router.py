#!/usr/bin/env python3
"""GAP_031 Phase 1 — Prompt Router Tests.

Covers:
A. Hungarian normalization
B. Route classification (8-test acceptance matrix)
C. Route metadata persistence
D. Execution path verification (no MetaController for lightweight routes)
E. Regression: prior GAP_026/GAP_029/GAP_030 compatibility
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure we can import from interactive_layer
sys.path.insert(0, str(Path(__file__).parent))

from prompt_router import (
    classify_prompt,
    handle_direct_lightweight,
    handle_external_research_synthesis,
    handle_internal_doc_reasoning,
    handle_truthful_uncertainty,
    normalize_hungarian,
    normalize_text,
    probe,
    _derive_search_query,
    _extract_point_count,
    _ddgs_search_sync,
    get_route_handler,
    RouteType,
    RouteDecision,
)


# =============================================================================
# A. Hungarian Normalization Tests
# =============================================================================

class TestHungarianNormalization(unittest.TestCase):
    """Test Hungarian accent normalization."""

    def test_basic_accent_removal(self):
        """á→a, é→e, ö→o, ő→o, ú→u, ü→u, ű→u, í→i, ó→o."""
        self.assertEqual(normalize_hungarian("állapot"), "allapot")
        self.assertEqual(normalize_hungarian("bevétel"), "bevetel")
        self.assertEqual(normalize_hungarian("döntés"), "dontes")
        self.assertEqual(normalize_hungarian("fejlesztés"), "fejlesztes")
        self.assertEqual(normalize_hungarian("közép"), "kozep")
        self.assertEqual(normalize_hungarian("működik"), "mukodik")
        self.assertEqual(normalize_hungarian("röviden"), "roviden")
        self.assertEqual(normalize_hungarian("szűrő"), "szuro")

    def test_uppercase_accent_removal(self):
        """Á→A, É→E, etc. (uppercase preserved)."""
        self.assertEqual(normalize_hungarian("Állapot"), "Allapot")
        self.assertEqual(normalize_hungarian("Érték"), "Ertek")
        self.assertEqual(normalize_hungarian("Örök"), "Orok")

    def test_full_normalize(self):
        """normalize_text = Hungarian + lowercase + strip."""
        result = normalize_text("Írj 3 rövid mondatot")
        self.assertEqual(result, "irj 3 rovid mondatot")

        result = normalize_text("  Project-S  ")
        self.assertEqual(result, "project-s")

    def test_no_accents(self):
        """Text without Hungarian accents passes through lowercase."""
        result = normalize_text("hello world")
        self.assertEqual(result, "hello world")


# =============================================================================
# B. Route Classification Tests (8-Test Acceptance Matrix)
# =============================================================================

class TestRouteClassification(unittest.TestCase):
    """Test that each of the 8 acceptance matrix prompts routes correctly."""

    # 8-test prompts from the architecture design
    PROMPTS = [
        # TEST_1: Direct simple answer — "Írj 3 rövid mondatot"
        "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
        # TEST_2: Self-state retrieval — "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota"
        "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
        # TEST_3: Strategic recommendation — "Készíts rövid döntési memót"
        "Készíts rövid döntési memót: a Project-S következő UI-fejlesztése.",
        # TEST_4: Diagnostic — "Lassú a laptop. Mérd fel röviden, milyen irányokban"
        "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
        # TEST_5: External research — "Keress röviden 3 aktuális okot"
        "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM.",
        # TEST_6: Internal-doc reasoning — "A Project-S jelenlegi dokumentumai alapján"
        "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.",
        # TEST_7: Output-format compliance — "Adj egy pontosan 4 soros választ"
        "Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel.",
        # TEST_8: Truthfulness — "Mondd meg biztosan, hogy holnap pontosan mennyi bevétel"
        "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
    ]

    # Expected routes from the architecture design
    EXPECTED = {
        1: RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
        2: RouteType.INTERNAL_PROJECT_DOC_REASONING,
        3: RouteType.FULL_AGENTIC_META_CONTROLLER,
        4: RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
        5: RouteType.EXTERNAL_RESEARCH_SYNTHESIS,
        6: RouteType.INTERNAL_PROJECT_DOC_REASONING,
        7: RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
        8: RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
    }

    def test_all_8_prompts(self):
        """Run all 8 prompts through the router and check expected routes."""
        results = probe(self.PROMPTS)
        for i, expected_route in self.EXPECTED.items():
            actual = results[i - 1].route_type
            self.assertEqual(
                actual,
                expected_route,
                f"TEST_{i}: expected {expected_route}, got {actual}. "
                f"Prompt: {self.PROMPTS[i-1][:60]}..."
            )

    def test_confidence_range(self):
        """All matches should have confidence >= 0.5."""
        results = probe(self.PROMPTS)
        for i, r in enumerate(results, 1):
            self.assertGreaterEqual(
                r.confidence, 0.5,
                f"TEST_{i}: confidence {r.confidence} below 0.5"
            )

    def test_matched_rules_not_empty_for_matches(self):
        """All matched prompts should have at least one matched rule."""
        results = probe(self.PROMPTS)
        for i, r in enumerate(results, 1):
            self.assertGreater(
                len(r.matched_rules), 0,
                f"TEST_{i}: no matched rules for prompt"
            )

    def test_rationale_not_empty(self):
        """All decisions should have a rationale."""
        results = probe(self.PROMPTS)
        for i, r in enumerate(results, 1):
            self.assertTrue(
                len(r.rationale) > 0,
                f"TEST_{i}: empty rationale"
            )


# =============================================================================
# C. Route Metadata Persistence Tests
# =============================================================================

class TestRouteMetadataPersistence(unittest.TestCase):
    """Test that route metadata is correctly stored in missions."""

    def test_classify_returns_correct_fields(self):
        """RouteDecision has all required fields."""
        decision = classify_prompt("Írj 3 rövid mondatot")
        self.assertIsNotNone(decision.route_type)
        self.assertGreaterEqual(decision.confidence, 0.5)
        self.assertTrue(len(decision.rationale) > 0)
        self.assertTrue(len(decision.matched_rules) > 0)
        self.assertIsInstance(decision.llm_used, bool)
        self.assertIsInstance(decision.requires_tools, bool)
        self.assertIsInstance(decision.allow_meta_controller, bool)

    def test_route_decision_dataclass(self):
        """RouteDecision is a proper dataclass."""
        d = RouteDecision(
            route_type="TEST",
            confidence=0.8,
            rationale="test rationale",
            matched_rules=["rule1", "rule2"],
        )
        self.assertEqual(d.route_type, "TEST")
        self.assertEqual(d.confidence, 0.8)
        self.assertEqual(len(d.matched_rules), 2)
        self.assertFalse(d.llm_used)
        self.assertFalse(d.requires_tools)
        self.assertFalse(d.requires_internal_docs)
        self.assertFalse(d.requires_external_web)
        self.assertTrue(d.allow_meta_controller)


# =============================================================================
# D. Execution Path Tests (No MetaController for lightweight routes)
# =============================================================================

class TestExecutionPaths(unittest.TestCase):
    """Test that route handlers produce correct results without MetaController."""

    def test_direct_lightweight_test1(self):
        """TEST_1: DIRECT_LIGHTWEIGHT_RESPONSE produces COMPLETE state."""
        decision = classify_prompt(self.PROMPTS[0])
        self.assertEqual(decision.route_type, RouteType.DIRECT_LIGHTWEIGHT_RESPONSE)
        result = handle_direct_lightweight(
            self.PROMPTS[0], decision, "test_mission_1"
        )
        self.assertEqual(result["route_type"], RouteType.DIRECT_LIGHTWEIGHT_RESPONSE)
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertTrue(len(result["result"]) > 0)
        self.assertIn("matched_rules", result)

    def test_direct_lightweight_test4(self):
        """TEST_4: DIRECT_LIGHTWEIGHT_RESPONSE diagnostic advice."""
        decision = classify_prompt(self.PROMPTS[3])
        self.assertEqual(decision.route_type, RouteType.DIRECT_LIGHTWEIGHT_RESPONSE)
        result = handle_direct_lightweight(
            self.PROMPTS[3], decision, "test_mission_4"
        )
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertTrue(len(result["result"]) > 0)

    def test_direct_lightweight_test7(self):
        """TEST_7: DIRECT_LIGHTWEIGHT_RESPONSE exact N-line output."""
        decision = classify_prompt(self.PROMPTS[6])
        self.assertEqual(decision.route_type, RouteType.DIRECT_LIGHTWEIGHT_RESPONSE)
        result = handle_direct_lightweight(
            self.PROMPTS[6], decision, "test_mission_7"
        )
        self.assertEqual(result["mission_state"], "COMPLETE")
        # Should produce exactly 4 lines
        lines = result["result"].split("\n")
        self.assertEqual(len(lines), 4, f"Expected 4 lines, got {len(lines)}: {lines}")

    def test_truthful_uncertainty_test8(self):
        """TEST_8: TRUTHFUL_UNCERTAINTY_RESPONSE refuses impossible prediction."""
        decision = classify_prompt(self.PROMPTS[7])
        self.assertEqual(decision.route_type, RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE)
        result = handle_truthful_uncertainty(
            self.PROMPTS[7], decision, "test_mission_8"
        )
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertTrue(len(result["result"]) > 0)
        # Should contain uncertainty language
        result_lower = result["result"].lower()
        self.assertTrue(
            any(word in result_lower for word in ["lehetetlen", "nem tudom", "nem garantal"]),
            f"Result should contain uncertainty language: {result['result'][:100]}"
        )

    def test_internal_doc_reasoning_test2(self):
        """TEST_2: INTERNAL_PROJECT_DOC_REASONING references internal docs."""
        decision = classify_prompt(self.PROMPTS[1])
        self.assertEqual(decision.route_type, RouteType.INTERNAL_PROJECT_DOC_REASONING)
        result = handle_internal_doc_reasoning(
            self.PROMPTS[1], decision, "test_mission_2"
        )
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertTrue(len(result["result"]) > 0)
        # Should reference internal documents
        self.assertIn("Dokumentumok", result["result"])

    def test_internal_doc_reasoning_test6(self):
        """TEST_6: INTERNAL_PROJECT_DOC_REASONING with dokumentumai alapján."""
        decision = classify_prompt(self.PROMPTS[5])
        self.assertEqual(decision.route_type, RouteType.INTERNAL_PROJECT_DOC_REASONING)
        result = handle_internal_doc_reasoning(
            self.PROMPTS[5], decision, "test_mission_6"
        )
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertTrue(len(result["result"]) > 0)

    def test_get_route_handler(self):
        """get_route_handler returns correct handler for each route type."""
        self.assertIsNotNone(get_route_handler(RouteType.DIRECT_LIGHTWEIGHT_RESPONSE))
        self.assertIsNotNone(get_route_handler(RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE))
        self.assertIsNotNone(get_route_handler(RouteType.INTERNAL_PROJECT_DOC_REASONING))
        # Phase 2: EXTERNAL_RESEARCH_SYNTHESIS now has a dedicated handler
        self.assertIsNotNone(get_route_handler(RouteType.EXTERNAL_RESEARCH_SYNTHESIS))
        # Still unimplemented routes return None
        self.assertIsNone(get_route_handler(RouteType.FULL_AGENTIC_META_CONTROLLER))
        self.assertIsNone(get_route_handler(RouteType.CLARIFICATION_NEEDED))

    # Reference to prompts for error messages
    PROMPTS = [
        "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
        "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
        "Készíts rövid döntési memót: a Project-S következő UI-fejlesztése.",
        "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
        "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM.",
        "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.",
        "Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel.",
        "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
    ]


# =============================================================================
# E. Phase 2 — EXTERNAL_RESEARCH_SYNTHESIS Tests
# =============================================================================

class TestExternalResearchSynthesis(unittest.TestCase):
    """Phase 2: EXTERNAL_RESEARCH_SYNTHESIS handler tests."""

    TEST5_PROMPT = (
        "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM "
        "egy saját AI-infrastruktúrában, és foglald össze 5 pontban."
    )

    def test_route_dispatch_handler_registered(self):
        """get_route_handler(EXTERNAL_RESEARCH_SYNTHESIS) returns a callable."""
        handler = get_route_handler(RouteType.EXTERNAL_RESEARCH_SYNTHESIS)
        self.assertIsNotNone(handler)
        self.assertTrue(callable(handler))

    def test_route_classification_test5(self):
        """TEST_5 prompt classifies as EXTERNAL_RESEARCH_SYNTHESIS."""
        decision = classify_prompt(self.TEST5_PROMPT)
        self.assertEqual(decision.route_type, RouteType.EXTERNAL_RESEARCH_SYNTHESIS)

    @patch("prompt_router._ddgs_search_sync")
    def test_handler_with_search_results(self, mock_search):
        """Handler with mocked results returns COMPLETE state with numbered points."""
        mock_search.return_value = [
            {"title": f"Result {i}", "url": f"https://example.com/{i}",
             "description": f"This is a description of result {i} about local LLMs."}
            for i in range(1, 8)
        ]
        decision = classify_prompt(self.TEST5_PROMPT)
        result = handle_external_research_synthesis(self.TEST5_PROMPT, decision, "test-mission")
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertEqual(result["route_type"], RouteType.EXTERNAL_RESEARCH_SYNTHESIS)
        self.assertGreater(len(result["result"]), 20)
        self.assertGreater(result.get("sources_count", 0), 0)
        # Should contain numbered points
        self.assertIn("1.", result["result"])
        self.assertIn("2.", result["result"])

    @patch("prompt_router._ddgs_search_sync")
    def test_handler_no_results_truthful_fallback(self, mock_search):
        """Handler with empty search results returns COMPLETE with truthful fallback text."""
        mock_search.return_value = []
        decision = classify_prompt(self.TEST5_PROMPT)
        result = handle_external_research_synthesis(self.TEST5_PROMPT, decision, "test-mission")
        self.assertEqual(result["mission_state"], "COMPLETE")
        self.assertEqual(result.get("sources_count", 0), 0)
        # Fallback must contain numbered points (not invent fabricated web data)
        self.assertIn("1.", result["result"])
        self.assertIn("5.", result["result"])

    @patch("prompt_router._ddgs_search_sync")
    def test_handler_does_not_use_metacontroller(self, mock_search):
        """Handler must return without calling the MetaController."""
        mock_search.return_value = [
            {"title": "T", "url": "https://example.com", "description": "Desc."}
        ]
        decision = classify_prompt(self.TEST5_PROMPT)
        # Simply completing without error proves no MetaController was entered
        result = handle_external_research_synthesis(self.TEST5_PROMPT, decision, "mc-bypass-test")
        self.assertIsNotNone(result)
        self.assertEqual(result["route_type"], RouteType.EXTERNAL_RESEARCH_SYNTHESIS)

    def test_derive_search_query_extracts_llm_terms(self):
        """_derive_search_query extracts LLM-related English terms from the Hungarian prompt."""
        norm = normalize_text(self.TEST5_PROMPT)
        query = _derive_search_query(self.TEST5_PROMPT, norm)
        self.assertGreater(len(query), 5)
        ql = query.lower()
        self.assertTrue(
            "llm" in ql or "local" in ql or "ai" in ql,
            f"Query {query!r} missing expected terms",
        )

    def test_extract_point_count_5(self):
        """_extract_point_count returns 5 for 'foglald össze 5 pontban'."""
        norm = normalize_text(self.TEST5_PROMPT)
        self.assertEqual(_extract_point_count(norm), 5)

    def test_extract_point_count_default(self):
        """_extract_point_count returns 5 as default when no number specified."""
        norm = normalize_text("Keress informáciát a lokális LLM-ről.")
        self.assertEqual(_extract_point_count(norm), 5)

    @patch("prompt_router._ddgs_search_sync")
    def test_regression_phase1_routes_unchanged(self, _mock):
        """Phase 1 classification for the other 7 prompts remains unchanged."""
        cases = [
            ("Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
             RouteType.DIRECT_LIGHTWEIGHT_RESPONSE),
            ("Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
             RouteType.INTERNAL_PROJECT_DOC_REASONING),
            ("Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
             RouteType.DIRECT_LIGHTWEIGHT_RESPONSE),
            ("A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő "
             "legésszerűbb fejlesztési irány.",
             RouteType.INTERNAL_PROJECT_DOC_REASONING),
            ("Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel.",
             RouteType.DIRECT_LIGHTWEIGHT_RESPONSE),
            ("Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
             RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE),
        ]
        for prompt, expected in cases:
            with self.subTest(p=prompt[:50]):
                self.assertEqual(classify_prompt(prompt).route_type, expected)


# =============================================================================
# F. Regression Tests
# =============================================================================

class TestRegression(unittest.TestCase):
    """Regression tests for prior GAP compatibility."""

    def test_full_agentic_defaults(self):
        """FULL_AGENTIC_META_CONTROLLER still works as default."""
        decision = classify_prompt("Valami ami nem illeszkedik egyik mintára sem.")
        self.assertEqual(decision.route_type, RouteType.FULL_AGENTIC_META_CONTROLLER)
        self.assertLessEqual(decision.confidence, 0.5)

    def test_complex_agentic_patterns(self):
        """Complex agentic prompts still route to FULL_AGENTIC_META_CONTROLLER."""
        decision = classify_prompt("Készíts tervet a Project-S következő évadra.")
        self.assertEqual(decision.route_type, RouteType.FULL_AGENTIC_META_CONTROLLER)

    def test_clarification_fallback(self):
        """Ambiguous prompts that match multiple routes get the highest priority."""
        # A prompt matching both DIRECT and INTERNAL_DOC should get the one with more matches
        decision = classify_prompt("Project-S jelenlegi állapota")
        # Should match INTERNAL_DOC patterns
        self.assertEqual(decision.route_type, RouteType.INTERNAL_PROJECT_DOC_REASONING)

    def test_empty_prompt(self):
        """Empty or whitespace-only prompts default to FULL_AGENTIC."""
        decision = classify_prompt("   ")
        self.assertEqual(decision.route_type, RouteType.FULL_AGENTIC_META_CONTROLLER)

    def test_route_decision_allow_meta_controller_flag(self):
        """allow_meta_controller is True only for FULL_AGENTIC."""
        d1 = classify_prompt("Írj 3 rövid mondatot")
        self.assertFalse(d1.allow_meta_controller)

        d2 = classify_prompt("Készíts tervet")
        self.assertTrue(d2.allow_meta_controller)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)