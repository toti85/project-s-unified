"""
GAP_022 — Evaluator JSON serialization fix tests.

Verifies that:
1. AgentHistoryList or representative non-serializable stub no longer causes evaluator failure
2. Sanitized result remains usable / non-empty
3. Ordinary JSON-native execution results remain unchanged
4. Serialization helper does not convert normal dict/list data unnecessarily
5. Evaluator path completes without TypeError
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.evaluator import Evaluator


# --- Representative non-serializable object mimicking browser_use.AgentHistoryList ---

class AgentHistoryList:
    """Mimics browser_use.AgentHistoryList — not JSON-serializable by default."""
    def __init__(self, history_items):
        self._items = history_items

    def __str__(self):
        return f"AgentHistoryList({len(self._items)} items)"

    def __repr__(self):
        return f"AgentHistoryList({self._items})"


class TestSanitizeForJson:
    """Tests for _sanitize_for_json helper method."""

    def setup_method(self):
        self.evaluator = Evaluator()

    def test_dict_with_non_serializable_leaf(self):
        """Non-serializable leaf value is converted to string."""
        obj = {
            "status": "success",
            "browser_history": AgentHistoryList(["page1", "page2"]),
            "count": 42
        }
        result = self.evaluator._sanitize_for_json(obj)
        assert result["status"] == "success"
        assert result["count"] == 42
        assert isinstance(result["browser_history"], str)
        assert "AgentHistoryList" in result["browser_history"]
        assert "non-serializable" in result["browser_history"]

    def test_list_with_non_serializable_item(self):
        """Non-serializable item in list is converted to string."""
        obj = [
            "normal_string",
            AgentHistoryList(["item1"]),
            123
        ]
        result = self.evaluator._sanitize_for_json(obj)
        assert result[0] == "normal_string"
        assert result[2] == 123
        assert isinstance(result[1], str)
        assert "AgentHistoryList" in result[1]

    def test_nested_dict_with_non_serializable(self):
        """Deeply nested non-serializable values are all converted."""
        obj = {
            "level1": {
                "level2": {
                    "browser_data": AgentHistoryList([]),
                    "normal": "value"
                }
            }
        }
        result = self.evaluator._sanitize_for_json(obj)
        assert result["level1"]["level2"]["normal"] == "value"
        assert isinstance(result["level1"]["level2"]["browser_data"], str)

    def test_normal_dict_unchanged(self):
        """Normal JSON-native dict is not modified."""
        obj = {
            "status": "success",
            "count": 42,
            "nested": {"key": "value"},
            "list": [1, 2, 3]
        }
        result = self.evaluator._sanitize_for_json(obj)
        assert result == obj

    def test_normal_list_unchanged(self):
        """Normal JSON-native list is not modified."""
        obj = [1, "string", True, None, {"key": "value"}, [1, 2]]
        result = self.evaluator._sanitize_for_json(obj)
        assert result == obj

    def test_string_value_preserved(self):
        """String values are preserved as-is."""
        obj = {"message": "hello world"}
        result = self.evaluator._sanitize_for_json(obj)
        assert result["message"] == "hello world"

    def test_number_values_preserved(self):
        """Numeric values are preserved as-is."""
        obj = {"int_val": 42, "float_val": 3.14, "neg": -10}
        result = self.evaluator._sanitize_for_json(obj)
        assert result["int_val"] == 42
        assert result["float_val"] == 3.14
        assert result["neg"] == -10

    def test_bool_and_none_preserved(self):
        """Boolean and None values are preserved."""
        obj = {"flag": True, "nothing": None, "other_flag": False}
        result = self.evaluator._sanitize_for_json(obj)
        assert result["flag"] is True
        assert result["nothing"] is None
        assert result["other_flag"] is False

    def test_truncation_of_long_repr(self):
        """Very long non-serializable objects are truncated to 500 chars."""
        class LongObj:
            def __str__(self):
                return "x" * 10000
        obj = {"data": LongObj()}
        result = self.evaluator._sanitize_for_json(obj)
        assert len(result["data"]) <= 500 + len("[non-serializable: LongObj] ")


class TestBuildEvaluationPromptWithSanitization:
    """Tests that _build_evaluation_prompt works with non-serializable execution results."""

    def setup_method(self):
        self.evaluator = Evaluator()

    def test_prompt_builds_with_agent_history_list(self):
        """Prompt builds successfully even when execution_result contains AgentHistoryList."""
        execution_result = {
            "status": "success",
            "browser_history": AgentHistoryList([
                {"url": "https://playwright.dev", "title": "Playwright"},
                {"url": "https://github.com/browser-use/browser-use", "title": "browser-use"}
            ]),
            "pages_visited": 2,
            "execution_time_ms": 94300
        }
        # This should NOT raise TypeError
        prompt = self.evaluator._build_evaluation_prompt(
            original_goal="Test browser automation",
            tool_used="browser_automation",
            tool_params={"urls": ["https://playwright.dev"]},
            execution_result=execution_result,
            context=None
        )
        assert "EVALUATION REQUEST" in prompt
        assert "Test browser automation" in prompt
        assert "browser_automation" in prompt
        # The sanitized AgentHistoryList should appear as a string
        assert "AgentHistoryList" in prompt or "non-serializable" in prompt

    def test_prompt_builds_with_normal_result(self):
        """Normal execution results still work correctly."""
        execution_result = {
            "status": "success",
            "content": "Page content here",
            "length": 1234
        }
        prompt = self.evaluator._build_evaluation_prompt(
            original_goal="Fetch page content",
            tool_used="web_page_fetch",
            tool_params={"url": "https://example.com"},
            execution_result=execution_result,
            context=None
        )
        assert "EVALUATION REQUEST" in prompt
        assert "Page content here" in prompt
        assert "1234" in prompt

    def test_prompt_builds_with_context_containing_non_serializable(self):
        """Context with non-serializable values is also sanitized."""
        execution_result = {"status": "ok"}
        context = {
            "extra_info": AgentHistoryList(["context_item"]),
            "normal_key": "normal_value"
        }
        prompt = self.evaluator._build_evaluation_prompt(
            original_goal="Test",
            tool_used="test_tool",
            tool_params={},
            execution_result=execution_result,
            context=context
        )
        assert "EVALUATION REQUEST" in prompt
        assert "normal_value" in prompt
        assert "AgentHistoryList" in prompt or "non-serializable" in prompt


class TestSafeJsonSerialize:
    """Tests for _safe_json_serialize helper method."""

    def setup_method(self):
        self.evaluator = Evaluator()

    def test_normal_dict_serializes(self):
        """Normal dict serializes to JSON string."""
        obj = {"key": "value", "num": 42}
        result = self.evaluator._safe_json_serialize(obj)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == obj

    def test_non_serializable_object_falls_back_to_str(self):
        """Non-serializable object falls back to str()."""
        obj = AgentHistoryList(["test"])
        result = self.evaluator._safe_json_serialize(obj)
        assert isinstance(result, str)
        assert "AgentHistoryList" in result

    def test_nested_with_non_serializable(self):
        """Nested structure with non-serializable inner value."""
        obj = {
            "status": "ok",
            "history": AgentHistoryList([])
        }
        result = self.evaluator._safe_json_serialize(obj)
        assert isinstance(result, str)
        # Should not raise


class TestEndToEndEvaluationPath:
    """End-to-end test that the evaluation path completes without TypeError."""

    def setup_method(self):
        self.evaluator = Evaluator()

    def test_evaluation_path_no_typeerror_with_agent_history(self):
        """The full _build_evaluation_prompt path completes without TypeError."""
        execution_result = {
            "status": "success",
            "browser_history": AgentHistoryList([
                {"url": "https://example.com", "title": "Example"}
            ]),
            "pages": 1,
            "time_ms": 5000
        }
        # This is the exact path that was failing before GAP_022 fix
        safe_result = self.evaluator._sanitize_for_json(execution_result)
        prompt = self.evaluator._build_evaluation_prompt(
            original_goal="Visit example.com",
            tool_used="browser_automation",
            tool_params={},
            execution_result=safe_result,
            context=None
        )
        # Verify prompt is buildable and contains key info
        assert "EVALUATION REQUEST" in prompt
        assert "Visit example.com" in prompt
        # Verify the sanitized data is present
        assert "success" in prompt
        # Verify json.dumps on the sanitized result works
        json.dumps(safe_result)  # Should NOT raise


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])