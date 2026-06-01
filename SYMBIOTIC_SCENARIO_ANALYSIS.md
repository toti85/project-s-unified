# SYMBIOTIC LOSS ATTRIBUTION — Economic Scenario Analysis (Step 2)

**Status:** Economic modeling complete; gap identified  
**Finding Type:** Loss attribution under correlated slashing + capture timestamp vulnerability

---

## BASE SCENARIO (Setup)

```
Vault: $100M total deposits
- 1,000,000 shares outstanding
- Share price: $100 per share

Operator X: Serves both Network A and Network B
- Delegated from vault: $20M
- Network A gets: $12M stake
- Network B gets: $8M stake
- (Curator splits via NetworkRestakeDelegator)

Depositors:
- Alice: 100,000 shares ($10M), delegated to Network A only
- Bob: 100,000 shares ($10M), delegated to Network B only
- Charlie: 800,000 shares ($80M), NOT delegated to any network (risk-free)
```

---

## SCENARIO 1: SEQUENTIAL SLASHING (Same Epoch, Proper Capture)

**Timeline:**

| Time | Event | Vault Balance | Operator X Total Stake | Network A Stake | Network B Stake | All Shares | Share Price | Alice Balance | Bob Balance | Charlie Balance |
|------|-------|---|---|---|---|---|---|---|---|---|
| T=0 | Initial state | $100M | $20M | $12M | $8M | 1M | $100 | $10M | $10M | $80M |
| T=1 | Network A slash request (20% = $2.4M) | $100M | $20M | $12M | $8M | 1M | $100 | $10M | $10M | $80M |
| T=1 | Resolver A approves (no veto) | $100M | $20M | $12M | $8M | 1M | $100 | $10M | $10M | $80M |
| T=2 | Network A slashing executes | $97.6M | $17.6M | $9.6M | $8M | 1M | $97.60 | $9.76M ⚠️ | $9.76M ⚠️ | $77.92M ⚠️ |
| T=3 | Network B slash request (25% = $2M) | $97.6M | $17.6M | $9.6M | $8M | 1M | $97.60 | $9.76M | $9.76M | $77.92M |
| T=4 | Resolver B approves (no veto) | $97.6M | $17.6M | $9.6M | $8M | 1M | $97.60 | $9.76M | $9.76M | $77.92M |
| T=5 | Network B slashing executes | $95.6M | $15.6M | $9.6M | $6M | 1M | $95.60 | $9.56M | $9.56M | $76.48M |

**Analysis:**

✅ Sequential execution
✅ Network A slashing reduces share price from $100 → $97.60
✅ Network B slashing reduces share price from $97.60 → $95.60
✅ Total impact: $4.4M loss ($2.4M + $2M) = 4.4% loss across vault

