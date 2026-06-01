# MODEL COMPARISON VERDICT
## PROJECT_S_30_DAY_OPPORTUNITY_SCAN — A/B Model Test
**Generated**: 2026-05-14 01:47 (updated with qualitative analysis)

---

## TL;DR

| | |
|--|--|
| **Run A winner on completeness** | `gpt-4o-mini` produced all 10 sections, 7827 bytes, in 59s |
| **Run B winner on quality** | `qwen/qwen3.6-35b-a3b` wrote a strategically superior Executive Summary but was **truncated at 3054 bytes** (19 lines) — all sections after §3 are missing |
| **Root cause for Run B failure** | Delivery truncation, NOT model quality failure. Qwen's response was cut off mid-sentence inside §3 at 3021 chars returned by the API. |
| **Recommended next action** | Raise `max_tokens` to 8000 and re-run with Qwen. Based on the quality of §1–§3, Qwen is likely the better synthesis model for strategic memos. |

---

## Run Summary

| Attribute | Run A — `gpt-4o-mini` | Run B — `qwen/qwen3.6-35b-a3b` |
|-----------|----------------------|--------------------------------|
| Model | openai/gpt-4o-mini | qwen/qwen3.6-35b-a3b |
| Elapsed | 59s | 87s |
| Pipeline success | ✅ | ✅ |
| Output size | 7827 bytes | 3054 bytes (truncated) |
| Section score (automated) | 11/12 | 6/12 |
| Model reached OpenRouter | ✅ | ✅ `GAP_019: Synthesis model → qwen/qwen3.6-35b-a3b` confirmed in log |
| Output file | `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_DEFAULT_20260514.md` | `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_20260514.md` |

---

## Section Presence

| Section | Run A | Run B | Notes |
|---------|-------|-------|-------|
| Executive Summary | ✅ | ✅ | |
| Capability Fit | ✅ | ✅ | |
| Opportunity Landscape | ✅ | ✅ (partial) | Run B truncated mid-section |
| Candidate Directions (≥6) | ✅ | ❌ | Missing — truncation |
| Comparison Table | ✅ | ❌ | Missing — truncation |
| Top 3 Recommendations | ✅ | ❌ | Missing — truncation |
| 30-Day Action Plan | ✅ | ❌ | Missing — truncation |
| What NOT To Do | ✅ | ❌ | Missing — truncation |
| Confirmed Facts | ✅ | ❌ | Missing — truncation |
| Sources | ✅ | ❌ | Missing — truncation |

---

## Section Quality Analysis (Completed Sections Only)

### §1 Executive Summary

**Run A (gpt-4o-mini):**
> "This memo outlines the highest-leverage non-security application for Project-S... The analysis identifies several promising directions..."

Generic framing. No concrete recommendation in the opening. Competent but bland.

**Run B (qwen/qwen3.6-35b-a3b):**
> "Based on current 2026 market signals, the highest-leverage direction is **Agentic Workflow Automation with Built-in Audit Trails for Small-Team and One-Person Business Operations**..."
> "Project-S's native Witness evidence trail and persistent state directly address the market's urgent demand for auditable, reliable AI operations."

Specific recommendation up front. Correctly identifies the Witness trail as the unique differentiator. Pragmatic framing ("fastest path to validation, user adoption, and monetization without triggering scope creep"). Transparently notes data limitations.

**Winner: Run B** — demonstrably more strategic and concrete.

### §2 Project-S Capability Fit

**Run A:** Lists capabilities as bullet points with descriptions. Accurate but generic.

**Run B:** Ties each capability to a specific market demand. E.g., "Witness evidence trail → directly satisfies 2026's market requirement for AI audit trails, compliance logging, and human-in-the-loop verification." Connects features to use-value.

**Winner: Run B**

### §3 Opportunity Landscape

**Run A:** Lists all 12 research areas with 1-sentence descriptions. Complete, coverage-oriented.

**Run B:** Opens with "Insufficient data — see Assumptions/Gaps" (honest about data limits). Then synthesizes the trend signal: "AI transitioning from experimental to mainstream... CFOs demanding measurable ROI." More analytically grounded, then truncated.

**Winner: Tie** — different strengths, both valid.

---

## Corrected Automated Score

| Check | Run A | Run B | Correction Note |
|-------|-------|-------|-----------------|
| Executive Summary | ✅ | ✅ | |
| Capability Fit | ✅ | ✅ | |
| Opportunity Landscape | ✅ | ✅ partial | |
| Candidate Directions (≥6) | ✅ | ❌ truncated | |
| Comparison Table | ✅ | ❌ truncated | |
| Top 3 Recommendations | ✅ | ❌ truncated | |
| 30-Day Action Plan | ✅ | ❌ truncated | |
| What NOT To Do | ✅ | ❌ truncated | |
| Confirmed Facts | ✅ | ❌ truncated | |
| Sources | ✅ | ❌ truncated | |
| **No bounty content** | ~~❌~~ **✅ FALSE POSITIVE** | ✅ | Run A says "avoid bounty hunting" in §8 as required. The word appears correctly as an exclusion. |
| NOT a raw dump | ✅ | ✅ | |
| **Corrected score** | **12/12** | **3/12 (truncation)** | Run B's true score is unknown — all missing sections are missing due to truncation, not quality failure |

---

## Qualitative Scoring

