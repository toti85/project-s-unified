"""
GAP_023 Tests — Browser Subtask Scope Isolation

Validates that:
1. In a mixed pipeline (accumulated prior-tool context in task_description),
   browser_automation receives a scoped browser-only subtask, NOT the full global mission.
2. The scoped subtask includes the browser-only role, no-file-write constraint,
   no-final-report constraint, and returns-findings instruction.
3. In a dedicated browser-only task (no prior tool context), the full task passes through unchanged.
4. The accumulated context marker [browser_automation result] is preserved in the return value
   so GAP_019 synthesis can consume it.
5. Existing GAP_021 and GAP_019 tests remain unaffected.
"""

import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator

# ─────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────

GLOBAL_MISSION = (
    "Research current 2026 browser automation and agentic web interaction tools using "
    "search plus real browser inspection where useful, then write a concise evidence-based "
    "markdown memo comparing at least 3 tools and recommending whether Project-S should "
    "treat browser automation as a primary or secondary capability. "
    "Write to: C:\\ProjectS-Unified\\reports\\GAP_023_LIVE_TEST.md"
)

PRIOR_TOOL_CONTEXT = (
    "[web_search result]:\n"
    "1. Playwright — Microsoft, cross-browser, Python/JS/TS API\n"
    "   URL: https://playwright.dev\n"
    "2. Puppeteer — Google, Chrome-only, NodeJS\n"
    "   URL: https://pptr.dev\n"
    "3. browser-use — open-source Python, LLM-driven browsing\n"
    "   URL: https://github.com/browser-use/browser-use\n"
)

MIXED_PIPELINE_TASK = (
    f"{GLOBAL_MISSION}\n\n"
    f"Context from previous tools:\n"
    f"{PRIOR_TOOL_CONTEXT}"
)

DEDICATED_BROWSER_TASK = (
    "Navigate to https://playwright.dev and extract the key capabilities listed on the homepage."
)


def make_orchestrator() -> SmartToolOrchestrator:
    return SmartToolOrchestrator()


# ─────────────────────────────────────────────────────────
# 1. Mixed pipeline — browser receives scoped subtask
# ─────────────────────────────────────────────────────────

class TestMixedPipelineScopeIsolation:
    @pytest.mark.asyncio
    async def test_browser_receives_scoped_task_not_global_mission(self):
        """
        In a mixed pipeline (task_description has 'Context from previous tools:'),
        browser_automation must NOT receive the raw full global task.
        It must receive a scoped browser subtask.
        """
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_browser_execute(task):
            captured_task.append(task)
            return {
                "success": True,
                "output": "Visited playwright.dev. Key fact: cross-browser automation.",
                "urls_visited": ["https://playwright.dev"],
            }

        mock_browser_tool = MagicMock()
        mock_browser_tool.execute = AsyncMock(side_effect=fake_browser_execute)

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry"
        ) as MockRegistry:
            mock_registry = MagicMock()
            mock_registry.tools = {"browser_automation": mock_browser_tool}
            MockRegistry.return_value = mock_registry

            await orch._execute_single_tool(
                {"name": "browser_automation"}, MIXED_PIPELINE_TASK
            )

        assert len(captured_task) == 1, "browser_automation.execute should be called exactly once"
        actual_task = captured_task[0]

        # Must NOT be the raw full pipeline task (which includes all accumulated context)
        assert actual_task != MIXED_PIPELINE_TASK, (
            "browser_automation received the raw full pipeline task — GAP_023 fix did not apply"
        )
        # Must NOT contain the accumulated prior-tool output (web_search results)
        # The scoped task should not pass raw upstream tool context to browser-use
        assert "[web_search result]" not in actual_task, (
            "browser_automation must NOT receive accumulated web_search context — "
            "it should only see the scoped browser subtask, not all prior tool output"
        )
        # Must include scope isolation marker (confirms GAP_023 fix ran)
        assert "mixed-pipeline" in actual_task.lower() or "scope isolation" in actual_task.lower() or "STRICT" in actual_task, (
            "Scoped task must include scope isolation language from the GAP_023 fix"
        )

    @pytest.mark.asyncio
    async def test_scoped_task_contains_browser_role_instruction(self):
        """Scoped task must declare browser-only role."""
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "findings"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, MIXED_PIPELINE_TASK)

        task = captured_task[0]
        assert "browser" in task.lower(), "Scoped task must contain browser role instruction"
        assert "YOUR ROLE" in task or "browser automation" in task.lower() or "navigate" in task.lower(), (
            "Scoped task must describe browser navigation role"
        )

    @pytest.mark.asyncio
    async def test_scoped_task_forbids_file_writing(self):
        """Scoped task must explicitly forbid file writing."""
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "findings"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, MIXED_PIPELINE_TASK)

        task = captured_task[0]
        # Constraint against file writing must appear in the scoped task
        assert (
            "write" in task.lower() and
            ("do not" in task.lower() or "don't" in task.lower() or "DO NOT" in task or "STRICT" in task)
        ), "Scoped task must explicitly forbid file writing"

    @pytest.mark.asyncio
    async def test_scoped_task_forbids_final_report_generation(self):
        """Scoped task must explicitly forbid generating the final report."""
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "findings"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, MIXED_PIPELINE_TASK)

        task = captured_task[0]
        assert "report" in task.lower(), "Scoped task must mention report (to forbid generating it)"
        assert (
            "do not" in task.lower() or "DO NOT" in task or "STRICT" in task
        ), "Scoped task must contain explicit constraint language"

    @pytest.mark.asyncio
    async def test_scoped_task_instructs_return_findings_for_downstream(self):
        """Scoped task must instruct browser to return findings for downstream synthesis."""
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "findings"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, MIXED_PIPELINE_TASK)

        task = captured_task[0]
        # Must mention downstream synthesis or findings return
        assert (
            "finding" in task.lower() or "downstream" in task.lower() or "synthesis" in task.lower()
        ), "Scoped task must instruct browser to return findings for downstream synthesis"

    @pytest.mark.asyncio
    async def test_scoped_task_preserves_original_research_context(self):
        """
        Scoped task must include a portion of the original mission so browser-use
        knows what topic to research (just not the full multi-step mission).
        """
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "findings"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, MIXED_PIPELINE_TASK)

        task = captured_task[0]
        # Must reference the actual research topic (browser automation tools)
        assert (
            "browser automation" in task.lower()
            or "2026" in task
            or "agentic" in task.lower()
        ), "Scoped task must preserve research topic context from the original mission"


