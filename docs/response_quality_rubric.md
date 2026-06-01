# Project-S Output Quality Rubric — v1.0

**Milestone:** MS-OQ1 — Output Quality Standard v1  
**Date:** 2026-05-21  
**Status:** Active — baseline measurement in progress  
**Scope:** All Interactive Layer route classes  

---

## Purpose

This rubric provides a formal, repeatable scoring framework for evaluating the quality of Project-S Interactive Layer responses. It is used by the baseline evaluator harness (`evaluate_output_quality_baseline.py`) and by human reviewers during manual audits.

The rubric is intentionally route-agnostic: the same 5 dimensions apply to all route classes, but the **scoring interpretation** may differ by route (noted in each dimension). A `DIRECT_LIGHTWEIGHT_RESPONSE` answer that scores 3 on Specificity looks different from a `FULL_AGENTIC_META_CONTROLLER` answer that scores 3 on Specificity — but the logical standard ("concrete details where appropriate") is the same.

---

## Scoring Scale

Each dimension is scored **0–3**. Maximum total: **15 points**.

| Score | Meaning |
|---|---|
| 0 | Unacceptable — fails the dimension entirely |
| 1 | Weak — partially meets the dimension |
| 2 | Acceptable — mostly meets the dimension |
| 3 | Strong — fully meets the dimension |

**Target threshold (future):** Average ≥ 12/15 across the 20-prompt corpus.

---

## Dimension 1 — Relevance

**Question:** Does the answer directly address the user prompt?

| Score | Description |
|---|---|
| 0 | Off-topic. The answer does not engage with what was asked. |
| 1 | Partially related. The answer touches the topic but misses the core question. |
| 2 | Mostly answers. The main question is addressed, minor gaps or detours. |
| 3 | Precisely answers. The response directly and fully addresses what was asked, nothing important is omitted. |

**Route-specific notes:**
- `DIRECT_LIGHTWEIGHT`: 3 requires the exact format/length/topic requested.
- `TRUTHFUL_UNCERTAINTY`: 3 requires acknowledging the specific uncertainty the prompt created (not just generic "I don't know").
- `INTERNAL_PROJECT_DOC_REASONING`: 3 requires the answer to be grounded in actual Project-S doc content, not generic AI knowledge.
- `EXTERNAL_RESEARCH_SYNTHESIS`: 3 requires the answer to address the specific research question, not just any web content.
- `FULL_AGENTIC_META_CONTROLLER`: 3 requires the full mission scope to be addressed, not just part of it.

---

## Dimension 2 — Specificity

**Question:** Is the answer concrete rather than generic?

| Score | Description |
|---|---|
| 0 | Vague or generic. Could apply to any prompt. No concrete details. |
| 1 | Some specifics. Attempts to be concrete but lacks real substance. |
| 2 | Useful specifics. Concrete content that adds real value. |
| 3 | Concrete details, examples, numbers, or data where appropriate for the prompt type. |

**Route-specific notes:**
- `DIRECT_LIGHTWEIGHT`: 3 requires the specific content requested (the list, the definition, the example), not a generic essay.
- `TRUTHFUL_UNCERTAINTY`: 3 requires specific language about WHAT is unknowable and WHY, not just "it's uncertain."
- `INTERNAL_PROJECT_DOC_REASONING`: 3 requires referencing specific gaps, dates, milestone IDs, or documented facts.
- `EXTERNAL_RESEARCH_SYNTHESIS`: 3 requires concrete synthesized findings (named tools, frameworks, numbers), not just "various sources suggest."
- `FULL_AGENTIC_META_CONTROLLER`: 3 requires concrete analysis, not filler paragraphs.

---

## Dimension 3 — Truthfulness / Uncertainty Markers

**Question:** Does the answer avoid unsupported certainty and clearly mark uncertainty?

| Score | Description |
|---|---|
| 0 | Misleading or overconfident. States uncertain things as facts. No uncertainty markers. |
| 1 | Weak uncertainty handling. Some hedging but inconsistent or insufficient. |
| 2 | Mostly truthful. Uncertainty is present and mostly appropriate. Minor overconfidence. |
| 3 | Explicitly truthful. Uncertainty and limits clearly stated where applicable. No false confidence. Known unknowns acknowledged. |

