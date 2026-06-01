"""
GAP_019 Synthesis Step — Focused Tests

Validates that:
1. _is_synthesis_task() triggers for web_search + report tasks
2. Synthesized content is passed to file_writer (not raw dumps)
3. No synthesis for ordinary file write tasks (no web markers)
4. Synthesis failure produces PARTIAL fallback, not clean success
"""

import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Make sure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tools.registry.smart_orchestrator import SmartToolOrchestrator


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def make_orchestrator() -> SmartToolOrchestrator:
    return SmartToolOrchestrator()


WEB_CONTEXT = (
    "[web_search result]:\n"
    "1. Qwen3-235B — Apache 2.0, SWE-bench 73.4%, vRAM ~48 GB\n"
    "2. DeepSeek-R2 — MIT, SWE-bench 71.2%, vRAM ~80 GB\n"
    "[web_scraper result]:\n"
    "Source: https://example.com/llm-bench  "
    "Qwen3 released 2025-04, DeepSeek-R2 released 2025-06\n"
)

PLAIN_CONTEXT = (
    "[file_reader result]:\n"
    "File /tmp/notes.txt contains: Hello World\n"
)

REPORT_TASK = (
    "Research the best open-source LLMs for local deployment and write a "
    "recommendation report to C:\\Reports\\llm_report.md"
)

PLAIN_TASK = (
    "Write the string 'Hello World' to C:\\tmp\\notes.txt"
)


# ─────────────────────────────────────────────────────────
# 1. _is_synthesis_task triggers for web + report task
# ─────────────────────────────────────────────────────────

class TestIsSynthesisTask:
    def test_triggers_for_web_search_plus_report_keyword(self):
        orch = make_orchestrator()
        assert orch._is_synthesis_task(REPORT_TASK, WEB_CONTEXT) is True

    def test_triggers_for_write_keyword(self):
        orch = make_orchestrator()
        task = "Write a comparison report on local LLMs and save to C:\\out.md"
        assert orch._is_synthesis_task(task, WEB_CONTEXT) is True

    def test_triggers_for_recommendation_keyword(self):
        orch = make_orchestrator()
        task = "Give a recommendation based on the web data and save to C:\\rec.md"
        assert orch._is_synthesis_task(task, WEB_CONTEXT) is True

    def test_no_trigger_without_web_markers(self):
        """Plain context (no web results) must NOT trigger synthesis."""
        orch = make_orchestrator()
        assert orch._is_synthesis_task(REPORT_TASK, PLAIN_CONTEXT) is False

    def test_no_trigger_for_plain_write_task(self):
        """Ordinary file write without web data must NOT trigger synthesis."""
        orch = make_orchestrator()
        assert orch._is_synthesis_task(PLAIN_TASK, PLAIN_CONTEXT) is False

    def test_no_trigger_keyword_but_no_web_data(self):
        """Task has report keyword but context has no web markers."""
        orch = make_orchestrator()
        assert orch._is_synthesis_task(REPORT_TASK, "") is False

    def test_no_trigger_web_data_but_no_report_keyword(self):
        """Context has web data but task keyword is not research/report."""
        orch = make_orchestrator()
        task = "Delete all temp files in C:\\tmp"
        assert orch._is_synthesis_task(task, WEB_CONTEXT) is False


# ─────────────────────────────────────────────────────────
# 2. file_writer passes synthesised content when synthesis succeeds
# ─────────────────────────────────────────────────────────

SYNTHESIZED_MARKDOWN = (
    "# LLM Local Deployment Report\n\n"
    "## Overview\nTwo leading open-source models evaluated.\n\n"
    "## Comparison Table\n| Model | SWE-bench | vRAM |\n"
    "|-------|-----------|------|\n"
    "| Qwen3-235B | 73.4% | 48 GB |\n"
    "| DeepSeek-R2 | 71.2% | 80 GB |\n\n"
    "## Confirmed Facts\n- Qwen3 released 2025-04 (source: example.com)\n\n"
    "## Recommendation\nUse Qwen3-235B for lower vRAM footprint.\n\n"
    "## Sources\n- https://example.com/llm-bench\n"
)


