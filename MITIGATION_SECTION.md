# MITIGATION STRATEGIES: H2 CASCADING LIQUIDATION FAILURE

**Objective:** Restore broken invariant without implying "current design is intended"  
**Structure:** 3 mitigation classes + tradeoffs

---

## MITIGATION CLASS A: PARAMETER-LEVEL ADJUSTMENTS

### **A1: Dynamic LTV Reduction Under High Oracle Staleness**

**Mechanism:**
- Monitor oracle update frequency per block
- If oracle lag > 2 blocks: Reduce max borrowable LTV automatically
- Example:
  - Normal (lag ≤ 1 block): max LTV = 95%
  - Elevated (lag 2-3 blocks): max LTV = 85%
  - High (lag ≥ 4 blocks): max LTV = 75%

**Invariant Restored:**
- "95% LTV is safe" becomes time-dependent claim
- Users can trust LTV claim at any moment (claim adjusts to match real conditions)

**Tradeoff:**
- Users lose access to high LTV during network stress
- Incentive alignment: When network is stressed (high priority fees), liquidation is most expensive
- Reduces capital efficiency during stress (acceptable; safety > efficiency)

---

### **A2: Stress-Adjusted Liquidation Threshold**

**Mechanism:**
- Track aggregate liquidation volume in past N blocks
- If liquidation volume > $5M in recent blocks: Raise liquidation threshold
- Example:
  - Normal: Liquidate when health factor = 1.0
  - Stress: Liquidate when health factor = 0.95 (earlier, less correlated volume)

**Invariant Restored:**
- "Only liquidate to threshold" becomes stress-aware
- Prevents cascade by triggering early liquidations before correlated breach

**Tradeoff:**
- Earlier liquidations mean more frequent liquidation events
- Users face more frequent margin calls during stress (acceptable; prevents cascade)
- Reduces net borrowing capacity per user (safety mechanism cost)

---

### **A3: Maximum LTV Reduction (Conservative Reset)**

**Mechanism:**
- Reduce protocol-wide max LTV from 95% to 80%
- Aligns with Aave/Compound baseline
- Eliminates competitive LTV advantage but fixes invariant

**Invariant Restored:**
- "80% LTV safe" is now historically-proven true (Aave/Compound track record)
- Eliminates need for complex stress mechanisms

**Tradeoff:**
- Loss of protocol differentiation
- Existing 95% LTV positions violate new rule (must trigger rebalancing)
- Impacts all users equally (fairness)
- **Fatal tradeoff:** Contradicts Fluid's market positioning entirely

---

## MITIGATION CLASS B: MECHANISM-LEVEL CHANGES

### **B1: Internalized Liquidation with Protocol-Owned Collateral Pool**

**Mechanism:**
- Replace DEX liquidation with internal debt-collateral exchange
- Protocol maintains collateral pool; buyers purchase collateral directly from pool at oracle price
- No DEX selling required; no slippage

**Example:**
- Position needs liquidation: $100k debt
- Protocol repays $100k from liquidity pool
- Protocol seizes $105.26k bSOL (at $0.95 oracle price)
- Liquidator purchases this bSOL at $100k (no slippage)
- Protocol absorbs $5.26k fee (market-making spread)

**Invariant Restored:**
- "Liquidation never exceeds 5% slippage" becomes deterministic (slippage = 0, protocol fee covers risk)
- Cascading liquidation impossible (no DEX liquidity constraint)

**Tradeoff:**
- Protocol becomes market maker; takes on collateral inventory risk
- Requires larger insurance fund ($10M+) to absorb price movements
- Significantly increases protocol operational complexity
- Liquidators earn less (direct purchase vs. DEX arbitrage)
- Architectural redesign required; not incremental change

---

### **B2: Backstop Liquidator (Protocol-Owned Keeper)**

**Mechanism:**
- Protocol maintains bot that automatically liquidates positions at threshold
- Bot operates even when profitable margin is thin (protocol absorbs cost)
- Guarantees liquidation execution regardless of market conditions

**Example:**
- Normal liquidators are unprofitable during stress (slippage too high)
- Protocol bot liquidates anyway, at protocol expense
- Ensures no bad debt accumulation

**Invariant Restored:**
- "Liquidation always happens" becomes deterministic (protocol-enforced)
- Prevents positions from drifting deeper underwater

**Tradeoff:**
- Protocol must fund losses: ~$3M per stress event in keeper losses
- Requires $5-10M+ insurance fund to cover multiple stress events
- Moral hazard: Users may take excess risk knowing protocol covers losses
- Sustainable only if stress events are rare (contradicts our 21% probability)

---

### **B3: Collateral-Specific Caps (Risk Isolation)**

**Mechanism:**
- For collateral with high depegging risk (bSOL, mSOL): Cap max LTV based on DEX liquidity
- Formula: `max_LTV[collateral] = min(0.95, Liquidity[DEX] / TVL[collateral] × 0.5)`
- Example: If bSOL/USDC has $10M liquidity and $50M bSOL on Fluid:
  - Max LTV for bSOL = min(0.95, 10M / 50M × 0.5) = min(0.95, 0.10) = **10%**
  - This is too conservative; adjust scaling

**Invariant Restored:**
- "95% LTV is safe for each collateral type" becomes individually verified
- Prevents correlated liquidation exceeding DEX capacity

