# DECISIONS.md – Moonwell 2-Hour Sprint

**Status:** PRE-SPRINT (decision log initialized)  
**Last Updated:** 2026-01-29  
**Sprint Duration:** 2 hours hard cap

---

## Strategic Decision: Moonwell Sprint Activation

**Date:** 2026-01-29  
**Rationale:**
- Moonwell Code4rena bug bounty identified (continuous, not timed)
- Max bounty $250k USD (higher EV than opportunistic OLAS)
- Scope is compact: core lending invariants (mToken, Comptroller, interest)
- 2-hour constraint enables rapid threat assessment

**Decision:** INITIATE Moonwell sprint with TOP 3 threat vectors.

---

## Pivot from Jupiter Lend

**Previous Plan:** Jupiter Lend strategic audit (Solana, 1-month engagement)  
**New Plan:** Moonwell rapid sprint (EVM, 2-hour assessment)  
**Rationale:**
- Moonwell bounty active now; Jupiter not until Feb 4
- EVM testing faster than Solana (Foundry vs Anchor)
- Moonwell has tighter scope (lending core vs multichain gov)
- 2-hour sprint de-risks time; quick exit if no exploits

**Status:** ACTIVE (parallel: Jupiter pre-scope docs remain complete for Feb 4)

---

## Threat Vector Prioritization

**Ranking Methodology:**
- **Probability of Exploit:** Based on complexity of accounting/rounding logic
- **Economic Impact:** Core invariants (exchange rate, close factor, accrual)
- **Testing Feasibility:** Can be tested in unit tests without external dependencies

**Top 3 Selected:**
1. **TV1-S1 (mToken Exchange Rate Rounding)** — State invariant; high probability
2. **TV2-S4 (Close Factor Boundary)** — Economic edge case; medium-high probability
3. **TV3-S1 (Interest Accrual Timestamp)** — State invariant; medium probability

**Deferred (Out of 2h Budget):**
- TV4-S2 (Oracle Staleness) — Requires oracle mock + 3rd party contracts
- TV5-S5 (Pause Guardian) — Governance role testing; complex setup

---

## Test Execution Plan

**Phase 1 (30 min):** TV1 harness + 100-cycle test  
**Phase 2 (30 min):** TV2 harness + boundary test  
**Phase 3 (15 min):** TV3 harness + accrual test  
**Reserve (15 min):** Findings documentation + exit  

**Testing Method:** Foundry unit tests (local; no mainnet)

---

## Exit Decision Tree (T+120 min)

```
IF all 3 TVs CLOSED
  → Record "No exploits found in Moonwell core lending"
  → Exit cleanly
  → Mark bounty as assessed

IF 1+ TV AMBIGUOUS
  → Continue if time permits (unlikely at 2h mark)
  → Document ambiguity + preconditions
  → Recommend deeper investigation post-sprint

IF 1+ TV SUBMIT-ready
  → Prepare minimal exploit PoC
  → Document numeric proof (before/after snapshots)
  → Record finding with impact estimate
  → Prepare Code4rena submission

IF time exceeded
  → Hard stop at T+120 min
  → Record partial results
  → Exit sprint
```

---

## Known Issues Excluded (No Points)

Per Moonwell's bug bounty scope:
- Reward accrual without claim() (design feature)
- Collateral seizure without enterMarkets() (design feature)
- Collateral factor = 0 bootstrap (design feature)
- Governance timestamp drift (design risk, out of scope)
- Wormhole dependency (3rd party contract)

**Decision:** Focus only on core accounting logic bugs; skip known issues.

---

## Scope Constraints

**Testing Restrictions:**
- No mainnet or public testnet (private testnets only)
- No oracle contract testing (3rd party, out of scope)
- No governance role exploitation (trusted roles excluded)
- No social engineering, phishing, or DoS

**Decision:** All tests will be local Foundry unit tests; no external dependencies.

---

## Previous Bounty Learnings Applied

**Kinetiq (Design vs Exploit):**
- Lesson: Distinguish design feature from invariant break
- Applied: Each TV tests numeric invariant, not design choice

**Pendle (Scope Clarity):**
- Lesson: Confirm boundaries upfront
- Applied: TARGET.md lists all in/out of scope items

**Polygon zkEVM (Exit Criteria):**
- Lesson: Don't extend if no exploit path found
- Applied: 2h hard cap; TV1–TV3 only; hard stop at T+120 min

---

## Success Definition

**Optimal:** 1 Critical finding (potential $100k–$250k depending on impact)  
**Good:** Multiple Medium findings ($1k–$5k each)  
**Clean:** All TVs CLOSED; clean exit; no exploits found  

**Any outcome is valid:** Sprint goal is rapid threat assessment, not guaranteed payout.

---

## Contingency Plans

**If Foundry setup blocked:**
- Pivot to Solidity static analysis (code review)
- Document findings as low-confidence hypotheses

**If test harness fails:**
- Skip to next TV
- Prioritize by probability

**If time overrun:**
- Hard stop at T+2:00 regardless
- Record partial results
- Exit sprint

---

## Decision Log (To Be Updated)

| Time | Decision | Reason | Status |
|------|----------|--------|--------|
| T+0:00 | Activate Moonwell sprint | $250k bounty; EVM testing fast | ✅ ACTIVE |
| T+0:30 | Focus top 3 TVs | Time constraint; high-probability targets | ✅ ACTIVE |
| T+1:30 | Exit decision pending | Results pending test completion | ⏳ PENDING |
| T+2:00 | Sprint conclusion | Hard stop; record findings | ⏳ PENDING |

---

## Next Action

**Immediate (T+0:15):** Begin Foundry harness setup for TV1.  
**At T+0:45:** Transition to TV2.  
**At T+1:45:** Transition to TV3 (trimmed).  
**At T+2:00:** Hard stop; finalize STATUS.md and conclude sprint.

