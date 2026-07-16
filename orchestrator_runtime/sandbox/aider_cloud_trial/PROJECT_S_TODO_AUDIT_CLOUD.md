# PROJECT-S TODO/FIXME/XXX AUDIT (AO9_T7 — Aider + DeepSeek V4 Flash)

## 1. Summary

| Field | Value |
|-------|-------|
| Scan date | 2026-07-16 |
| Python files scanned | 501 |
| Files with findings | 12 |
| Total findings | 77 |
| TODO | 55 |
| FIXME | 22 |
| XXX | 0 |
| Executor | Aider CLI 0.86.2 |
| Model | DeepSeek V4 Flash (via OpenRouter) |

## 2. Counts by Marker Type

- **FIXME**: 22
- **TODO**: 55

## 3. Counts by Severity

- **HIGH**: 1
- **MEDIUM**: 36
- **LOW**: 40

## 4. Counts by Directory

- `organism`: 57
- `orchestrator_runtime`: 10
- `(root)`: 9
- `tests`: 1

## 5. Complete Finding List

### Finding #1

- **File**: `debug_kill_list.py`
- **Line**: 40
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={'priority': todo.get('priority', 'TODO')}`
- **Context**: `issue_url=todo.get('issue_url', ''),`

### Finding #2

- **File**: `debug_kill_list.py`
- **Line**: 73
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={'priority': todo.get('priority', 'TODO')}`
- **Context**: `issue_url=todo.get('issue_url', ''),`

### Finding #3

- **File**: `debug_rabbit_hole.py`
- **Line**: 37
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={'priority': todo.get('priority', 'TODO')}`
- **Context**: `issue_url=todo.get('issue_url', ''),`

### Finding #4

- **File**: `debug_rabbit_hole.py`
- **Line**: 63
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={'priority': todo.get('priority', 'TODO')}`
- **Context**: `issue_url=todo.get('issue_url', ''),`

### Finding #5

- **File**: `debug_rabbit_hole.py`
- **Line**: 89
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={'priority': todo.get('priority', 'TODO')}`
- **Context**: `issue_url=todo.get('issue_url', ''),`

### Finding #6

- **File**: `debug_rename_detailed.py`
- **Line**: 31
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={'priority': todo.get('priority', 'TODO')}`
- **Context**: `issue_url=todo.get('issue_url', ''),`

### Finding #7

- **File**: `test_kill_detection_mock.py`
- **Line**: 29
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `description="[TODO] Rename to EcdsLibStub (file:7)",`
- **Context**: `task_id="test_rename",`

### Finding #8

- **File**: `test_kill_detection_mock.py`
- **Line**: 34
- **Type**: TODO
- **Severity**: LOW
- **Text**: `metadata={"priority": "TODO"}`
- **Context**: `text="Rename to EcdsLibStub",`

### Finding #9

- **File**: `test_protection_direct.py`
- **Line**: 18
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `snippet="# TODO: Test with dust amounts (1 wei, etc.)",`
- **Context**: `text="Test with dust amounts (1 wei, etc.)",`

### Finding #10

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 4
- **Type**: TODO
- **Severity**: LOW
- **Text**: `Operator scans the repository for TODO/FIXME/XXX markers.`
- **Context**: `Feeds raw scan data to Ornith 9B.`

### Finding #11

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 50
- **Type**: TODO
- **Severity**: LOW
- **Text**: `TODO_PATTERN = re.compile(r"\\b(TODO|FIXME|XXX)\\b")`
- **Context**: `}`

### Finding #12

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 117
- **Type**: TODO
- **Severity**: LOW
- **Text**: `Scan all Python files under root for TODO/FIXME/XXX.`
- **Context**: `"""`

### Finding #13

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 256
- **Type**: TODO
- **Severity**: LOW
- **Text**: `print("\n[PHASE 1] Scanning repository for TODO/FIXME/XXX in Python files...")`
- **Context**: `# ── PHASE 1: Operator scan ────────────────────────────────────────────────`

