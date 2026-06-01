# THREAT_VECTORS.md – Moonwell 2-Hour Sprint

**Status:** PRE-TEST (5 TVs preseed, top 3 ranked)  
**Last Updated:** 2026-01-29  
**Testing Duration:** 90 minutes (3 TVs max)

---

## TV Coverage & Ranking

| Rank | TV ID | Category | Hypothesis | Status |
|------|-------|----------|-----------|--------|
| **1** | TV1-S1 | Accounting | mToken exchange rate rounding → cumulative drift | OPEN |
| **2** | TV2-S4 | Liquidation | Close factor enforcement bypass in edge cases | OPEN |
| **3** | TV3-S1 | Interest | Interest accrual timestamp not updated mid-transaction | OPEN |
| 4 | TV4-S2 | Oracle | Chainlink oracle staleness not checked (stale price used) | OPEN |
| 5 | TV5-S5 | Access | Comptroller market admin actions bypass pause guardian | OPEN |

---

## TV1-S1: mToken Exchange Rate Rounding Drift

**Rank:** 1 (HIGHEST PROBABILITY)  
**Category:** S1 (State Invariants - Accounting)  
**Hypothesis:** 
Exchange rate = totalBorrows / totalSupply calculated with integer rounding.  
Over many transactions, rounding errors accumulate; lender receives <expected redemption value.

**Invariant at Risk:**
```
(mToken.balanceOf[user] * exchangeRate) ≈ underlying_owed[user]
```

**Target Function:**
- `Comptroller.exchangeRateStored()` → ExchangeRateModel
- `mToken.redeemInternal()` → Share redemption calculation

**Required Proof (JSON):**
```json
{
  "num_transactions": 100,
  "exchange_rate_t0": 1000000000000000000,
  "exchange_rate_final": 1000000000000000001,
  "rounding_drift_detected": true,
  "user_balance_before": 10000000000000000000,
  "expected_redemption": 10000100000000000000,
  "actual_redemption": 10000099000000000000,
  "loss_per_share": 1000000000,
  "cumulative_loss": 10000000000
}
```

**Status:** OPEN

---

## TV2-S4: Close Factor Boundary Bypass

**Rank:** 2 (HIGH PROBABILITY)  
**Category:** S4 (Economic - Liquidation)  
**Hypothesis:**
Close factor = 50% (typical). Liquidator can repay > 50% by exploiting edge case:
- Debt rounds down in validation check
- Debt rounds up in actual repayment
- Close factor violated

**Invariant at Risk:**
```
debt_repaid ≤ closeFactorMantissa * debt_current (typically 0.5)
```

**Target Function:**
- `Comptroller.liquidateCalculateSeizeTokens()`
- `mToken.liquidateBorrow()` → Close factor check

**Required Proof (JSON):**
```json
{
  "debt_current": 100000000000000000000,
  "close_factor_pct": 5000,
  "max_debt_allowed": 50000000000000000000,
  "debt_repay_requested": 50000000000000000001,
  "close_factor_check_passed": true,
  "debt_repaid_actual": 50000000000000000001,
  "violation": true,
  "excess_repay": 1
}
```

**Status:** OPEN

---

## TV3-S1: Interest Accrual Timestamp Skip

**Rank:** 3 (MEDIUM-HIGH PROBABILITY)  
**Category:** S1 (State Invariants - Interest)  
**Hypothesis:**
Interest accrues based on block timestamp: `debt_new = debt_old * (1 + rate * Δt)`.
If `accrualBlockNumber` not updated after accrual, next call re-accrues same time period.

**Invariant at Risk:**
```
debt[t2] ≥ debt[t1] for all t2 > t1 (monotonic)
Δdebt = debt_old * rate * Δt (accurate time delta)
```

**Target Function:**
- `mToken.accrueInterest()`
- `mToken.accrualBlockNumber` state variable

**Required Proof (JSON):**
```json
{
  "debt_before": 1000000000000000000,
  "interest_rate_per_block": 100000000000000,
  "block_before": 1000,
  "block_after_accrual": 2000,
  "accrual_block_updated": false,
  "debt_after_accrual_call_1": 1100000000000000000,
  "debt_after_accrual_call_2": 1200000000000000000,
  "double_accrual": true,
  "expected_debt": 1100000000000000000,
  "actual_debt": 1200000000000000000
}
```

**Status:** OPEN

---

## TV4-S2: Oracle Staleness Not Checked

**Rank:** 4 (MEDIUM)  
**Category:** S2 (Cross-Contract - Oracle)  
**Hypothesis:**
Chainlink oracle price fetched without staleness check.
If price feed updates infrequently (e.g., > 1 hour), stale price used for liquidation.

**Invariant at Risk:**
```
price_age = now - price_timestamp ≤ maxStaleness (e.g., 3600 seconds)
```

**Status:** OPEN (requires oracle mock; skip in 2h sprint)

---

## TV5-S5: Pause Guardian Authority Escalation

**Rank:** 5 (MEDIUM)  
**Category:** S5 (Access Control)  
**Hypothesis:**
Pause Guardian can pause markets. Can they also unpause without governor approval?
Or call admin functions while paused?

**Invariant at Risk:**
```
pauseGuardian ≠ governor (role isolation)
pauseGuardian can only call pause(), not unpause() or _setXXX()
```

**Status:** OPEN (requires governance testing; skip in 2h sprint)

---

## Test Execution Plan (90 minutes)

### Phase 1 (30 min): TV1 Test
- Create local mToken with exchange rate calculation
- Run 100 deposit/withdraw/redeem cycles
- Assert rounding drift ≤ expected tolerance

### Phase 2 (30 min): TV2 Test
- Mock liquidation scenario
- Test close factor boundary with edge-case debt amounts
- Assert debt_repaid ≤ closeFactorMantissa * debt

### Phase 3 (30 min): TV3 Test
- Mock accrueInterest with timestamp logic
- Call accrue twice without block advance
- Assert debt doesn't double-accrue

---

## Exit Decision (90 min mark)

| Outcome | Decision |
|---------|----------|
| All 3 CLOSED | Record clean findings; Exit bounty (no exploits) |
| 1+ SUBMIT-ready | Prepare exploit PoC; Record finding |
| 1+ AMBIGUOUS | Continue refinement; may exceed 2h |
| Time reached | Stop; record findings and exit |

