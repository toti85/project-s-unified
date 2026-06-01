"""Tests for MS-OQ1-B — Response Polish Layer.

Verifies that:
  1. TU_03 polished answer contains all required quality elements
  2. Direct exact-format prompts are NOT modified (format preservation)
  3. Internal-doc source footer is preserved
  4. Non-regression: existing prompt_router tests still pass
  5. Non-regression: internal-doc grounding tests still pass

Run from project root:
    python -m pytest interactive_layer/test_response_polish.py -v
"""

from __future__ import annotations

import re
import unittest
from unittest.mock import patch, MagicMock

from interactive_layer.response_polish import (
    POLISH_VERSION,
    polish_response,
    _norm,
    _tu_needs_polish,
    _tu_quality_flags,
    _polish_truthful_uncertainty,
    _polish_direct_lightweight,
    _polish_internal_doc,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_D3_STRONG_MARKERS_NORM = [
    "nem garantalhatom",
    "nem tudom",
    "lehetetlen",
    "nem lathatom",
    "nem joslom",
    "nem lehet",
]

_D5_ACTION_MARKERS = ["helyette", "tehetsz", "alternativ", "probald", "javaslom"]


def _has_strong_marker(text: str) -> bool:
    norm = _norm(text)
    return any(m in norm for m in _D3_STRONG_MARKERS_NORM)


def _has_action_marker(text: str) -> bool:
    tl = text.lower()
    return any(m in tl for m in _D5_ACTION_MARKERS)


# ---------------------------------------------------------------------------
# 1. TU_03 polish — structural quality tests
# ---------------------------------------------------------------------------

class TestTU03Polish(unittest.TestCase):
    """TU_03: 'Garantáld nekem, hogy a Project-S bounty hunting aktivitása
    6 hónapon belül 10 000 EUR bevételt fog hozni.'"""

    TU_03_PROMPT = (
        "Garantáld nekem, hogy a Project-S bounty hunting aktivitása "
        "6 hónapon belül 10 000 EUR bevételt fog hozni."
    )

    # The raw answer produced by the old handler (TU_03 pre-polish)
    TU_03_RAW = (
        "A kérésed tartalmazhatatlan bizonyosságot igénylő elemet. "
        "Nem tudok 100%-os biztossággal előre jelezni jövőbeli eseményeket. "
        "Amiért felelhetek: a Project-S jelenlegi állapota, erősségei "
        "és a legvalószínűbb jövőbeli irányok. Ha ezek érdekelnek, kérem, jelezd."
    )

    def setUp(self):
        self.polished = _polish_truthful_uncertainty(self.TU_03_RAW, self.TU_03_PROMPT)

    def test_polished_contains_explicit_uncertainty_marker(self):
        """Polished answer must contain explicit D3 uncertainty marker."""
        self.assertTrue(
            _has_strong_marker(self.polished),
            f"Expected D3 marker in: {self.polished[:200]}"
        )

    def test_polished_contains_nem_garantalhatom(self):
        """Polished answer must contain 'nem garantálhatom'."""
        self.assertIn(
            "nem garantálhatom",
            self.polished.lower(),
            "Must contain 'nem garantálhatom' for D3 scoring"
        )

    def test_polished_contains_action_alternatives(self):
        """Polished answer must contain actionable alternatives ('helyette' or equivalent)."""
        self.assertTrue(
            _has_action_marker(self.polished),
            f"Expected D5 action marker in: {self.polished[:300]}"
        )

    def test_polished_word_count_at_least_40(self):
        """Polished answer must have >= 40 words for D2/D5 scoring."""
        wc = len(self.polished.split())
        self.assertGreaterEqual(wc, 40, f"Word count {wc} is below 40")

    def test_polished_is_multi_line(self):
        """Polished answer must have >= 2 non-empty lines (D4 structure)."""
        lines = [l for l in self.polished.splitlines() if l.strip()]
        self.assertGreaterEqual(len(lines), 2, "Must have multi-line structure for D4=3")

    def test_polished_references_bounty_domain(self):
        """Polished answer must reference bounty hunting domain from prompt."""
        self.assertIn(
            "bounty",
            self.polished.lower(),
            "Must acknowledge the bounty hunting domain"
        )

    def test_polished_does_not_fabricate_guarantee(self):
        """Polished answer must NOT claim to guarantee anything."""
        norm = _norm(self.polished)
        self.assertNotIn(
            "garantalom",
            norm,
            "Must NOT fabricate a guarantee"
        )
        self.assertNotIn(
            "biztos leszek",
            norm,
            "Must NOT promise certainty"
        )

    def test_polished_does_not_fabricate_exact_revenue_number(self):
        """Polished answer must NOT invent a specific future revenue prediction."""
        # It may mention "10 000 EUR" in context of WHY it can't be guaranteed
        # but must NOT say "you will earn exactly 10 000 EUR"
        norm = _norm(self.polished)
        self.assertNotIn(
            "pontosan 10 000 eur bevételt fogsz",
            norm,
        )
        self.assertNotIn(
            "biztosan hozni fog",
            norm,
        )

    def test_tu_needs_polish_on_raw_answer(self):
        """Raw TU_03 answer must be detected as needing polish."""
        self.assertTrue(
            _tu_needs_polish(self.TU_03_RAW),
            "Raw TU_03 answer should fail quality check"
        )

    def test_full_handler_pipeline_polishes_tu03(self):
        """End-to-end: polish_response on a TU handler result for TU_03."""
        raw_result = {
            "result": self.TU_03_RAW,
            "mission_state": "COMPLETE",
            "route_type": "TRUTHFUL_UNCERTAINTY_RESPONSE",
        }
        polished = polish_response(raw_result, "TRUTHFUL_UNCERTAINTY_RESPONSE", self.TU_03_PROMPT)
        self.assertTrue(polished["response_polished"])
        self.assertEqual(polished["polish_version"], POLISH_VERSION)
        self.assertTrue(_has_strong_marker(polished["result"]))
        self.assertTrue(_has_action_marker(polished["result"]))


# ---------------------------------------------------------------------------
# 2. TU_01 — already-good answer must NOT be modified
# ---------------------------------------------------------------------------

class TestTU01PreservedIfGood(unittest.TestCase):
    """TU_01 answer already scores 14/15 — polish must leave it unchanged."""

    TU_01_PROMPT = (
        "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele "
        "lesz a Project-S-nek."
    )

    # Fully-structured TU answer — passes all 4 quality flags
    TU_01_GOOD = (
        "Nem tudom és nem is garantálhatom, hogy holnap pontosan mennyi "
        "bevétel lesz a Project-S-nek.\n"
        "Ez lehetetlen előrejelzés — a jövő bevétele számos változótól függ, "
        "és nincs rá megbízható módszerrel határozott válasz.\n"
        "A jelenlegi állapot és fejlődési irány pozitív, de a konkrét "
        "bevétel előrejelezése nem valós feladat.\n\n"
        "**Amit helyette tehetsz:**\n"
        "- Kövesd a havi aktivitást és az elfogadási arányt\n"
        "- Tűzz ki tevékenységalapú célt (pl. heti beküldések száma)\n"
        "- Rendszeresen vizsgáld felül a stratégiádat valós adatok alapján"
    )

    def test_good_tu_answer_not_polished(self):
        """A TU answer that already has all quality markers must pass through unchanged."""
        self.assertFalse(
            _tu_needs_polish(self.TU_01_GOOD),
            "TU_01 good answer should NOT need polish"
        )
        result = _polish_truthful_uncertainty(self.TU_01_GOOD, self.TU_01_PROMPT)
        self.assertEqual(result, self.TU_01_GOOD, "Good answer must be returned unchanged")

    def test_polish_response_not_polished_for_good_tu(self):
        """polish_response must set response_polished=False for a good TU answer."""
        raw_result = {
            "result": self.TU_01_GOOD,
            "mission_state": "COMPLETE",
        }
        out = polish_response(raw_result, "TRUTHFUL_UNCERTAINTY_RESPONSE", self.TU_01_PROMPT)
        self.assertFalse(out["response_polished"])
        self.assertEqual(out["result"], self.TU_01_GOOD)


# ---------------------------------------------------------------------------
# 3. Direct Lightweight — exact format preservation
# ---------------------------------------------------------------------------

class TestDirectLightweightFormatPreservation(unittest.TestCase):
    """Exact-format DL prompts must pass through without modification."""

    def test_exact_4_line_prompt_not_modified(self):
        """A 'pontosan 4 soros' response must not have lines added or removed."""
        prompt = (
            "Adj pontosan 4 soros választ. Minden sor elején legyen egy kötőjel. "
            "Téma: mik a Python előnyei más nyelvekkel szemben."
        )
        raw = (
            "- Python szintaxisa olvasható és tanuló-barát\n"
            "- Hatalmas könyvtár-ökoszisztéma (pip, PyPI)\n"
            "- Kiválóan alkalmas gépi tanuláshoz (TensorFlow, PyTorch)\n"
            "- Gyors prototípus-fejlesztés szkript szinten"
        )
        result = _polish_direct_lightweight(raw, prompt)
        # Must not add any extra lines
        result_lines = [l for l in result.splitlines() if l.strip()]
        raw_lines = [l for l in raw.splitlines() if l.strip()]
        self.assertEqual(len(result_lines), len(raw_lines),
                         "Format-preserving polish must not change line count")

    def test_exact_3_sentence_prompt_not_modified(self):
        """A '3 mondatot' response must pass through unchanged."""
        prompt = "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció."
        raw = (
            "A pontos dokumentáció segíti az új fejlesztőket a kód megértésében. "
            "Csökkenti a hibák kockázatát, mert a funkcionalitás leírt formában elérhető. "
            "Hosszú távon időt takarít meg a karbantartás során."
        )
        result = _polish_direct_lightweight(raw, prompt)
        self.assertEqual(result, raw.strip(), "Sentence-count prompt must not be modified")

    def test_no_extra_footer_added(self):
        """DL polish must NOT append any footer, summary, or follow-up section."""
        prompt = "Adj pontosan 4 soros választ. Minden sor elején legyen egy kötőjel."
        raw = "- sor1\n- sor2\n- sor3\n- sor4"
        result = _polish_direct_lightweight(raw, prompt)
        self.assertNotIn("Forrás", result)
        self.assertNotIn("Összefoglalás", result)
        self.assertNotIn("következő lépés", result.lower())

    def test_polish_response_passthrough_for_good_dl(self):
        """polish_response must set response_polished=False for a well-formed DL answer."""
        prompt = "Adj pontosan 4 soros választ. Minden sor elején legyen egy kötőjel."
        raw = "- sor1\n- sor2\n- sor3\n- sor4"
        raw_result = {"result": raw, "mission_state": "COMPLETE"}
        out = polish_response(raw_result, "DIRECT_LIGHTWEIGHT_RESPONSE", prompt)
        # Either unchanged or only whitespace-stripped
        self.assertEqual(out["result"].strip(), raw.strip())
        self.assertEqual(out["polish_version"], POLISH_VERSION)


# ---------------------------------------------------------------------------
# 4. Internal doc — source footer and facts preserved
# ---------------------------------------------------------------------------

class TestInternalDocPreservation(unittest.TestCase):
    """INTERNAL_PROJECT_DOC answers must not lose source footer or doc facts."""

    SAMPLE_ID_ANSWER = (
        "Dokumentumok felhasználva: self_state.json (base: phase, active_focus, gaps_summary, recent_gaps), "
        "self_state.json (current_state block), PROJECT_S_OVERVIEW.md (section 2)\n\n"
        "1. Fázis: **production_stable** (utolsó frissítés: 2026-05-20)\n"
        "2. GAP összesítő: 31 összesen — 30 RESOLVED, 0 ACTIVE, 1 ACCEPTED.\n"
        "3. Aktív fókusz: GAP_031 routing issue RESOLVED.\n"
        "4. Következő lépés: Interactive Layer v1 fully validated.\n"
        "5. Legutóbbi gap: **GAP_031** (RESOLVED)\n\n"
        "[Forrás: self_state.json | Megbízhatóság: HIGH | Szándék: current_state]"
    )

    def test_source_footer_preserved(self):
        """[Forrás:...] footer must survive polish."""
        result = _polish_internal_doc(self.SAMPLE_ID_ANSWER, "bármilyen prompt")
        self.assertIn("[Forrás:", result)
        self.assertIn("HIGH", result)

    def test_docs_used_header_preserved(self):
        """'Dokumentumok felhasználva:' header must survive polish."""
        result = _polish_internal_doc(self.SAMPLE_ID_ANSWER, "bármilyen prompt")
        self.assertIn("Dokumentumok felhasználva:", result)

    def test_doc_derived_numbers_preserved(self):
        """Real doc values (31, 30, production_stable) must survive polish."""
        result = _polish_internal_doc(self.SAMPLE_ID_ANSWER, "bármilyen prompt")
        self.assertIn("31", result)
        self.assertIn("30", result)
        self.assertIn("production_stable", result)

    def test_id_polish_response_metadata(self):
        """polish_response for ID route must set correct metadata."""
        raw_result = {"result": self.SAMPLE_ID_ANSWER, "mission_state": "COMPLETE"}
        out = polish_response(raw_result, "INTERNAL_PROJECT_DOC_REASONING", "Mi a Project-S állapota?")
        self.assertIn("[Forrás:", out["result"])
        self.assertEqual(out["polish_version"], POLISH_VERSION)


# ---------------------------------------------------------------------------
# 5. Error / skip pass-through
# ---------------------------------------------------------------------------

class TestPolishPassThrough(unittest.TestCase):
    """Failed / skipped / empty results must pass through unmodified."""

    def test_error_result_not_polished(self):
        raw_result = {"result": "", "mission_state": "ERROR"}
        out = polish_response(raw_result, "TRUTHFUL_UNCERTAINTY_RESPONSE", "any")
        self.assertFalse(out["response_polished"])
        self.assertEqual(out["result"], "")

    def test_skipped_result_not_polished(self):
        raw_result = {"result": "", "mission_state": "SKIPPED_NO_SERVER"}
        out = polish_response(raw_result, "FULL_AGENTIC_META_CONTROLLER", "any")
        self.assertFalse(out["response_polished"])

    def test_er_route_passes_through(self):
        """ER route: no polish applied in v1 — result unchanged."""
        raw = "1. Lokális LLM előnye: adatvédelem.\n2. Olcsóbb futtatás.\n3. Offline képesség."
        raw_result = {"result": raw, "mission_state": "COMPLETE"}
        out = polish_response(raw_result, "EXTERNAL_RESEARCH_SYNTHESIS", "Lokális LLM?")
        self.assertEqual(out["result"], raw)
        self.assertFalse(out["response_polished"])

    def test_polish_metadata_always_present(self):
        """polish_route and polish_version must always be set."""
        raw_result = {"result": "bármilyen válasz", "mission_state": "COMPLETE"}
        out = polish_response(raw_result, "DIRECT_LIGHTWEIGHT_RESPONSE", "prompt")
        self.assertIn("response_polished", out)
        self.assertIn("polish_route", out)
        self.assertIn("polish_version", out)
        self.assertEqual(out["polish_version"], POLISH_VERSION)


# ---------------------------------------------------------------------------
# 6. Polish quality flags helper tests
# ---------------------------------------------------------------------------

class TestPolishQualityFlags(unittest.TestCase):
    """Unit tests for the internal quality flag checker."""

    def test_weak_answer_flags(self):
        """TU_03 raw answer should have all flags False."""
        raw = (
            "A kérésed tartalmazhatatlan bizonyosságot igénylő elemet. "
            "Nem tudok 100%-os biztossággal előre jelezni jövőbeli eseményeket. "
            "Amiért felelhetek: a Project-S jelenlegi állapota, erősségei "
            "és a legvalószínűbb jövőbeli irányok. Ha ezek érdekelnek, kérem, jelezd."
        )
        flags = _tu_quality_flags(raw)
        self.assertFalse(flags["has_strong_marker"], "Raw TU_03 should not have D3 marker")
        self.assertFalse(flags["is_long_enough"], "Raw TU_03 has < 40 words")
        self.assertFalse(flags["is_structured"], "Raw TU_03 is single-line")

    def test_good_answer_flags(self):
        """TU_01 good answer should have all flags True."""
        raw = (
            "Nem tudom és nem is garantálhatom ezt.\n"
            "Lehetetlen előrejelzés — a jövő bevétele számos változótól függ.\n"
            "Amit helyette tehetsz: kövesd a havi aktivitásod és finomítsd a stratégiát.\n"
            "Rendszeres felülvizsgálattal célzottan javíthatod az eredményeket."
        )
        flags = _tu_quality_flags(raw)
        self.assertTrue(flags["has_strong_marker"])
        self.assertTrue(flags["has_alternatives"])
        self.assertTrue(flags["is_structured"])

    def test_norm_hungarian_chars(self):
        """_norm must strip Hungarian accents."""
        self.assertEqual(_norm("garantálhatom"), "garantalhatom")
        self.assertEqual(_norm("Nem tudom"), "nem tudom")
        self.assertEqual(_norm("lehetetlen"), "lehetetlen")


# ---------------------------------------------------------------------------
# 7. Non-regression: prompt_router tests
# ---------------------------------------------------------------------------

class TestPromptRouterNonRegression(unittest.TestCase):
    """Ensure existing routing tests are unaffected by the polish layer."""

    def test_route_and_execute_function_exists(self):
        """route_and_execute must be importable from prompt_router."""
        from interactive_layer.prompt_router import route_and_execute
        self.assertTrue(callable(route_and_execute))

    def test_get_route_handler_still_works(self):
        """get_route_handler must still return handlers for all 4 direct routes."""
        from interactive_layer.prompt_router import get_route_handler, RouteType
        self.assertIsNotNone(get_route_handler(RouteType.DIRECT_LIGHTWEIGHT_RESPONSE))
        self.assertIsNotNone(get_route_handler(RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE))
        self.assertIsNotNone(get_route_handler(RouteType.INTERNAL_PROJECT_DOC_REASONING))
        self.assertIsNotNone(get_route_handler(RouteType.EXTERNAL_RESEARCH_SYNTHESIS))

    def test_route_and_execute_returns_polish_metadata(self):
        """route_and_execute must return response_polished + polish_version fields."""
        from interactive_layer.prompt_router import route_and_execute
        result = route_and_execute(
            "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
            "test_mission_nr",
        )
        self.assertIn("response_polished", result)
        self.assertIn("polish_version", result)
        self.assertIn("result", result)

    def test_existing_routing_unchanged(self):
        """Router must still classify prompts correctly after polish integration."""
        from interactive_layer.prompt_router import classify_prompt, RouteType
        cases = [
            ("Írj 3 rövid mondatot.", RouteType.DIRECT_LIGHTWEIGHT_RESPONSE),
            ("Garantáld nekem, hogy ez biztosan megtörténik.", RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE),
            ("Mi a Project-S jelenlegi állapota?", RouteType.INTERNAL_PROJECT_DOC_REASONING),
        ]
        for prompt, expected_route in cases:
            with self.subTest(prompt=prompt[:50]):
                d = classify_prompt(prompt)
                self.assertEqual(d.route_type, expected_route)


if __name__ == "__main__":
    unittest.main()
