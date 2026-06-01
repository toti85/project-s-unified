# Jupiter Lend — Finding H2 Adaptation Notes

**Status:** Fork-ready variant prep for Feb 4 audit window (if Jupiter is targeted)

---

## Executive Summary

Fluid H2 (Cascading Liquidation @ 95% LTV) translates to Jupiter Lend **if and only if** the following parameters match:

| Parameter | Fluid (Ethereum) | Jupiter (Solana) | Status |
|-----------|---|---|---|
| LTV Claim | 95% safe borrow | [VERIFY] | ❓ Requires Jupiter docs |
| Oracle Lag | 1-5 blocks (Ethereum) | 1-3 slots (Solana, ~400ms) | ✅ Faster, same class |
| Liquidation Mechanism | DEX-based (Uniswap) | DEX-based (Orca/Marinade) | ✅ Equivalent |
| Liquidator Incentive | Fee + slippage recovery | [VERIFY] | ❓ Requires contract audit |
| Collateral Depegging Risk | bSOL (Lido wrapper) | [VERIFY] | ❓ Check supported collateral |

---

## Part 1: What Transfers 1:1

✅ **Causal Chain Structure:**
1. User borrows 95% LTV (if claim exists)
2. Collateral depegs 5% in 2 slots
3. Oracle updates with lag (Solana ~400ms < Ethereum 12sec, so FASTER recovery = MORE SAFE)
4. Liquidations begin
5. DEX slippage prevents liquidator profit
6. Bad debt accrues

✅ **Probability Model:** Same framework applies
- Oracle lag: ✅ (faster on Solana)
- Price drop: ✅ (same 5% depegging scenarios)
- DEX liquidity: ❓ (Solana DEX depth varies; Orca < Uniswap)
- Position distribution: ❓ (Jupiter TVL vs. Fluid TVL unknown)

✅ **Mitigations:** All 3 apply (Backstop, Dynamic LTV, Disclosure)

---

## Part 2: What Requires Re-Verification

### 2.1 Jupiter's LTV Claims (CRITICAL)

**Action:** Search Jupiter docs / blog for equivalent of Fluid's "95% safe" claim

**Where to Look:**
- https://jupiter.ag/ (main marketing)
- https://docs.jupiter.ag/ (technical docs)
- Jupiter Lend whitepaper (if public)

**Question to Answer:** Does Jupiter explicitly claim positions at 95% LTV are safe from liquidation under normal market conditions?

**If YES:** Finding H2 transfers directly  
**If NO:** Finding is only applicable to Fluid; Jupiter may have different design assumptions

### 2.2 Liquidation Mechanics (REQUIRED)

**Action:** Audit Jupiter's liquidation contract

**Where to Look:**
- Jupiter Lend smart contracts (Solana, likely on GitHub)
- Search for: `liquidate()`, `liquidationBonus`, `liquidationPenalty`

**Parameters to Extract:**
- Liquidation discount (incentive to liquidators)
- Bonus structure (fee vs. slippage recovery)
- Penalty on user (how much of debt must be covered)

**Expected Finding:**
- If liquidation bonus is 3-5% (typical), then H2 applies (same slippage problem)
- If liquidation bonus is >10%, liquidators have buffer (may mitigate H2)

### 2.3 Supported Collateral & Depegging Scenarios (REQUIRED)

**Action:** Check what assets Jupiter accepts as collateral; identify depegging risk

**Where to Look:**
- Jupiter Lend risk dashboard (if public)
- Solana ecosystem assets similar to bSOL (LST wrappers, yield-bearing assets)

**Assets to Check:**
- **jUSDC, jUSDT** — stablecoins; depegging unlikely
- **jSOL** — Lido staked SOL; HAS DEPEGGED (2023, 2024)
- **jMSOL** — Marinade staked SOL; HAS DEPEGGED
- **Wrapped tokens** — Wormhole/Portal; bridging risks

**Key Insight:** If Jupiter accepts wrapped/staked SOL at high LTV, H2 scenario is IDENTICAL to Fluid

### 2.4 TVL & Position Distribution (ESTIMATION)

**Action:** Estimate which positions are actually at 95% LTV

**Data Source:**
- Jupiter Lend TVL (if dashboard exists)
- Loan distribution (histogram of LTV across active loans)
- Estimate positions at >90% LTV as percentage of TVL

**Question:** Are there 100+ positions at 93%+ LTV (like Fluid's 150)?

**If YES:** H2's $15M scenario scales proportionally  
**If NO:** Finding applies only to subset of Jupiter; lower severity

---

## Part 3: Numeric Scenario Adaptation

### Template: Jupiter H2 Scenario (If All Parameters Match)

```
Liquidation Event Trigger:
- Jupiter TVL at risk (estimate from dashboard): $X million
- Positions at 93%+ LTV: ~Y% of TVL
- At-risk capital: $Z million

Stress Scenario:
- jSOL/jMSOL depegs 5% (happens ~every 12 months)
- Oracle lags 1-3 Solana slots
- Liquidations begin
- Orca/Marinade pool depth: [VERIFY] $W million
- Slippage across batch: [ESTIMATE] 20-30% (adjust if Solana DEX depth differs)

Outcome:
- Liquidation proceeds: ~$Z × 0.75 (25% slippage)
- Liquidator loss: $0 (negative incentive)
- Bad debt: $Z × 0.25 = ~$X million

Probability (per 6 months):
- P(jSOL depegs) = [EMPIRICAL from Solana history]
- P(oracle lag overlap) = ~0.95 (same as Ethereum)
- P(relevant positions exist) = [VERIFY from data]
- P(DEX liquidity insufficient) = [ESTIMATE from Orca depth]
```

---

## Part 4: Go / No-Go Decision Framework

### GO (Submit Jupiter Variant) IF:

- ✅ Jupiter explicitly claims "95% LTV safe"
- ✅ Jupiter accepts jSOL/jMSOL at high LTV
- ✅ Liquidation incentive < 5% (same problem class)
- ✅ At-risk capital >$5M
- ✅ Depegging history shows 5%+ drops (Solana ecosystem documented)

### NO-GO (Do Not Submit Jupiter Variant) IF:

- ❌ Jupiter caps LTV at 80% or lower
- ❌ Jupiter does NOT accept wrapped assets
- ❌ Liquidation bonus >10% (sufficient buffer)
- ❌ At-risk capital <$1M (too small for CRITICAL)
- ❌ No documented depegging scenarios

---

## Recommended Execution

**If Feb 4 includes Jupiter in audit scope:**

1. **Day 1 (Feb 1):** Run Part 2 verification (LTV claims + mechanics)
2. **Day 2 (Feb 2):** Extract collateral list + depegging history
3. **Day 3 (Feb 3):** Estimate TVL at risk; build numeric scenario
4. **Day 4 (Feb 4):** If GO decision → submit Jupiter_H2_CRITICAL variant

**If Jupiter does NOT meet criteria:** Remain focused on Fluid submission only.

---

## Key Files for Reference

- **Original Finding:** FLUID_H2_CRITICAL_ANALYSIS.md
- **Submission Document:** CODE4RENA_FINAL_SUBMISSION.md
- **Mitigation Reference:** MITIGATION_SECTION.md
- **Jupiter Execution Checklist:** [This file — JUPITER_ADAPTATION_NOTES.md]
