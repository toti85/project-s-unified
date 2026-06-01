# STATUS.md – Moonwell 2-Hour Sprint

**Status:** IN PROGRESS (Sprint started 2026-01-29)  
**Sprint Duration:** 2 hours hard cap  
**Current Phase:** Scope acquisition COMPLETE; TV execution NOT YET STARTED

---

## Sprint Summary

| Task | Status | Completion |
|------|--------|-----------|
| Acquire scope (TARGET.md) | ✅ COMPLETE | 15 min |
| Generate TVs (THREAT_VECTORS.md) | ✅ COMPLETE | 15 min |
| Setup harness (CODE) | ❌ NOT STARTED | (30 min budget) |
| TV1 execution | ⏳ PENDING | (30 min budget) |
| TV2 execution | ⏳ PENDING | (30 min budget) |
| TV3 execution (trimmed) | ⏳ PENDING | (15 min budget) |
| Findings consolidation | ⏳ PENDING | (varies) |

---

## Scope Acquired

**Protocol:** Moonwell (continuous Code4rena bounty)  
**Blockchains:** Base, Optimism, Moonbeam, Moonriver  
**Max Bounty:** $250k USD (minimum $100k per Critical)  
**Focus:** Core lending (mToken, Comptroller, interest accrual)  
**Repos:** https://github.com/moonwell-fi  

---

## Threat Vectors Status

| TV | Category | Rank | Hypothesis | Status |
|----|----------|------|-----------|--------|
| TV1-S1 | Accounting | #1 | mToken exchange rate rounding drift | OPEN |
| TV2-S4 | Liquidation | #2 | Close factor boundary bypass | OPEN |
| TV3-S1 | Interest | #3 | Accrual timestamp skip | OPEN |
| TV4-S2 | Oracle | #4 | Staleness not checked | OPEN |
| TV5-S5 | Access | #5 | Pause guardian escalation | OPEN |

---

## Test Plan

**Testing Strategy:** Foundry unit tests (no mainnet/testnet)  
**Top 3 Focus:** TV1, TV2, TV3  
**Time Budget:** 90 minutes (tests), 30 minutes (results + exit)

### Phase 1: TV1 Setup & Execution (30 min)
- Deploy mock mToken contract
- Simulate 100 deposit/withdraw/redeem cycles
- Assert exchange rate rounding drift
- Conclusion: CLOSED / AMBIGUOUS / SUBMIT

### Phase 2: TV2 Setup & Execution (30 min)
- Mock Comptroller liquidation
- Test close factor boundary with edge debt amounts
- Assert close factor enforcement
- Conclusion: CLOSED / AMBIGUOUS / SUBMIT

### Phase 3: TV3 Setup & Execution (15 min, trimmed)
- Mock accrueInterest logic
- Test double-accrual with zero block advancement
- Assert monotonic debt increase
- Conclusion: CLOSED / AMBIGUOUS / SUBMIT

---

## Exit Criteria (T+2:00)

| Outcome | Decision |
|---------|----------|
| All 3 CLOSED | Record findings; clean exit; no exploits |
| 1+ AMBIGUOUS | Continue refinement (if time permits) |
| 1+ SUBMIT-ready | Prepare minimal PoC; record finding |
| Time reached | Hard stop; record status; exit |

---

## Known Constraints

**Out of Scope (Skipped):**
- Oracle staleness testing (3rd party oracle contracts out of scope)
- Pause guardian escalation testing (governance role testing excluded)
- Wormhole bridge testing (3rd party dependency)
- Mainnet/testnet execution (unit tests only)

**Known Issues Excluded:**
- Reward accrual without claim() (by design)
- Collateral seizure without enterMarkets() (by design)
- Governance timestamp drift > 45s (by design)

---

## Success Metrics

✅ **Scope Acquisition:** Complete  
✅ **TV Generation:** Complete (5 TVs, top 3 ranked)  
⏳ **TV Testing:** In progress (0 of 3 complete)  
⏳ **Findings:** Pending test results

---

## Next Update: T+2:00 (Sprint Conclusion)

- All tests completed or time expired
- Findings consolidated
- Exit decision recorded
- Pivot status finalized

