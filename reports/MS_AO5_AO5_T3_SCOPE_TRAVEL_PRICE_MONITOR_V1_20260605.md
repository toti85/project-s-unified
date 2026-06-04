# AO5_T3 SCOPE — Travel Price Monitor v1

**Date:** 2026-06-05
**Status:** SCOPE ONLY — no implementation started
**RISK_008:** Active/mitigated — Cline PREP only, human CLI verification required

---

## 1. Mission Goal

A minimal travel price monitor that tracks **one manually supplied URL** and produces a **repeatable price/availability snapshot report**. The output is a markdown file stored in `reports/travel_price_monitor/`.

This is the first external-value mission for Project-S: real-world data extraction with human-verified output.

---

## 2. Inputs Required from Operator

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `target_url` | string (URL) | YES | — |
| `expected_item_title` | string | YES | — |
| `price_selector` | string (CSS selector or hint) | NO | auto-detect |
| `currency` | string (ISO 4217) | NO | inferred from page |
| `run_frequency` | string | NO | `daily` |
| `output_dir` | string (path) | NO | `reports/travel_price_monitor/` |

Operator provides these inputs as a JSON config file before each run.

---

## 3. Out of Scope for v1

- [ ] Scheduler / cron / background daemon
- [ ] Multi-site comparison
- [ ] Login / captcha handling
- [ ] Payment / booking actions
- [ ] Automatic purchase
- [ ] Browser automation (unless static fetch fails in a later implementation phase)
- [ ] Autonomous background execution
- [ ] Price alert notifications (beyond governance feed)

---

## 4. Proposed PREP-Only Architecture

```
Operator provides config JSON
    ↓
Cline prepares handoff (PREP only)
    ↓
Copilot / bridge executor performs actual execution
    ↓
Output stored under reports/travel_price_monitor/
    ↓
Human verifies output via CLI/dashboard
```

**Roles:**
- **Cline:** PREP only — creates handoff files, scope documents, config templates
- **Copilot / bridge executor:** Performs actual web fetch + extraction
- **Human:** Verifies output, approves next steps

---

## 5. Output Format — Markdown Snapshot Template

```markdown
# Price Snapshot — [target_url]

| Field | Value |
|-------|-------|
| Timestamp | 2026-06-05T01:00:00+00:00 |
| Target URL | https://example.com/flight/... |
| Extracted Title/Item | Budapest → Tokyo, 2026-07-15 |
| Extracted Price | 245,000 HUF |
| Currency | HUF |
| Extraction Method | static_fetch + CSS selector #price |
| Confidence | HIGH / MEDIUM / LOW |
| Raw Evidence Excerpt | "<span id='price'>245,000 Ft</span>" |
| Failure Reason | (none) |
```

If extraction fails:

```markdown
| Failure Reason | URL unreachable (HTTP 403) |
| Confidence | N/A |
| Raw Evidence Excerpt | "<html><body><h1>Access Denied</h1>..." |
```

---

## 6. Acceptance Criteria for AO5_T3 Scope

| Criterion | Met? |
|-----------|------|
| Scope document exists | YES |
| Required input fields defined | YES (6 fields) |
| Output report template defined | YES (markdown table) |
| Failure modes defined | YES (7 modes) |
| RISK_008 preserved | YES (PREP only) |
| No implementation started | YES |
| No src/ modifications | YES |

---

## 7. Failure Modes

| # | Failure Mode | Detection | Response |
|---|-------------|-----------|----------|
| 1 | URL unreachable | HTTP status != 200 | Report failure reason, confidence N/A |
| 2 | Static HTML does not contain price | No price pattern in response | Report "price_not_found", suggest browser fallback |
| 3 | Price ambiguous | Multiple price candidates | Report all candidates, confidence LOW |
| 4 | Currency missing | No ISO 4217 match | Report "currency_unknown", flag for human review |
| 5 | Anti-bot / captcha / login required | HTTP 403/401, captcha keywords in HTML | Report "access_blocked", no retry |
| 6 | Extracted content changed unexpectedly | Title mismatch vs expected_item_title | Report "content_changed", confidence LOW |
| 7 | Network timeout | Request timeout (>30s) | Report "timeout", no retry |

---

## 8. Next-Step Recommendation

After scope approval, recommend **AO5_T3_IMPL_PREP** as a separate future task:

1. Create config template JSON
2. Create handoff (PREP only)
3. Human executor performs first real run
4. Verify output matches template
5. Iterate on extraction hints if needed

**Do NOT implement now.** This task is scope definition only.

---

## Safety

- No src/ modifications: **YES**
- No implementation code created: **YES**
- No browser automation started: **YES**
- RISK_008 preserved: **YES**