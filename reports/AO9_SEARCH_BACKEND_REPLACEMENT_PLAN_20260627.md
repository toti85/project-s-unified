# AO9 — Search Backend Replacement Plan

**Date:** 2026-06-27
**Status:** Proposed — NOT implemented
**Previous backend:** DDGS (DuckDuckGo Search) — returns 0 results from this environment
**Successor to:** AO7 (SAI pipeline partial recovery)

---

## 1. Objective

Replace DDGS with a working search backend so the SAI pipeline can execute real web research → synthesis → file write tasks.

---

## 2. Backend Comparison

| Feature | Self-Hosted SearXNG | Brave Search API | Tavily | Playwright Browser | Paid Fallback Provider |
|---------|--------------------|-----------------|--------|--------------------|--------------------|
| **Cost** | Free (self-hosted) | Free tier: 2,000 queries/month. Paid: 0.5¢/query | Free tier: 100 queries/month. Paid: $0.50/query | Free | Varies ($0.002–$0.01/query) |
| **Setup complexity** | Medium (Docker) | Low (API key) | Low (API key) | High (browser automation) | Low (API key) |
| **Reliability** | High (own server) | High | High | Medium (CAPTCHAs) | Very High |
| **Latency** | Fast (local) | Fast | Fast | Slow (page load) | Fast |
| **No rate limiting** | Yes (self-controlled) | No (2k/month free) | No (100/month free) | N/A | Yes (paid tier) |
| **Privacy** | Full (own data) | Partial | Partial | Full (local browser) | Low |
| **Result quality** | Aggregated (DuckDuckGo, Google, Bing) | Good | Good (AI-optimized) | Full page content | Good |
| **Maintenance** | Docker updates | None | None | Browser/WebDriver updates | None |
| **Current status** | Not installed | Not registered | Not registered | `browser_use` module missing | Not configured |

---

## 3. Recommended Architecture

### Primary: Brave Search API (fastest to prove)

```
SAI Pipeline → Brave Search API → Direct search results
```

- API key from https://api.search.brave.com
- Free tier: 2,000 queries/month (sufficient for proving the pipeline)
- Fastest integration path: 1 API key, 1 HTTP call
- No infrastructure setup required

### Fallback 1: Playwright Browser Search

```
SAI Pipeline → Playwright → Headless browser → Search page scrape
```

- Used when Brave API is unavailable or rate-limited
- Requires `playwright` Python package + browser install
- Slow, fragile, but bypasses API rate limits

### Future: Self-Hosted SearXNG

```
SAI Pipeline → SearXNG API (local Docker) → Aggregated search results
```

- API key from https://api.search.brave.com
- Free tier: 2,000 queries/month (more than sufficient)
- Low latency, high reliability
- Used when SearXNG is unavailable or returns empty results

### Last-Resort Fallback: Playwright Browser Search

```
SAI Pipeline → Playwright → Headless browser → Search page scrape
```

- Requires `playwright` Python package + browser install
- Only used when both SearXNG and Brave API fail
- Slow, fragile, but works when other backends are blocked

---

## 4. Backend Interface

```python
# orchestrator_runtime/search/backend_interface.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str  # "searxng", "brave", "playwright", "ddgs"
    raw: Optional[dict] = None


@dataclass
class SearchResponse:
    results: list[SearchResult]
    total: int
    backend: str
    latency_ms: float
    error: Optional[str] = None
    fallback_chain: list[str] = field(default_factory=list)


class SearchBackend(ABC):
    """Abstract interface for search backends."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> SearchResponse:
        """Execute a search query and return structured results."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the backend is operational."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release any held resources (sessions, browser instances, etc.)."""
        ...

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable backend identifier."""
        ...
```

---

## 5. Implementation Plan

### Step 1: Create search backend directory

- `orchestrator_runtime/search/__init__.py`
- `orchestrator_runtime/search/backend_interface.py` (interface)
- `orchestrator_runtime/search/searxng_backend.py` (primary)
- `orchestrator_runtime/search/brave_backend.py` (fallback)
- `orchestrator_runtime/search/playwright_backend.py` (last-resort)
- `orchestrator_runtime/search/search_orchestrator.py` (fallback chain)

### Step 2: Create fallback orchestrator

```python
class SearchOrchestrator:
    def __init__(self):
        self.backends = [
            BraveSearchBackend(),        # Primary: fastest to prove
            PlaywrightSearchBackend(),   # Fallback 1: no API key needed
            SearXNGSearchBackend(),      # Future: self-hosted, requires Docker
        ]

    def search(self, query: str, max_results: int = 5) -> SearchResponse:
        errors = []
        for backend in self.backends:
            try:
                if not backend.health_check():
                    errors.append(f"{backend.backend_name}: health check failed")
                    continue
                response = backend.search(query, max_results)
                if response.total > 0:
                    return response
                errors.append(f"{backend.backend_name}: returned 0 results")
            except Exception as e:
                errors.append(f"{backend.backend_name}: {e}")
        return SearchResponse(
            results=[], total=0, backend="none",
            latency_ms=0, error="; ".join(errors)
        )
```