### Finding #14

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 269
- **Type**: TODO
- **Severity**: LOW
- **Text**: `print(f"  By type: TODO={type_counts.get('TODO',0)} FIXME={type_counts.get('FIXME',0)} XXX={type_counts.get('XXX',0)}")`
- **Context**: `print(f"  Total findings: {scan_count}")`

### Finding #15

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 292
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# PROJECT-S TODO/FIXME/XXX AUDIT`

### Finding #16

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 295
- **Type**: TODO
- **Severity**: LOW
- **Text**: `State: date of scan ({scan_ts[:10]}), Python files scanned ({files_scanned}), files with findings ({files_with}), total findings ({scan_count}), breakdown by type (TODO: {type_counts.get('TODO',0)}, FIXME: {type_counts.get('FIXME',0)}, XXX: {type_counts.get('XXX',0)}).`
- **Context**: `## 1. Summary`

### Finding #17

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 298
- **Type**: TODO
- **Severity**: LOW
- **Text**: `{"If there are no findings, write: No TODO/FIXME/XXX markers were found." if scan_count == 0 else f"For each of the {scan_count} findings above, list: file path, line number, type, the text, surrounding context, and severity classification."}`
- **Context**: `## 2. Findings`

### Finding #18

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 349
- **Type**: TODO
- **Severity**: LOW
- **Text**: `"type": "<TODO|FIXME|XXX>",`
- **Context**: `"line": <line number as integer>,`

### Finding #19

- **File**: `orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py`
- **Line**: 434
- **Type**: TODO
- **Severity**: LOW
- **Text**: `Findings by type: TODO={type_counts.get('TODO',0)}, FIXME={type_counts.get('FIXME',0)}, XXX={type_counts.get('XXX',0)}`
- **Context**: `Total findings from scan: {scan_count}`

### Finding #20

- **File**: `organism/core/loop.py`
- **Line**: 73
- **Type**: TODO
- **Severity**: LOW
- **Text**: `text=todo['text'],  # Original TODO/FIXME text`
- **Context**: `metadata={'priority': todo['priority']},`

### Finding #21

- **File**: `organism/core/observer.py`
- **Line**: 6
- **Type**: TODO
- **Severity**: LOW
- **Text**: `- Extract TODO/FIXME annotations`
- **Context**: `- Scan repository changes (git diff)`

### Finding #22

- **File**: `organism/core/observer.py`
- **Line**: 30
- **Type**: TODO
- **Severity**: LOW
- **Text**: `"""TODO annotation found in source."""`
- **Context**: `class TodoItem(TypedDict):`

### Finding #23

- **File**: `organism/core/observer.py`
- **Line**: 34
- **Type**: TODO
- **Severity**: LOW
- **Text**: `priority: str  # 'TODO', 'FIXME'`
- **Context**: `text: str`

### Finding #24

- **File**: `organism/core/observer.py`
- **Line**: 55
- **Type**: TODO
- **Severity**: LOW
- **Text**: `text: str = ""  # Original TODO/FIXME text`
- **Context**: `line: int = 0`

### Finding #25

- **File**: `organism/core/observer.py`
- **Line**: 177
- **Type**: TODO
- **Severity**: LOW
- **Text**: `Scan source files for TODO/FIXME annotations in actual code comments only.`
- **Context**: `"""`

### Finding #26

- **File**: `organism/core/observer.py`
- **Line**: 213
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# Python format: ^(\\s*)#\\s*(TODO|FIXME)`
- **Context**: `# Only match actual code comments (anchored to line start, after whitespace)`

### Finding #27

- **File**: `organism/core/observer.py`
- **Line**: 214
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# JavaScript format: ^(\\s*)//(TODO|FIXME)`
- **Context**: `# Python format: ^(\\s*)#\\s*(TODO|FIXME)`

### Finding #28

- **File**: `organism/core/observer.py`
- **Line**: 219
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# Check if line is a Python comment with TODO/FIXME`
- **Context**: `py_match = None`

