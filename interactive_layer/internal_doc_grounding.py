"""MS-OQ1-A — Internal Document Grounding module.

Provides deterministic file-grounded reasoning for the
INTERNAL_PROJECT_DOC_REASONING route.

Core documents:
  - self_state.json          (canonical live system state)
  - PROJECT_S_OVERVIEW.md    (architecture + current status summary)
  - PROJECT_S_STATUS_AND_JOURNAL.md  (historical journal)

RAG Index (V1.2):
  - sentence-transformers + multilingual-e5-small
  - 384-dim embeddings, 599 chunks, 35 files
  - Local index at: interactive_layer/rag_index/

No LLM calls are made here. Answers are synthesized deterministically
from extracted document content, supplemented by RAG retrieval.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RAG Index Support
# ---------------------------------------------------------------------------

_RAG_INDEX_DIR = Path(__file__).parent / "rag_index"
_RAG_AVAILABLE = (
    _RAG_INDEX_DIR.exists()
    and (_RAG_INDEX_DIR / "vectors.npy").exists()
    and (_RAG_INDEX_DIR / "metadata.jsonl").exists()
)


def _load_rag_index():
    """Load RAG vectors and metadata. Returns (vectors, metadata) or (None, None)."""
    if not _RAG_AVAILABLE:
        return None, None
    try:
        import numpy as np
        vectors = np.load(str(_RAG_INDEX_DIR / "vectors.npy"))
        metadata = []
        with open(_RAG_INDEX_DIR / "metadata.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                metadata.append(json.loads(line))
        return vectors, metadata
    except Exception as e:
        logger.warning("Failed to load RAG index: %s", e)
        return None, None


def _get_query_embedding(query: str) -> Optional[List[float]]:
    """Get embedding for a query using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
        # Cache model in module-level variable
        if not hasattr(_get_query_embedding, "model"):
            _get_query_embedding.model = SentenceTransformer(
                "intfloat/multilingual-e5-small", device="cpu"
            )
        emb = _get_query_embedding.model.encode(
            query, normalize_embeddings=True, show_progress_bar=False
        )
        return emb.tolist()
    except Exception as e:
        logger.warning("Failed to get query embedding: %s", e)
        return None


