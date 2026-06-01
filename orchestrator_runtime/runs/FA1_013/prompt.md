# Cline Prompt: FA1_013

**Run ID:** FA1_013
**Drafted:** 2026-05-26T08:08:36.153943Z

---

## INSTRUCTIONS

**IMPORTANT: Read all instructions before starting.**

### SAFETY BOUNDARY — DO NOT VIOLATE

- You may **ONLY** modify files under `C:\ProjectS-Unified\orchestrator_runtime\sandbox`
- Do **NOT** modify any files outside the sandbox
- Do **NOT** modify any config, router, or server files
- Do **NOT** make external network calls

### TASK

NAGY CÉL — MS-FA1 AUTO MODE V1 READINESS PACKAGE

Készíts egy teljes Auto Mode v1 readiness csomagot a Project-S MS-FA1 rendszerhez.

A cél nem új funkció implementálása, hanem annak felmérése és dokumentálása, hogy a rendszer készen áll-e korlátozott auto módra.

Feladatok:
1. Nézd át az MS-FA1 eddigi evidence/report anyagait:
   - FA1.1 manual loop
   - FA1.2 semi-automated loop
   - FA1.2H hardening
   - FA1.3 AI prompt drafter + evaluator
   - FA1.4 controlled multi-iteration
   - FA1.5 file-based handoff polling
   - Hardening 001 AI prompt drafting
   - Hardening 002 AI verdict evaluator

2. Készíts egy Auto Mode v1 policy dokumentumot:
   - mi engedélyezett automatikusan;
   - mi tiltott;
   - mikor kell NEEDS_HUMAN;
   - max iteráció;
   - safety stop feltételek;
   - sandbox/docs-only szabályok.

3. Készíts egy operátori használati példát:
   - hogyan adunk meg egy nagy célt;
   - hogyan bontja Project-S részfeladatokra;
   - hogyan kerül Cline-hoz a prompt;
   - hogyan jön vissza az output;
   - hogyan születik verdict;
   - mikor áll meg.

4. Készíts egy readiness verdictet:
   - Auto Mode v1: READY / PARTIAL / NOT READY;
   - milyen taskokra engedhető;
   - milyen taskokra nem;
   - mi legyen a következő lépés.

Korlátok:
- Ne módosíts src/core fájlokat.
- Ne módosíts interactive_layer fájlokat.
- Ne módosíts self_state.json-t.
- Ne módosíts router/server/network configot.
- Ne törölj fájlokat.
- Ne csinálj git commitot/tag-et.
- Dokumentációs és report feladatként kezeld.

Elvárt kimenetek:
1. reports/MS_FA1_AUTO_MODE_V1_POLICY_20260524.md
2. reports/MS_FA1_AUTO_MODE_V1_OPERATOR_EXAMPLE_20260524.md
3. reports/MS_FA1_AUTO_MODE_V1_READINESS_VERDICT_20260524.md

Végén add vissza:
A. Nagy cél részfeladatokra bontva? yes/no
B. Auto Mode policy elkészült? yes/no
C. Operator example elkészült? yes/no
D. Readiness verdict elkészült? yes/no
E. Auto Mode v1 státusz: READY / PARTIAL / NOT READY
F. Bármilyen production fájl módosult? yes/no
G. Safety violation count
H. Következő ajánlott lépés

### Deliverables

Create the requested files in the sandbox directory.
Include unit tests where applicable.

### Testing

- Run all tests before completing
- All tests must pass

### Final Output

After completing the task, write your final report to:

```
C:\ProjectS-Unified\orchestrator_runtime\cline_outbox\last_output.md
```

The report must include:
- What was created/modified
- Test results
- Any issues encountered
- Files changed (full paths)

---
