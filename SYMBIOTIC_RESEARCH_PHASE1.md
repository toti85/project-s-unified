# SYMBIOTIC LOSS ATTRIBUTION RESEARCH — Phase 1 Context

**Date:** February 4, 2026  
**Target:** Loss Attribution Failure under correlated network breaches  
**Status:** Architecture research (contract code reading pending)

---

## ARCHITECTURE UNDERSTANDING (from docs.symbiotic.fi)

### Core Components

1. **Collateral** — Any ERC-20 (ETH, LSTs, stablecoins, LP tokens)
2. **Vaults** — Pool deposits; delegate stake to operators; execute slashing
3. **Operators** — Validate for multiple networks simultaneously
4. **Networks** — Consume security (AVS-like); submit slashing requests
5. **Resolvers** — Arbitration layer; can veto slashing during grace period
6. **Curators** — Manage vault delegation strategies

### Key Design Principle

> "Networks can customize slashing logic fully."

**Assumption (critical):**  
> Operators can serve multiple networks. Stake is shared.

---

## RESEARCH QUESTIONS TO ANSWER IN CODE

### Q1: Slashing Ordering & Depletion ⚠️

**Scenario:**
```
Operator X serves Network A + Network B
- Network A slashes: 20% of delegated stake
- Network B slashes: 30% of delegated stake (same block/epoch)

Question: Sequential (50%) or concurrent (56%) depletion?
         If vault balance < 50%: who gets slashed first?
```

**Where to look:**
- Vault slashing execution logic
- VetoSlasher contract (queue vs. atomic execution)
- NetworkMiddleware (can two networks slash in same block?)

**Invariant to test:**
> "Total slashing from correlated events ≤ 100% of operator's delegated stake"

---

### Q2: Loss Attribution to Depositors ⚠️

**Scenario:**
```
Vault: $100M total deposits
- $20M delegated to Operator X (serves Network A + Network B)
- Network A slashes $5M (25% of Operator X's $20M)

Question: Who bears the $5M loss?
- Option 1: All $100M depositors (dilution across vault)
- Option 2: Only $20M who delegated to Operator X
- Option 3: Only depositors who opted into Network A
```

**Where to look:**
- Vault withdrawal logic after slashing
- Share accounting (global vs. local reduction)
- Delegation tracking (per-network vs. per-operator)

**Invariant to test:**
> "Depositors NOT delegated to Network A must NOT bear Network A's slashing loss"

---

### Q3: Resolver Veto Coordination ⚠️

**Scenario:**
```
Network A slashing: veto window 7 days (Resolver A)
Network B slashing: veto window 7 days (Resolver B)

Question: Can Resolver A veto Network A slashing
         while Resolver B approves Network B slashing
         on the SAME OPERATOR?

Failure mode: Resolvers are independent; one veto might block another's valid slash
```

**Where to look:**
- VetoSlasher tracking (per-network vs. per-operator)
- Resolver veto logic (per-request vs. global)

**Invariant to test:**
> "Resolver for Network A must NOT block slashing for Network B"

---

### Q4: Cascade Amplification ⚠️

**Scenario:**
```
Vault: $100M delegated to Operator X
- Network A: 50M  
- Network B: 50M

Event 1: Network A slashes $30M (operator breach)
→ Vault balance: $70M

Event 2: Network B security requirement: "vault ≥ $80M"
→ Vault now under-secured

Question: Does Network B auto-revoke delegation?
         Does this trigger further slashing?
         Does Network B operate under-secured without notice?
```

**Where to look:**
- Network security requirement enforcement (pull vs. push)
- Vault collateral monitoring (auto-revoke on threshold breach)

**Invariant to test:**
> "One network's slashing must not cause another network to unknowingly operate under-secured"

---

## EVIDENCE NEEDED (to proceed to Step 2)

- [ ] **Contract location:** Where is VaultStorage / vault slashing logic?
- [ ] **Slashing execution:** Is it sequential, queued, or atomic?
- [ ] **Share accounting:** Global or per-network?
- [ ] **Multi-network coordination:** Can two networks slash same operator simultaneously?
- [ ] **Resolver independence:** Per-request or global per-operator?
- [ ] **Security thresholds:** Dynamic enforcement or static?

---

## TIME ALLOCATION

- **Hours 0-2:** Contract reading (this phase)
  - [ ] Find VaultStorage + slashing execution
  - [ ] Trace multi-network request handling
  - [ ] Identify queue/ordering mechanism
  
- **Hours 2-4:** Economic scenario modeling
  - [ ] Build table: T=0 to T=3 with correlated slashing
  - [ ] Calculate depletion paths
  - [ ] Answer Q1-Q4 numerically

- **Hours 4-5:** Invariant + proof
  - [ ] Write falsifiable invariant
  - [ ] Map to code location
  - [ ] Test: pass or fail

- **Hours 5-6:** Submission outline
  - [ ] Immunefi format (9 sections)
  - [ ] No full PoC yet; skeleton only

---

## SUCCESS CRITERIA (midway checkpoint)

After contract reading:
1. Can I describe exactly how slashing executes under correlated events?
2. Can I identify a loss attribution gap (or confirm design is safe)?
3. Is there a numeric scenario where vault balance becomes ambiguous?

If ALL 3 are YES → proceed to Step 2 (economic modeling)  
If ANY is NO → loop back to code reading or STOP

---

## NEXT ACTION

**READ CONTRACT STACK:**
1. Vault storage + delegation (where does stake go?)
2. Slashing execution (how does network submit slash?)
3. VetoSlasher (veto window + coordination logic)
4. NetworkMiddleware (multi-network request handling)

**Search terms:**
- `slash`, `slashing`, `VetoSlasher`, `Vault`, `Middleware`, `resolve`

**Max 2 hours before proceeding to economic modeling.**
