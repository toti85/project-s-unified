# Chunk 2 — Findings #26–#50

## #26 [TODO] organism/core/observer.py:213
- Severity: LOW
- Text: `# Python format: ^(\\s*)#\\s*(TODO|FIXME)`

## #27 [TODO] organism/core/observer.py:214
- Severity: LOW
- Text: `# JavaScript format: ^(\\s*)//(TODO|FIXME)`

## #28 [TODO] organism/core/observer.py:219
- Severity: LOW
- Text: `# Check if line is a Python comment with TODO/FIXME`

## #29 [TODO] organism/core/observer.py:224
- Severity: MEDIUM
- Text: `py_match = re.match(r'#\\s*(TODO|FIXME)[:\\s]+(.*?)(?:\\s*$)', stripped)`

## #30 [TODO] organism/core/observer.py:226
- Severity: LOW
- Text: `# Check if line is a JavaScript/Solidity comment with TODO/FIXME`

## #31 [TODO] organism/core/observer.py:228
- Severity: MEDIUM
- Text: `js_match = re.match(r'//\\s*(TODO|FIXME)[:\\s]+(.*?)(?:\\s*$)', stripped)`

## #32 [TODO] organism/core/observer.py:234
- Severity: MEDIUM
- Text: `priority = match.group(1)  # 'TODO' or 'FIXME'`

## #33 [TODO] organism/core/prioritizer.py:29
- Severity: LOW
- Text: `text: str          # Original TODO/FIXME text`

## #34 [TODO] organism/core/prioritizer.py:36
- Severity: LOW
- Text: `priority: str      # 'TODO' or 'FIXME'`

## #35 [FIXME] organism/core/prioritizer.py:61
- Severity: MEDIUM
- Text: `'FIXME': 1.0,`

## #36 [TODO] organism/core/prioritizer.py:66
- Severity: MEDIUM
- Text: `'TODO': 0.6,`

## #37 [FIXME] organism/core/prioritizer.py:76
- Severity: LOW
- Text: `- FIXME items: high impact (0.8-1.0)`

## #38 [TODO] organism/core/prioritizer.py:129
- Severity: LOW
- Text: `# Easy tasks: typo, doc, comment, rename, TODO cleanup`

## #39 [FIXME] organism/core/prioritizer.py:137
- Severity: MEDIUM
- Text: `elif 'fix' in text_combined and 'FIXME' not in task.text:`

## #40 [TODO] organism/core/prioritizer.py:139
- Severity: LOW
- Text: `# Standard TODO`

## #41 [TODO] organism/core/prioritizer.py:140
- Severity: MEDIUM
- Text: `elif 'TODO' in task.text:`

## #42 [FIXME] organism/core/prioritizer.py:142
- Severity: LOW
- Text: `# FIXME usually harder`

## #43 [FIXME] organism/core/prioritizer.py:143
- Severity: MEDIUM
- Text: `elif 'FIXME' in task.text:`

## #44 [FIXME] organism/core/prioritizer.py:195
- Severity: LOW
- Text: `- If file contains \"/test/\" and FIXME: +0.15 bonus`

## #45 [FIXME] organism/core/prioritizer.py:210
- Severity: LOW
- Text: `# Test file FIXME = higher confidence`

## #46 [FIXME] organism/core/prioritizer.py:211
- Severity: MEDIUM
- Text: `if '/test/' in task.file.lower() and task.metadata.get('priority') == 'FIXME':`

## #47 [TODO] organism/core/prioritizer.py:225
- Severity: MEDIUM
- Text: `elif 'TODO' in task.text and 'verify' in text_combined:`

## #48 [TODO] organism/core/prioritizer.py:562
- Severity: MEDIUM
- Text: `'priority': task.metadata.get('priority', 'TODO'),`

## #49 [FIXME] organism/core/proposer.py:303
- Severity: LOW
- Text: `- FIXME + (timeout/connection) => config/refactor steps`

## #50 [FIXME] organism/core/proposer.py:304
- Severity: LOW
- Text: `- FIXME + (complicated/conditions/implement in future) => spec-first steps`
