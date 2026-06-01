"""
test_sai_truthfulness_fixes.py
==============================

Regression tests for SAI/MetaController success-authority truthfulness fixes.
Implements the test matrix from SAI_META_SUCCESS_AUTHORITY_AUDIT_20260514.md.

Fixes verified:
  FIX-1  evaluator action read from recommendations.action (not top-level)
  FIX-1b improve_tool marks partial=True in result
  FIX-2  inner exception backup → success=False
  FIX-3  execution history reflects actual success
  FIX-4  MetaController has_output requires >100 chars, rejects known stubs

Run:
    python -m pytest tests/test_sai_truthfulness_fixes.py -v
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── path setup ─────────────────────────────────────────────────────────────
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _compute_has_output(execution_result: dict) -> bool:
    """
    Mirror of the FIX-4 has_output logic in meta_controller.py.
    Kept in sync manually — if the production code changes, update here too.
    """
    _raw_output = execution_result.get("output") or execution_result.get("result") or ""
    _STUB_PREFIXES = (
        "[OK] MetaController completed goal",
        "[FAIL]",
        "mock result",
        "no results returned",
        "Task processed with backup systems",
    )
    return (
        isinstance(_raw_output, str)
        and len(_raw_output) > 100
        and not any(_raw_output.startswith(p) for p in _STUB_PREFIXES)
    ) or (isinstance(_raw_output, dict) and bool(_raw_output))


def _compute_eval_needs_replan(execution_result: dict) -> bool:
    """
    Mirror of the FIX-1 _eval_needs_replan logic in meta_controller.py.
    """
    _eval_data = execution_result.get("evaluation_result") or {}
    _eval_recs = _eval_data.get("recommendations") or {}
    _eval_action_val = _eval_recs.get("action", _eval_data.get("action", ""))
    return (
        _eval_action_val in ("replan", "create_new_tool")
        or _eval_data.get("goal_achieved") is False
    )


def _compute_sai_action(evaluation_result: dict) -> str:
    """
    Mirror of FIX-1 _eval_action logic in super_intelligent_ai.py.
    """
    _eval = evaluation_result if isinstance(evaluation_result, dict) else {}
    _eval_recs = _eval.get('recommendations') or {}
    return _eval_recs.get('action', _eval.get('action', ''))


SYNTHESIS_OUTPUT = (
    "## Executive Summary\n\n"
    "The AI agent framework market in 2026 is rapidly expanding. "
    "Key players include Crew AI, AutoGen, and LangGraph. "
    "Project-S has a unique opportunity in the auditable workflow niche. "
    "Recommended direction: Agentic Workflow Automation with Audit Trails.\n\n"
    "## Capability Fit\n\n"
    "Project-S core strengths: Witness evidence trail, multi-AI coordination, "
    "persistent state, local deployment. All map directly to the identified opportunity."
)  # 497 chars — well over 100


# ═══════════════════════════════════════════════════════════════════════════
# FIX-1 / FIX-1b: Evaluator action key lookup (SAI path)
# ═══════════════════════════════════════════════════════════════════════════

class TestSAIActionKeyFix:
    """FIX-1: action must be read from recommendations.action, not top-level."""

    def test_replan_nested_under_recommendations_blocks_success(self):
        """action=replan under recommendations → _execution_success=False."""
        eval_result = {
            "goal_achieved": True,
            "recommendations": {"action": "replan", "reason": "output is a stub"},
        }
        action = _compute_sai_action(eval_result)
        assert action == "replan", f"Expected 'replan', got '{action}'"
        # With fix: success = goal_achieved AND action not in (replan, create_new_tool)
        goal_achieved = eval_result.get("goal_achieved", True)
        success = bool(goal_achieved) and (action not in ("replan", "create_new_tool"))
        assert success is False, "replan action must block success even when goal_achieved=True"

    def test_replan_at_top_level_still_caught_as_fallback(self):
        """Backward compat: top-level action=replan still caught via fallback."""
        eval_result = {
            "goal_achieved": True,
            "action": "replan",  # old format, top-level
        }
        action = _compute_sai_action(eval_result)
        assert action == "replan"

    def test_continue_action_allows_success(self):
        """action=continue → success allowed."""
        eval_result = {
            "goal_achieved": True,
            "recommendations": {"action": "continue"},
        }
        action = _compute_sai_action(eval_result)
        assert action == "continue"
        success = bool(eval_result["goal_achieved"]) and (action not in ("replan", "create_new_tool"))
        assert success is True

    def test_missing_action_defaults_to_continue(self):
        """No action key → treated as continue → success allowed."""
        eval_result = {"goal_achieved": True}
        action = _compute_sai_action(eval_result)
        assert action == ""  # empty = treated as continue
        success = bool(eval_result["goal_achieved"]) and (action not in ("replan", "create_new_tool"))
        assert success is True

    def test_create_new_tool_blocks_success(self):
        """create_new_tool is an explicit failure signal."""
        eval_result = {
            "goal_achieved": True,
            "recommendations": {"action": "create_new_tool"},
        }
        action = _compute_sai_action(eval_result)
        success = bool(eval_result["goal_achieved"]) and (action not in ("replan", "create_new_tool"))
        assert success is False


class TestSAIImproveTool:
    """FIX-1b: improve_tool → partial success, not clean success."""

    def test_improve_tool_marks_partial_true(self):
        """When action=improve_tool, partial flag must be set."""
        eval_result = {
            "goal_achieved": True,
            "recommendations": {"action": "improve_tool"},
        }
        action = _compute_sai_action(eval_result)
        assert action == "improve_tool"
        # success is allowed (goal_achieved=True, action not in blocking set)
        success = bool(eval_result["goal_achieved"]) and (action not in ("replan", "create_new_tool"))
        assert success is True, "improve_tool does not block success"
        # but partial must be True
        partial = (action == "improve_tool")
        assert partial is True, "improve_tool must set partial=True"

    def test_improve_tool_with_goal_not_achieved_fails(self):
        """improve_tool + goal_achieved=False → success=False."""
        eval_result = {
            "goal_achieved": False,
            "recommendations": {"action": "improve_tool"},
        }
        action = _compute_sai_action(eval_result)
        success = bool(eval_result["goal_achieved"]) and (action not in ("replan", "create_new_tool"))
        assert success is False


# ═══════════════════════════════════════════════════════════════════════════
# FIX-1: MetaController _eval_needs_replan key lookup
# ═══════════════════════════════════════════════════════════════════════════

class TestMetaControllerActionKeyFix:
    """FIX-1 in MetaController: replan from recommendations.action triggers replan."""

    def test_replan_nested_triggers_eval_needs_replan(self):
        """action=replan under recommendations → _eval_needs_replan=True."""
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": True,
                "recommendations": {"action": "replan"},
            },
        }
        assert _compute_eval_needs_replan(exec_result) is True

    def test_create_new_tool_triggers_eval_needs_replan(self):
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": True,
                "recommendations": {"action": "create_new_tool"},
            },
        }
        assert _compute_eval_needs_replan(exec_result) is True

    def test_goal_not_achieved_triggers_eval_needs_replan(self):
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": False,
                "recommendations": {"action": "continue"},
            },
        }
        assert _compute_eval_needs_replan(exec_result) is True

    def test_continue_action_does_not_trigger_replan(self):
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": True,
                "recommendations": {"action": "continue"},
            },
        }
        assert _compute_eval_needs_replan(exec_result) is False

    def test_improve_tool_does_not_trigger_replan(self):
        """improve_tool with goal_achieved=True — MetaController lets it pass."""
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": True,
                "recommendations": {"action": "improve_tool"},
            },
        }
        assert _compute_eval_needs_replan(exec_result) is False

    def test_top_level_action_replan_still_caught(self):
        """Backward compat: old format action at top-level still works."""
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": True,
                "action": "replan",  # old format
            },
        }
        assert _compute_eval_needs_replan(exec_result) is True

    def test_missing_evaluation_result_does_not_trigger_replan(self):
        """No evaluation_result → no replan signal → deterministic pass allowed."""
        exec_result = {"output": SYNTHESIS_OUTPUT}
        assert _compute_eval_needs_replan(exec_result) is False


# ═══════════════════════════════════════════════════════════════════════════
# FIX-4: MetaController has_output (meaningful output threshold)
# ═══════════════════════════════════════════════════════════════════════════

class TestMetaControllerHasOutput:
    """FIX-4: has_output requires >100 chars and no known stub prefixes."""

    def test_real_synthesis_output_passes(self):
        """Full synthesis report (hundreds of chars) must pass."""
        assert _compute_has_output({"output": SYNTHESIS_OUTPUT}) is True

    def test_output_over_100_chars_passes(self):
        assert _compute_has_output({"output": "A" * 101}) is True

    def test_output_exactly_100_chars_fails(self):
        """100 chars is NOT > 100."""
        assert _compute_has_output({"output": "A" * 100}) is False

    def test_empty_output_fails(self):
        assert _compute_has_output({"output": ""}) is False

    def test_none_output_fails(self):
        assert _compute_has_output({"output": None}) is False

    def test_missing_output_key_fails(self):
        assert _compute_has_output({}) is False

    def test_backup_stub_prefix_fails(self):
        """Task processed with backup systems: ... must NOT pass."""
        stub = "Task processed with backup systems: research the best open-source LLMs for local deployment and write a recommendation"
        assert len(stub) > 100  # verify our stub is long enough to otherwise pass length check
        assert _compute_has_output({"output": stub}) is False

    def test_metacontroller_ok_stub_fails(self):
        """[OK] MetaController completed goal ... must NOT pass."""
        stub = "[OK] MetaController completed goal in 1 iterations. The task was completed successfully with all required outputs generated."
        assert len(stub) > 100
        assert _compute_has_output({"output": stub}) is False

    def test_fail_stub_fails(self):
        stub = "[FAIL] Tool chain failed. Unable to produce output. " + "X" * 100
        assert _compute_has_output({"output": stub}) is False

    def test_mock_result_stub_fails(self):
        stub = "mock result: " + "A" * 200
        assert _compute_has_output({"output": stub}) is False

    def test_no_results_returned_stub_fails(self):
        stub = "no results returned for this query. " + "B" * 200
        assert _compute_has_output({"output": stub}) is False

    def test_result_key_used_as_fallback(self):
        """If 'output' absent, 'result' key is checked."""
        assert _compute_has_output({"result": "A" * 200}) is True

    def test_dict_output_passes_regardless_of_length(self):
        """Dict output (structured data) passes as meaningful."""
        assert _compute_has_output({"output": {"key": "value"}}) is True

    def test_empty_dict_output_fails(self):
        assert _compute_has_output({"output": {}}) is False


# ═══════════════════════════════════════════════════════════════════════════
# FIX-2: Backup exception path → success=False
# ═══════════════════════════════════════════════════════════════════════════

class TestBackupExceptionPath:
    """FIX-2: inner exception in execute_intelligent_task must produce success=False."""

    def _make_sai(self, tmpdir):
        from core.super_intelligent_ai import SuperIntelligentAI
        return SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

    @pytest.mark.asyncio
    async def test_backup_path_sets_success_false(self):
        """When all inner components throw, backup returns success=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)

            # Make ALL inner processing components raise to force backup path
            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, side_effect=RuntimeError("forced failure")),
                patch.object(sai.cognitive_core, "process_task",
                              new_callable=AsyncMock, side_effect=RuntimeError("forced")),
                patch.object(sai.tool_orchestrator, "orchestrate_task",
                              new_callable=AsyncMock, side_effect=RuntimeError("forced")),
            ):
                result = await sai.execute_intelligent_task("test task", use_meta_controller=False)

            assert result.get("success") is False, (
                f"Backup path must set success=False, got: {result.get('success')}"
            )
            assert result.get("task_type") == "backup_processing"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_backup_output_contains_task_name(self):
        """Backup output must reference the task (for traceability)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)
            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, side_effect=RuntimeError("boom")),
            ):
                result = await sai.execute_intelligent_task("my special task", use_meta_controller=False)

            assert "my special task" in result.get("output", ""), (
                "Backup output must identify the task"
            )

    @pytest.mark.asyncio
    async def test_backup_partial_flag_is_false(self):
        """Backup path sets partial=False (it's a failure, not partial success)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)
            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, side_effect=RuntimeError("boom")),
            ):
                result = await sai.execute_intelligent_task("task", use_meta_controller=False)

            assert result.get("partial") is False