### Finding #29

- **File**: `organism/core/observer.py`
- **Line**: 224
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `py_match = re.match(r'#\\s*(TODO|FIXME)[:\\s]+(.*?)(?:\\s*$)', stripped)`
- **Context**: `if stripped.startswith('#'):`

### Finding #30

- **File**: `organism/core/observer.py`
- **Line**: 226
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# Check if line is a JavaScript/Solidity comment with TODO/FIXME`
- **Context**: `if stripped.startswith('//'):`

### Finding #31

- **File**: `organism/core/observer.py`
- **Line**: 228
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `js_match = re.match(r'//\\s*(TODO|FIXME)[:\\s]+(.*?)(?:\\s*$)', stripped)`
- **Context**: `if stripped.startswith('//'):`

### Finding #32

- **File**: `organism/core/observer.py`
- **Line**: 234
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `priority = match.group(1)  # 'TODO' or 'FIXME'`
- **Context**: `comment_text = match.group(2).strip()`

### Finding #33

- **File**: `organism/core/prioritizer.py`
- **Line**: 29
- **Type**: TODO
- **Severity**: LOW
- **Text**: `text: str          # Original TODO/FIXME text`
- **Context**: `line: int          # Line number`

### Finding #34

- **File**: `organism/core/prioritizer.py`
- **Line**: 36
- **Type**: TODO
- **Severity**: LOW
- **Text**: `priority: str      # 'TODO' or 'FIXME'`
- **Context**: `issue_url: str     # GitHub/issue tracker URL if present`

### Finding #35

- **File**: `organism/core/prioritizer.py`
- **Line**: 61
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `'FIXME': 1.0,`
- **Context**: `self.high_impact_keywords = {`

### Finding #36

- **File**: `organism/core/prioritizer.py`
- **Line**: 66
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `'TODO': 0.6,`
- **Context**: `'performance': 0.7,`

### Finding #37

- **File**: `organism/core/prioritizer.py`
- **Line**: 76
- **Type**: FIXME
- **Severity**: LOW
- **Text**: `- FIXME items: high impact (0.8-1.0)`
- **Context**: `- HEAVILY PENALIZE organism/ and other ignored dirs (-0.95 impact)`

### Finding #38

- **File**: `organism/core/prioritizer.py`
- **Line**: 129
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# Easy tasks: typo, doc, comment, rename, TODO cleanup`
- **Context**: `easy_keywords = ['typo', 'doc', 'comment', 'rename', 'clean up', 'remove', 'add docstring']`

### Finding #39

- **File**: `organism/core/prioritizer.py`
- **Line**: 137
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `elif 'fix' in text_combined and 'FIXME' not in task.text:`
- **Context**: `# Medium-easy: simple fixing`

### Finding #40

- **File**: `organism/core/prioritizer.py`
- **Line**: 139
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# Standard TODO`
- **Context**: `effort = 3`

### Finding #41

- **File**: `organism/core/prioritizer.py`
- **Line**: 140
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `elif 'TODO' in task.text:`
- **Context**: `# Standard TODO`

### Finding #42

- **File**: `organism/core/prioritizer.py`
- **Line**: 142
- **Type**: FIXME
- **Severity**: LOW
- **Text**: `# FIXME usually harder`
- **Context**: `effort = 4`

### Finding #43

- **File**: `organism/core/prioritizer.py`
- **Line**: 143
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `elif 'FIXME' in task.text:`
- **Context**: `# FIXME usually harder`

### Finding #44

- **File**: `organism/core/prioritizer.py`
- **Line**: 195
- **Type**: FIXME
- **Severity**: LOW
- **Text**: `- If file contains \"/test/\" and FIXME: +0.15 bonus`
- **Context**: `- If issue_url present: ev = 0.65 (already discussed/tracked)`

### Finding #45

- **File**: `organism/core/prioritizer.py`
- **Line**: 210
- **Type**: FIXME
- **Severity**: LOW
- **Text**: `# Test file FIXME = higher confidence`
- **Context**: `if '/test/' in task.file.lower() and task.metadata.get('priority') == 'FIXME':`