class TestSynthesisPassedToFileWriter:
    @pytest.mark.asyncio
    async def test_synthesized_markdown_is_written(self):
        """When synthesis succeeds, file_writer receives synthesized content."""
        orch = make_orchestrator()

        written_content: list = []

        # Mock real_tool (FileWriteTool)
        mock_file_tool = MagicMock()
        mock_file_tool.execute = AsyncMock(return_value={"success": True, "output": "written"})
        mock_file_tool.execute.side_effect = lambda path, content: (
            written_content.append(content) or {"success": True, "output": "written"}
        )

        # Stub: _synthesize_web_results returns a clean report
        orch._synthesize_web_results = AsyncMock(return_value=SYNTHESIZED_MARKDOWN)

        task_description = (
            f"{REPORT_TASK}\n\n"
            f"Context from previous tools:\n{WEB_CONTEXT}"
        )

        tool_input = {"name": "file_writer"}

        with patch(
            "tools.tools.registry.smart_orchestrator.SmartToolOrchestrator."
            "_execute_single_tool",
            wraps=orch._execute_single_tool,
        ):
            # Patch ToolRegistry to return our mock file tool
            with patch(
                "tools.tools.registry.tool_registry_golden.ToolRegistry"
            ) as MockRegistry:
                mock_registry_inst = MagicMock()
                mock_registry_inst.tools = {"file_writer": mock_file_tool}
                MockRegistry.return_value = mock_registry_inst

                await orch._execute_single_tool(tool_input, task_description)

        # The content written must be the synthesized markdown, not a raw dump
        assert len(written_content) == 1
        written = written_content[0]
        assert "## Comparison Table" in written, "Synthesized report should contain comparison table"
        assert "## Confirmed Facts" in written, "Synthesized report should contain confirmed facts"
        assert "## Sources" in written, "Synthesized report should contain sources"
        assert "[web_search result]" not in written, "Raw web markers must not appear in final output"


# ─────────────────────────────────────────────────────────
# 3. No synthesis for ordinary file write tasks
# ─────────────────────────────────────────────────────────

class TestNoSynthesisForPlainTasks:
    @pytest.mark.asyncio
    async def test_plain_write_skips_synthesis(self):
        """Ordinary file write (no web data) must not call _synthesize_web_results."""
        orch = make_orchestrator()
        orch._synthesize_web_results = AsyncMock(return_value=SYNTHESIZED_MARKDOWN)

        task_description = (
            f"{PLAIN_TASK}\n\n"
            f"Context from previous tools:\n{PLAIN_CONTEXT}"
        )

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry"
        ) as MockRegistry:
            mock_file_tool = MagicMock()
            mock_file_tool.execute = AsyncMock(return_value={"success": True, "output": "ok"})
            mock_registry_inst = MagicMock()
            mock_registry_inst.tools = {"file_writer": mock_file_tool}
            MockRegistry.return_value = mock_registry_inst

            await orch._execute_single_tool({"name": "file_writer"}, task_description)

        orch._synthesize_web_results.assert_not_called()


# ─────────────────────────────────────────────────────────
# 4. Synthesis failure → PARTIAL fallback, not clean success
# ─────────────────────────────────────────────────────────

class TestSynthesisFailureFallback:
    @pytest.mark.asyncio
    async def test_failure_writes_partial_fallback(self):
        """When synthesis returns None, a PARTIAL report is written and success=False."""
        orch = make_orchestrator()
        # Synthesis returns None → failure
        orch._synthesize_web_results = AsyncMock(return_value=None)

        written_content: list = []
        returned_results: list = []

        async def fake_file_execute(path, content):
            written_content.append(content)
            return {"success": True, "output": "written"}

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry"
        ) as MockRegistry:
            mock_file_tool = MagicMock()
            mock_file_tool.execute = AsyncMock(side_effect=fake_file_execute)
            mock_registry_inst = MagicMock()
            mock_registry_inst.tools = {"file_writer": mock_file_tool}
            MockRegistry.return_value = mock_registry_inst

            task_description = (
                f"{REPORT_TASK}\n\n"
                f"Context from previous tools:\n{WEB_CONTEXT}"
            )
            result = await orch._execute_single_tool(
                {"name": "file_writer"}, task_description
            )
            returned_results.append(result)

        assert len(written_content) == 1
        written = written_content[0]
        # Must clearly label as partial
        assert "PARTIAL" in written.upper(), "Fallback must contain PARTIAL label"
        # Must include raw data for debugging
        assert "web_search" in written or "Raw" in written

        # The returned result must not claim clean success
        final_result = returned_results[0]
        # Either the inner result or the outer wrapper should signal failure
        inner = final_result.get("real_result", {}) if isinstance(final_result, dict) else {}
        outer_success = final_result.get("success", True) if isinstance(final_result, dict) else True
        inner_success = inner.get("success", True) if isinstance(inner, dict) else True
        assert not outer_success or not inner_success, (
            "Result must not report clean success when synthesis failed"
        )

    @pytest.mark.asyncio
    async def test_failure_does_not_silently_pass_raw_dump_as_synthesized(self):
        """Raw tool dump must NEVER appear as the primary synthesised content when synthesis fails."""
        orch = make_orchestrator()
        orch._synthesize_web_results = AsyncMock(return_value=None)

        written_content: list = []

        async def fake_file_execute(path, content):
            written_content.append(content)
            return {"success": True, "output": "written"}

        with patch(
            "tools.tools.registry.tool_registry_golden.ToolRegistry"
        ) as MockRegistry:
            mock_file_tool = MagicMock()
            mock_file_tool.execute = AsyncMock(side_effect=fake_file_execute)
            mock_registry_inst = MagicMock()
            mock_registry_inst.tools = {"file_writer": mock_file_tool}
            MockRegistry.return_value = mock_registry_inst

            task_description = (
                f"{REPORT_TASK}\n\n"
                f"Context from previous tools:\n{WEB_CONTEXT}"
            )
            await orch._execute_single_tool({"name": "file_writer"}, task_description)

        written = written_content[0]
        # The file must not look like a clean synthesised report (no Comparison Table, no
        # Confirmed Facts) — it should be the PARTIAL fallback label instead
        assert "# LLM Local Deployment Report" not in written


