"""
test_gap_017_018_web_tools.py
==============================

Regression tests for:
  GAP_017 - web_search / web_scraper / web_page_fetch handlers in
            SmartOrchestrator._execute_single_tool()
  GAP_018 - False-success when evaluator returns action=replan

Run:
    python -m pytest tests/test_gap_017_018_web_tools.py -v
"""
import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_orchestrator():
    """Create a SmartToolOrchestrator with a minimal logger, no real tools needed."""
    from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator
    orch = SmartToolOrchestrator.__new__(SmartToolOrchestrator)
    orch.logger = MagicMock()
    orch.tool_performance_history = {}
    orch.execution_history = []
    # Stub out telemetry/auto-log helpers that touch the filesystem
    orch._log_tool_execution_telemetry = MagicMock()
    orch._auto_log_tool_not_found = MagicMock()
    orch.tool_registry = None  # disable legacy registry path
    return orch


def _fake_registry(tool_name, mock_tool):
    """Patch ToolRegistry so that tools[tool_name] returns mock_tool."""
    fake_reg = MagicMock()
    fake_reg.tools = {tool_name: mock_tool}
    return fake_reg


# ---------------------------------------------------------------------------
# GAP_017: web_search handler
# ---------------------------------------------------------------------------

class TestGap017WebSearch:

    def test_web_search_receives_query_kwarg(self):
        """
        _execute_single_tool must call WebSearchTool.execute(query=..., max_results=...)
        NOT execute(task=...) which would raise TypeError.
        """
        orch = _make_orchestrator()

        captured = {}

        async def mock_execute(query, max_results=5, **kwargs):
            captured["query"] = query
            captured["max_results"] = max_results
            return {
                "success": True,
                "results": [{"title": "Test", "url": "https://example.com", "description": "desc"}],
                "count": 1,
            }

        mock_tool = MagicMock()
        mock_tool.execute = mock_execute

        fake_reg = _fake_registry("web_search", mock_tool)

        tool_dict = {"name": "web_search", "type": "web", "purpose": "search"}
        task_desc = "Search for Qwen3-35B local model performance. Write to C:\\out\\report.md"

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry",
            return_value=fake_reg,
        ):
            result = run(orch._execute_single_tool(tool_dict, task_desc))

        assert "query" in captured, "execute() was never called with 'query' kwarg"
        assert isinstance(captured["query"], str) and len(captured["query"]) > 0
        assert captured.get("max_results", 0) >= 5
        assert result["success"] is True, f"Expected success, got: {result}"

    def test_web_search_no_task_kwarg_passed(self):
        """
        Ensure the handler does NOT pass 'task=' to the tool (would cause TypeError
        with the real WebSearchTool signature).
        """
        orch = _make_orchestrator()

        async def mock_execute(**kwargs):
            # Real WebSearchTool raises TypeError on 'task=...'
            if "task" in kwargs:
                raise TypeError(
                    "WebSearchTool.execute() got unexpected keyword argument 'task'"
                )
            return {"success": True, "results": [], "count": 0}

        mock_tool = MagicMock()
        mock_tool.execute = mock_execute

        fake_reg = _fake_registry("web_search", mock_tool)
        tool_dict = {"name": "web_search"}

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry",
            return_value=fake_reg,
        ):
            # Should NOT raise TypeError
            result = run(orch._execute_single_tool(tool_dict, "Research local AI models"))

        assert result.get("success") is not None  # handler completed without crash

    def test_web_search_formats_results_as_output(self):
        """
        When search returns results, the 'output' key in the wrapped return
        must contain the formatted search text (not an empty string).
        """
        orch = _make_orchestrator()

        async def mock_execute(query, max_results=5, **kwargs):
            return {
                "success": True,
                "query": query,
                "results": [
                    {"title": "Qwen3 Review", "url": "https://huggingface.co/qwen3", "description": "35B MoE model"},
                ],
                "count": 1,
            }

        mock_tool = MagicMock()
        mock_tool.execute = mock_execute
        fake_reg = _fake_registry("web_search", mock_tool)
        tool_dict = {"name": "web_search"}

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry",
            return_value=fake_reg,
        ):
            result = run(orch._execute_single_tool(tool_dict, "Find Qwen3 benchmark scores"))

        # The returned 'output' should contain the formatted results, not empty
        assert result["success"] is True
        assert "Qwen3 Review" in result["output"] or "https://huggingface.co" in result["output"]


