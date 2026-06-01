"""
witness/bridges/organism_to_meta.py
-------------------------------------
DRY-RUN / OBSERVE hid: Organism Proposer -> MetaController goal string.

Mit csinal:
  1. Olvassa a top_proposals.md elso propoziciojat.
  2. General egy goal stringet sablon alapjan.
  3. Kir egy PENDING_HUMAN_REVIEW JSON-t a pending_goals/ mappaba.
  4. Frissiti a self_state.json "bridges.organism_to_meta" blokkjat.
  5. Konzolra irja a generalt goal stringet.
  6. Ha --observe flag aktiv: MetaController.observe()-t hiv (non-blocking).

Mit NEM csinal:
  - NEM hiv run_goal()-t.
  - NEM indit subprocess-t.
  - NEM hiv AI modellt.

Exit kodok:
  0 -- sikeres generalas
  1 -- nincs feldolgozható proposal
  2 -- fajl hiba / parse hiba

Futtatas:
  python -m witness.bridges.organism_to_meta
  python -m witness.bridges.organism_to_meta --observe
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# -- Utvonalak -----------------------------------------------------------------
REPO_ROOT       = Path(__file__).parent.parent.parent
PROPOSALS_FILE  = REPO_ROOT / "organism" / "evidence" / "top_proposals.md"
PENDING_DIR     = Path(__file__).parent / "pending_goals"
SELF_STATE_PATH = REPO_ROOT / "self_state.json"
SELF_STATE_TMP  = REPO_ROOT / "self_state.json.tmp"
EVIDENCE_PATH   = REPO_ROOT / "memory" / "intelligence" / "meta_evidence.jsonl"


# -- Segfggvenyek -------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(path: Path, data: dict) -> None:
    """JSON-t atomikusan ir (tmp + os.replace)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# -- Parser -------------------------------------------------------------------

def _extract_text_after(lines: list, header: str) -> str:
    collecting = False
    parts = []
    for line in lines:
        if line.strip().lower() == header.strip().lower():
            collecting = True
            continue
        if collecting:
            stripped = line.strip()
            if stripped.startswith("##"):
                break
            if stripped:
                parts.append(stripped)
    return "\n".join(parts)


