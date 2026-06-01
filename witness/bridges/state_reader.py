"""
witness/bridges/state_reader.py
================================
Read-only adapter for PersistentStateManager.

PURPOSE:
    Provides a synchronous interface to the async PersistentStateManager
    so that Witness modules (pure stdlib, sync) can query persistent state
    without owning the event loop or modifying any state.

WHAT THIS MODULE DOES NOT DO:
    - Does NOT write, mutate, or delete any state
    - Does NOT modify self_state.json (that is a separate step)
    - Does NOT call AI or subprocesses
    - Does NOT expose PersistentStateManager's write methods

ARCHITECTURE NOTE:
    witness/ is not part of the src/ package. We extend sys.path to
    WORKSPACE_ROOT so that `from src.core.state...` imports work.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Workspace root — state_reader.py lives at:
#   <root>/witness/bridges/state_reader.py
#   → parent = bridges/, parent.parent = witness/, parent.parent.parent = root
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.resolve()
STORAGE_PATH = WORKSPACE_ROOT / "memory" / "state"

if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# ---------------------------------------------------------------------------
# Fail-safe import
# ---------------------------------------------------------------------------
PSM_AVAILABLE: bool = False
_PersistentStateManager = None
_StateType = None

try:
    from src.core.state.persistent_manager import PersistentStateManager as _PSMClass
    from src.core.state.base_state import StateType as _StateTypeClass
    _PersistentStateManager = _PSMClass
    _StateType = _StateTypeClass
    PSM_AVAILABLE = True
except Exception as _import_exc:
    logger.warning(
        "state_reader: PersistentStateManager not importable — "
        "all queries will return empty results. Reason: %s", _import_exc
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_async(coro) -> Any:
    """
    Run an async coroutine from sync context.

    Raises RuntimeError if already inside a running event loop
    (state_reader must not be called from async code).
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            raise RuntimeError(
                "state_reader cannot be called from inside an async context. "
                "Use 'await' directly on PersistentStateManager methods instead."
            )
    except RuntimeError as e:
        # get_running_loop() raises RuntimeError when there is no loop — that's fine.
        if "state_reader cannot be called" in str(e):
            raise
    t0 = time.monotonic()
    result = asyncio.run(coro)
    elapsed_ms = (time.monotonic() - t0) * 1000
    logger.debug("state_reader async call completed in %.1f ms", elapsed_ms)
    return result


