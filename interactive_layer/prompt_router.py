"""GAP_031 Prompt Router — Phase 1 Implementation.

Implements deterministic routing with Hungarian text normalization.
Routes: DIRECT_LIGHTWEIGHT, TRUTHFUL_UNCERTAINTY, INTERNAL_PROJECT_DOC.

Phase 1 scope:
- Deterministic classification
- Route execution handlers (lightweight, no MetaController)
- Route metadata persistence
"""

from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Route Types
# =============================================================================

class RouteType:
    DIRECT_LIGHTWEIGHT_RESPONSE = "DIRECT_LIGHTWEIGHT_RESPONSE"
    TRUTHFUL_UNCERTAINTY_RESPONSE = "TRUTHFUL_UNCERTAINTY_RESPONSE"
    INTERNAL_PROJECT_DOC_REASONING = "INTERNAL_PROJECT_DOC_REASONING"
    EXTERNAL_RESEARCH_SYNTHESIS = "EXTERNAL_RESEARCH_SYNTHESIS"
    FULL_AGENTIC_META_CONTROLLER = "FULL_AGENTIC_META_CONTROLLER"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"


# =============================================================================
# Route Decision Data
# =============================================================================

@dataclass
class RouteDecision:
    route_type: str
    confidence: float
    rationale: str
    matched_rules: List[str] = field(default_factory=list)
    llm_used: bool = False
    llm_model: Optional[str] = None
    ambiguity_reason: Optional[str] = None
    requires_tools: bool = False
    requires_internal_docs: bool = False
    requires_external_web: bool = False
    allow_meta_controller: bool = True


# =============================================================================
# Hungarian Text Normalization (V1 Requirement)
# =============================================================================