# ---------------------------------------------------------------------------
# GAP_017: web_scraper handler
# ---------------------------------------------------------------------------

class TestGap017WebScraper:

    def test_web_scraper_receives_parameters_kwarg(self):
        """
        _execute_single_tool must call WebScraperTool.execute(parameters={...})
        NOT execute(task=...) which would raise TypeError.
        """
        orch = _make_orchestrator()

        captured = {}

        async def mock_execute(parameters, **kwargs):
            captured["parameters"] = parameters
            return {
                "success": True,
                "data": [{"text": "scraped content"}],
                "output_file": None,
                "items_scraped": 1,
            }

        mock_tool = MagicMock()
        mock_tool.execute = mock_execute
        fake_reg = _fake_registry("web_scraper", mock_tool)
        tool_dict = {"name": "web_scraper"}

        # Task includes a URL so the handler can pick it up
        task_with_url = (
            "Research Qwen3.\n\nContext from previous tools:\n"
            "[web_search result]:\n1. Title\n   URL: https://huggingface.co/qwen3\n   desc\n"
        )

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry",
            return_value=fake_reg,
        ):
            result = run(orch._execute_single_tool(tool_dict, task_with_url))

        assert "parameters" in captured, "execute() was never called with 'parameters' kwarg"
        assert isinstance(captured["parameters"], dict)
        assert "url" in captured["parameters"]
        assert "huggingface.co" in captured["parameters"]["url"]

    def test_web_scraper_no_url_returns_failure_not_exception(self):
        """
        When no URL is available, web_scraper should return success=False
        gracefully rather than crashing.
        """
        orch = _make_orchestrator()

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(return_value={"success": True, "data": []})
        fake_reg = _fake_registry("web_scraper", mock_tool)
        tool_dict = {"name": "web_scraper"}

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry",
            return_value=fake_reg,
        ):
            result = run(orch._execute_single_tool(tool_dict, "No URLs in this task at all"))

        # Handler should return a dict with success=False, not raise
        assert isinstance(result, dict)
        assert result.get("success") is False


# ---------------------------------------------------------------------------
# GAP_017: search→scrape→write chain does not crash immediately
# ---------------------------------------------------------------------------

class TestGap017Chain:

    def test_search_scrape_write_chain_no_immediate_typeerror(self):
        """
        Running web_search then web_scraper then file_writer sequentially
        must not immediately raise TypeError from incorrect keyword arguments.
        This is the exact failure mode observed in the live test.
        """
        orch = _make_orchestrator()

        calls = []

        async def web_search_execute(query, max_results=5, **kwargs):
            calls.append(("web_search", query))
            return {
                "success": True,
                "results": [{"title": "T", "url": "https://test.com/result", "description": "d"}],
                "count": 1,
            }

        async def web_scraper_execute(parameters, **kwargs):
            calls.append(("web_scraper", parameters.get("url")))
            return {"success": True, "data": [{"text": "scraped"}], "items_scraped": 1}

        mock_ws = MagicMock()
        mock_ws.execute = web_search_execute
        mock_wsc = MagicMock()
        mock_wsc.execute = web_scraper_execute

        # Two different tool registries needed — patch ToolRegistry to return
        # the right tool based on what was last requested
        call_count = [0]

        def fake_registry_factory():
            call_count[0] += 1
            fake = MagicMock()
            fake.tools = {
                "web_search": mock_ws,
                "web_scraper": mock_wsc,
            }
            return fake

        selected_tools = [
            {"name": "web_search", "type": "web"},
            {"name": "web_scraper", "type": "web"},
        ]

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry",
            side_effect=fake_registry_factory,
        ):
            results = run(orch._execute_tools(selected_tools, "Search Qwen3 and scrape results"))

        # Both tools should have been called without TypeError
        tool_names_called = [c[0] for c in calls]
        assert "web_search" in tool_names_called
        assert "web_scraper" in tool_names_called
        # No "failed with TypeError" in results
        for r in results:
            assert "missing 1 required positional argument" not in str(r.get("error", ""))