def query_rag_index(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Query the local RAG index for relevant chunks.

    Returns list of dicts with: file_path, chunk_type, text, score, start_line, end_line
    """
    vectors, metadata = _load_rag_index()
    if vectors is None:
        return []

    q_emb = _get_query_embedding(query)
    if q_emb is None:
        return []

    import numpy as np
    q_vec = np.array(q_emb)
    scores = vectors @ q_vec
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        meta = metadata[idx]
        results.append({
            "file_path": meta.get("file_path", ""),
            "chunk_type": meta.get("chunk_type", ""),
            "text": meta.get("text", ""),
            "score": float(scores[idx]),
            "start_line": meta.get("start_line", 0),
            "end_line": meta.get("end_line", 0),
            "header": meta.get("header", meta.get("name", meta.get("label", ""))),
        })
    return results

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent

CORE_DOCS = {
    "self_state": _ROOT / "self_state.json",
    "overview": _ROOT / "PROJECT_S_OVERVIEW.md",
    "journal": _ROOT / "PROJECT_S_STATUS_AND_JOURNAL.md",
    "foundation": _ROOT / "PROJECT_S_FOUNDATION.md",
}

# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

# Intent labels in priority order
_INTENTS = [
    "gap_query",
    "architecture",
    "next_step",
    "current_state",
    "milestone",
    "general",
]

_INTENT_PATTERNS: Dict[str, List[str]] = {
    "gap_query": [
        r"gap_0\d\d",
        r"megoldott\s+gap",
        r"gap.*tortenet",
        r"gap.*statusz",
        r"resolved\s+gap",
        r"sorolj\s+fel.*gap",
    ],
    "architecture": [
        r"milyen.*model",
        r"milyen\s+ai\s+model",
        r"konfiguralt.*model",
        r"model_policy",
        r"model\s+nev",
        r"architektura",
        r"osszetevo",
        r"komponens",
        r"melyiket\s+mire",
        r"synthesis.*model",
    ],
    "next_step": [
        r"kovetkezo\s+legesszerubb",
        r"kovetkezo.*fejlesztesi\s+irany",
        r"dokumentumai\s+alapjan",
        r"next_concrete_step",
        r"mi\s+a\s+kovetkezo",
        r"mire\s+kell\s+fokuszal",
        r"legkozelebb",
        r"ajanlott\s+irany",
    ],
    "current_state": [
        r"jelenlegi\s+allapot",
        r"allapota\b",
        r"statusza\b",
        r"statusz\b",
        r"fejlodesi\s+allapot",
        r"hol\s+tart",
        r"mi\s+tortent",
        r"fazis\b",
        r"phase\b",
    ],
    "milestone": [
        r"milestone",
        r"merfoldko",
        r"mikor\s+tortent",
        r"tortenet",
        r"elert.*eredmeny",
        r"gap.*lista",
        r"elmuld.*fejlesztes",
    ],
}


def detect_intent(prompt_norm: str) -> str:
    """Detect the semantic intent of a normalized internal-doc prompt.

    Returns one of: gap_query, architecture, next_step, current_state,
    milestone, general.
    """
    for intent in _INTENTS[:-1]:  # skip "general" — that's the fallback
        for pattern in _INTENT_PATTERNS.get(intent, []):
            if re.search(pattern, prompt_norm):
                return intent
    return "general"


# ---------------------------------------------------------------------------
# Document loaders
# ---------------------------------------------------------------------------

def load_self_state() -> Dict[str, Any]:
    """Load and return self_state.json as a dict. Returns {} on failure."""
    path = CORE_DOCS["self_state"]
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Could not load self_state.json: %s", exc)
        return {}


def load_markdown_doc(key: str) -> str:
    """Load a markdown doc by key. Returns '' on failure."""
    path = CORE_DOCS.get(key)
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not load %s: %s", key, exc)
        return ""


def load_core_docs() -> Dict[str, Any]:
    """Load all available core documents. Returns dict of loaded content."""
    return {
        "self_state": load_self_state(),
        "overview": load_markdown_doc("overview"),
        "journal": load_markdown_doc("journal"),
    }


# ---------------------------------------------------------------------------
# Context extraction helpers
# ---------------------------------------------------------------------------

def _extract_base_context(ss: Dict[str, Any]) -> Dict[str, Any]:
    """Mandatory compact base context always included regardless of intent.

    Contains the minimum set of fields needed for any grounded answer:
    - what_i_am, phase, active_focus, next_concrete_step
    - gaps_summary (total, resolved, active, accepted)
    - last 3 known_gaps (most recent entries)
    - last 3 milestone descriptions
    - server/active_loop state summary

    This ensures that even if intent detection picks a narrow category,
    the answer is always grounded on the most current system state.
    """
    cs = ss.get("current_state", {})
    identity = ss.get("identity", {})
    gaps = cs.get("gaps_summary", {})

    # Last 3 known_gaps (most recent — keep full entry for sentinel testing)
    known_gaps = identity.get("known_gaps", [])
    recent_gaps = known_gaps[-3:] if known_gaps else []

    # Last 3 milestones as strings
    milestones_raw = ss.get("milestones", [])
    recent_milestones: List[str] = []
    if isinstance(milestones_raw, list):
        for m in milestones_raw[-3:]:
            if isinstance(m, str):
                recent_milestones.append(m)
            elif isinstance(m, dict):
                recent_milestones.append(m.get("description") or m.get("title") or "")

    return {
        "what_i_am": identity.get("what_i_am", ""),
        "phase": cs.get("phase", ""),
        "active_focus": cs.get("active_focus", ""),
        "next_concrete_step": cs.get("next_concrete_step", ""),
        "gaps_total": gaps.get("total", "?"),
        "gaps_resolved": gaps.get("resolved", "?"),
        "gaps_active": gaps.get("active", "?"),
        "gaps_accepted": gaps.get("accepted", "?"),
        "recent_gaps": recent_gaps,
        "recent_milestones": recent_milestones,
        "active_loop": cs.get("active_loop", ""),
        "last_updated": ss.get("last_updated", ""),
    }


def _extract_current_state_context(ss: Dict[str, Any]) -> Dict[str, Any]:
    """Extract current state fields from self_state.json."""
    cs = ss.get("current_state", {})
    gaps = cs.get("gaps_summary", {})
    return {
        "phase": cs.get("phase", "unknown"),
        "active_focus": cs.get("active_focus", ""),
        "gaps_total": gaps.get("total", "?"),
        "gaps_resolved": gaps.get("resolved", "?"),
        "gaps_active": gaps.get("active", "?"),
        "gaps_accepted": gaps.get("accepted", "?"),
        "next_concrete_step": cs.get("next_concrete_step", ""),
        "last_updated": ss.get("last_updated", ""),
    }


def _extract_gap_context(ss: Dict[str, Any], prompt_norm: str) -> List[Dict[str, Any]]:
    """Extract specific or recent GAP entries from self_state.json.

    If a specific GAP_NNN is referenced, return only that gap.
    Otherwise return the last 3 gaps from known_gaps.
    """
    known_gaps: List[Dict[str, Any]] = ss.get("identity", {}).get("known_gaps", [])

    # Check for specific GAP reference (e.g. gap_031)
    m = re.search(r"gap_0(\d+)", prompt_norm)
    if m:
        target_id = f"GAP_{int(m.group(1)):03d}"
        for gap in known_gaps:
            if gap.get("gap_id", "").upper() == target_id:
                return [gap]
        # Not found — return last 3 as fallback
        logger.info("GAP %s not found in known_gaps, returning recent gaps", target_id)

    # Return last 3 resolved gaps
    resolved = [g for g in known_gaps if g.get("status") == "RESOLVED"]
    return resolved[-3:] if resolved else known_gaps[-3:]


def _extract_architecture_context(ss: Dict[str, Any], overview_md: str) -> Dict[str, Any]:
    """Extract model/architecture info from self_state + overview."""
    cs = ss.get("current_state", {})
    model_policy = cs.get("model_policy", {})
    components_active = ss.get("identity", {}).get("components_active", [])
    components_sleeping = ss.get("identity", {}).get("components_ready_but_sleeping", [])

    # Extract model_policy section from overview if available
    overview_model_section = ""
    if overview_md:
        m = re.search(
            r"\*\*Model policy[^*]*\*\*.*?(?=\n\n\*\*|\n## )",
            overview_md, re.DOTALL
        )
        if m:
            overview_model_section = m.group(0)[:600]

    return {
        "model_policy": model_policy,
        "components_active": components_active,
        "components_sleeping": components_sleeping,
        "overview_model_excerpt": overview_model_section,
    }


def _extract_next_step_context(ss: Dict[str, Any]) -> Dict[str, Any]:
    """Extract next step and focus context from self_state.json."""
    cs = ss.get("current_state", {})
    return {
        "next_concrete_step": cs.get("next_concrete_step", ""),
        "active_focus": cs.get("active_focus", ""),
        "phase": cs.get("phase", ""),
        "gaps_summary": cs.get("gaps_summary", {}),
    }


def _extract_milestone_context(ss: Dict[str, Any]) -> List[str]:
    """Extract last 5 milestones from self_state.json."""
    milestones = ss.get("milestones", [])
    if isinstance(milestones, list):
        # Take last 5
        recent = milestones[-5:] if len(milestones) > 5 else milestones
        # Each may be a string or dict
        results = []
        for m in recent:
            if isinstance(m, str):
                results.append(m)
            elif isinstance(m, dict):
                results.append(m.get("description") or m.get("title") or str(m))
        return results
    return []


def _extract_overview_section(overview_md: str, heading: str) -> str:
    """Extract a section from overview markdown by heading prefix."""
    if not overview_md:
        return ""
    pattern = re.compile(
        rf"^(##?\s*{re.escape(heading)}[^\n]*\n)(.*?)(?=^##?\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(overview_md)
    if m:
        return (m.group(1) + m.group(2))[:1500]
    return ""


# ---------------------------------------------------------------------------
# Context selection
# ---------------------------------------------------------------------------

def select_relevant_context(
    intent: str,
    prompt_norm: str,
    docs: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    """Select relevant context sections based on detected intent.

    Always includes a compact mandatory base context (phase, active_focus,
    next_concrete_step, gaps_summary, recent_gaps, recent_milestones) so
    every answer is grounded regardless of intent classification accuracy.

    Then adds dynamic context specific to the detected intent.

    Returns (context_dict, docs_used_list).
    """
    ss = docs.get("self_state", {})
    overview_md = docs.get("overview", "")
    journal_md = docs.get("journal", "")

    docs_used: List[str] = []
    context: Dict[str, Any] = {"intent": intent}

    # ------------------------------------------------------------------
    # MANDATORY BASE CONTEXT — always included from self_state.json
    # This is the grounding guarantee: even if intent detection is wrong,
    # the answer always reflects real current document state.
    # ------------------------------------------------------------------
    base = _extract_base_context(ss)
    context["base"] = base
    docs_used.append("self_state.json (base: phase, active_focus, gaps_summary, recent_gaps)")

    # ------------------------------------------------------------------
    # DYNAMIC CONTEXT — intent-specific additions
    # ------------------------------------------------------------------
    if intent == "gap_query":
        gaps = _extract_gap_context(ss, prompt_norm)
        context["gaps"] = gaps
        context["gaps_summary"] = ss.get("current_state", {}).get("gaps_summary", {})
        docs_used.append("self_state.json (known_gaps full match)")

    elif intent == "architecture":
        arch = _extract_architecture_context(ss, overview_md)
        context["architecture"] = arch
        docs_used.append("self_state.json (model_policy, components)")
        if overview_md:
            docs_used.append("PROJECT_S_OVERVIEW.md (model policy section)")

    elif intent == "next_step":
        ns = _extract_next_step_context(ss)
        context["next_step"] = ns
        docs_used.append("self_state.json (next_concrete_step, active_focus)")
        if overview_md:
            sec = _extract_overview_section(overview_md, "2. Current system state")
            if sec:
                context["overview_current_state"] = sec[:800]
                docs_used.append("PROJECT_S_OVERVIEW.md (section 2)")

    elif intent == "current_state":
        cs_ctx = _extract_current_state_context(ss)
        context["current_state"] = cs_ctx
        docs_used.append("self_state.json (current_state block)")
        if overview_md:
            sec = _extract_overview_section(overview_md, "2. Current system state")
            if sec:
                context["overview_section_2"] = sec[:600]
                docs_used.append("PROJECT_S_OVERVIEW.md (section 2)")

    elif intent == "milestone":
        milestones = _extract_milestone_context(ss)
        context["milestones"] = milestones
        gaps = _extract_gap_context(ss, prompt_norm)
        context["recent_gaps"] = gaps
        docs_used.append("self_state.json (milestones, known_gaps)")
        if journal_md:
            context["journal_tail"] = journal_md[-600:]
            docs_used.append("PROJECT_S_STATUS_AND_JOURNAL.md (recent entries)")

    else:  # general — base context is sufficient
        cs_ctx = _extract_current_state_context(ss)
        context["current_state"] = cs_ctx
        docs_used.append("self_state.json (current_state)")

    return context, docs_used


# ---------------------------------------------------------------------------
# Answer synthesis (deterministic, no LLM)
# ---------------------------------------------------------------------------

def synthesize_answer(
    prompt: str,
    intent: str,
    context: Dict[str, Any],
) -> str:
    """Build a grounded answer from the extracted context.

    Returns a concise user-facing answer in Hungarian.
    The answer is deterministically formatted from document content.
    """
    if intent == "gap_query":
        return _synthesize_gap_answer(context)
    elif intent == "architecture":
        return _synthesize_architecture_answer(context)
    elif intent == "next_step":
        return _synthesize_next_step_answer(context)
    elif intent == "current_state":
        return _synthesize_current_state_answer(context)
    elif intent == "milestone":
        return _synthesize_milestone_answer(context)
    else:
        return _synthesize_general_answer(context)


def _synthesize_current_state_answer(context: Dict[str, Any]) -> str:
    # Prefer dedicated current_state extraction if present; fall back to base
    cs = context.get("current_state") or context.get("base", {})
    base = context.get("base", {})
    lines: List[str] = []

    phase = cs.get("phase") or base.get("phase", "ismeretlen")
    total = cs.get("gaps_total") or base.get("gaps_total", "?")
    resolved = cs.get("gaps_resolved") or base.get("gaps_resolved", "?")
    active = cs.get("gaps_active") or base.get("gaps_active", "?")
    accepted = cs.get("gaps_accepted") or base.get("gaps_accepted", "?")
    focus = cs.get("active_focus") or base.get("active_focus", "")
    updated = cs.get("last_updated") or base.get("last_updated", "")

    lines.append(f"1. Fázis: **{phase}** (utolsó frissítés: {updated[:10] if updated else 'ismeretlen'})")
    lines.append(
        f"2. GAP összesítő: {total} összesen — {resolved} RESOLVED, "
        f"{active} ACTIVE, {accepted} ACCEPTED."
    )
    if focus:
        focus_short = focus[:200].rstrip(",.")
        lines.append(f"3. Aktív fókusz: {focus_short}.")
    else:
        lines.append("3. Aktív fókusz: nincs külön feljegyezve.")

    next_step = cs.get("next_concrete_step") or base.get("next_concrete_step", "")
    if next_step:
        next_short = next_step[:200].rstrip(",.")
        lines.append(f"4. Következő lépés: {next_short}.")
    else:
        lines.append(f"4. Következő lépés: nincs nyitott GAP, a rendszer {phase} fázisban.")

    # Line 5: derive from recent gaps in base context (no hardcoded Project-S facts)
    recent_gaps = base.get("recent_gaps", [])
    if recent_gaps:
        last_gap = recent_gaps[-1]
        gid = last_gap.get("gap_id", "?")
        gstatus = last_gap.get("status", "?")
        gtitle = last_gap.get("title", "")[:80]
        lines.append(f"5. Legutóbbi gap: **{gid}** ({gstatus}) — {gtitle}")
    else:
        lines.append(f"5. Rendszer állapot: {phase}, {total} gap, {resolved} megoldva.")
    return "\n".join(lines)


def _synthesize_gap_answer(context: Dict[str, Any]) -> str:
    gaps: List[Dict[str, Any]] = context.get("gaps", [])
    # Prefer dedicated gaps_summary; fall back to base context
    base = context.get("base", {})
    summary = context.get("gaps_summary", {})
    if not summary:
        summary = {
            "total": base.get("gaps_total", "?"),
            "resolved": base.get("gaps_resolved", "?"),
        }
    # If no direct gaps matched, use recent_gaps from base
    if not gaps:
        gaps = base.get("recent_gaps", [])
    lines: List[str] = []

    total = summary.get("total", "?")
    resolved = summary.get("resolved", "?")

    if not gaps:
        return (
            f"A self_state.json szerint összesen {total} GAP van nyilvántartva, "
            f"amelyből {resolved} RESOLVED. Konkrét GAP nem található a lekérdezéshez."
        )

    lines.append(f"GAP összesítő: {total} összesen, {resolved} RESOLVED.")
    lines.append("")
    for i, gap in enumerate(gaps, 1):
        gid = gap.get("gap_id", "?")
        title = gap.get("title", "")
        status = gap.get("status", "?")
        resolved_at = gap.get("resolved_at", "")
        resolution = gap.get("resolution", "")[:200] if gap.get("resolution") else ""
        date_str = f", megoldva: {resolved_at[:10]}" if resolved_at else ""
        lines.append(f"{i}. **{gid}** — {status}{date_str}")
        if title:
            lines.append(f"   Cím: {title}")
        if resolution:
            lines.append(f"   Megoldás: {resolution.rstrip(',.')}.")
        lines.append("")
    return "\n".join(lines).strip()


def _synthesize_architecture_answer(context: Dict[str, Any]) -> str:
    arch = context.get("architecture", {})
    model_policy = arch.get("model_policy", {})
    active = arch.get("components_active", [])
    sleeping = arch.get("components_sleeping", [])
    lines: List[str] = []

    lines.append("**AI modell konfiguráció (self_state.json → model_policy):**")
    lines.append("")
    if model_policy:
        for role, model in model_policy.items():
            lines.append(f"- {role}: `{model}`")
    else:
        # Hardcoded fallback from overview doc
        lines.append("- synthesis_default: `qwen/qwen3.6-35b-a3b`")
        lines.append("- Cognitive Phase 1: `qwen/qwen3-235b-a22b`")
        lines.append("- Evaluator: `deepseek/deepseek-chat`")

    lines.append("")
    lines.append("**Aktív komponensek:**")
    for c in active:
        lines.append(f"- {c}")

    if sleeping:
        lines.append("")
        lines.append("**Alvó (de kész) komponensek:**")
        for c in sleeping[:3]:
            lines.append(f"- {c}")

    # Include overview excerpt if available
    excerpt = arch.get("overview_model_excerpt", "")
    if excerpt:
        lines.append("")
        lines.append("**Overview doc részlet:**")
        lines.append(excerpt[:400])

    return "\n".join(lines)


def _synthesize_next_step_answer(context: Dict[str, Any]) -> str:
    ns = context.get("next_step", {})
    base = context.get("base", {})
    # Prefer dedicated extraction; fall back to base
    next_step = ns.get("next_concrete_step") or base.get("next_concrete_step", "")
    focus = ns.get("active_focus") or base.get("active_focus", "")
    phase = ns.get("phase") or base.get("phase", "")
    gaps = ns.get("gaps_summary") or {
        "active": base.get("gaps_active", 0),
        "resolved": base.get("gaps_resolved", "?"),
    }
    lines: List[str] = []

    lines.append(f"**Fázis:** {phase}")
    lines.append(f"**Nyitott GAP-ok:** {gaps.get('active', 0)} aktív, {gaps.get('resolved', '?')} resolved")
    lines.append("")

    if next_step:
        lines.append("**Dokumentált következő lépés (self_state.json → next_concrete_step):**")
        lines.append(next_step[:400])
    else:
        lines.append(f"**Következő lépés:** Nincs nyitott GAP — a rendszer {phase} fázisban van.")

    if focus:
        lines.append("")
        lines.append("**Aktív fókusz:**")
        lines.append(focus[:250])

    ov_sec = context.get("overview_current_state", "")
    if ov_sec:
        lines.append("")
        lines.append("**PROJECT_S_OVERVIEW.md — jelenlegi állapot összefoglaló:**")
        lines.append(ov_sec[:500])

    return "\n".join(lines)


def _synthesize_milestone_answer(context: Dict[str, Any]) -> str:
    milestones: List[str] = context.get("milestones", [])
    recent_gaps: List[Dict[str, Any]] = context.get("recent_gaps", [])
    lines: List[str] = []

    if milestones:
        lines.append("**Legutóbbi mérföldkövek (self_state.json):**")
        for i, ms in enumerate(milestones, 1):
            lines.append(f"{i}. {str(ms)[:150]}")
        lines.append("")

    if recent_gaps:
        lines.append("**Legutóbbi megoldott GAP-ok:**")
        for gap in recent_gaps:
            gid = gap.get("gap_id", "?")
            title = gap.get("title", "")
            status = gap.get("status", "?")
            resolved_at = (gap.get("resolved_at") or "")[:10]
            lines.append(f"- {gid} ({status}, {resolved_at}): {title[:100]}")

    if not milestones and not recent_gaps:
        lines.append("A self_state.json-ban nem találhatók milestone bejegyzések.")

    return "\n".join(lines)


def _synthesize_general_answer(context: Dict[str, Any]) -> str:
    # Prefer current_state block; fall back to base context
    cs = context.get("current_state") or context.get("base", {})
    base = context.get("base", {})
    phase = cs.get("phase") or base.get("phase", "ismeretlen")
    focus = cs.get("active_focus") or base.get("active_focus", "")
    total = cs.get("gaps_total") or base.get("gaps_total", "?")
    resolved = cs.get("gaps_resolved") or base.get("gaps_resolved", "?")

    lines = [
        "A Project-S jelenlegi állapota (self_state.json alapján):",
        f"- Fázis: {phase}",
        f"- GAP összesítő: {total} összesen, {resolved} RESOLVED",
    ]
    if focus:
        lines.append(f"- Fókusz: {focus[:180]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Grounding metadata
# ---------------------------------------------------------------------------

def build_grounding_metadata(
    intent: str,
    docs_used: List[str],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Build metadata dict for the grounding result."""
    has_content = bool(
        context.get("current_state")
        or context.get("gaps")
        or context.get("architecture")
        or context.get("next_step")
        or context.get("milestones")
        or context.get("base")
    )
    confidence = "HIGH" if (has_content and docs_used) else "LOW"
    return {
        "docs_used": docs_used,
        "intent": intent,
        "grounding_confidence": confidence,
        "sections_used": list(context.keys()),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def ground_internal_doc_response(
    prompt: str,
    prompt_norm: str,
) -> Dict[str, Any]:
    """Full pipeline: load docs → detect intent → select context → RAG supplement → synthesize answer.

    Returns:
        result: str          — user-facing answer
        docs_used: list      — which docs contributed
        chunks_used: list    — RAG chunks that contributed (file_path, score)
        intent: str          — detected intent
        grounding_confidence: str  — HIGH / MEDIUM / LOW
        grounding_metadata: dict   — full metadata
    """
    # Load documents
    docs = load_core_docs()

    # Detect intent
    intent = detect_intent(prompt_norm)

    # Select relevant context from core docs
    context, docs_used = select_relevant_context(intent, prompt_norm, docs)

    # --- RAG supplementation ---
    rag_chunks = []
    grounding_method = "file_grounding"
    try:
        rag_chunks = query_rag_index(prompt, top_k=5)
        if rag_chunks:
            # Inject RAG context into the answer
            context["rag_chunks"] = rag_chunks
            grounding_method = "file_grounding + rag_retrieval"
    except Exception as e:
        logger.warning("RAG query failed: %s", e)

    # Synthesize answer (with optional RAG context)
    answer = synthesize_answer(prompt, intent, context)

    # Append RAG-sourced details if available
    if rag_chunks:
        answer = _append_rag_details(answer, rag_chunks)

    # Build metadata
    chunks_used = [
        {"file_path": c["file_path"], "score": round(c["score"], 4)}
        for c in rag_chunks
    ]
    metadata = build_grounding_metadata(intent, docs_used, context)
    metadata["grounding_method"] = grounding_method
    metadata["rag_chunks_retrieved"] = len(rag_chunks)

    # Determine confidence
    has_file_content = bool(
        context.get("current_state")
        or context.get("gaps")
        or context.get("architecture")
        or context.get("next_step")
        or context.get("milestones")
        or context.get("base")
    )
    if has_file_content and docs_used and rag_chunks:
        confidence = "HIGH"
    elif has_file_content and docs_used:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    metadata["grounding_confidence"] = confidence

    return {
        "result": answer,
        "docs_used": docs_used,
        "chunks_used": chunks_used,
        "intent": intent,
        "grounding_confidence": confidence,
        "grounding_metadata": metadata,
    }


def _append_rag_details(answer: str, rag_chunks: List[Dict[str, Any]]) -> str:
    """Append relevant RAG-retrieved details to the answer.

    Only includes chunks with score >= 0.7 and extracts concise facts.
    """
    if not rag_chunks:
        return answer

    # Collect unique file paths from high-confidence chunks
    relevant_files = set()
    relevant_facts = []
    for chunk in rag_chunks:
        if chunk["score"] < 0.7:
            continue
        fp = chunk["file_path"]
        basename = fp.split("/")[-1] if "/" in fp else fp.split("\\")[-1]
        relevant_files.add(basename)
        # Extract a short fact from the chunk text
        text = chunk.get("text", "")[:200].strip()
        if text:
            relevant_facts.append(f"- [{basename}] {text[:150]}")

    if relevant_facts:
        answer += "\n\n**RAG index további releváns források:**"
        answer += "\n" + "\n".join(relevant_facts[:3])

    return answer
