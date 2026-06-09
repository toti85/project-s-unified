# Risk Backlog — Project-S Governance

## RISK_010 — Cline post-checksum modification

**Discovered:** 2026-06-10
**Pattern:** Cline writes `output_ready.json` with checksum X,
then makes a final formatting pass on `last_output.md`,
producing checksum Y. Bridge_runner rejects.
**Frequency:** 3/3 missions (AO5_T6, AO5_T7_CWI)
**Root cause:** Order of operations — checksum computed before
`last_output.md` is truly final.
**Fix:** Mandatory order:
  1. Write `last_output.md` (FINAL — no more edits)
  2. Compute checksum from file bytes
  3. Write `output_ready.json` LAST
  4. STOP — never touch `last_output.md` after step 3
**Status:** DOCUMENTED — rule added to Cline instructions