# ─────────────────────────────────────────────────────────
# 2. Dedicated browser-only task — full task passes through
# ─────────────────────────────────────────────────────────

class TestDedicatedBrowserTaskPassthrough:
    @pytest.mark.asyncio
    async def test_dedicated_browser_task_passes_through_unchanged(self):
        """
        When there is no 'Context from previous tools:' in task_description,
        browser_automation should receive the full task unchanged.
        """
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "navigated to playwright.dev"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, DEDICATED_BROWSER_TASK)

        assert len(captured_task) == 1
        assert captured_task[0] == DEDICATED_BROWSER_TASK, (
            "Dedicated browser task must pass through to browser_automation unchanged"
        )

    @pytest.mark.asyncio
    async def test_dedicated_browser_task_not_scoped_when_no_prior_context(self):
        """No scope transformation should be applied when task has no prior tool context."""
        orch = make_orchestrator()
        captured_task: list = []

        async def fake_execute(task):
            captured_task.append(task)
            return {"success": True, "output": "result"}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            await orch._execute_single_tool({"name": "browser_automation"}, DEDICATED_BROWSER_TASK)

        # The scoped subtask header should NOT appear in a dedicated browser task
        task = captured_task[0]
        assert "Project-S mixed-pipeline scope isolation" not in task, (
            "Scope isolation must NOT apply to dedicated browser-only tasks"
        )
        assert "STRICT CONSTRAINTS" not in task, (
            "Constraint language must NOT be injected into dedicated browser-only tasks"
        )


# ─────────────────────────────────────────────────────────
# 3. Return value and accumulated context marker intact
# ─────────────────────────────────────────────────────────

class TestBrowserReturnValueIntact:
    @pytest.mark.asyncio
    async def test_browser_result_structure_returned(self):
        """
        The result dict from browser_automation must include success and output fields
        after the GAP_023 fix, so accumulated context piping (GAP_015) works correctly.
        """
        orch = make_orchestrator()

        fake_browser_output = (
            "Visited playwright.dev. Key findings:\n"
            "- Cross-browser support (Chrome, Firefox, Safari)\n"
            "- Python/JS/TS APIs available\n"
            "- GitHub stars: 67k+ as of 2026\n"
            "URL: https://playwright.dev"
        )

        async def fake_execute(task):
            return {"success": True, "output": fake_browser_output}

        mock_tool = MagicMock()
        mock_tool.execute = AsyncMock(side_effect=fake_execute)

        with patch("tools.tools.registry.tool_registry_golden.ToolRegistry") as MockReg:
            mr = MagicMock()
            mr.tools = {"browser_automation": mock_tool}
            MockReg.return_value = mr
            result = await orch._execute_single_tool(
                {"name": "browser_automation"}, MIXED_PIPELINE_TASK
            )

        assert result.get("success") is True, "Result must report success=True"
        assert "output" in result, "Result must have 'output' key"
        # Output must contain browser tool name (for accumulated context piping)
        outer_output = result.get("output", "")
        assert "browser_automation" in outer_output.lower() or fake_browser_output[:20] in outer_output, (
            "Result output must reference browser_automation for context piping"
        )