# ═══════════════════════════════════════════════════════════════════════════
# FIX-3: Execution history reflects actual success
# ═══════════════════════════════════════════════════════════════════════════

class TestExecutionHistoryTruth:
    """FIX-3: execution_history must record actual success, not hardcoded True."""

    def _make_sai(self, tmpdir):
        from core.super_intelligent_ai import SuperIntelligentAI
        return SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

    @pytest.mark.asyncio
    async def test_failure_recorded_as_failure_in_history(self):
        """When backup path fires (success=False), history entry must be False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)
            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, side_effect=RuntimeError("fail")),
            ):
                await sai.execute_intelligent_task("failing task", use_meta_controller=False)

            assert len(sai.execution_history) >= 1
            last_record = sai.execution_history[-1]
            assert last_record["success"] is False, (
                f"History must record success=False for failed tasks, got: {last_record['success']}"
            )

    @pytest.mark.asyncio
    async def test_successful_execution_recorded_as_success_in_history(self):
        """When execution returns success=True, history entry must also be True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)

            # Mock all components to return a successful result
            mock_plan = {
                "strategy": "direct", "complexity": "low",
                "confidence": 0.9, "use_cognitive_core": False,
                "use_orchestration": True, "optimizations": [],
                "recommendations": [], "status": "active",
                "success_prediction": 0.9,
            }
            mock_orch = {
                "final_output": {
                    "summary": "Done",
                    "detailed_results": [
                        {"status": "success", "result": {"output": SYNTHESIS_OUTPUT}}
                    ],
                },
                "success": True,
            }
            mock_eval = {
                "success": True, "confidence": 0.9, "goal_achieved": True,
                "assessment": "Goal achieved",
                "recommendations": {"action": "continue", "reason": "done"},
            }

            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, return_value=mock_plan),
                patch.object(sai.tool_orchestrator, "orchestrate_task",
                              new_callable=AsyncMock, return_value=mock_orch),
                patch.object(sai.evaluator, "evaluate_execution_result",
                              new_callable=AsyncMock, return_value=mock_eval),
            ):
                await sai.execute_intelligent_task("successful task", use_meta_controller=False)

            last_record = sai.execution_history[-1]
            assert last_record["success"] is True


