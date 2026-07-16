# Chunk 3 — Findings #51–#77

## #51 [TODO] organism/core/proposer.py:305
- Severity: MEDIUM
- Text: `- TODO + (verify/test) => concrete test steps`

## #52 [FIXME] organism/core/proposer.py:306
- Severity: MEDIUM
- Text: `- Other FIXME => debug flow`

## #53 [TODO] organism/core/proposer.py:307
- Severity: MEDIUM
- Text: `- Other TODO => implementation flow`

## #54 [FIXME] organism/core/proposer.py:310
- Severity: MEDIUM
- Text: `is_fixme = task['priority'].upper() == 'FIXME'`

## #55 [FIXME] organism/core/proposer.py:312
- Severity: MEDIUM
- Text: `# ===== FIXME: TIMEOUT/CONNECTION ISSUES =====`

## #56 [FIXME] organism/core/proposer.py:319
- Severity: MEDIUM
- Text: `# ===== FIXME: COMPLICATED CONDITIONS/FUTURE WORK =====`

## #57 [FIXME] organism/core/proposer.py:326
- Severity: MEDIUM
- Text: `# ===== FIXME: GENERAL DEBUGGING FLOW =====`

## #58 [FIXME] organism/core/proposer.py:328
- Severity: MEDIUM
- Text: `return ("1. **Read FIXME context** — Review the comment and surrounding code\n"`

## #59 [TODO] organism/core/proposer.py:333
- Severity: MEDIUM
- Text: `# ===== TODO: VERIFICATION/TESTING =====`

## #60 [TODO] organism/core/proposer.py:340
- Severity: MEDIUM
- Text: `# ===== TODO: REFACTORING =====`

## #61 [TODO] organism/core/proposer.py:347
- Severity: HIGH
- Text: `# ===== TODO: PERFORMANCE/SECURITY =====`

## #62 [TODO] organism/core/proposer.py:354
- Severity: LOW
- Text: `# ===== TODO: DOCUMENTATION =====`

## #63 [TODO] organism/core/proposer.py:361
- Severity: MEDIUM
- Text: `# ===== TODO: GENERIC IMPLEMENTATION =====`

## #64 [TODO] organism/core/proposer.py:362
- Severity: MEDIUM
- Text: `return ("1. **Read the TODO context** — Understand the requirement\n"`

## #65 [TODO] organism/core/state_observer.py:7
- Severity: MEDIUM
- Text: `Cél: Az Organism ne csak TODO/FIXME/git diff/terminál-históriát lásson,`

## #66 [FIXME] organism/core/state_observer.py:26
- Severity: MEDIUM
- Text: `# => FIXME marker = high/medium gap-eknek az optimális jelölő`

## #67 [FIXME] organism/core/state_observer.py:28
- Severity: MEDIUM
- Text: `"high":   "FIXME",`

## #68 [FIXME] organism/core/state_observer.py:29
- Severity: MEDIUM
- Text: `"medium": "FIXME",`

## #69 [TODO] organism/core/state_observer.py:30
- Severity: MEDIUM
- Text: `"low":    "TODO",`

## #70 [TODO] organism/core/state_observer.py:69
- Severity: MEDIUM
- Text: `marker = _PRIORITY_MARKER.get(priority, "TODO")`

## #71 [FIXME] organism/core/state_observer.py:72
- Severity: MEDIUM
- Text: `# "FIXME" → impact +0.2, ev → 0.80 (prioritizer.py scoring)`

## #72 [TODO] organism/core/state_observer.py:95
- Severity: LOW
- Text: `# text = az "eredeti TODO szöveg" ekvivalense (proposer title-hez és _generate_action-höz)`

## #73 [FIXME] organism/core/state_observer.py:118
- Severity: MEDIUM
- Text: `# FONTOS: marker értéket ('FIXME'/'TODO') kell itt tárolni, NEM a priority szintet!`

## #74 [TODO] organism/core/state_observer.py:119
- Severity: LOW
- Text: `# A prioritizer.py task.metadata.get('priority', 'TODO') alapján tölti be a`

## #75 [FIXME] organism/core/state_observer.py:121
- Severity: MEDIUM
- Text: `# használ: task['priority'].upper() == 'FIXME'`

## #76 [TODO] organism/core/state_observer.py:122
- Severity: MEDIUM
- Text: `# Ha itt 'medium'/'high' lenne, is_fixme=False → generikus TODO Steps (nem megfelelő)`

## #77 [TODO] tests/test_sai_tool_selection_file_list.py:129
- Severity: MEDIUM
- Text: `"grep for TODO in source",`