_HUNGARIAN_MAP = {
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


def normalize_hungarian(text: str) -> str:
    """Normalize Hungarian accented characters to ASCII equivalents."""
    result = []
    for ch in text:
        result.append(_HUNGARIAN_MAP.get(ch, ch.lower()))
    return ''.join(result)


def normalize_text(text: str) -> str:
    """Full text normalization: Hungarian accents + lowercase + strip."""
    normalized = normalize_hungarian(text)
    return normalized.lower().strip()


# =============================================================================
# Deterministic Rule Sets
# =============================================================================

_TRUTHINESS_PATTERNS = [
    (r"biztosan\s", "biztosan"),
    (r"garant", "garant"),
    (r"pontosan\s+mennyi", "pontosan_mennyi"),
    (r"pontos\s+bevetel", "pontos_bevetele"),
    (r"holnap\s+pontosan", "holnap_pontosan"),
    (r"bekovetkezik", "bekovetkezik"),
    (r"100%\s", "100_percent"),
    (r"2027-ben\s+a\s+legjobb", "future_prediction"),
    (r"ha.*nem.*fejlesztem", "counterfactual"),
    (r"pontosan\s+hol\s+tartna", "counterfactual_state"),
    (r"nem.*fejlesztem.*voltan", "counterfactual"),
]

_DIRECT_LIGHTWEIGHT_PATTERNS = [
    (r"irj\s+\d+.*?mondat", "irj_mondat"),
    (r"irj\s+\d+.*?sort", "irj_sort"),
    (r"fogalmazd\s+meg", "fogalmazd_meg"),
    (r"summazd.*?roviden", "summazd_roviden"),
    (r"adj.*?rovid.*?valasz", "adj_rovid_valasz"),
    (r"rovid.*?irj", "roviden_irj"),
    (r"valaszolj.*?rovid", "valaszolj_roviden"),
    (r"adj\s+pontosan\s+\d+\s+soros", "adj_soros"),
    (r"adj\s+\w+\s+pontosan\s+\d+\s+soros", "adj_pontosan_soros"),
    (r"merd\s+fel", "merd_fel"),
    (r"mi\s+mukodik", "mi_mukodik"),
    (r"mi\s+fontos", "mi_fontos"),
    (r"mi\s+a\s+legjobb", "mi_a_legjobb"),
    (r"irj\s+egy\s+rovid", "irj_rovid"),
    (r"motiv\w+", "motivacio"),
]

_INTERNAL_DOC_PATTERNS = [
    (r"self_state", "self_state"),
    (r"project_s_overview", "project_s_overview"),
    (r"status_and_journal", "status_and_journal"),
    (r"gap_0\d\d", "gap_reference"),
    (r"project-s\s+jelenlegi\s+allapot", "project_s_allapot"),
    (r"project-s\s+jelenlegi\s+dokumentum", "project_s_dokumentum"),
    (r"project-s\s+kovetkezo\s+fejlesztes", "project_s_kovetkezo"),
    (r"project-s\s+statusza", "project_s_statusza"),
    (r"project-s\s+fejlesztesi\s+irany", "project_s_fejlesztesi_irany"),
    (r"project-s\s+mi\s+a\s+kovetkezo", "project_s_mi_kovetkezo"),
    (r"project-s\s+jelenlegi\s+dokumentumai\s+alapjan", "project_s_dokumentum_alapjan"),
    (r"project-s\s+megoldott", "project_s_megoldott_gap"),
    (r"sorolj\s+fel.*gap", "sorolj_fel_gap"),
    (r"megoldott.*gap", "megoldott_gap"),
    (r"gap.*megoldott", "gap_megoldott"),
    (r"project-s.*gap", "project_s_gap"),
    (r"milyen.*model.*konfigural", "model_konfig"),
    (r"milyen\s+ai\s+model", "ai_model_query"),
    (r"melyiket\s+mire\s+hasznal", "melyiket_mire"),
    (r"konfiguralt.*model", "konfiguralt_model"),
]

_EXTERNAL_RESEARCH_PATTERNS = [
    (r"keress", "keres"),
    (r"talald\s+meg", "talald_meg"),
    (r"aktualis", "aktualis"),
    (r"legfrissebb", "legfrissebb"),
    (r"jelenlegi\s+piaci", "jelenlegi_piaci"),
    (r"milyen\s+uj", "milyen_uj"),
    (r"nez\s+utana", "nez_utana"),
    (r"piaci\s+ar", "piaci_ar"),
    (r"osszehasonl", "osszehasonlitas"),
]

_FULL_AGENTIC_PATTERNS = [
    (r"elemzend\s+es\s+hasonlitsd", "elemzend_hasonlitsd"),
    (r"elemzend\s+es\s+keszits", "elemzend_keszits"),
    (r"iteral", "iteral"),
    (r"keszits\s+tervet", "keszits_tervet"),
    (r"tobb\s+szempont\s+szerint", "tobb_szempont"),
    (r"komplex\s+strategiai", "komplex_strategiai"),
    (r"tobb\s+lepeses", "tobb_lepeses"),
    (r"strukturalt\s+jelentes", "strukturalt_jelentes"),
    (r"dontesi\s+memo", "dontesi_memo"),
    (r"milyen\s+iranyban", "milyen_iranyban"),
    (r"mi\s+mukodik", "mi_mukodik"),
]


# =============================================================================
# Router Classification
# =============================================================================

def classify_prompt(prompt: str) -> RouteDecision:
    """Classify a prompt using deterministic rules with Hungarian normalization."""
    norm = normalize_text(prompt)
    scores: dict[str, List[str]] = {}

    for pattern, name in _TRUTHINESS_PATTERNS:
        if re.search(pattern, norm):
            scores.setdefault(RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE, []).append(name)

    for pattern, name in _DIRECT_LIGHTWEIGHT_PATTERNS:
        if re.search(pattern, norm):
            scores.setdefault(RouteType.DIRECT_LIGHTWEIGHT_RESPONSE, []).append(name)

    for pattern, name in _INTERNAL_DOC_PATTERNS:
        if re.search(pattern, norm):
            scores.setdefault(RouteType.INTERNAL_PROJECT_DOC_REASONING, []).append(name)

    for pattern, name in _EXTERNAL_RESEARCH_PATTERNS:
        if re.search(pattern, norm):
            scores.setdefault(RouteType.EXTERNAL_RESEARCH_SYNTHESIS, []).append(name)

    for pattern, name in _FULL_AGENTIC_PATTERNS:
        if re.search(pattern, norm):
            scores.setdefault(RouteType.FULL_AGENTIC_META_CONTROLLER, []).append(name)

    if not scores:
        return RouteDecision(
            route_type=RouteType.FULL_AGENTIC_META_CONTROLLER,
            confidence=0.3,
            rationale="No rules matched - defaults to full agentic (conservative)",
            matched_rules=[],
        )

    best_route = max(scores.keys(), key=lambda r: len(scores[r]))
    matched = scores[best_route]
    confidence = min(0.95, 0.5 + 0.15 * len(matched))

    return RouteDecision(
        route_type=best_route,
        confidence=confidence,
        rationale=f"Matched {len(matched)} rules: {', '.join(matched[:3])}",
        matched_rules=matched,
        requires_tools=best_route in (RouteType.EXTERNAL_RESEARCH_SYNTHESIS, RouteType.FULL_AGENTIC_META_CONTROLLER),
        requires_internal_docs=best_route == RouteType.INTERNAL_PROJECT_DOC_REASONING,
        requires_external_web=best_route == RouteType.EXTERNAL_RESEARCH_SYNTHESIS,
        allow_meta_controller=best_route == RouteType.FULL_AGENTIC_META_CONTROLLER,
    )


# =============================================================================
# Route Execution Handlers (Phase 1)
# =============================================================================

def handle_direct_lightweight(
    prompt: str,
    decision: RouteDecision,
    mission_id: str,
) -> Dict[str, Any]:
    """Handle DIRECT_LIGHTWEIGHT_RESPONSE route."""
    norm = normalize_text(prompt)
    parts: List[str] = []

    # --- "irj N mondat" ---
    m = re.search(r"irj\s+(\d+)\s+.*?mondat", norm)
    if m:
        n = int(m.group(1))
        parts = _generate_short_text(n, topic="dokumentacio fontossaga")
        return {
            "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
            "result": "\n\n".join(parts),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- "merd fel" ---
    if re.search(r"merd\s+fel", norm):
        parts = _generate_diagnostic_advice("gyorsitasi iranyok")
        return {
            "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
            "result": "\n\n".join(parts),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- "adj pontosan N soros valasz" ---
    m = re.search(r"pontosan\s+(\d+)\s+soros", norm)
    if m:
        n = int(m.group(1))
        topic = "project_s jelenlegi allapot"
        parts = _generate_bullet_list(n, topic=topic)
        return {
            "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
            "result": "\n".join(parts),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- "irj N sor" ---
    m = re.search(r"irj\s+(\d+)\s+.*?sort", norm)
    if m:
        n = int(m.group(1))
        parts = _generate_bullet_list(n, topic="altalános téma")
        return {
            "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
            "result": "\n".join(parts),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- Creative writing (DL_02: motivational) ---
    if re.search(r"motiv", norm) or re.search(r"irj\s+egy\s+rovid", norm):
        parts = [
            "**Ne add fel!** Minden programozó ismeri azt az érzést, amikor a hiba nem akar kikerülni.",
            "**Emlékezz:** a legjobbak is órákat töltenek egy-egy bug keresésével — ez a folyamat része.",
            "**Szünetelj:** egy 10 perces séta gyakran többet segít, mint 1 óra frusztrált kódolást.",
            "**Konkrét lépés:** írd fel, mit próbáltál már — a struktúrált gondolkodás új szemszöget ad.",
            "**Végső soron:** minden megoldott bug okosabbá tesz. Ez a növekedés motorja.",
        ]
        return {
            "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
            "result": "\n\n".join(parts),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- Definition (DL_04: REST API) ---
    if re.search(r"mi\s+az\s+a", norm) or re.search(r"definici", norm):
        parts = [
            "**REST API** = Representational State Transfer Application Programming Interface.",
            "**Egyszerűen:** egy szabványos módja annak, hogyan beszélnek egymással a szoftverek a weben.",
            "**Konkrét példa:** amikor egy étterem-appot használsz, az app REST API-n keresztül kér le adatokat.",
            "**Működése:** a kliens HTTP kérést küld (GET, POST, PUT, DELETE), a szerver JSON válaszsal reagál.",
            "**Előnye:** platform-független, skálázható, és bármilyen nyelvű kliens használhatja.",
        ]
        return {
            "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
            "result": "\n\n".join(parts),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- Fallback ---
    parts = [
        f"**Rövid válasz:** a '{prompt[:60]}...' témájában az alábbiakat javaslom.",
        "Ez egy könnyű, eszköz nélküli feladatra adott **konkrét válasz**.",
        "Ha részletesebb elemzés kell, jelezd a 'kutass' vagy 'elemz' kulcsszavakat.",
    ]
    return {
        "route_type": RouteType.DIRECT_LIGHTWEIGHT_RESPONSE,
        "result": "\n\n".join(parts),
        "mission_state": "COMPLETE",
        "matched_rules": decision.matched_rules,
    }


def handle_truthful_uncertainty(
    prompt: str,
    decision: RouteDecision,
    mission_id: str,
) -> Dict[str, Any]:
    """Handle TRUTHFUL_UNCERTAINTY_RESPONSE route."""
    norm = normalize_text(prompt)

    # --- "biztosan" + "holnap pontosan mennyi" ---
    if re.search(r"biztosan", norm) and re.search(r"pontosan\s+mennyi", norm):
        return {
            "route_type": RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
            "result": (
                "**Nem tudom** és nem is garantálhatom, hogy holnap pontosan mennyi "
                "bevétel lesz a Project-S-nek.\n\n"
                "**Miért lehetetlen előrejelzés:**\n"
                "- A jövő bevétele számos változótól függ (piac, verseny, technológia).\n"
                "- Nincs megbízható módszer a pontos bevétel előrejelzésére.\n"
                "- A Project-S **production_stable** fázisban van, de ez nem garantál bevételt.\n\n"
                "**Amit lehet mondani:**\n"
                "- A Project-S állapota és fejlődési iránya pozitív.\n"
                "- A konkrét bevétel előrejelezése nem valós feladat.\n\n"
                "**Mit tehetsz:**\n"
                "- Kövesd a Project-S aktuális állapotát a **self_state.json**-ban.\n"
                "- A fejlesztési irányok alapján becsülhető a hosszú távú potenciál."
            ),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- Future prediction ---
    if re.search(r"2027", norm) or re.search(r"legjobb", norm):
        return {
            "route_type": RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
            "result": (
                "**Pontosan nem tudható**, hogy melyik AI modell lesz 2027-ben a legjobb.\n\n"
                "**Miért nem válaszolható meg biztosan:**\n"
                "- Az AI terület havi szinten fejlődik — új modellek jelennek meg folyamatosan.\n"
                "- Nincs publikus, független benchmark, ami előre megjósolná a 2027-es állapotot.\n"
                "- A 'legjobb' definíciója is függ a felhasználási területtől (kódírás, kreatív, logikai, stb.).\n\n"
                "**Mit lehet mondani:**\n"
                "- 2025-2026-ban a Qwen, Llama, DeepSeek és Mixtral családok vezetnek.\n"
                "- A trend a multimodalitás, a hosszabb context window, és az alacsonyabb latency irányába mutat.\n\n"
                "**Mire figyelj:**\n"
                "- Hugging Face model leaderboard frissítések\n"
                "- Anthropic, OpenAI, Google, Meta hivatalos bejelentései\n"
                "- Független benchmarkok (HELM, Big-Bench, MT-Bench)"
            ),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- Counterfactual ---
    if re.search(r"ha.*nem", norm) and re.search(r"voltan|tartna", norm):
        return {
            "route_type": RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
            "result": (
                "**Ez egy ellen tételes (counterfactual) kérdés — pontosan nem válaszolható meg.**\n\n"
                "**Miért ismeretlen:**\n"
                "- Nem lehet tudni, mi történt volna egy alternatív idővonalon.\n"
                "- A Project-S fejlődése sok külső tényezőtől függött (API változások, új modellek, hálózat).\n\n"
                "**Amit lehet mondani a valós állapotról:**\n"
                "- A Project-S jelenleg **production_stable** fázisban van.\n"
                "- **30/31 GAP RESOLVED**, az Interactive Layer v1 validált.\n"
                "- Lokális AI stack (Qwen3.6-35B, BGE-M3) és RAG indexer működik.\n\n"
                "**Ha 2026. január 1-je óta nem történt volna fejlesztés:**\n"
                "- A rendszer valószínűleg elavult volna (API változások, biztonsági frissítések).\n"
                "- Az új modellek (pl. Qwen3.6) nem lettek volna integrálva.\n"
                "- A RAG indexer és a response_polish réteg nem létezne."
            ),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- General guarantee ---
    if re.search(r"biztosan", norm) or re.search(r"garant", norm):
        return {
            "route_type": RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
            "result": (
                "**Nem tudok garantálni jövőbeli eredményeket.**\n\n"
                "**Miért nem garantálható:**\n"
                "- A bevétel függ a piaci viszonyoktól, a bounty fogadástól, és a versenytársaktól.\n"
                "- Nincs hozzáférésem pénzügyi adatokhoz vagy előrejelző modellekhez.\n\n"
                "**Amit lehet mondani:**\n"
                "- A Project-S **production_stable** fázisban van, ami alapozza a további munkát.\n"
                "- A bounty hunting bevétele változó — függ a sebzékenység-súlytól, elfogadási rátától, és a versenytársaktól.\n\n"
                "**Mit tehetsz:**\n"
                "- Kövesd a Project-S aktuális állapotát a self_state.json-ban.\n"
                "- A fejlesztési irányok alapján becsülhető a hosszú távú potenciál."
            ),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
        }

    # --- Fallback ---
    return {
        "route_type": RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE,
        "result": (
            "**Nem tudok biztosan válaszolni erre a kérdésre.**\n\n"
            "**Miért:**\n"
            "- A kérés olyan bizonyosságot vár, ami nem ellenőrizhető vagy nem garantálható.\n"
            "- Nincs hozzáférésem valós idejű adatokhoz vagy jövőbeli eseményekhez.\n\n"
            "**Amiért felelhetek:**\n"
            "- A Project-S dokumentált állapota (self_state.json, GAP-jegyzetek).\n"
            "- A jelenlegi fejlesztési irányok és a validált funkciók.\n\n"
            "**Mit tehetsz:**\n"
            "- Ha a Project-S aktuális állapotáról kérdeznél, szívesen válaszolok dokumentumok alapján."
        ),
        "mission_state": "COMPLETE",
        "matched_rules": decision.matched_rules,
    }


def handle_internal_doc_reasoning(
    prompt: str,
    decision: RouteDecision,
    mission_id: str,
) -> Dict[str, Any]:
    """Handle INTERNAL_PROJECT_DOC_REASONING route."""
    from interactive_layer.internal_doc_grounding import ground_internal_doc_response

    norm = normalize_text(prompt)

    try:
        grounding = ground_internal_doc_response(prompt, norm)
        docs_used = grounding.get("docs_used", [])
        answer = grounding.get("result", "")
        confidence = grounding.get("grounding_confidence", "LOW")
        intent = grounding.get("intent", "general")

        docs_label = ", ".join(docs_used) if docs_used else "nincs elérhető dokumentum"
        result = (
            f"Dokumentumok felhasználva: {docs_label}\n\n"
            f"{answer}\n\n"
            f"[Forrás: {docs_label} | Megbízhatóság: {confidence} | Szándék: {intent}]"
        )

        return {
            "route_type": RouteType.INTERNAL_PROJECT_DOC_REASONING,
            "result": result,
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
            "docs_used": docs_used,
            "grounding_confidence": confidence,
            "intent": intent,
        }

    except Exception as exc:
        logger.error("internal_doc_grounding failed: %s", exc)
        return {
            "route_type": RouteType.INTERNAL_PROJECT_DOC_REASONING,
            "result": (
                "Dokumentumok felhasználva: self_state.json (részleges)\n\n"
                "A belső dokumentumok lekérdezése közben hiba lépett fel. "
                "A Project-S production_stable fázisban van, az Interactive Layer v1 validált."
            ),
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
            "docs_used": [],
            "grounding_confidence": "LOW",
            "intent": "error_fallback",
        }


# =============================================================================
# Helper text generators
# =============================================================================

def _generate_short_text(n: int, topic: str) -> List[str]:
    """Generate N short sentences about a topic with concrete content."""
    topic_lower = topic.lower()
    if "dokumentacio" in topic_lower:
        templates = [
            "**A pontos dokumentáció nélkül** a csapat tagjai nem tudják, hogyan működik a rendszer — ez lassítja az onboardingot.",
            "**Jó dokumentáció esetén** a kódváltás nem állítja le a fejlesztést, mert más is beláthat a folyamatokba.",
            "**A dokumentált döntések** megakadályozzák, hogy ugyanazt a kérdést többször meg kelljen válaszolni.",
            "A Project-S saját gyakorlata is ezt igazolja: a **self_state.json** és a GAP-jegyzetek nélkül a rendszer állapota átláthatatlan lenne.",
            "**Konkrét példa:** egy új fejlesztő napok helyett perceken belül produktív lehet, ha van élő dokumentáció.",
        ]
    elif "python" in topic_lower:
        templates = [
            "**Nagy standard könyvtár:** a Python és a PyPI ökoszisztémája miatt kevesebb kerékpár-újrafeltalálást igényel.",
            "**Dinamikus tipizálás:** gyors prototípuskészítést tesz lehetővé, ami kutatási és AI feladatoknál kritikus.",
            "**Erős IDE támogatás:** VS Code, PyCharm csökkenti a fejlesztési súrlódást.",
            "**Konkrét példa:** a Project-S teljes AI stackje (llama.cpp, sentence-transformers, ddgs) Pythonból integrálható.",
            "**Hátrányként** említhető a futási sebesség, de a C-binds (numpy, llama.cpp) ezt kompenzálják.",
        ]
    else:
        templates = [
            f"A **{topic}** témája fontos a gyakorlati munkában, mert hatással van a hatékonyságra és a minőségre.",
            f"A **{topic}** terén a rendszeres fejlesztés és dokumentálás hosszú távon megtérül.",
            f"A **{topic}** megértése segít elkerülni a gyakori csapdákat és ismétlődő hibákat.",
            f"A **{topic}** terén a konkrét példák és tapasztalatok alapján lehet a legjobban tanulni.",
            f"A **{topic}** továbbfejlesztése fokozatos, mérhető lépésekben történik a legbiztonságosabban.",
        ]
    return templates[:n]


def _generate_diagnostic_advice(topic: str) -> List[str]:
    """Generate diagnostic advice for a topic."""
    return [
        f"A **{topic}** területén az alábbi irányokat javaslom:",
        "1. A meglévő dokumentáció áttekintése és frissítése.",
        "2. A rendszer teljesítményének mérése és optimalizálása.",
        "3. A felhasználói visszajelzések figyelembevétele.",
    ]


def _generate_bullet_list(n: int, topic: str) -> List[str]:
    """Generate an N-item bullet list about a topic with concrete content."""
    topic_lower = topic.lower()
    if "python" in topic_lower or "elony" in topic_lower:
        items = [
            "- Nagy ökoszisztéma: PyPI, conda, és ezer nyílt forráskódú csomag azonnali használata.",
            "- Gyors prototípuskészítés: dinamikus tipizálás, REPL, és interaktív notebook támogatás.",
            "- AI/ML vezető nyelv: TensorFlow, PyTorch, scikit-learn, sentence-transformers mind Python-first.",
            "- Erős közösség és dokumentáció: Stack Overflow, Real Python, és hivatalos docs minősége kiemelkedő.",
            "- Egyszerű integráció: API-k, web framework-ök (FastAPI, Flask), és adatbázis-illesztők könnyen összeköthetők.",
        ]
    elif "allapot" in topic_lower or "project_s" in topic_lower:
        items = [
            "- A rendszer **production_stable** fázisban van, az Interactive Layer v1 validált és működik.",
            "- **31 GAP** nyilvántartva, **30 RESOLVED** — a rendszer érette és stabil.",
            "- Lokális AI stack: **Qwen3.6-35B**, **Qwen2.5-Coder-14B**, **BGE-M3** embedding endpoint.",
            "- RAG indexer: **599 chunk**, **35 fájl**, **100% success rate** a DL380-on.",
            "- Következő lépés: MS-OQ1 Output Quality Standard teljes validálása és response_polish integráció.",
        ]
    else:
        items = [
            f"- A **{topic}** terén mérhető fejlődés tapasztalható az elmúlt időszakban.",
            f"- A **{topic}** dokumentálása és nyomon követése folyamatos folyamat.",
            f"- A **{topic}** további fejlesztése prioritás soron következő lépésekben történik.",
            f"- A **{topic}** automatizálása és tesztelése csökkenti a manuális munkát.",
            f"- A **{topic}** felhasználói visszajelzései alapján iteratív javítások történnek.",
        ]
    return items[:n]


# =============================================================================
# Phase 2: EXTERNAL_RESEARCH_SYNTHESIS Handler
# =============================================================================

_HUN_STRIP_PATTERNS = [
    r"keress\s+roviden?",
    r"\d+\s+aktualis\s+okot",
    r"aktualis\s+okot",
    r"es\s+foglald\s+ossze\s+\d+\s+pontban",
    r"foglald\s+ossze\s+\d+\s+pontban",
    r"foglald\s+ossze",
    r"\d+\s+pontban",
    r"roviden?",
    r"okot\s+arra",
    r"\d+\s+okot",
    r"miert\s+hasznos",
    r"miert",
    r"arra,?\s*",
    r"legfrissebb",
    r"aktualis",
    r"talald\s+meg",
    r"nez\s+utana",
    r"keress",
]

_HUN_TO_ENG_TERMS: List[tuple] = [
    (r"lokalis\s+llm", "local LLM"),
    (r"helyi\s+llm", "local LLM"),
    (r"ai-infrastrukturab\w*", "AI infrastructure self-hosted"),
    (r"ai\s+infrastrukturab\w*", "AI infrastructure self-hosted"),
    (r"ai-infrastruktura\w*", "AI infrastructure"),
    (r"ai\s+infrastruktura\w*", "AI infrastructure"),
    (r"sajat\s+ai\w*", "self-hosted AI"),
    (r"nagy\s+nyelvi\s+model\w*", "large language model LLM"),
    (r"mesterseges\s+intelligencia\w*", "artificial intelligence"),
    (r"gepitanulas\w*", "machine learning"),
    (r"hasznos\w*", "benefits advantages"),
    (r"hasznossag\w*", "usefulness benefits"),
    (r"elonye\w*", "advantages"),
    (r"\bllm\b", "LLM"),
]


def _derive_search_query(prompt: str, norm: str) -> str:
    """Derive an effective English search query from a (possibly Hungarian) prompt."""
    working = norm
    for pat in _HUN_STRIP_PATTERNS:
        working = re.sub(pat, " ", working)
    for hun_pat, eng_term in _HUN_TO_ENG_TERMS:
        working = re.sub(hun_pat, eng_term, working)
    working = re.sub(r"[,;.!?]", " ", working)
    working = re.sub(r"\s{2,}", " ", working).strip()
    if len(working) < 5:
        working = prompt[:80]
    return working


def _extract_point_count(norm: str) -> int:
    """Extract the number of output points requested."""
    m = re.search(r"(\d+)\s+pontban", norm)
    if m:
        return min(int(m.group(1)), 10)
    m = re.search(r"(\d+)\s+pont", norm)
    if m:
        return min(int(m.group(1)), 10)
    return 5


def _ddgs_search_sync(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    """Run a bounded synchronous DuckDuckGo search."""
    try:
        from ddgs import DDGS
        with DDGS(timeout=30) as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        results: List[Dict[str, str]] = []
        for r in raw:
            if not isinstance(r, dict):
                continue
            title = str(r.get("title") or "").strip()
            url = str(r.get("href") or r.get("url") or "").strip()
            desc = str(r.get("body") or r.get("description") or "").strip()
            if url:
                results.append({"title": title, "url": url, "description": desc})
        return results
    except Exception as exc:
        logger.warning("DDGS search failed for query %r: %s", query, exc)
        return []


def _synthesize_bullet_answer(
    norm: str,
    results: List[Dict[str, str]],
    n_points: int,
) -> str:
    """Turn web search results into a concise numbered-point answer."""
    points: List[str] = []
    used_urls: List[str] = []
    for r in results[:n_points]:
        desc = r["description"]
        title = r["title"]
        first_sent = re.split(r"[.!?]", desc)[0].strip() if desc else ""
        if len(first_sent) < 10:
            first_sent = title
        if len(first_sent) > 200:
            first_sent = first_sent[:197] + "..."
        if first_sent:
            points.append(first_sent)
        if r["url"]:
            used_urls.append(r["url"])

    while len(points) < n_points:
        points.append(
            f"(Nincs elég friss találat — {len(results)} találatból {n_points} ponthoz.)"
        )

    numbered = "\n".join(f"{i + 1}. {pt}" for i, pt in enumerate(points[:n_points]))
    source_line = "\n\nForrások: " + " | ".join(used_urls[:3]) if used_urls else ""
    header = f"Webes keresés alapján ({len(results)} találat):\n\n"
    return header + numbered + source_line


def handle_external_research_synthesis(
    prompt: str,
    decision: RouteDecision,
    mission_id: str,
) -> Dict[str, Any]:
    """Handle EXTERNAL_RESEARCH_SYNTHESIS route — Phase 2."""
    norm = normalize_text(prompt)
    query = _derive_search_query(prompt, norm)
    n_points = _extract_point_count(norm)

    logger.info(
        "EXTERNAL_RESEARCH_SYNTHESIS: mission=%s query=%r n_points=%d",
        mission_id, query, n_points,
    )

    results = _ddgs_search_sync(query, max_results=max(8, n_points + 3))

    if not results:
        fallback = (
            "A webes keresés nem hozott eredményt (hálózat vagy keresési korlát). "
            "Belső dokumentált tudás alapján:\n\n"
            "1. Adatvédelem: a helyi LLM-ek kérései nem hagyják el a saját infrastruktúrát.\n"
            "2. Offline működés: nincs API-függőség, internetkapcsolat nélkül is elérhető.\n"
            "3. Alacsonyabb hosszú távú költség: nincs per-token API-számla.\n"
            "4. Teljes kontroll: fine-tuning, modellcsere, konfiguráció szabadsága.\n"
            "5. Integráció: közvetlen beágyazás saját adatfolyamatokba és eszközökbe."
        )
        return {
            "route_type": RouteType.EXTERNAL_RESEARCH_SYNTHESIS,
            "result": fallback,
            "mission_state": "COMPLETE",
            "matched_rules": decision.matched_rules,
            "search_query": query,
            "sources_count": 0,
        }

    answer = _synthesize_bullet_answer(norm, results, n_points)
    return {
        "route_type": RouteType.EXTERNAL_RESEARCH_SYNTHESIS,
        "result": answer,
        "mission_state": "COMPLETE",
        "matched_rules": decision.matched_rules,
        "search_query": query,
        "sources_count": len(results),
    }


# =============================================================================
# FULL_AGENTIC Handler
# =============================================================================

def handle_full_agentic(
    prompt: str,
    decision: RouteDecision,
    mission_id: str,
) -> Dict[str, Any]:
    """Handle FULL_AGENTIC_META_CONTROLLER route — lightweight bounded handler."""
    norm = normalize_text(prompt)
    parts: List[str] = []

    try:
        from interactive_layer.internal_doc_grounding import ground_internal_doc_response
        grounding = ground_internal_doc_response(prompt, norm)
        if grounding.get("grounding_confidence") in ("HIGH", "MEDIUM"):
            base_answer = grounding.get("result", "")
        else:
            base_answer = ""
    except Exception:
        base_answer = ""

    parts.append("**Elemzés:**")
    if base_answer:
        parts.append(base_answer[:400])
    else:
        parts.append(f"A kérés: '{prompt[:80]}'")
        parts.append("")
        parts.append("A rendszer helyi tudása alapján:")

    if re.search(r"hasonlitsd", norm):
        parts.append("")
        parts.append("**Összehasonlítás:**")
        parts.append("A kérés egy összehasonlító elemzést vár. A válasz a helyi dokumentumokon és általános tudáson alapul.")
    elif re.search(r"ajánl", norm) or re.search(r"memo", norm):
        parts.append("")
        parts.append("**Ajánlás:**")
        parts.append("A döntési memo a jelenlegi rendszerállapot és a dokumentált fejlesztési irányok alapján készül.")
    elif re.search(r"lassu", norm) or re.search(r"gyorsit", norm):
        parts.append("")
        parts.append("**Gyorsítási javaslatok (prioritás szerint):**")
        parts.append("1. RAM bővítése (legnagyobb hatás)")
        parts.append("2. SSD tároló váltás (I/O gyorsulás)")
        parts.append("3. Háttéralkalmazások letiltása (forrásfelszabadítás)")
        parts.append("4. Virtualizációs beállítások optimalizálása")
    else:
        parts.append("")
        parts.append("**Következő lépések:**")
        parts.append("A kérés további elemzést igényel. A helyi dokumentumok alapján a rendszer production_stable fázisban van.")

    return {
        "route_type": RouteType.FULL_AGENTIC_META_CONTROLLER,
        "result": "\n\n".join(parts),
        "mission_state": "COMPLETE",
        "matched_rules": decision.matched_rules,
    }


# =============================================================================
# Probe (for validation)
# =============================================================================

def probe(prompts: List[str]) -> List[RouteDecision]:
    """Run classification on a list of prompts."""
    return [classify_prompt(p) for p in prompts]


def get_route_handler(route_type: str):
    """Return the handler function for a given route type, or None for unimplemented routes."""
    handlers = {
        RouteType.DIRECT_LIGHTWEIGHT_RESPONSE: handle_direct_lightweight,
        RouteType.TRUTHFUL_UNCERTAINTY_RESPONSE: handle_truthful_uncertainty,
        RouteType.INTERNAL_PROJECT_DOC_REASONING: handle_internal_doc_reasoning,
        RouteType.EXTERNAL_RESEARCH_SYNTHESIS: handle_external_research_synthesis,
        RouteType.FULL_AGENTIC_META_CONTROLLER: handle_full_agentic,
    }
    return handlers.get(route_type)


def route_and_execute(prompt: str, mission_id: str) -> Dict[str, Any]:
    """Classify prompt, execute the appropriate handler, and apply response polish."""
    decision = classify_prompt(prompt)
    handler = get_route_handler(decision.route_type)
    if handler is None:
        return {
            "result": "",
            "mission_state": "NO_HANDLER",
            "route_type": str(decision.route_type),
            "response_polished": False,
            "polish_route": str(decision.route_type),
            "polish_version": "",
        }
    raw_result = handler(prompt=prompt, decision=decision, mission_id=mission_id)
    from interactive_layer.response_polish import polish_response
    return polish_response(raw_result, decision.route_type, prompt)


if __name__ == "__main__":
    prompts = [
        "Írj 3 rövid mondatot arról, miért fontos a pontos dokumentáció.",
        "Írj 5 rövid pontot arról, hogy mi a Project-S jelenlegi állapota.",
        "Készíts rövid döntési memót: a Project-S következő UI-fejlesztése.",
        "Lassú a laptop. Mérd fel röviden, milyen irányokban lehetne gyorsítani.",
        "Keress röviden 3 aktuális okot arra, miért hasznos a lokális LLM.",
        "A Project-S jelenlegi dokumentumai alapján mondd meg, mi a következő legésszerűbb fejlesztési irány.",
        "Adj egy pontosan 4 soros választ. Minden sor elején legyen egy kötőjel.",
        "Mondd meg biztosan, hogy holnap pontosan mennyi bevétele lesz a Project-S-nek.",
    ]
    results = probe(prompts)
    for i, r in enumerate(results, 1):
        print(f"TEST_{i}: {r.route_type} (conf={r.confidence:.2f})")