### Finding #46

- **File**: `organism/core/prioritizer.py`
- **Line**: 211
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `if '/test/' in task.file.lower() and task.metadata.get('priority') == 'FIXME':`
- **Context**: `# Test file FIXME = higher confidence`

### Finding #47

- **File**: `organism/core/prioritizer.py`
- **Line**: 225
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `elif 'TODO' in task.text and 'verify' in text_combined:`
- **Context**: `ev = max(ev, 0.80)  # FIXMEs are usually proven issues`

### Finding #48

- **File**: `organism/core/prioritizer.py`
- **Line**: 562
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `'priority': task.metadata.get('priority', 'TODO'),`
- **Context**: `'issue_url': task.issue_url,`

### Finding #49

- **File**: `organism/core/proposer.py`
- **Line**: 303
- **Type**: FIXME
- **Severity**: LOW
- **Text**: `- FIXME + (timeout/connection) => config/refactor steps`
- **Context**: `Categories:`

### Finding #50

- **File**: `organism/core/proposer.py`
- **Line**: 304
- **Type**: FIXME
- **Severity**: LOW
- **Text**: `- FIXME + (complicated/conditions/implement in future) => spec-first steps`
- **Context**: `- FIXME + (timeout/connection) => config/refactor steps`

### Finding #51

- **File**: `organism/core/proposer.py`
- **Line**: 305
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `- TODO + (verify/test) => concrete test steps`
- **Context**: `- FIXME + (complicated/conditions/implement in future) => spec-first steps`

### Finding #52

- **File**: `organism/core/proposer.py`
- **Line**: 306
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `- Other FIXME => debug flow`
- **Context**: `- TODO + (verify/test) => concrete test steps`

### Finding #53

- **File**: `organism/core/proposer.py`
- **Line**: 307
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `- Other TODO => implementation flow`
- **Context**: `- Other FIXME => debug flow`

### Finding #54

- **File**: `organism/core/proposer.py`
- **Line**: 310
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `is_fixme = task['priority'].upper() == 'FIXME'`
- **Context**: `text_combined = (task['text'] + " " + task['description']).lower()`

### Finding #55

- **File**: `organism/core/proposer.py`
- **Line**: 312
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# ===== FIXME: TIMEOUT/CONNECTION ISSUES =====`
- **Context**: `if is_fixme and any(kw in text_combined for kw in ['timeout', 'connection']):`

### Finding #56

- **File**: `organism/core/proposer.py`
- **Line**: 319
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# ===== FIXME: COMPLICATED CONDITIONS/FUTURE WORK =====`
- **Context**: `if is_fixme and any(kw in text_combined for kw in ['complicated', 'conditions', 'implement in the future']):`

### Finding #57

- **File**: `organism/core/proposer.py`
- **Line**: 326
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# ===== FIXME: GENERAL DEBUGGING FLOW =====`
- **Context**: `if is_fixme:`

### Finding #58

- **File**: `organism/core/proposer.py`
- **Line**: 328
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `return ("1. **Read FIXME context** — Review the comment and surrounding code\n"`
- **Context**: `if is_fixme:`

### Finding #59

- **File**: `organism/core/proposer.py`
- **Line**: 333
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `# ===== TODO: VERIFICATION/TESTING =====`
- **Context**: `if 'verify' in text_combined or 'test' in text_combined:`

### Finding #60

- **File**: `organism/core/proposer.py`
- **Line**: 340
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `# ===== TODO: REFACTORING =====`
- **Context**: `if 'refactor' in text_combined or 'rewrite' in text_combined:`

### Finding #61

- **File**: `organism/core/proposer.py`
- **Line**: 347
- **Type**: TODO
- **Severity**: HIGH
- **Text**: `# ===== TODO: PERFORMANCE/SECURITY =====`
- **Context**: `if any(kw in text_combined for kw in ['security', 'performance', 'optimize']):`

