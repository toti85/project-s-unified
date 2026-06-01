"""One-time script to restore self_state.json after file_writer path-bug corruption."""
import json, shutil

# Load base from bak_cleanup
data = json.loads(open('self_state.json.bak_cleanup', 'rb').read())

existing_ids = {g['gap_id'] for g in data['identity']['known_gaps']}

new_gaps = []

if 'GAP_012' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_012",
        "title": "AI provider routing hianyzik — task_model_mapping kulcs hianyzik",
        "discovered": "2026-04-28",
        "status": "RESOLVED",
        "resolved_at": "2026-04-28T14:00:00Z",
        "resolution": "models.yaml analysis mapping added [qwen3-235b, deepseek-v3, gpt-4o-mini], code-fallback to defaults.model. qwen3-235b now explicit on OpenRouter."
    })

if 'GAP_017' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_017",
        "title": "WebSearchTool Google HTML scraper — bot-detection, nincs fallback",
        "discovered": "2026-05-14",
        "status": "RESOLVED",
        "resolved_at": "2026-05-14",
        "resolution": "WebSearchTool replaced with DDGS (DuckDuckGo) backend — no API key, primp TLS bypass, bot-detection resistant. 26 tests pass. GAP_018 covered by this fix."
    })

if 'GAP_019' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_019",
        "title": "LLM szintezis lepes hianyzik az orchestratorbol",
        "discovered": "2026-05-14",
        "status": "RESOLVED",
        "resolved_at": "2026-05-14",
        "resolution": "_synthesize_web_results() + _is_synthesis_task() added to smart_orchestrator.py. Synthesis model: qwen/qwen3.6-35b-a3b (max_tokens=8000). A/B test: 7/8 dimensions beats gpt-4o-mini. 11 synthesis tests green."
    })

if 'GAP_020' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_020",
        "title": "SAI/MetaController false-success — 5 rejett igazsag-kapu bug",
        "discovered": "2026-05-14",
        "status": "RESOLVED",
        "resolved_at": "2026-05-14",
        "resolution": "5 fixes: evaluator nested key, backup exception swallow, execution history empty-list, has_output stub rejection, replan blocking. 40 regression tests, 4/4 live scenarios pass."
    })

if 'GAP_021' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_021",
        "title": "Strategiai tervezo vak a browser_automation toolra",
        "discovered": "2026-05-14",
        "status": "RESOLVED",
        "resolved_at": "2026-05-14",
        "resolution": "TOOL MANIFEST added to Phase 1 planning prompt (26 lines, 5 numbered tools, explicit browser_automation criteria). 6 tests green, live mission PASS 9/9 (Chromium, 3 URLs, 94.30s)."
    })

if 'GAP_022' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_022",
        "title": "Evaluator TypeError — browser_use AgentHistoryList not JSON-serializable",
        "discovered": "2026-05-14",
        "status": "RESOLVED",
        "resolved_at": "2026-05-14",
        "resolution": "_sanitize_for_json() recursive helper added to evaluator.py. Handles all non-JSON-serializable tool outputs. 16/16 tests green."
    })

if 'GAP_023' not in existing_ids:
    new_gaps.append({
        "gap_id": "GAP_023",
        "title": "browser_automation vegyes pipeline-ban teljes task leirast kap — scope pollution",
        "discovered": "2026-05-14",
        "status": "RESOLVED",
        "resolved_at": "2026-05-14",
        "resolution": "_build_browser_subtask() added to smart_orchestrator.py: browser-only subtask generation (URLs, research questions, explicit no-write constraint). 9/9 unit tests + 23/23 total pass."
    })

data['identity']['known_gaps'].extend(new_gaps)
print("Added gaps:", [g['gap_id'] for g in new_gaps])
print("Total gaps now:", len(data['identity']['known_gaps']))

# Update gaps summary to the last Cline-validated state
data['current_state']['gaps_summary'] = {
    "total": 22,
    "resolved": 21,
    "active": 0,
    "accepted": 1
}

# Add model policy
if 'model_policy' not in data['current_state']:
    data['current_state']['model_policy'] = {}
data['current_state']['model_policy']['synthesis_default'] = 'qwen/qwen3.6-35b-a3b'

# Add tool capabilities
if 'tool_capabilities' not in data['current_state']:
    data['current_state']['tool_capabilities'] = {}
data['current_state']['tool_capabilities']['browser_automation'] = 'VERIFIED'
data['current_state']['tool_capabilities']['web_search'] = 'VERIFIED'
data['current_state']['tool_capabilities']['file_reader'] = 'PARTIAL'
data['current_state']['tool_capabilities']['file_writer'] = 'VERIFIED'

# Update metadata
data['last_updated'] = '2026-05-15T00:00:00Z'
data['updated_by'] = 'GitHub Copilot + Toti (self_state.json restored from backup+milestone docs after file_writer path-bug corruption 2026-05-14T23:34)'
data['current_state']['active_focus'] = 'GAP_024 (file_reader no dispatch) + GAP_025 (file_writer path regex) — native pipeline repair in progress'
data['current_state']['phase'] = 'production_stable'

with open('self_state.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Wrote self_state.json — size:", len(open('self_state.json', 'rb').read()), "bytes")

# Validate
data2 = json.loads(open('self_state.json', 'rb').read())
gs = data2['current_state']['gaps_summary']
mp = data2['current_state']['model_policy']
assert gs['total'] == 22 and gs['resolved'] == 21 and gs['active'] == 0 and gs['accepted'] == 1
assert mp['synthesis_default'] == 'qwen/qwen3.6-35b-a3b'
print("VALIDATION OK: total=%d resolved=%d accepted=%d synthesis_default=%s" % (
    gs['total'], gs['resolved'], gs['accepted'], mp['synthesis_default']))
