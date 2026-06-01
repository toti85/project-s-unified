"""
test_sai_tool_selection_file_list.py
=====================================

Regression test: SmartOrchestrator task type classification for file
listing operations.

Bizonyítja, hogy a "List all Python files ... recursively" típusú
feladatok task_type == "file_search"-ként kerülnek besorolásra, és
nem jutnak el a web_page_fetch fallback-hez.

Rögzíti a 2026-04-30 bugfix-et: smart_orchestrator.py _analyze_task()
file_search keyword listájába bekerült: "list", "recursively",
"recursive", "*.py", "relative paths", "directory", "folder".

Futtatás:
    python tests/test_sai_tool_selection_file_list.py
"""
import sys
import asyncio
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "tools"))


def _get_orchestrator():
    """Load SmartOrchestrator directly to avoid package init side-effects."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "smart_orchestrator",
        repo_root / "tools" / "tools" / "registry" / "smart_orchestrator.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SmartToolOrchestrator()


def test_list_recursively_classified_as_file_search():
    """
    The exact task from the live validation run must be classified as
    directory_listing (not general, not file_search).
    REGRESSION: was returning task_type="general" → web_page_fetch selected.
    """
    orch = _get_orchestrator()
    task = "List all Python files in C:\\ProjectS-Unified\\witness recursively and return exact relative paths."
    result = asyncio.run(orch._analyze_task(task))
    assert result["task_type"] == "directory_listing", (
        f"REGRESSION: task classified as '{result['task_type']}', expected 'directory_listing'"
    )


def test_list_keyword_triggers_file_search():
    orch = _get_orchestrator()
    for task in [
        "list all files in the directory",
        "List Python files in src/",
        "LIST files recursively",
    ]:
        result = asyncio.run(orch._analyze_task(task))
        assert result["task_type"] == "directory_listing", (
            f"'{task}' → got '{result['task_type']}', expected 'directory_listing'"
        )


def test_recursively_keyword_triggers_file_search():
    orch = _get_orchestrator()
    for task in [
        "scan recursively under data/",
        "walk directories recursively",
        "recursive scan of project",
    ]:
        result = asyncio.run(orch._analyze_task(task))
        assert result["task_type"] == "directory_listing", (
            f"'{task}' → got '{result['task_type']}', expected 'directory_listing'"
        )


def test_py_glob_triggers_file_search():
    orch = _get_orchestrator()
    result = asyncio.run(orch._analyze_task("find all *.py files under src"))
    assert result["task_type"] == "directory_listing", (
        f"*.py task got '{result['task_type']}', expected 'directory_listing'"
    )


def test_directory_folder_keywords_trigger_file_search():
    orch = _get_orchestrator()
    for task in [
        "show files in directory witness/",
        "enumerate the folder structure",
    ]:
        result = asyncio.run(orch._analyze_task(task))
        assert result["task_type"] == "directory_listing", (
            f"'{task}' → got '{result['task_type']}', expected 'directory_listing'"
        )


def test_file_search_does_not_select_web_page_fetch():
    """
    When task_type is file_search, web_page_fetch must NOT be the
    selected tool. This was the root failure in the live validation run.
    """
    orch = _get_orchestrator()
    task = "List all Python files in witness/ recursively and return relative paths."
    analysis = asyncio.run(orch._analyze_task(task))
    assert analysis["task_type"] == "directory_listing"

    selected = asyncio.run(orch._select_tools(analysis))
    tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in selected]
    assert "web_page_fetch" not in tool_names, (
        f"REGRESSION: web_page_fetch still selected for directory_listing task. tools={tool_names}"
    )
    # Should use directory_lister
    tool_name_strs = [t.get('name', str(t)) if isinstance(t, dict) else getattr(t, 'name', str(t)) for t in selected]
    assert any('directory_lister' in str(n) for n in tool_name_strs), (
        f"Expected directory_lister to be selected, got: {tool_name_strs}"
    )


def test_existing_keywords_still_work():
    """
    Original content-search keywords must still trigger file_search (no regression).
    """
    orch = _get_orchestrator()
    for task in [
        "search for errors in log",
        "grep for TODO in source",
    ]:
        result = asyncio.run(orch._analyze_task(task))
        assert result["task_type"] == "file_search", (
            f"REGRESSION: original keyword task '{task}' → got '{result['task_type']}'"
        )


# ──────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_list_recursively_classified_as_file_search,
        test_list_keyword_triggers_file_search,
        test_recursively_keyword_triggers_file_search,
        test_py_glob_triggers_file_search,
        test_directory_folder_keywords_trigger_file_search,
        test_file_search_does_not_select_web_page_fetch,
        test_existing_keywords_still_work,
    ]

    passed = 0
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  [PASS] {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed}/{len(tests)} passed")
    sys.exit(0 if failed == 0 else 1)
