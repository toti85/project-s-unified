# TEST_LOG.md – Moonwell 2-Hour Sprint

**Status:** NOT YET STARTED (awaiting Foundry setup)  
**Sprint Start:** 2026-01-29  
**Sprint Duration:** 2 hours hard cap  
**Last Updated:** 2026-01-29

---

## Sprint Execution Timeline

| Time | Phase | Status | Notes |
|------|-------|--------|-------|
| T+0:00 | Scope acquisition | ✅ COMPLETE | Moonwell repos identified; in-scope contracts listed |
| T+0:15 | TV1 setup | NOT STARTED | mToken exchange rate harness |
| T+0:45 | TV1 execution | NOT STARTED | Run 100-cycle rounding test |
| T+1:00 | TV2 setup | NOT STARTED | Liquidation close factor harness |
| T+1:30 | TV2 execution | NOT STARTED | Run close factor boundary test |
| T+1:45 | TV3 setup | NOT STARTED | Interest accrual timestamp harness |
| T+2:00 | STOP | — | Hard cap; record findings and exit |

---

## Test Execution Log (To Be Filled)

### TV1-S1: mToken Exchange Rate Rounding

**Scheduled:** T+0:15–T+0:45 (30 min)  
**Status:** PENDING

```
// PLACEHOLDER: Foundry test structure

// forge test --match-test "test_exchange_rate_rounding"
// 
// function test_exchange_rate_rounding() public {
//     // Setup: Deploy mToken with mock ERC20 underlying
//     // Scenario: User deposits, borrows, repays cycle 100x
//     // Assert: abs(exchange_rate_final - exchange_rate_initial) < tolerance
// }
```

**Expected Command:**
```bash
cd /moonwell/core-contracts  # or appropriate repo path
forge test --match-test "test_exchange_rate_rounding" -vvv
```

**Expected Result:**
- PASS: Rounding drift within tolerance → CLOSED
- FAIL: Cumulative drift > threshold → Investigate (AMBIGUOUS/SUBMIT)

---

### TV2-S4: Close Factor Bypass

**Scheduled:** T+1:00–T+1:30 (30 min)  
**Status:** PENDING

```
// PLACEHOLDER: Foundry test structure

// forge test --match-test "test_close_factor_boundary"
//
// function test_close_factor_boundary() public {
//     // Setup: Position with debt = 100e18
//     // closeFactorMantissa = 0.5
//     // Scenario: Liquidate with debt_repay = closeFactorMantissa * debt + 1
//     // Assert: Liquidation reverts OR debt_repaid ≤ allowed
// }
```

**Expected Command:**
```bash
cd /moonwell/core-contracts
forge test --match-test "test_close_factor_boundary" -vvv
```

**Expected Result:**
- PASS: Liquidation blocked or enforced → CLOSED
- FAIL: Over-repayment allowed → SUBMIT (exploit found)

---

### TV3-S1: Interest Accrual Timestamp

**Scheduled:** T+1:45–T+2:00 (15 min, trimmed)  
**Status:** PENDING

```
// PLACEHOLDER: Foundry test structure

// forge test --match-test "test_interest_double_accrual"
//
// function test_interest_double_accrual() public {
//     // Setup: mToken with debt and rate
//     // Scenario: Call accrueInterest() twice in same block
//     // Assert: Second call detects zero block advancement; no re-accrual
// }
```

**Expected Command:**
```bash
cd /moonwell/core-contracts
forge test --match-test "test_interest_double_accrual" -vvv
```

**Expected Result:**
- PASS: No double accrual → CLOSED
- FAIL: Interest accrues twice → SUBMIT (exploit found)

---

## Findings Log (To Be Populated)

| TV | Result | Finding | Status |
|----|--------|---------|--------|
| TV1 | — | (pending) | PENDING |
| TV2 | — | (pending) | PENDING |
| TV3 | — | (pending) | PENDING |

---

## Sprint Conclusion

**Time Remaining:** (to be updated at T+2:00)

**Summary:**
- TV1: [CLOSED / AMBIGUOUS / SUBMIT]
- TV2: [CLOSED / AMBIGUOUS / SUBMIT]
- TV3: [CLOSED / AMBIGUOUS / SUBMIT]

**Next Action:** [Exit clean / Prepare exploit / Continue investigation]

---

## Notes for Next Phase (If Findings Found)

1. If SUBMIT-ready: Prepare detailed repro steps
2. Capture numeric proof JSON with before/after snapshots
3. Write minimal PoC code demonstrating invariant break
4. Document exploit preconditions and impact
5. Submit to Code4rena bounty form