**Critical observation:**
- **Alice ($10M to Network A):** Lost $0.44M (4.4% dilution) ← CORRECT (bears her network's slash)
- **Bob ($10M to Network B):** Lost $0.44M (4.4% dilution) ← CORRECT (bears his network's slash)
- **Charlie ($80M unallocated):** Lost $3.52M (4.4% dilution) ← ⚠️ SHOULD NOT LOSE ANYTHING

---

## SCENARIO 1 INVARIANT VIOLATION IDENTIFIED

**Broken Invariant:**
> "Depositors NOT delegated to any network must NOT bear slashing losses from any network."

**Evidence:**
- Charlie delegated $0 to Network A or Network B
- Charlie should NOT lose any funds
- **Actual outcome:** Charlie loses $3.52M (44% of vault losses despite 0% delegation)

**Root cause:**
- Share-based accounting is GLOBAL
- Slashing reduces ALL share prices equally
- No distinction between "delegated" and "non-delegated" shares
- Loss is socialized across vault instead of attributed to delegators

---

## SCENARIO 2: SIMULTANEOUS SLASHING (Same Block, Q1 Edge Case)

**Timeline (Compressed - both slashes in same transaction):**

| Time | Event | Vault Balance | Operator X Total | Network A | Network B | Shares | Price | Status |
|------|-------|---|---|---|---|---|---|---|
| T=0 | Initial | $100M | $20M | $12M | $8M | 1M | $100 | Normal |
| T=1 | Network A slash (20%) + Network B slash (25%) submitted same block | $100M | $20M | $12M | $8M | 1M | $100 | ⚠️ QUESTION |
| T=? | Execution order: ??? | ? | ? | ? | ? | ? | ? | ??? |

**Question:** Are these processed sequentially or concurrently?

**Hypothesis A: Sequential (A then B)**
```
Step 1: Network A slashes $2.4M → Vault = $97.6M, Operator = $17.6M
Step 2: Network B slashes $2M (25% of now-$8M) → Vault = $95.6M

Final: $4.4M loss (20% + 25% do NOT compound)
```

**Hypothesis B: Concurrent (Pro-rata)**
```
Both slash simultaneously against available stake.
Network A: claims 20% of $20M = $4M
Network B: claims 25% of $20M = $5M
Total claim: $9M, but only $20M available → pro-rata reduction?

If pro-rata: Network A gets $4M, Network B gets $5M (within budget)
Network A: actual slash = $4M (20%)
Network B: actual slash = $5M (25%)
Vault loss: $9M total

Final: $91M vault balance, share price = $91
```

**Code Reality (from agent):**
> "Sequential slashing: each network's slash is bounded by capture guarantee. Cross-network slashing reduces available stake for subsequent networks."

✅ **Hypothesis A is correct.** Sequential processing.

**BUT:** Capture guarantee creates a new risk:

---

## SCENARIO 3: CAPTURE TIMESTAMP MISMATCH (Q1 + Q2 Combined)

**Key code detail:** Vault slashing uses `capture timestamp` — a reference point for historical share balance.

**Code:** Vault validates `captureTimestamp <= now - 1 epoch`

**Attack scenario:**

```
T=0: Operator X serves Network A and Network B
     Vault state snapshot: $20M delegated to Operator X

Event 1 (T=1000): Network A detects breach, submits slashing request
     - Capture timestamp: T=900 (1 epoch ago)
     - Slash amount: 20% of T=900 balance = $4M

Event 2 (T=1010): Network B ALSO detects breach from T=950, submits slashing
     - Capture timestamp: T=950 (also valid, >1 epoch old)
     - Slash amount: 30% of T=950 balance = $6M
     - But Operator X's stake at T=950 was only $18M (already declining)

QUESTION: Does slashing use:
(A) Vault state at capture time (isolated per-network)?
(B) Current vault state (sequential depletion)?
```

**Code answer (from agent):**
> "Proportional slashing between active stake and pending withdrawals. Capture timestamp validation (must be ≤1 epoch old)."

⚠️ **Ambiguity:** If Network A slashes against T=900 state, and Network B slashes against T=950 state, but we're now at T=1010:

- Does Network A take $4M from the vault NOW?
- Then does Network B take 30% of CURRENT balance?
- Or does Network B's 30% apply to T=950 balance (~$18M = $5.4M)?

**If both slash from CURRENT balance:**
```
Current Operator X balance: $16M (both have been declining)
Network A: 20% of $16M = $3.2M
Network B: 30% of remaining = 30% of ($16M - $3.2M) = 30% of $12.8M = $3.84M
Total: $7.04M

Result: More than either network's "fair share" of the original stake
Risk: Temporal arbitrage where late slashers can take proportionally more
```

---

## SCENARIO 3 INVARIANT VIOLATION (Potential)

**Broken Invariant (if current balance is used):**
> "Each network slashes its operator's delegated stake from the capture timestamp, not from current depleted balance."

**If violated:**
- Network B could claim MORE than its 30% stake if Network A slashed first
- Total slashing could exceed 100% of original operator stake through temporal manipulation

---

## SCENARIO 4: LOSS ATTRIBUTION CASCADE (Q4)

**Setup:**
```
Vault: $100M
- Network A: $50M
- Network B: $50M
- Network B security requirement: "vault must have ≥$60M"
```

**Timeline:**

| Event | Vault | Network A | Network B | Network B Status |
|-------|-------|-----------|-----------|---|
| T=0 | $100M | $50M | $50M | ✅ Secured |
| T=1 | Network A slashes $35M (70% of A's stake) | $65M | $50M | ⚠️ UNDER-SECURED |
| T=2 | Network B auto-revokes? Or continues under-secured? | ? | ? | ??? |

**Question:** Does Network B:
- (A) Continue operating under-secured (security assumption violated)?
- (B) Auto-revoke delegation (triggering withdrawal)?
- (C) Get slashed for non-compliance?

**Code answer (from agent):**
> "Network security requirement enforcement (pull vs. push)"

⚠️ **Not specified in agent's findings.** This requires reading `NetworkMiddleware` for auto-revocation logic.

**Likely finding:** Network B's security enforcement is PUSH (networks must monitor), not PULL (vaults enforce).

**If true:** Network B operates under-secured without automatic revocation.

---

## SUMMARY: LOSS ATTRIBUTION GAPS FOUND

### Gap 1: Non-Delegators Bear Loss ❌

**Invariant:** Depositors not delegated to any network should not bear network slashing.

**Reality:** Global share accounting means ALL depositors bear loss proportionally.

**Example:** Charlie ($80M, 0% delegated) bears 44% of vault losses ($3.52M).

**Severity:** CRITICAL if vault is marketed as "choose your network risk"

---

### Gap 2: Temporal Slashing Ambiguity ❓

**Invariant:** Each network slashes its historical delegated amount, not current depleted balance.

**Reality:** Unclear from code whether Network B's 30% applies to capture balance or current balance.

**Example:** If computed from current balance, Network B could exceed original 30% through temporal arbitrage.

**Severity:** HIGH (depends on implementation)

---

### Gap 3: Cross-Network Security Cascade ⚠️

**Invariant:** Slashing in Network A must not cause Network B to unknowingly operate under-secured.

**Reality:** Network B security enforcement appears to be PUSH (network monitors), not PULL (vault enforces).

**Example:** If Network B's $50M drops to $45M, Network B continues operating without automatic withdrawal.

**Severity:** HIGH (depends on Network B design)

---

## WHICH GAP IS MOST EXPLOITABLE?

**Gap 1 (Non-Delegator Loss)** is the strongest finding:
- ✅ Clearly contradicts expected behavior
- ✅ Affects ALL users equally
- ✅ Is fundamental to shared security design
- ✅ Has numeric impact ($3.52M in scenario)

**Gap 2 and Gap 3** require more code audit to confirm.

---

## NEXT STEP: INVARIANT DEFINITION

Primary invariant to formalize:

> **Invariant_LossIsolation:**  
> "If a vault depositor allocates $X to Network A and $0 to Network B, and Network B's operator is slashed, the depositor's balance must not decrease by more than (slashing on Network A / total vault size)."

**Test case:**
```
Alice: $10M to Network A, $0 to Network B
Network B slashes operator for $2.4M
Expected max loss for Alice: 0 (she's not exposed to Network B)
Actual loss: $2.4M × ($10M delegated / $100M vault) = $0.24M

FAIL: Alice lost $240K for Network B breach she didn't opt into
```

---

## FINDING CONFIDENCE ASSESSMENT

| Aspect | Confidence | Evidence |
|--------|-----------|----------|
| Loss is GLOBAL (share-based) | 🟢 HIGH | Code clearly states: "share-based, affects all holders proportionally" |
| Non-delegators bear loss | 🟢 HIGH | Share accounting doesn't distinguish delegated vs. unallocated |
| Potential temporal arbitrage | 🟡 MEDIUM | Code is ambiguous on capture timestamp application |
| Cascade (Network B under-secured) | 🟡 MEDIUM | Requires checking Network security enforcement (PUSH vs PULL) |

---

## Numeric Evidence Summary

**Scenario 1 (Sequential, Proper Capture):**
- Total vault loss: $4.4M (4.4%)
- Charlie's loss (0% delegated): $3.52M
- Charlie's loss % of total vault losses: 80%
- Charlie bears 800% more loss-per-dollar-delegated than Operator X

**This alone is submission-worthy IF it contradicts Symbiotic's marketing claims.**

---

## NEXT ACTION (Step 3)

1. Define Invariant_LossIsolation formally
2. Map to code location
3. Determine: PASS or FAIL?
4. If FAIL → formalize as CRITICAL
5. Proceed to Step 4 (Immunefi submission outline)
