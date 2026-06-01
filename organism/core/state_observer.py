"""
State Observer — GAP_008 megoldása

Új Observer-forrás az Organism pipeline-ba.
self_state.json known_gaps (ACTIVE) → Task objektumok.

Cél: Az Organism ne csak TODO/FIXME/git diff/terminál-históriát lásson,
hanem a rendszer saját ismert hiányosságait (self_state.json) is.

Foundation.md elv: meglévő modulokat összekötjük, nem helyettesítjük.
Az Observer.observe() nincs módosítva — ez MELLÉ adódó forrás.
"""

import json
import hashlib
from pathlib import Path

from .observer import Task

# Alapértelmezett self_state.json elérési út (project root relativ)
_DEFAULT_STATE_PATH = Path(__file__).parent.parent.parent / "self_state.json"

# Prioritás → szöveg-marker mapping
# A prioritizer.py impact_keywords közt: ['fixme', 'critical', 'crash', 'security', 'data loss', 'broken', 'error']
# A prioritizer.py ev: 'fixme' → ev >= 0.80
# => FIXME marker = high/medium gap-eknek az optimális jelölő
_PRIORITY_MARKER = {
    "high":   "FIXME",
    "medium": "FIXME",
    "low":    "TODO",
}


def read_self_state_gaps(
    self_state_path: Path = _DEFAULT_STATE_PATH,
) -> list[Task]:
    """
    Olvassa a self_state.json identity.known_gaps listáját,
    kiszűri az ACTIVE + priority != None gap-eket,
    és Task objektumokat ad vissza az Organism pipeline számára.

    Hibatűrő: FileNotFoundError / JSONDecodeError esetén üres listát ad.

    Returns:
        list[Task] — a Prioritizer + Proposer pipeline-hoz kompatibilis lista.
    """
    try:
        with open(self_state_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    gaps: list[dict] = data.get("identity", {}).get("known_gaps", [])
    tasks: list[Task] = []

    for gap in gaps:
        # Csak ACTIVE + explicit prioritású gap-ek
        if gap.get("status") != "ACTIVE":
            continue
        priority: str | None = gap.get("priority")
        if not priority:
            continue

        gap_id: str = gap.get("gap_id", "GAP_???")
        title: str = gap.get("title", "(no title)")
        context: str = gap.get("context", "")
        proposed: str = gap.get("proposed_solution", "")

        marker = _PRIORITY_MARKER.get(priority, "TODO")

        # --- Description tervezés ---
        # "FIXME" → impact +0.2, ev → 0.80 (prioritizer.py scoring)
        # "tool"  → strategic_score = 8.5
        # "observer", "prioritizer", "proposer" → learning_value boost
        # "implement" → rabbit_hole 0.4 (medium, nem HIGH)
        #
        # Ha van proposed_solution: beágyazódik a description-be,
        # így a _generate_action() text_combined-ban látja a kulcsszavakat,
        # és az Action Plan gazdagabb lesz.
        base_scoring_hint = (
            f"implement tool (self_state observer, prioritizer, proposer, {priority} priority)"
        )
        if proposed:
            description = (
                f"[{gap_id}] {title}\n"
                f"Context: {context[:150]}\n\n"
                f"PROPOSED SOLUTION:\n{proposed}\n\n"
                f"({base_scoring_hint})"
            )
        else:
            description = (
                f"[{gap_id}] {marker}: {title} — {base_scoring_hint}"
            )

        # text = az "eredeti TODO szöveg" ekvivalense (proposer title-hez és _generate_action-höz)
        text = f"{marker}: {title}"

        # snippet = kontextus + proposed_solution (megjelenik a "Code Context" szekcióban
        # a top_proposals.md-ben, és részben a bridge metadata-ban)
        snippet_parts = [p for p in [context, proposed] if p]
        snippet = " | ".join(snippet_parts)[:400]

        # Determinisztikus task_id a gap_id alapján
        task_id = "gap_" + hashlib.sha1(gap_id.encode("utf-8")).hexdigest()[:8]

        task = Task(
            task_id=task_id,
            description=description,
            source="self_state",
            file="",              # nincs forrásfájl — self_state.json az origó
            line=0,
            text=text,
            snippet=snippet,
            source_path="self_state.json",
            issue_url="",
            metadata={
                "gap_id": gap_id,
                # FONTOS: marker értéket ('FIXME'/'TODO') kell itt tárolni, NEM a priority szintet!
                # A prioritizer.py task.metadata.get('priority', 'TODO') alapján tölti be a
                # TaskScore['priority'] mezőt, amit a proposer._generate_action() is_fixme check-je
                # használ: task['priority'].upper() == 'FIXME'
                # Ha itt 'medium'/'high' lenne, is_fixme=False → generikus TODO Steps (nem megfelelő)
                "priority": marker,
                "gap_priority": priority,    # eredeti szint (high/medium/low) megőrzésre
                "status": "ACTIVE",
                "discovered": gap.get("discovered", ""),
                "discovered_by": gap.get("discovered_by", ""),
                "proposed_solution": proposed,
            },
        )
        tasks.append(task)

    return tasks