### Finding #62

- **File**: `organism/core/proposer.py`
- **Line**: 354
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# ===== TODO: DOCUMENTATION =====`
- **Context**: `if any(kw in text_combined for kw in ['doc', 'comment', 'clarify']):`

### Finding #63

- **File**: `organism/core/proposer.py`
- **Line**: 361
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `# ===== TODO: GENERIC IMPLEMENTATION =====`
- **Context**: `return ("1. **Read the TODO context** — Understand the requirement\n"`

### Finding #64

- **File**: `organism/core/proposer.py`
- **Line**: 362
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `return ("1. **Read the TODO context** — Understand the requirement\n"`
- **Context**: `# ===== TODO: GENERIC IMPLEMENTATION =====`

### Finding #65

- **File**: `organism/core/state_observer.py`
- **Line**: 7
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `Cél: Az Organism ne csak TODO/FIXME/git diff/terminál-históriát lásson,`
- **Context**: `hanem a rendszer saját ismert hiányosságait (self_state.json) is.`

### Finding #66

- **File**: `organism/core/state_observer.py`
- **Line**: 26
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# => FIXME marker = high/medium gap-eknek az optimális jelölő`
- **Context**: `# A prioritizer.py ev: 'fixme' → ev >= 0.80`

### Finding #67

- **File**: `organism/core/state_observer.py`
- **Line**: 28
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `"high":   "FIXME",`
- **Context**: `_PRIORITY_MARKER = {`

### Finding #68

- **File**: `organism/core/state_observer.py`
- **Line**: 29
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `"medium": "FIXME",`
- **Context**: `"high":   "FIXME",`

### Finding #69

- **File**: `organism/core/state_observer.py`
- **Line**: 30
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `"low":    "TODO",`
- **Context**: `"medium": "FIXME",`

### Finding #70

- **File**: `organism/core/state_observer.py`
- **Line**: 69
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `marker = _PRIORITY_MARKER.get(priority, "TODO")`

### Finding #71

- **File**: `organism/core/state_observer.py`
- **Line**: 72
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# "FIXME" → impact +0.2, ev → 0.80 (prioritizer.py scoring)`
- **Context**: `# --- Description tervezés ---`

### Finding #72

- **File**: `organism/core/state_observer.py`
- **Line**: 95
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# text = az "eredeti TODO szöveg" ekvivalense (proposer title-hez és _generate_action-höz)`
- **Context**: `text = f"{marker}: {title}"`

### Finding #73

- **File**: `organism/core/state_observer.py`
- **Line**: 118
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# FONTOS: marker értéket ('FIXME'/'TODO') kell itt tárolni, NEM a priority szintet!`
- **Context**: `"gap_id": gap_id,`

### Finding #74

- **File**: `organism/core/state_observer.py`
- **Line**: 119
- **Type**: TODO
- **Severity**: LOW
- **Text**: `# A prioritizer.py task.metadata.get('priority', 'TODO') alapján tölti be a`
- **Context**: `# FONTOS: marker értéket ('FIXME'/'TODO') kell itt tárolni, NEM a priority szintet!`

### Finding #75

- **File**: `organism/core/state_observer.py`
- **Line**: 121
- **Type**: FIXME
- **Severity**: MEDIUM
- **Text**: `# használ: task['priority'].upper() == 'FIXME'`
- **Context**: `# TaskScore['priority'] mezőt, amit a proposer._generate_action() is_fixme check-je`

### Finding #76

- **File**: `organism/core/state_observer.py`
- **Line**: 122
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `# Ha itt 'medium'/'high' lenne, is_fixme=False → generikus TODO Steps (nem megfelelő)`
- **Context**: `# használ: task['priority'].upper() == 'FIXME'`

### Finding #77

- **File**: `tests/test_sai_tool_selection_file_list.py`
- **Line**: 129
- **Type**: TODO
- **Severity**: MEDIUM
- **Text**: `"grep for TODO in source",`
- **Context**: `"search for errors in log",`
