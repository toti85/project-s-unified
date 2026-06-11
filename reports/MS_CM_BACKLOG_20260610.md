# MS-CM / Sz Backlog — 2026-06-09

**Created:** 2026-06-09
**Status:** BACKLOG — Not blocking Ghost Branch
**Priority Order:** BACKLOG_003 (HIGH) > BACKLOG_001 (MEDIUM) > BACKLOG_002 (LOW)

---

## Current Priority (MOST)

**MS-CM v0.1 + Ghost Branch / Kódrégész**

This is the immediate next step. All backlog items below must NOT block this.

### Immediate Actions:
1. Sz név rögzítése
2. pending self_state update
3. MS-CM v0.1 indítás
4. Ghost Branch / Kódrégész első mission
5. 10 relevancia-link + 1 resurrection proposal

---

## BACKLOG_003 — Compute Arbiter Model Cost Matrix

**Priority:** HIGH
**Timing:** After Ghost Branch initial mission, before Compute Arbiter v0.1
**Status:** PENDING

### Source
Pintér Zsolt video table / NBA test model comparison

### Action
Extract model cost/performance table and convert it into an initial Compute Arbiter config.

### Output
- `orchestrator_runtime/modelvault/compute_arbiter_cost_matrix.json`
- `reports/MS_CM_COMPUTE_ARBITER_COST_MATRIX_202606.md`

### Goal
Create initial routing hints for:
- local model vs OpenRouter
- cheap model vs frontier model
- coding task vs reasoning task vs summarization task
- expected cost
- expected reliability
- when to escalate

### Reason
Directly useful for Compute Arbiter v0.1 and OpenRouter cost control.

### Risk
Benchmark may not match Project-S tasks. Treat as seed data, not truth.

---

## BACKLOG_001 — Hermes Agent Comparison Study

**Priority:** MEDIUM
**Timing:** After MS-CM v0.1 + Ghost Branch initial run
**Status:** PENDING

### Action
Read hermes-agent.nousresearch.com/docs/ and compare Hermes architecture with Project-S / Sz.

### Output
`reports/MS_CM_HERMES_VS_PROJECT_S_COMPARISON_202606.md`

### Goal
Produce:
- 5–10 capabilities Hermes has that Sz / Project-S currently lacks
- 5–10 capabilities Project-S has that are unique or stronger
- 3 concrete ideas worth importing
- 3 ideas explicitly rejected as not fitting Project-S
- final verdict: inspiration only / compatibility target / no action

### Reason
Vision validation and external architecture comparison.

### Risk
Can become distraction/meta-research. Must not block Ghost Branch.

---

## BACKLOG_002 — agentskills.io Compatibility Probe

**Priority:** LOW
**Timing:** 3–6 month horizon
**Status:** PENDING

### Action
Check whether Project-S / Sz output formats could converge with agentskills.io-style skill packaging.

### Output
`orchestrator_runtime/sandbox/agentskills_compat_probe.md`

### Goal
Answer:
- Can Sz proposals become portable skills?
- Can Project-S missions be expressed as reusable skill manifests?
- What metadata would be needed?
- Is portability worth preserving now, or premature?

### Reason
Future interoperability.

### Risk
Premature standardization. Do not reshape Project-S around an external skill format yet.

---

## Summary

| Backlog | Priority | Timing | Status |
|---------|----------|--------|--------|
| BACKLOG_003 — Compute Arbiter Cost Matrix | HIGH | After Ghost Branch initial mission | PENDING |
| BACKLOG_001 — Hermes Agent Comparison | MEDIUM | After MS-CM v0.1 + Ghost Branch | PENDING |
| BACKLOG_002 — agentskills.io Compatibility | LOW | 3–6 month horizon | PENDING |

**Decision:**
- BACKLOG_003 = HIGH, mert később pénzt spórolhat
- BACKLOG_001 = MEDIUM, mert architektúra-validáció
- BACKLOG_002 = LOW, mert túl korai standardizáció

**Holnapi főszál marad:**
1. Sz név rögzítése
2. pending self_state update
3. MS-CM v0.1 indítás
4. Ghost Branch / Kódrégész első mission
5. 10 relevancia-link + 1 resurrection proposal

Ezek a backlogok jók, csak ne engedd, hogy a Ghost Branch elé kerüljenek.