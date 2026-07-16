# Chunk 1 — Findings #1–#25

## #1 [TODO] debug_kill_list.py:40
- Severity: LOW
- Text: `metadata={'priority': todo.get('priority', 'TODO')}`

## #2 [TODO] debug_kill_list.py:73
- Severity: LOW
- Text: `metadata={'priority': todo.get('priority', 'TODO')}`

## #3 [TODO] debug_rabbit_hole.py:37
- Severity: LOW
- Text: `metadata={'priority': todo.get('priority', 'TODO')}`

## #4 [TODO] debug_rabbit_hole.py:63
- Severity: LOW
- Text: `metadata={'priority': todo.get('priority', 'TODO')}`

## #5 [TODO] debug_rabbit_hole.py:89
- Severity: LOW
- Text: `metadata={'priority': todo.get('priority', 'TODO')}`

## #6 [TODO] debug_rename_detailed.py:31
- Severity: LOW
- Text: `metadata={'priority': todo.get('priority', 'TODO')}`

## #7 [TODO] test_kill_detection_mock.py:29
- Severity: MEDIUM
- Text: `description="[TODO] Rename to EcdsLibStub (file:7)",`

## #8 [TODO] test_kill_detection_mock.py:34
- Severity: LOW
- Text: `metadata={"priority": "TODO"}`

## #9 [TODO] test_protection_direct.py:18
- Severity: MEDIUM
- Text: `snippet="# TODO: Test with dust amounts (1 wei, etc.)",`

## #10 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:4
- Severity: LOW
- Text: `Operator scans the repository for TODO/FIXME/XXX markers.`

## #11 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:50
- Severity: LOW
- Text: `TODO_PATTERN = re.compile(r"\\b(TODO|FIXME|XXX)\\b")`

## #12 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:117
- Severity: LOW
- Text: `Scan all Python files under root for TODO/FIXME/XXX.`

## #13 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:256
- Severity: LOW
- Text: `print("\n[PHASE 1] Scanning repository for TODO/FIXME/XXX in Python files...")`

## #14 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:269
- Severity: LOW
- Text: `print(f"  By type: TODO={type_counts.get('TODO',0)} FIXME={type_counts.get('FIXME',0)} XXX={type_counts.get('XXX',0)}")`

## #15 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:292
- Severity: LOW
- Text: `# PROJECT-S TODO/FIXME/XXX AUDIT`

## #16 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:295
- Severity: LOW
- Text: `State: date of scan ({scan_ts[:10]}), Python files scanned ({files_scanned}), files with findings ({files_with}), total findings ({scan_count}), breakdown by type (TODO: {type_counts.get('TODO',0)}, FIXME: {type_counts.get('FIXME',0)}, XXX: {type_counts.get('XXX',0)}).`

## #17 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:298
- Severity: LOW
- Text: `{"If there are no findings, write: No TODO/FIXME/XXX markers were found." if scan_count == 0 else f"For each of the {scan_count} findings above, list: file path, line number, type, the text, surrounding context, and severity classification."}`

## #18 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:349
- Severity: LOW
- Text: `"type": "<TODO|FIXME|XXX>",`

## #19 [TODO] orchestrator_runtime/sandbox/ornith_executor_trial/run_ao9_t5.py:434
- Severity: LOW
- Text: `Findings by type: TODO={type_counts.get('TODO',0)}, FIXME={type_counts.get('FIXME',0)}, XXX={type_counts.get('XXX',0)}`

## #20 [TODO] organism/core/loop.py:73
- Severity: LOW
- Text: `text=todo['text'],  # Original TODO/FIXME text`

## #21 [TODO] organism/core/observer.py:6
- Severity: LOW
- Text: `- Extract TODO/FIXME annotations`

## #22 [TODO] organism/core/observer.py:30
- Severity: LOW
- Text: `"""TODO annotation found in source."""`

## #23 [TODO] organism/core/observer.py:34
- Severity: LOW
- Text: `priority: str  # 'TODO', 'FIXME'`

## #24 [TODO] organism/core/observer.py:55
- Severity: LOW
- Text: `text: str = ""  # Original TODO/FIXME text`

## #25 [TODO] organism/core/observer.py:177
- Severity: LOW
- Text: `Scan source files for TODO/FIXME annotations in actual code comments only.`