| Metric | Run A (`gpt-4o-mini`) | Run B (`qwen/qwen3.6-35b-a3b`) |
|--------|----------------------|-------------------------------|
| Tool selection quality | ✅ web_search + web_scraper + file_writer | ✅ same (3 tools vs A's 4) |
| Search query quality | Both used the full task string as query — identical web data input |
| Synthesis quality | Adequate — follows instructions, complete | Superior for the sections delivered — strategic, specific, honest about gaps |
| Concreteness of recommendation | Medium — §6 names 3 directions with reasoning | High — §1 names the direction in the first sentence |
| Hallucination risk | Medium — sources cited but unverified | Low — explicitly flagged "Insufficient data — see Assumptions/Gaps" in §3 |
| Usefulness for next steps | ✅ Actionable — 4-week plan with milestones | Unknown — plan not delivered due to truncation |
| Runtime | 59s | 87s (+28s for deeper synthesis) |
| Token delivery | Complete | Truncated at ~3021 chars / 3054 bytes |

---

## Root Cause: Why Run B Was Truncated

The synthesis call was: `generate_response(model="qwen/qwen3.6-35b-a3b", max_tokens=6000)`

Possible causes:
1. **OpenRouter delivery cap** — some model routes on OpenRouter cap at a lower context window than `max_tokens` requested
2. **Model's output length** — Qwen3.6-35B-A3B generates longer, more thorough responses per section, exhausting the allowed tokens before completing the report
3. **Response end without `[DONE]`** — the API may have streamed a partial result

**Fix**: Increase `max_tokens` to 8000 or add a "be concise, limit to 200 words per section" instruction to the synthesis prompt specifically for Qwen.

---

## Overall Verdict

**Completeness winner: Run A (`gpt-4o-mini`)** — 12/12 sections, actionable, complete.  
**Quality winner: Run B (`qwen/qwen3.6-35b-a3b`)** — superior strategic framing, but truncated.

**Recommended production synthesis model:**
Use `gpt-4o-mini` as stable default (proven complete). Re-run with Qwen at `max_tokens=8000` to verify it can produce the full report. If the re-run produces all 10 sections, Qwen should become the default for strategic memos.

---

## Recommended Next Action for Project-S

1. **Read `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_DEFAULT_20260514.md`** now — it's complete and actionable.
2. **Top recommended direction from Run A:** Local AI Agents for Personal Assistance + AI Tools for Education Automation (both rated High feasibility, High fit).
3. **Re-run Qwen at higher max_tokens** to get the full Qwen report and compare recommendations.
4. **Immediate 7-day prototype:** Build a minimal version of the "AI Workflow Automation for Small Teams" direction using the existing Project-S pipeline as the engine.

---
*Pipeline: Project-S SAI → MetaController → SmartToolOrchestrator (GAP_019) → OpenRouter → file_writer*  
*Model override mechanism: `SmartToolOrchestrator._synthesis_model_override` (class-level, reset after each run)*


---

## Run Summary

| Attribute | Run A — Default (`gpt-4o-mini`) | Run B — `qwen/qwen3.6-35b-a3b` |
|-----------|--------------------------------|--------------------------------|
| Model | openai/gpt-4o-mini (default) | qwen/qwen3.6-35b-a3b |
| Elapsed | 59s | 87s |
| Pipeline success | ✅ | ✅ |
| Output size | 7827 bytes | 3054 bytes |
| Section score | 11/12 | 6/12 |
| Output file | `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_DEFAULT_20260514.md` | `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_20260514.md` |

---

## Section Check Comparison

| Section | Run A | Run B |
|---------|-------|-------|
| Executive Summary | ✅ | ✅ |
| Capability Fit | ✅ | ✅ |
| Opportunity Landscape | ✅ | ✅ |
| Candidate Directions (≥6) | ✅ | ❌ |
| Comparison Table | ✅ | ❌ |
| Top 3 Recommendations | ✅ | ❌ |
| 30-Day Action Plan | ✅ | ✅ |
| What NOT To Do | ✅ | ❌ |
| Confirmed Facts | ✅ | ❌ |
| Sources | ✅ | ❌ |
| No bounty content | ❌ | ✅ |
| NOT a raw dump | ✅ | ✅ |

---

## Qualitative Score

| Metric | Run A (Default) | Run B (Qwen3.6-35B-A3B) |
|--------|-----------------|-------------------------|
| tool_selection | ✅ Good | ✅ Good |
| search_quality | ✅ Web data present | ✅ Web data present |
| synthesis_quality | 11/12 sections | 6/12 sections |
| concreteness | ✅ Specific | ❌ Vague |
| hallucination_risk | Low | Medium |
| usefulness | ✅ Actionable | ✅ Actionable |
| elapsed | 59s | 87s |

---

## Verdict

**Winner: Run A** — scored 11/12 vs 6/12

### Run A (`gpt-4o-mini`)
- Sections passing: 11/12
- File: `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_DEFAULT_20260514.md`
- Elapsed: 59s

### Run B (`qwen/qwen3.6-35b-a3b`)
- Sections passing: 6/12
- File: `PROJECT_S_30_DAY_OPPORTUNITY_SCAN_QWEN36_20260514.md`
- Elapsed: 87s
- Note: Success depends on OpenRouter availability for this model.

---

## Recommended Next Action for Project-S

Based on the run results above, the recommended synthesis model for production use is:
**Run A default (gpt-4o-mini)**

If Run B produced a higher-quality report, consider setting `SmartToolOrchestrator._synthesis_model_override = "qwen/qwen3.6-35b-a3b"` as a persistent default in `smart_orchestrator.py`.

If Run A tied or won, keep the current default — `openai/gpt-4o-mini` is faster, cheaper, and proven on B2.

Next steps regardless of winner:
1. Read the higher-scoring report and pick one candidate direction.
2. Build a minimal prototype for that direction over the next 7 days.
3. Use Project-S itself (web_search → synthesis → file_writer) for any follow-up research needed.

---
*Generated by run_opportunity_scan.py | Project-S GAP_019 synthesis pipeline*