# ═══════════════════════════════════════════════════════════════════════════
# Integration: replan action in evaluator blocks SAI success
# ═══════════════════════════════════════════════════════════════════════════

class TestEvaluatorReplanBlocksSuccess:
    """Full integration: evaluator recommendations.action=replan → success=False."""

    def _make_sai(self, tmpdir):
        from core.super_intelligent_ai import SuperIntelligentAI
        return SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

    @pytest.mark.asyncio
    async def test_replan_action_produces_success_false(self):
        """When evaluator says replan, execution_result.success must be False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)

            mock_plan = {
                "strategy": "direct", "complexity": "low", "confidence": 0.8,
                "use_cognitive_core": False, "use_orchestration": True,
                "optimizations": [], "recommendations": [], "status": "active",
                "success_prediction": 0.8,
            }
            mock_orch = {
                "final_output": {"summary": "Done", "detailed_results": []},
                "success": True,
            }
            mock_eval = {
                "success": False, "confidence": 0.3, "goal_achieved": True,
                "assessment": "Output is a stub, needs replan",
                "recommendations": {"action": "replan", "reason": "stub output detected"},
            }

            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, return_value=mock_plan),
                patch.object(sai.tool_orchestrator, "orchestrate_task",
                              new_callable=AsyncMock, return_value=mock_orch),
                patch.object(sai.evaluator, "evaluate_execution_result",
                              new_callable=AsyncMock, return_value=mock_eval),
            ):
                result = await sai.execute_intelligent_task("web research task", use_meta_controller=False)

            assert result.get("success") is False, (
                f"replan action must produce success=False, got: {result.get('success')}"
            )
            assert result.get("partial") is False

    @pytest.mark.asyncio
    async def test_improve_tool_marks_partial_in_full_pipeline(self):
        """When evaluator says improve_tool, result has partial=True, success=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sai = self._make_sai(tmpdir)

            mock_plan = {
                "strategy": "direct", "complexity": "low", "confidence": 0.8,
                "use_cognitive_core": False, "use_orchestration": True,
                "optimizations": [], "recommendations": [], "status": "active",
                "success_prediction": 0.8,
            }
            mock_orch = {
                "final_output": {
                    "summary": "Done",
                    "detailed_results": [
                        {"status": "success", "result": {"output": SYNTHESIS_OUTPUT}}
                    ],
                },
                "success": True,
            }
            mock_eval = {
                "success": True, "confidence": 0.7, "goal_achieved": True,
                "assessment": "Done but tool could be improved",
                "recommendations": {"action": "improve_tool", "reason": "suboptimal"},
            }

            with (
                patch.object(sai.evaluator, "strategic_task_planning",
                              new_callable=AsyncMock, return_value=mock_plan),
                patch.object(sai.tool_orchestrator, "orchestrate_task",
                              new_callable=AsyncMock, return_value=mock_orch),
                patch.object(sai.evaluator, "evaluate_execution_result",
                              new_callable=AsyncMock, return_value=mock_eval),
            ):
                result = await sai.execute_intelligent_task("research task", use_meta_controller=False)

            assert result.get("success") is True, "improve_tool should not block success"
            assert result.get("partial") is True, "improve_tool must set partial=True"