# ─────────────────────────────────────────────────────────
# 5. Synthesis model selection — default and override
#    (Added 2026-05-14: verifies Qwen3.6 runtime default alignment fix)
# ─────────────────────────────────────────────────────────

class TestSynthesisModelSelection:
    """
    Verifies that:
    - When _synthesis_model_override is None (default), Qwen3.6 is used.
    - When _synthesis_model_override is set, it wins over the default.
    - Override is isolated to the run (class variable can be reset).
    """

    @pytest.mark.asyncio
    async def test_no_override_uses_qwen36_default(self):
        """With no override set, synthesis must select qwen/qwen3.6-35b-a3b."""
        # Ensure no override from a prior test
        SmartToolOrchestrator._synthesis_model_override = None

        orch = SmartToolOrchestrator()
        captured_model: list = []

        async def fake_generate(prompt, model, **kwargs):
            captured_model.append(model)
            return "# Synthesised Report\n\n## Overview\nTest.\n"

        from unittest.mock import AsyncMock as _AsyncMock, MagicMock as _MagicMock, patch as _patch

        mock_ai_client = _MagicMock()
        mock_ai_client.generate_response = _AsyncMock(side_effect=fake_generate)

        with _patch(
            "src.integrations.ai_models.multi_model_ai_client.AIClient",
            return_value=mock_ai_client,
        ):
            result = await orch._synthesize_web_results(
                original_task=REPORT_TASK,
                tool_context=WEB_CONTEXT,
                file_path="C:\\tmp\\test_out.md",
            )

        assert len(captured_model) == 1, "AIClient.generate_response should be called once"
        assert captured_model[0] == "qwen/qwen3.6-35b-a3b", (
            f"Expected qwen/qwen3.6-35b-a3b as default synthesis model, got: {captured_model[0]}"
        )
        assert result is not None, "Synthesis should return content"

    @pytest.mark.asyncio
    async def test_explicit_override_wins(self):
        """When _synthesis_model_override is set, it overrides the qwen3.6 default."""
        SmartToolOrchestrator._synthesis_model_override = "openai/gpt-4o-mini"

        orch = SmartToolOrchestrator()
        captured_model: list = []

        async def fake_generate(prompt, model, **kwargs):
            captured_model.append(model)
            return "# Synthesised Report\n\n## Overview\nOverride test.\n"

        from unittest.mock import AsyncMock as _AsyncMock, MagicMock as _MagicMock, patch as _patch

        mock_ai_client = _MagicMock()
        mock_ai_client.generate_response = _AsyncMock(side_effect=fake_generate)

        try:
            with _patch(
                "src.integrations.ai_models.multi_model_ai_client.AIClient",
                return_value=mock_ai_client,
            ):
                result = await orch._synthesize_web_results(
                    original_task=REPORT_TASK,
                    tool_context=WEB_CONTEXT,
                    file_path="C:\\tmp\\test_out.md",
                )
        finally:
            # Always reset override after test to avoid polluting other tests
            SmartToolOrchestrator._synthesis_model_override = None

        assert len(captured_model) == 1, "AIClient.generate_response should be called once"
        assert captured_model[0] == "openai/gpt-4o-mini", (
            f"Expected override model openai/gpt-4o-mini, got: {captured_model[0]}"
        )
        assert result is not None, "Synthesis should return content"

    @pytest.mark.asyncio
    async def test_override_reset_restores_default(self):
        """After resetting _synthesis_model_override to None, default (Qwen3.6) is restored."""
        SmartToolOrchestrator._synthesis_model_override = "openai/gpt-4o-mini"
        SmartToolOrchestrator._synthesis_model_override = None  # reset

        orch = SmartToolOrchestrator()
        captured_model: list = []

        async def fake_generate(prompt, model, **kwargs):
            captured_model.append(model)
            return "# Report\n\n## Overview\nReset test.\n"

        from unittest.mock import AsyncMock as _AsyncMock, MagicMock as _MagicMock, patch as _patch

        mock_ai_client = _MagicMock()
        mock_ai_client.generate_response = _AsyncMock(side_effect=fake_generate)

        with _patch(
            "src.integrations.ai_models.multi_model_ai_client.AIClient",
            return_value=mock_ai_client,
        ):
            await orch._synthesize_web_results(
                original_task=REPORT_TASK,
                tool_context=WEB_CONTEXT,
                file_path="C:\\tmp\\test_out.md",
            )

        assert captured_model[0] == "qwen/qwen3.6-35b-a3b", (
            f"Expected qwen3.6 after reset, got: {captured_model[0]}"
        )
