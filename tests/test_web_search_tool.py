"""
Tests for WebSearchTool DDGS backend (GAP_017 follow-up).

Covers:
- query passed correctly to _ddgs_search
- result schema normalisation (href → url, body → description)
- zero-results path (success=True, count=0)
- backend exception path (success=False, error key present)
- malformed result objects (missing keys handled gracefully)
"""
import asyncio
import pytest
from unittest.mock import MagicMock, patch


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_tool():
    from tools.tools.implementations.web_tools import WebSearchTool
    return WebSearchTool()


# ---------------------------------------------------------------------------
# Query forwarding
# ---------------------------------------------------------------------------

class TestWebSearchQuery:
    def test_query_passed_to_ddgs(self):
        """_ddgs_search is called with the exact query string."""
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=[]) as mock_search:
            run(tool.execute(query="Llama 4 Scout benchmark", max_results=5))
        mock_search.assert_called_once_with("Llama 4 Scout benchmark", 5)

    def test_max_results_forwarded(self):
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=[]) as mock_search:
            run(tool.execute(query="test", max_results=10))
        mock_search.assert_called_once_with("test", 10)


# ---------------------------------------------------------------------------
# Result schema normalisation
# ---------------------------------------------------------------------------

class TestWebSearchSchema:
    """Verify the returned dict matches the schema the orchestrator expects."""

    _DDGS_ROWS = [
        {"title": "Title A", "href": "https://example.com/a", "body": "Snippet A"},
        {"title": "Title B", "href": "https://example.com/b", "body": "Snippet B"},
    ]

    def test_top_level_keys(self):
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=self._DDGS_ROWS):
            r = run(tool.execute(query="q", max_results=5))
        assert r["success"] is True
        assert "query" in r
        assert "results" in r
        assert "count" in r

    def test_result_item_keys(self):
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=self._DDGS_ROWS):
            r = run(tool.execute(query="q", max_results=5))
        assert r["count"] == 2
        item = r["results"][0]
        assert "title" in item
        assert "url" in item          # href → url
        assert "description" in item  # body → description

    def test_href_mapped_to_url(self):
        tool = _make_tool()
        row = {"title": "T", "href": "https://example.com/x", "body": "B"}
        with patch.object(tool, "_ddgs_search", return_value=[row]):
            r = run(tool.execute(query="q", max_results=1))
        assert r["results"][0]["url"] == "https://example.com/x"

    def test_body_mapped_to_description(self):
        tool = _make_tool()
        row = {"title": "T", "href": "https://example.com/x", "body": "My snippet"}
        with patch.object(tool, "_ddgs_search", return_value=[row]):
            r = run(tool.execute(query="q", max_results=1))
        assert r["results"][0]["description"] == "My snippet"

    def test_query_echoed_in_result(self):
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=self._DDGS_ROWS):
            r = run(tool.execute(query="my_query", max_results=5))
        assert r["query"] == "my_query"


# ---------------------------------------------------------------------------
# Zero-results path
# ---------------------------------------------------------------------------

class TestWebSearchZeroResults:
    def test_empty_list_success_true(self):
        """If DDGS returns [], result is success=True with count=0 (not an error)."""
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=[]):
            r = run(tool.execute(query="q", max_results=5))
        assert r["success"] is True
        assert r["count"] == 0
        assert r["results"] == []

    def test_none_backend_result_is_failure(self):
        """If _ddgs_search returns None (exception inside), report failure."""
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=None):
            r = run(tool.execute(query="q", max_results=5))
        assert r["success"] is False
        assert "error" in r


# ---------------------------------------------------------------------------
# Exception path
# ---------------------------------------------------------------------------

class TestWebSearchException:
    def test_backend_exception_returns_failure(self):
        """If _ddgs_search raises, execute() catches and returns success=False."""
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", side_effect=RuntimeError("network down")):
            r = run(tool.execute(query="q", max_results=5))
        assert r["success"] is False
        assert "error" in r

    def test_error_key_present_on_failure(self):
        tool = _make_tool()
        with patch.object(tool, "_ddgs_search", return_value=None):
            r = run(tool.execute(query="q", max_results=5))
        assert "error" in r
        assert len(r["error"]) > 0


# ---------------------------------------------------------------------------
# Malformed result objects
# ---------------------------------------------------------------------------

class TestWebSearchMalformedResults:
    def test_result_without_href_skipped(self):
        """Results missing url/href are silently dropped."""
        tool = _make_tool()
        rows = [
            {"title": "Good", "href": "https://example.com", "body": "ok"},
            {"title": "Bad"},   # no href/url
        ]
        with patch.object(tool, "_ddgs_search", return_value=rows):
            r = run(tool.execute(query="q", max_results=5))
        assert r["count"] == 1
        assert r["results"][0]["url"] == "https://example.com"

    def test_non_dict_result_skipped(self):
        tool = _make_tool()
        rows = [
            {"title": "Good", "href": "https://example.com", "body": "ok"},
            "not_a_dict",
            None,
        ]
        with patch.object(tool, "_ddgs_search", return_value=rows):
            r = run(tool.execute(query="q", max_results=5))
        assert r["count"] == 1

    def test_missing_title_defaults_to_empty_string(self):
        tool = _make_tool()
        rows = [{"href": "https://example.com", "body": "snippet"}]
        with patch.object(tool, "_ddgs_search", return_value=rows):
            r = run(tool.execute(query="q", max_results=1))
        assert r["results"][0]["title"] == ""

    def test_missing_body_defaults_to_empty_string(self):
        tool = _make_tool()
        rows = [{"title": "T", "href": "https://example.com"}]
        with patch.object(tool, "_ddgs_search", return_value=rows):
            r = run(tool.execute(query="q", max_results=1))
        assert r["results"][0]["description"] == ""