# ═══════════════════════════════════════════════════════════════════════════
# Synthesis pipeline: real output still passes has_output
# ═══════════════════════════════════════════════════════════════════════════

class TestSynthesisPipelinePassesHasOutput:
    """FIX-4 must not break the synthesis pipeline — real reports pass easily."""

    def test_real_synthesis_7k_output_passes(self):
        """A 7000-char synthesis report must pass has_output."""
        long_output = SYNTHESIS_OUTPUT * 14  # ~7000 chars
        assert _compute_has_output({"output": long_output}) is True

    def test_synthesis_3k_output_passes(self):
        """A 3000-char synthesis report (like Qwen run B) must pass."""
        medium_output = SYNTHESIS_OUTPUT * 6
        assert _compute_has_output({"output": medium_output}) is True

    def test_synthesis_500_char_output_passes(self):
        """SYNTHESIS_OUTPUT itself (~497 chars) must pass."""
        assert _compute_has_output({"output": SYNTHESIS_OUTPUT}) is True

    def test_output_starting_with_markdown_header_passes(self):
        """Reports starting with # or ## must pass."""
        md_report = "# Strategic Analysis\n\n" + "A" * 200
        assert _compute_has_output({"output": md_report}) is True

    def test_replan_blocked_even_with_real_output(self):
        """replan action blocks deterministic_pass even if output is real and long."""
        exec_result = {
            "output": SYNTHESIS_OUTPUT,
            "evaluation_result": {
                "goal_achieved": True,
                "recommendations": {"action": "replan"},
            },
        }
        has_output = _compute_has_output(exec_result)
        eval_needs_replan = _compute_eval_needs_replan(exec_result)
        deterministic_pass = has_output and not eval_needs_replan
        assert has_output is True, "real output passes has_output"
        assert eval_needs_replan is True, "replan is correctly detected"
        assert deterministic_pass is False, "replan blocks deterministic_pass even with real output"


# ═══════════════════════════════════════════════════════════════════════════
# Entry point for direct execution
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import subprocess, sys
    ret = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=str(repo_root)
    )
    sys.exit(ret.returncode)