def parse_top_proposal(proposals_path: Path):
    if not proposals_path.exists():
        return None

    with open(proposals_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    if not content.strip():
        return None

    first_block_match = re.search(
        r"^(## \[1\].+?)(?=^## \[2\]|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if not first_block_match:
        return None

    block = first_block_match.group(1)
    lines = block.splitlines()

    header_line = lines[0]
    title_match = re.match(r"^##\s+\[\d+\]\s+(.+?)(?:\s+[🟢🟡🔴].*)?$", header_line)
    title = title_match.group(1).strip() if title_match else header_line.strip("# ").strip()
    title = re.sub(r"\s+🔴\s+ESCALATED", " [ESCALATED]", title)

    if "🔴" in header_line:
        risk_emoji = "high"
    elif "🟡" in header_line:
        risk_emoji = "medium"
    else:
        risk_emoji = "low"

    issue_url = ""
    issue_match = re.search(r"\*\*Issue\*\*:\s*\[(.+?)\]\((.+?)\)", block)
    if issue_match:
        issue_url = issue_match.group(2).strip()

    locations = []
    in_locations = False
    for line in lines:
        stripped = line.strip()
        if stripped == "**Locations**:":
            in_locations = True
            continue
        if in_locations:
            if stripped.startswith("- `"):
                loc_match = re.match(r"- `(.+?)` -- (.+)", stripped)
                if not loc_match:
                    loc_match = re.match(r"- `(.+?)` - (.+)", stripped)
                if not loc_match:
                    loc_match = re.match(r"- `(.+?)`.*", stripped)
                if loc_match:
                    if loc_match.lastindex and loc_match.lastindex >= 2:
                        locations.append(f"{loc_match.group(1)} -- {loc_match.group(2)[:60]}")
                    else:
                        locations.append(loc_match.group(1))
            elif stripped.startswith("**") or stripped.startswith("##"):
                in_locations = False

    priority_score = None
    ps_match = re.search(r"\*\*Priority Score\*\*:\s*([\d.]+)", block)
    if ps_match:
        try:
            priority_score = float(ps_match.group(1))
        except ValueError:
            pass

    action_steps = []
    in_action = False
    for line in lines:
        stripped = line.strip()
        if stripped == "### Consolidated Action Plan":
            in_action = True
            continue
        if in_action:
            if stripped.startswith("###") or stripped.startswith("##"):
                break
            step_match = re.match(r"^\d+\.\s+(.+)", stripped)
            if step_match:
                step_text = re.sub(r"\*\*(.+?)\*\*", r"\1", step_match.group(1))
                action_steps.append(step_text)

    strategic_score = None
    ss_match = re.search(r"\*\*Strategic Score\*\*:\s*([\d.]+)/10", block)
    if ss_match:
        try:
            strategic_score = float(ss_match.group(1))
        except ValueError:
            pass

    rabbit_hole_risk = "unknown"
    rh_match = re.search(r"\*\*Rabbit Hole Risk\*\*:\s*(\w+)\s*\(([\d.]+)\)", block)
    if rh_match:
        rabbit_hole_risk = rh_match.group(1).upper()

    risk_level = "unknown"
    rl_match = re.search(r"- (?:\*\*)?Risk Level(?:\*\*)?:\s*(\w+)", block)
    if rl_match:
        risk_level = rl_match.group(1).upper()

    quick_win = False
    qw_match = re.search(r"\*\*Quick Win\*\*:\s*(Yes|No)", block, re.IGNORECASE)
    if qw_match:
        quick_win = qw_match.group(1).lower() == "yes"

    generated_at = ""
    gen_match = re.search(r"^Generated:\s*(.+)$", content, re.MULTILINE)
    if gen_match:
        generated_at = gen_match.group(1).strip()

    hash_input = f"{title}|{locations[0] if locations else ''}|{generated_at}"
    proposal_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    return {
        "title": title,
        "risk_emoji": risk_emoji,
        "issue_url": issue_url,
        "locations": locations,
        "priority_score": priority_score,
        "action_steps": action_steps,
        "strategic_score": strategic_score,
        "rabbit_hole_risk": rabbit_hole_risk,
        "risk_level": risk_level,
        "quick_win": quick_win,
        "generated_at": generated_at,
        "proposal_hash": proposal_hash,
    }


# -- Goal string genertor -----------------------------------------------------

def build_goal_string(proposal: dict) -> str:
    title = proposal["title"]
    steps = proposal["action_steps"]
    locations = proposal["locations"]
    issue_url = proposal.get("issue_url", "")

    loc_summary = ""
    if locations:
        if len(locations) == 1:
            loc_summary = f"in {locations[0].split(' -- ')[0]}"
        else:
            files = [loc.split(" -- ")[0] for loc in locations[:3]]
            loc_summary = f"across {len(locations)} location(s): {', '.join(files)}"

    issue_ref = f" (ref: {issue_url})" if issue_url else ""

    if steps:
        steps_text = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(steps))
        steps_block = f"\nSteps:\n{steps_text}"
    else:
        steps_block = ""

    goal = (
        f"Task: {title}{issue_ref}\n"
        f"Scope: {loc_summary}\n"
        f"{steps_block}\n"
        f"Success criteria: All steps completed, changes reviewed and tested. "
        f"No regressions introduced."
    ).strip()

    return goal


# -- Komplexitas becslés -------------------------------------------------------

def estimate_complexity(proposal: dict) -> str:
    risk = proposal.get("risk_level", "").upper()
    if risk == "HIGH":
        return "high"
    if risk == "MEDIUM":
        return "medium"
    return "low"


# -- Fuggvenyek a pending_goals kezelesehez -----------------------------------

def _collect_existing_hashes() -> set:
    hashes = set()
    if not PENDING_DIR.exists():
        return hashes
    for f in PENDING_DIR.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            h = data.get("proposal_hash")
            if h:
                hashes.add(h)
        except Exception:
            pass
    return hashes


def _count_pending_goals() -> int:
    count = 0
    if not PENDING_DIR.exists():
        return count
    for f in PENDING_DIR.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("status") == "PENDING_HUMAN_REVIEW":
                count += 1
        except Exception:
            pass
    return count


# -- Observe wrapper ----------------------------------------------------------

def _call_observe(goal_string: str, bridge_id: str, proposal: dict):
    """Szinkron wrapper: MetaController.observe() hivas, fail-safe.
    RISK_001 biztonsag: NEM hivja run_goal()-t, csak observe()-t."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        sys.path.insert(0, str(REPO_ROOT))
        from core.meta.meta_controller import MetaController
        mc = MetaController(
            council=None,
            executor=None,
            validator=None,
            evidence_logger=None,
            evidence_path=str(EVIDENCE_PATH),
        )
        observe_result = {
            "bridge_id": bridge_id,
            "proposal_hash": proposal["proposal_hash"],
            "source": "organism_proposer",
            "priority_score": proposal.get("priority_score"),
            "strategic_score": proposal.get("strategic_score"),
            "locations_count": len(proposal.get("locations", [])),
        }
        asyncio.run(mc.observe(goal=goal_string[:200], result=observe_result))
        observe_at = _now_utc()
        print(f"[OBSERVE] external_observation irodott: {EVIDENCE_PATH}")
        return True, observe_at
    except Exception as exc:
        print(f"[WARN] observe() hivas sikertelen (non-fatal): {exc}", file=sys.stderr)
        return False, None


# -- self_state.json kezelese -------------------------------------------------

def _update_self_state(bridge_id, now, pending_count,
                       observe_called=False, observe_at=None):
    if not SELF_STATE_PATH.exists():
        return
    try:
        with open(SELF_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)

        state.setdefault("bridges", {})
        existing = state["bridges"].get("organism_to_meta", {})
        observe_calls = existing.get("observe_calls", 0)
        if observe_called:
            observe_calls += 1

        state["bridges"]["organism_to_meta"] = {
            "modes": ["DRY_RUN (default)", "OBSERVE (--observe flag)"],
            "mode": "OBSERVE" if observe_called else "DRY_RUN",
            "last_run": now,
            "pending_goals_count": pending_count,
            "last_generated_goal_id": bridge_id,
            "live_mode": False,
            "observe_calls": observe_calls,
            "last_observe_at": observe_at if observe_at else existing.get("last_observe_at"),
        }
        state["last_updated"] = now

        _atomic_write(SELF_STATE_PATH, state)
    except Exception as exc:
        print(f"[WARN] self_state.json frissites sikertelen: {exc}", file=sys.stderr)


def _update_self_state_no_proposals():
    if not SELF_STATE_PATH.exists():
        return
    try:
        with open(SELF_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)

        now = _now_utc()
        state.setdefault("bridges", {})
        state["bridges"]["organism_to_meta"] = {
            "mode": "DRY_RUN",
            "last_run": now,
            "pending_goals_count": _count_pending_goals(),
            "last_generated_goal_id": None,
            "live_mode": False,
            "last_status": "no_proposals_available",
        }
        state["last_updated"] = now

        _atomic_write(SELF_STATE_PATH, state)
    except Exception as exc:
        print(f"[WARN] self_state.json frissites sikertelen: {exc}", file=sys.stderr)


# -- Fo fuggveny --------------------------------------------------------------

def run_bridge(observe=False):
    """
    A hid fo belepesi pontja.

    Args:
        observe: Ha True, MetaController.observe()-t hiv (observe-only mod,
                 RISK_001 elkerulve). Default: False (DRY-RUN).
    Returns:
        exit code (0 / 1 / 2)
    """
    # 1. Parse proposal
    try:
        proposal = parse_top_proposal(PROPOSALS_FILE)
    except Exception as exc:
        print(f"[ERROR] Proposal fajl olvasasi hiba: {exc}", file=sys.stderr)
        return 2

    if proposal is None:
        print(
            "[WARN] Nincs feldolgozhato proposal.\n"
            f"  Ellenorzott fajl: {PROPOSALS_FILE}\n"
            "  Futtasd eloabb az Organism-ot: python organism/quickstart.py",
            file=sys.stderr,
        )
        _update_self_state_no_proposals()
        return 1

    # 2. Duplikacio ellenorzes
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    existing_hashes = _collect_existing_hashes()
    phash = proposal["proposal_hash"]

    if phash in existing_hashes:
        print(
            f"[SKIP] Duplikatam -- ez a proposal mar el lett mentve "
            f"(hash: {phash}).\n"
            "  Torold vagy dolgozd fel a pending_goals/ mappaban levo fajlt."
        )
        return 0

    # 3. Goal string generalas
    goal_string = build_goal_string(proposal)

    # 4. Pending goal JSON osszeallitas
    bridge_id = str(uuid.uuid4())
    now = _now_utc()
    complexity = estimate_complexity(proposal)

    loc_summary = (
        proposal["locations"][0] if proposal["locations"]
        else "(no location)"
    )

    pending = {
        "bridge_id": bridge_id,
        "proposal_hash": phash,
        "generated_at": now,
        "source": {
            "module": "organism.proposer",
            "input_file": str(PROPOSALS_FILE),
            "input_generated_at": proposal.get("generated_at", ""),
            "input_summary": f"{proposal['title']} -- priority score: {proposal['priority_score']}",
        },
        "generated_goal": goal_string,
        "metadata": {
            "priority_score": proposal.get("priority_score"),
            "strategic_score": proposal.get("strategic_score"),
            "rabbit_hole_risk": proposal.get("rabbit_hole_risk"),
            "risk_level": proposal.get("risk_level"),
            "quick_win": proposal.get("quick_win"),
            "estimated_complexity": complexity,
            "issue_url": proposal.get("issue_url", ""),
            "locations_count": len(proposal.get("locations", [])),
            "blocking_risks": ["RISK_001 (DORMANT)"],
        },
        "status": "PENDING_HUMAN_REVIEW",
        "next_action": (
            "Toti ellenorzi, es ha rendben van: "
            "python meta_launcher.py --goal '<generated_goal>'"
        ),
    }

    # 5. Pending fajl atomikus mentese
    timestamp_slug = now.replace(":", "-").replace("T", "_").rstrip("Z")
    out_path = PENDING_DIR / f"{timestamp_slug}_{bridge_id[:8]}.json"
    _atomic_write(out_path, pending)

    # 5b. OBSERVE MOD -- MetaController.observe() hivas (ha --observe flag aktiv)
    observe_called = False
    observe_at = None
    if observe:
        observe_called, observe_at = _call_observe(
            goal_string=goal_string,
            bridge_id=bridge_id,
            proposal=proposal,
        )

    # 6. self_state.json frissites
    pending_count = _count_pending_goals()
    _update_self_state(bridge_id, now, pending_count, observe_called, observe_at)

    # 7. Konzol kimenet
    print("=" * 60)
    mode_label = "OBSERVE" if observe else "DRY-RUN"
    print(f"ORGANISM -> META BRIDGE -- {mode_label}")
    print("=" * 60)
    print(f"Bridge ID  : {bridge_id}")
    print(f"Proposal   : {proposal['title']}")
    print(f"Hash       : {phash}")
    print(f"Complexity : {complexity}  |  Risk: {proposal['risk_level']}  |  Score: {proposal['priority_score']}")
    print(f"Pending at : {out_path}")
    if observe:
        obs_status = "OK -- external_observation irva" if observe_called else "FAILED (non-fatal, pending mentve)"
        print(f"Observe    : {obs_status}")
    print()
    print("-- GENERALT GOAL STRING ---------------------------------------")
    print(goal_string)
    print("---------------------------------------------------------------")
    print()
    print("STATUS: PENDING_HUMAN_REVIEW")
    if not observe:
        print("Kovetkezo lepes: Toti jovahagyja, majd:")
        print(f"  python meta_launcher.py --goal '<goal string>'")
        print()
        print("[FIGYELEM] A MetaController NEM lett meghivva. Ez DRY-RUN.")
    else:
        print("[INFO] observe() hivas lefutott -- external_observation a meta_evidence.jsonl-ben.")
        print("[FIGYELEM] run_goal() NEM lett meghivva. Dispatcher mentes (RISK_001 ok).")

    return 0


# -- Belepesi pont ------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Organism -> MetaController bridge"
    )
    parser.add_argument(
        "--observe",
        action="store_true",
        default=False,
        help=(
            "Ha megadva: MetaController.observe() hivas is lefut "
            "(observe-only, RISK_001 biztonságos). Default: csak pending JSON (DRY-RUN)."
        ),
    )
    args = parser.parse_args()
    sys.exit(run_bridge(observe=args.observe))


if __name__ == "__main__":
    main()