**Tradeoff:**
- Reduces practical LTV for illiquid collaterals to 20-40%
- Users cannot use risky collaterals at 95% LTV (addresses root cause)
- Requires ongoing monitoring of DEX liquidity (automation necessary)

---

## MITIGATION CLASS C: DISCLOSURE-LEVEL CHANGES

### **C1: Explicit Risk Disclosure (Revised Claim)**

**Current Claim:**
> "Borrow up to 95% safely"

**Revised Claim:**
> "Borrow up to 95% LTV on major collaterals. During network stress or rapid price movements, liquidation slippage may exceed 20%, resulting in uncompensated loss. Users should maintain LTV <80% to avoid this risk."

**Invariant Restored:**
- No false claim; risk is explicit
- Users who read documentation cannot claim surprise

**Tradeoff:**
- Eliminates "95% LTV is safe" marketing claim
- Protocol loses competitive advantage (drops to Aave/Compound tier)
- Reduces user perception of safety and capital efficiency
- **Honest but commercially fatal**

---

### **C2: Remove "100x Advancement" Marketing Claim**

**Current Claim:**
> "Liquidation mechanism represents 100x advancement over existing protocols"

**Revised Claim:**
> "Liquidation mechanism is optimized for capital efficiency but may experience slippage during correlated liquidation events. Not suitable for maximum leverage strategies."

**Invariant Restored:**
- Claim becomes accurate (mechanism is optimized, but has limits)
- Users understand tradeoffs

**Tradeoff:**
- Damages protocol brand
- Suggests liquidation mechanism has known vulnerabilities
- Users migrate to Aave/Compound (perceived as safer)

---

## COMPARISON TABLE: MITIGATION TRADEOFFS

| Mitigation | Restores Invariant | Implementation Cost | User Impact | Protocol Commercial Cost | Recommended |
|---|---|---|---|---|---|
| **A1: Dynamic LTV** | Partial (time-dependent) | MEDIUM | Reduced LTV in stress | LOW-MEDIUM | ✅ YES (short-term) |
| **A2: Stress Threshold** | Partial (cascade prevention) | MEDIUM | More frequent liquidation | MEDIUM | ✅ YES (short-term) |
| **A3: LTV Reduction** | FULL (to 80%) | LOW | Permanent LTV cut | VERY HIGH (brand damage) | ❌ NO |
| **B1: Internalized Liquidation** | FULL (slippage = 0) | VERY HIGH (redesign) | Improved; faster | MEDIUM (operational) | ⚠️ LONG-TERM |
| **B2: Backstop Keeper** | FULL (guaranteed liquidation) | HIGH ($5-10M/year) | Improved; guaranteed | VERY HIGH (fund cost) | ❌ NO (unsustainable) |
| **B3: Collateral-Specific Caps** | FULL (per-collateral LTV) | HIGH (monitoring automation) | Reduced LTV for risky collateral | MEDIUM (reduced revenue) | ✅ YES (targeted fix) |
| **C1: Risk Disclosure** | Indirect (user expectation) | LOW (documentation) | Users informed; accept risk | VERY HIGH (brand) | ❌ NO (too late) |
| **C2: Remove 100x Claim** | Indirect (accuracy) | LOW (marketing change) | No impact | HIGH (removes differentiation) | ❌ NO (too late) |

---

## RECOMMENDED MITIGATION PATH (Short + Long Term)

### **Immediate (Weeks 1-4):**
1. Deploy **A1 (Dynamic LTV Reduction)** — Reduces user access during stress but prevents immediate bad debt
2. Deploy **B3 (Collateral-Specific Caps)** — Targets risky collateral (bSOL, mSOL) with reduced LTV

**Effect:** Eliminates the 95% LTV guarantee for risky collateral; users forced to <50% LTV on bSOL. Removes risk exposure within 4 weeks.

### **Medium-Term (Months 1-3):**
3. Deploy **A2 (Stress Threshold Adjustment)** — Prevents cascade by liquidating earlier during stress
4. Begin architecture review for **B1 (Internalized Liquidation)**

**Effect:** Adds cascade prevention; signals path to permanent fix.

### **Long-Term (Months 3-12):**
5. Implement **B1 (Internalized Liquidation)** — Redesigns mechanism to eliminate DEX dependence

**Effect:** Restores 95% LTV safety claim with internal market-making.

---

## CONSEQUENCE IF NO MITIGATION

- **Timeline to bad debt event:** 6-12 months (21% probability per 6 months)
- **Expected loss magnitude:** $3-15M per event
- **User impact:** $15M+ TVL at risk each 6 months
- **Protocol solvency:** Threatened if reserves <$5M
- **Regulatory risk:** "False advertising" claims if marketed as safe but fails
- **Code4rena impact:** CRITICAL ruling establishes precedent; attracts white-hats to similar issues

---

## CONCLUSION

**No mitigation exists that preserves the 95% LTV claim without significant mechanism change.**

Mitigations A1-A2 are stop-gap (reduce LTV under stress; not solution).  
Mitigation A3 is honest but commercial suicide.  
Mitigation B1 is correct but requires 6-12 month redesign.  
Mitigation B3 is targeted but shifts blame to specific collateral risk (technically accurate but uncomfortable).  
Mitigations C1-C2 are disclosure-only (admission of guilt).

**Recommendation:** Deploy A1 + B3 immediately. Commit to B1 redesign roadmap. Acknowledge design limitation in updated terms.