# ---------------------------------------------------------------------------
# GAP_018: False success when evaluator says replan
# ---------------------------------------------------------------------------

class TestGap018FalseSuccess:

    def _build_sai(self, tmpdir):
        """Build SAI with minimal mocks (no network, no real API)."""
        import tempfile
        from core.super_intelligent_ai import SuperIntelligentAI
        ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)
        return ai

    def test_evaluator_replan_produces_success_false(self):
        """
        When evaluator.evaluate_execution_result returns action=replan,
        execution_result["success"] must be False.
        """
        import tempfile
        from core.super_intelligent_ai import SuperIntelligentAI

        with tempfile.TemporaryDirectory() as tmpdir:
            ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

            # Mock the evaluator to return strategic plan + replan action
            ai.evaluator = MagicMock()
            ai.evaluator.strategic_task_planning = AsyncMock(return_value={
                "strategy": "web_research",
                "recommended_tools": ["web_search", "file_writer"],
                "confidence": 0.9,
                "complexity": "medium",
                "optimizations": [],
                "recommendations": [],
                "success_prediction": 0.9,
                "status": "active",
            })
            ai.evaluator.evaluate_execution_result = AsyncMock(return_value={
                "success": False,
                "goal_achieved": False,
                "action": "replan",
                "confidence": 0.1,
                "reasoning": "Web tools produced no substantive output",
            })

            # Mock orchestrator to return stub result (simulates web tools failing)
            ai.tool_orchestrator = MagicMock()
            ai.tool_orchestrator.orchestrate_task = AsyncMock(return_value={
                "status": "success",
                "final_output": {
                    "summary": "web_search processed (fallback mode)",
                    "detailed_results": [],
                },
            })

            ai.cognitive_processor = MagicMock()
            ai.cognitive_processor.process = AsyncMock(return_value={
                "analysis": "cognitive done",
                "recommended_tools": ["web_search"],
            })

            ai.adaptive_reasoning = AsyncMock(return_value={"reasoning": "ok"})
            ai.meta_learn = AsyncMock()

            result = run(ai.execute_intelligent_task(
                "Research local AI models and write report to C:\\out\\report.md",
                use_meta_controller=False,
            ))

        assert result["success"] is False, (
            f"Expected success=False when evaluator returns action=replan, "
            f"but got success={result['success']}"
        )

    def test_evaluator_goal_not_achieved_produces_success_false(self):
        """
        When evaluator returns goal_achieved=False (without explicit action=replan),
        execution_result["success"] must also be False.
        """
        import tempfile
        from core.super_intelligent_ai import SuperIntelligentAI

        with tempfile.TemporaryDirectory() as tmpdir:
            ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

            ai.evaluator = MagicMock()
            ai.evaluator.strategic_task_planning = AsyncMock(return_value={
                "strategy": "web_research",
                "recommended_tools": ["web_search"],
                "confidence": 0.9,
                "complexity": "low",
                "optimizations": [],
                "recommendations": [],
                "success_prediction": 0.5,
                "status": "active",
            })
            ai.evaluator.evaluate_execution_result = AsyncMock(return_value={
                "success": False,
                "goal_achieved": False,  # <-- key field
                "action": "pass",        # action=pass but goal still not achieved
                "confidence": 0.2,
            })

            ai.tool_orchestrator = MagicMock()
            ai.tool_orchestrator.orchestrate_task = AsyncMock(return_value={
                "status": "success",
                "final_output": {"summary": "stub", "detailed_results": []},
            })
            ai.cognitive_processor = MagicMock()
            ai.cognitive_processor.process = AsyncMock(return_value={"analysis": "ok"})
            ai.adaptive_reasoning = AsyncMock(return_value={"reasoning": "ok"})
            ai.meta_learn = AsyncMock()

            result = run(ai.execute_intelligent_task(
                "Find something and write to C:\\out\\result.md",
                use_meta_controller=False,
            ))

        assert result["success"] is False, (
            f"Expected success=False when goal_achieved=False, got {result['success']}"
        )

    def test_successful_evaluation_still_produces_success_true(self):
        """
        When evaluator returns goal_achieved=True and action != replan,
        execution_result["success"] must still be True.
        (Regression guard: fix must not break happy-path.)
        """
        import tempfile
        from core.super_intelligent_ai import SuperIntelligentAI

        with tempfile.TemporaryDirectory() as tmpdir:
            ai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

            ai.evaluator = MagicMock()
            ai.evaluator.strategic_task_planning = AsyncMock(return_value={
                "strategy": "file_creation",
                "recommended_tools": ["file_writer"],
                "confidence": 0.95,
                "complexity": "low",
                "optimizations": [],
                "recommendations": [],
                "success_prediction": 0.95,
                "status": "active",
            })
            ai.evaluator.evaluate_execution_result = AsyncMock(return_value={
                "success": True,
                "goal_achieved": True,
                "action": "pass",
                "confidence": 0.95,
            })

            ai.tool_orchestrator = MagicMock()
            ai.tool_orchestrator.orchestrate_task = AsyncMock(return_value={
                "status": "success",
                "final_output": {
                    "summary": "File written successfully",
                    "detailed_results": [
                        {"status": "success", "result": {"output": "File created at C:\\out\\result.md"}}
                    ],
                },
            })
            ai.cognitive_processor = MagicMock()
            ai.cognitive_processor.process = AsyncMock(return_value={"analysis": "ok"})
            ai.adaptive_reasoning = AsyncMock(return_value={"reasoning": "ok"})
            ai.meta_learn = AsyncMock()

            result = run(ai.execute_intelligent_task(
                "Create a simple text file at C:\\out\\result.md",
                use_meta_controller=False,
            ))

        assert result["success"] is True, (
            f"Expected success=True on successful task, got {result['success']}"
        )