def _get_manager() -> Optional[Any]:
    """Instantiate PersistentStateManager with the project's storage path."""
    if not PSM_AVAILABLE:
        return None
    try:
        return _PersistentStateManager(
            name="state_reader_ro",
            storage_path=STORAGE_PATH,
        )
    except Exception as exc:
        logger.warning("state_reader: could not instantiate PSM: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API — sync wrappers (read-only)
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """True if PersistentStateManager is importable and instantiable."""
    if not PSM_AVAILABLE:
        return False
    mgr = _get_manager()
    return mgr is not None


def list_state_types() -> List[str]:
    """Return all StateType values available in the system."""
    if not PSM_AVAILABLE or _StateType is None:
        return []
    try:
        return [st.value for st in _StateType]
    except Exception as exc:
        logger.warning("list_state_types error: %s", exc)
        return []


def list_contexts(limit: int = 50) -> List[Dict]:
    """
    Return metadata for up to `limit` context state entries.
    Returns empty list if storage is empty or PSM unavailable.
    """
    if not PSM_AVAILABLE:
        logger.warning("state_reader: PSM unavailable, list_contexts returns []")
        return []
    try:
        mgr = _get_manager()
        if mgr is None:
            return []

        async def _fetch():
            await mgr._check_async_init()
            return await mgr.list_states(
                state_type=_StateType.CONTEXT,
                limit=limit,
            )

        entries = _run_async(_fetch())
        result = []
        for entry in entries:
            if hasattr(entry, "metadata"):
                result.append(entry.metadata.to_dict())
            elif isinstance(entry, dict):
                result.append(entry)
        return result
    except Exception as exc:
        logger.warning("list_contexts error: %s", exc)
        return []


def load_context(context_id: str) -> Optional[Dict]:
    """
    Load and return a single context entry by ID.
    Returns None if not found or PSM unavailable.
    """
    if not PSM_AVAILABLE:
        logger.warning("state_reader: PSM unavailable, load_context returns None")
        return None
    try:
        mgr = _get_manager()
        if mgr is None:
            return None

        async def _fetch():
            await mgr._check_async_init()
            entry = await mgr.get_state(context_id, state_type=_StateType.CONTEXT)
            if entry is None:
                return None
            if hasattr(entry, "to_dict"):
                return entry.to_dict()
            return entry

        return _run_async(_fetch())
    except Exception as exc:
        logger.warning("load_context(%s) error: %s", context_id, exc)
        return None


def list_sessions(limit: int = 50) -> List[Dict]:
    """
    Return metadata for up to `limit` session state entries.
    Returns empty list if storage is empty or PSM unavailable.
    """
    if not PSM_AVAILABLE:
        logger.warning("state_reader: PSM unavailable, list_sessions returns []")
        return []
    try:
        mgr = _get_manager()
        if mgr is None:
            return []

        async def _fetch():
            await mgr._check_async_init()
            return await mgr.list_states(
                state_type=_StateType.SESSION,
                limit=limit,
            )

        entries = _run_async(_fetch())
        result = []
        for entry in entries:
            if hasattr(entry, "metadata"):
                result.append(entry.metadata.to_dict())
            elif isinstance(entry, dict):
                result.append(entry)
        return result
    except Exception as exc:
        logger.warning("list_sessions error: %s", exc)
        return []


def get_conversation_history(session_id: str, limit: int = 100) -> List[Dict]:
    """
    Return conversation history for a session.
    Returns empty list if not found or PSM unavailable.
    """
    if not PSM_AVAILABLE:
        logger.warning("state_reader: PSM unavailable, get_conversation_history returns []")
        return []
    try:
        mgr = _get_manager()
        if mgr is None:
            return []

        async def _fetch():
            await mgr._check_async_init()
            return await mgr.get_conversation_history(
                session_id=session_id,
                limit=limit,
            )

        result = _run_async(_fetch())
        return result if result is not None else []
    except Exception as exc:
        logger.warning("get_conversation_history(%s) error: %s", session_id, exc)
        return []


def get_statistics() -> Dict:
    """
    Return PersistentStateManager's own statistics (sync method, no wrapper needed).
    Returns empty dict if PSM unavailable.
    """
    if not PSM_AVAILABLE:
        return {}
    try:
        mgr = _get_manager()
        if mgr is None:
            return {}
        return mgr.get_persistent_statistics()
    except Exception as exc:
        logger.warning("get_statistics error: %s", exc)
        return {}


def summarize_state() -> Dict:
    """
    High-level summary of the entire persistent state.

    Returns:
        {
          'available': bool,
          'storage_path': str,
          'context_count': int,
          'session_count': int,
          'has_data': bool,
          'last_modified': ISO timestamp string | None
        }

    This is the primary entry point used by the Witness to decide
    whether persistent state data exists before attempting to read it.
    """
    summary: Dict = {
        "available": PSM_AVAILABLE,
        "storage_path": str(STORAGE_PATH),
        "context_count": 0,
        "session_count": 0,
        "has_data": False,
        "last_modified": None,
    }

    if not PSM_AVAILABLE:
        return summary

    try:
        contexts = list_contexts(limit=200)
        summary["context_count"] = len(contexts)
    except Exception as exc:
        logger.warning("summarize_state: context count failed: %s", exc)

    try:
        sessions = list_sessions(limit=200)
        summary["session_count"] = len(sessions)
    except Exception as exc:
        logger.warning("summarize_state: session count failed: %s", exc)

    summary["has_data"] = (summary["context_count"] + summary["session_count"]) > 0

    # Last-modified: newest .json mtime in storage tree (filesystem-level, no async)
    try:
        json_files = list(STORAGE_PATH.rglob("*.json"))
        if json_files:
            newest = max(json_files, key=lambda f: f.stat().st_mtime)
            mtime = newest.stat().st_mtime
            from datetime import datetime, timezone
            summary["last_modified"] = datetime.fromtimestamp(
                mtime, tz=timezone.utc
            ).isoformat()
    except Exception as exc:
        logger.warning("summarize_state: last_modified failed: %s", exc)

    return summary


# ---------------------------------------------------------------------------
# Self-state integration
# ---------------------------------------------------------------------------

SELF_STATE_PATH = WORKSPACE_ROOT / "self_state.json"
SELF_STATE_TMP  = WORKSPACE_ROOT / "self_state.json.tmp"


def update_self_state() -> Dict:
    """
    Read the persistent state summary and write it into the 'persistent_state'
    block of self_state.json.

    Only 'persistent_state' and 'last_updated' (root) are modified.
    All other fields are preserved.

    Atomic write: tmp file + os.replace(), same pattern as evidence_reader.py.

    Returns:
        The dict that was written into self_state['persistent_state'].
        Returns empty dict on any error (logs warning, never raises).
    """
    import os
    from datetime import datetime, timezone

    try:
        summary = summarize_state()
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        block = dict(summary)
        block["last_scanned_at"] = now_utc

        # Read current self_state.json
        with open(SELF_STATE_PATH, encoding="utf-8") as fh:
            state = json.load(fh)

        # Patch only the persistent_state block and last_updated
        state["persistent_state"] = block
        state["last_updated"] = now_utc

        # Atomic write
        with open(SELF_STATE_TMP, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(SELF_STATE_TMP, SELF_STATE_PATH)

        logger.info("update_self_state: persistent_state block written to self_state.json")
        return block

    except Exception as exc:
        logger.warning("update_self_state failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="state_reader — read-only PersistentStateManager adapter"
    )
    parser.add_argument(
        "--update-state",
        action="store_true",
        help="Write summarize_state() result into self_state.json/persistent_state (atomic)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    print("=== state_reader — PersistentStateManager summary ===")
    print(f"Workspace root : {WORKSPACE_ROOT}")
    print(f"Storage path   : {STORAGE_PATH}")
    print()

    if not PSM_AVAILABLE:
        print("PSM_AVAILABLE : False")
        print("PersistentStateManager could not be imported.")
        print("Check that aiofiles and langgraph are installed and src/ is intact.")
        sys.exit(0)

    t0 = time.monotonic()
    summary = summarize_state()
    elapsed_ms = (time.monotonic() - t0) * 1000

    print(f"PSM_AVAILABLE  : {summary['available']}")
    print()

    if not summary["has_data"]:
        print("No persistent state yet (storage is empty).")
    else:
        print(f"context_count  : {summary['context_count']}")
        print(f"session_count  : {summary['session_count']}")
        print(f"last_modified  : {summary['last_modified']}")

    print()
    print("Full summary (JSON):")
    print(json.dumps(summary, indent=2, default=str))
    print()
    print(f"summarize_state() completed in {elapsed_ms:.1f} ms")

    if args.update_state:
        print()
        print("--- --update-state: writing persistent_state to self_state.json ---")
        t1 = time.monotonic()
        block = update_self_state()
        write_ms = (time.monotonic() - t1) * 1000
        if block:
            print("persistent_state block written:")
            print(json.dumps(block, indent=2, default=str))
            print(f"update_self_state() completed in {write_ms:.1f} ms")
        else:
            print("update_self_state() returned empty — check warnings above.")