**Route-specific notes:**
- `DIRECT_LIGHTWEIGHT`: Score 3 is achievable even without explicit uncertainty markers, as long as no false claims are made.
- `TRUTHFUL_UNCERTAINTY`: The entire purpose of this route is to handle unknowable certainty correctly. Score 3 requires explicit naming of the limit ("cannot be known in advance," "depends on factors outside current data," etc.).
- `INTERNAL_PROJECT_DOC_REASONING`: 3 requires the answer to distinguish between "documented fact" and "inferred from docs."
- `EXTERNAL_RESEARCH_SYNTHESIS`: 3 requires noting when web content is recent/stale, and distinguishing synthesis from verified fact.
- `FULL_AGENTIC_META_CONTROLLER`: 3 requires that confidence in recommendations is calibrated, not "the best option is X" without caveats.

---

## Dimension 4 — Structure / Readability

**Question:** Is the answer easy to read and follow?

| Score | Description |
|---|---|
| 0 | Messy wall of text. No structure, hard to parse. |
| 1 | Minimally structured. Some paragraphs or line breaks, but navigation is unclear. |
| 2 | Clear. Good use of paragraphs, lists, or headings as appropriate. Reader can follow the answer. |
| 3 | Very well structured for the route and prompt type. Format matches content (lists for lists, headers for multi-section, numbered for sequences). |

**Route-specific notes:**
- `DIRECT_LIGHTWEIGHT`: 3 requires format to match what was asked (e.g., if 4 bullet points were requested, 4 bullet points are given, with the right prefix character).
- `TRUTHFUL_UNCERTAINTY`: 3 requires a clean explanation structure: what was asked → why it cannot be answered with certainty → what CAN be said.
- `INTERNAL_PROJECT_DOC_REASONING`: 3 requires organized sections or clear flow when the answer involves multiple doc facts.
- `EXTERNAL_RESEARCH_SYNTHESIS`: 3 requires numbered or bulleted synthesis points, clearly separated from any sources or metadata.
- `FULL_AGENTIC_META_CONTROLLER`: 3 requires proper memo/report structure with clearly labeled sections.

---

## Dimension 5 — Action-Readiness

**Question:** Can the user act on the answer?

| Score | Description |
|---|---|
| 0 | No clear next step or value. The answer provides nothing the user can do with. |
| 1 | Weakly useful. There is something there, but acting on it would be hard. |
| 2 | Useful. The user can take the answer and do something with it. |
| 3 | Directly actionable or decision-ready. The user has what they need to act or decide. |

**Route-specific notes:**
- `DIRECT_LIGHTWEIGHT`: 3 = the requested content is present in a form that can be directly used (pasted, read, acted on).
- `TRUTHFUL_UNCERTAINTY`: 3 = the user understands what CAN be acted on vs. what cannot, and optionally receives proxies or alternatives.
- `INTERNAL_PROJECT_DOC_REASONING`: 3 = the user receives a clear picture of the documented state, sufficient for a planning decision.
- `EXTERNAL_RESEARCH_SYNTHESIS`: 3 = the user gets synthesized points they can act on (choose a tool, inform a strategy, answer a question).
- `FULL_AGENTIC_META_CONTROLLER`: 3 = the mission result is a decision memo or analysis the user can directly act on or share.

---

## Scoring Worksheet

Use this template when manually scoring a response:

```
Prompt ID: ___________
Route expected: ___________
Route selected: ___________
Elapsed: ___________

D1 Relevance:         ___ / 3   Notes: ___
D2 Specificity:       ___ / 3   Notes: ___
D3 Truthfulness:      ___ / 3   Notes: ___
D4 Structure:         ___ / 3   Notes: ___
D5 Action-readiness:  ___ / 3   Notes: ___
                      ---------
Total:                ___ / 15

Pass threshold (≥12): YES / NO
```

---

## Corpus-Level Thresholds

| Metric | Current Baseline Target | Future Polish Target |
|---|---|---|
| Average score | Measure only | ≥ 12.0 / 15 |
| Minimum per prompt | Measure only | ≥ 9 / 15 |
| Route mismatch rate | Measure only | 0% |
| COMPLETE state rate | Measure only | 100% |

---

## Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-05-21 | Initial rubric — MS-OQ1 baseline measurement |