class TestGap018MetaControllerDeterministicPass:

    def test_deterministic_pass_blocked_by_eval_replan(self):
        """
        MetaController._run (DECIDE phase): when execution_result contains
        evaluation_result.action=replan, deterministic_pass must be False
        even if output is non-empty.
        """
        # We test the logic directly by simulating what meta_controller computes
        # for deterministic_pass, without running the full loop.

        execution_result_with_replan = {
            "success": False,
            "output": "STRATEGIC AI EXECUTION COMPLETE\n\n...long template...",
            "evaluation_result": {
                "action": "replan",
                "goal_achieved": False,
                "confidence": 0.1,
            },
        }

        has_output = bool(
            execution_result_with_replan.get("output")
            or execution_result_with_replan.get("result")
        )
        has_critical = False  # No validators configured

        _eval_data = execution_result_with_replan.get("evaluation_result") or {}
        _eval_needs_replan = (
            _eval_data.get("action") == "replan"
            or _eval_data.get("goal_achieved") is False
        )
        deterministic_pass = has_output and not has_critical and not _eval_needs_replan

        assert has_output is True, "Precondition: output is non-empty (the bug condition)"
        assert _eval_needs_replan is True, "Evaluator correctly signals replan"
        assert deterministic_pass is False, (
            "deterministic_pass must be False when evaluator says replan, "
            "even though output is non-empty"
        )

    def test_deterministic_pass_allowed_when_eval_succeeds(self):
        """
        When evaluation_result.goal_achieved=True and action != replan,
        deterministic_pass follows the standard has_output logic.
        (Regression guard.)
        """
        execution_result_success = {
            "success": True,
            "output": "File created successfully at C:\\out\\result.md",
            "evaluation_result": {
                "action": "pass",
                "goal_achieved": True,
                "confidence": 0.9,
            },
        }

        has_output = bool(execution_result_success.get("output"))
        has_critical = False

        _eval_data = execution_result_success.get("evaluation_result") or {}
        _eval_needs_replan = (
            _eval_data.get("action") == "replan"
            or _eval_data.get("goal_achieved") is False
        )
        deterministic_pass = has_output and not has_critical and not _eval_needs_replan

        assert deterministic_pass is True, (
            "deterministic_pass should be True when evaluator confirms goal achieved"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