### Step 3: Health checks

```
SearXNG:   GET http://localhost:8888/health → 200 OK
Brave:     POST https://api.search.brave.com/resolver/v1/web/search → 200 OK (with valid API key)
Playwright: page.goto("about:blank") → no exception
```

All health checks must complete within 5 seconds. Timeout = `FAIL`.

### Step 4: Timeout handling

```python
import asyncio
from functools import wraps

def with_timeout(seconds: int = 10):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs), timeout=seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"{func.__name__} timed out after {seconds}s")
        return wrapper
    return decorator
```

### Step 5: Empty-result detection

- Check `SearchResponse.total == 0`
- Distinguish: "no results found" (query-specific) vs. "backend unavailable" (systematic)
- If 3 consecutive queries return 0 results from the primary backend, promote fallback to primary for the next 5 minutes

### Step 6: Deduplication

```python
def deduplicate(results: list[SearchResult]) -> list[SearchResult]:
    seen_urls = set()
    unique = []
    for r in results:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique.append(r)
    return unique
```

### Step 7: Source attribution

- Each `SearchResult` includes a `source` field (`"searxng"`, `"brave"`, `"playwright"`)
- The `SearchResponse` includes a `fallback_chain` list showing which backends were tried
- Attribution is passed to the SAI pipeline for citation

---

## 6. Integration with SAI Pipeline

In `src/core/super_intelligent_ai.py`, replace:

```python
# OLD — DDGS only
from ddgs import DDGS
results = DDGS().text(query, max_results=5)
```

With:

```python
# NEW — Fallback search orchestrator
from orchestrator_runtime.search.search_orchestrator import SearchOrchestrator

search = SearchOrchestrator()
response = search.search(query, max_results=5)
if response.total == 0:
    logger.warning(f"Search returned 0 results. Chain: {response.fallback_chain}")
```

---

## 7. Test Scenarios

| Test | Query | Expected | Backend |
|------|-------|----------|---------|
| T1 — Simple query | "MCP 2026 adoption" | >= 3 results | SearXNG |
| T2 — Empty query | "" | 0 results, no crash | SearXNG |
| T3 — Special characters | "C++ vs Rust 2026" | >= 1 result | SearXNG |
| T4 — Non-English | "Écosse whisky 2026" | >= 1 result | SearXNG |
| T5 — SearXNG failure | Stop Docker, query | Fallback to Brave | Brave |
| T6 — Brave failure | Invalid API key | Fallback to Playwright | Playwright |
| T7 — All backends fail | Block all | 0 results, error chain | None |
| T8 — Performance | 10 sequential queries | Each < 10s | All |
| T9 — Deduplication | Query that returns same URL from multiple backends | Unique URLs only | All |
| T10 — SAI integration | Full pipeline: search → synthesize → write | File created with citations | All |

---

## 8. Acceptance Criteria

1. ✅ `SearchResponse` contains >= 1 result for a valid query from at least one backend
2. ✅ No exception propagates to the SAI pipeline for any failure mode
3. ✅ Fallback chain is tested: SearXNG → Brave → Playwright → empty response
4. ✅ Health checks pass before each search attempt
5. ✅ Timeout at 10 seconds per backend
6. ✅ Deduplication removes exact URL duplicates
7. ✅ Source attribution is preserved in results
8. ✅ Empty-result detection distinguishes between "no matches" and "backend unavailable"
9. ✅ Full SAI pipeline completes: search → synthesize → write file
10. ✅ `browser_use` module (if needed) is installed

---

## 9. Implementation Order

```
1. Create orchestrator_runtime/search/ directory + interface
2. Implement SearXNG backend (primary)
3. Implement Brave backend (fallback)
4. Implement SearchOrchestrator with fallback chain
5. Implement health checks + timeouts
6. Implement deduplication
7. Test T1-T4 (SearXNG alone)
8. Implement Playwright backend (last-resort)
9. Test T5-T7 (fallback chain)
10. Test T8 (performance)
11. Integrate with SAI pipeline
12. Test T10 (full pipeline)
```

---

## 10. Files to Modify

| File | Change |
|------|--------|
| `orchestrator_runtime/search/__init__.py` | NEW — package init |
| `orchestrator_runtime/search/backend_interface.py` | NEW — abstract interface |
| `orchestrator_runtime/search/searxng_backend.py` | NEW — SearXNG implementation |
| `orchestrator_runtime/search/brave_backend.py` | NEW — Brave Search implementation |
| `orchestrator_runtime/search/playwright_backend.py` | NEW — Playwright implementation |
| `orchestrator_runtime/search/search_orchestrator.py` | NEW — fallback chain orchestrator |
| `src/core/super_intelligent_ai.py` | MODIFY — replace DDGS import with SearchOrchestrator |

---

*End of AO9 Search Backend Replacement Plan*