# COPILOT PROMPT: SYMBIOTIC — LOSS ATTRIBUTION FAILURE RESEARCH

---

## MODE: DESIGN-LEVEL VULNERABILITY RESEARCH

**NOT code bug hunting.**  
**NOT exploit PoC writing.**  
**YES economic invariant violation detection.**

This is Immunefi submission prep, not C4.

---

## TARGET

**Protocol:** Symbiotic (shared security / restaking)  
**Mainnet:** Jan 30, 2025 (fresh deployment, <1 week old)  
**Bug Bounty:** Immunefi — $500K max CRITICAL, $100K min  
**Submission type:** Design-level finding with economic modeling PoC

**Bounty page:** https://immunefi.com/bug-bounty/symbiotic/

---

## WHAT WE'RE HUNTING

**Hypothesis:**  
> "Loss Attribution Failure Under Correlated Consumer Breach"

**In plain English:**
- Multiple networks (consumers) use shared stake from the same vault
- Network A breach → slashing event
- Network B independent breach → slashing event (same time window)
- **Question:** Who pays? How much? Is the loss correctly attributed?
- **Failure mode:** Loss is externalized, double-counted, or cascade-amplified

**This is NOT:**
- A code bug (slashing works correctly)
- An oracle issue
- A reentrancy attack

**This IS:**
- A design gap between "shared security" claim and loss allocation reality
- An economic invariant violation under correlated stress
- A "claim vs implementation" mismatch

---

## ARCHITECTURE SUMMARY (use this, don't re-research)

Symbiotic has 6 core components:

1. **Collateral** — any ERC-20 (ETH, LSTs, stablecoins, LP tokens)
2. **Vaults** — pool deposits, delegate stake to operators, execute slashing
3. **Operators** — validate for multiple networks simultaneously
4. **Networks** — consume security (AVS-like), submit slashing requests
5. **Resolvers** — arbitration layer (can veto slashing during grace period)
6. **Curators** — manage vault delegation strategies

**Key design choice:** Operators can serve multiple networks. Stake is shared.

**Slashing flow:**
1. Network detects operator misbehavior → submits slashing request
2. Resolver has veto window (if vault uses VetoSlasher)
3. If not vetoed → slashing executes on vault
4. Vault burns/redistributes collateral

**Critical assumption (stated in docs):**
> "Networks can customize slashing logic fully."

**Our attack surface:**
> What happens when TWO networks slash the SAME operator at the SAME time?

---

## RESEARCH QUESTIONS (answer these, don't code yet)

### **Q1: Slashing Ordering & Depletion**

If Operator X serves Network A and Network B:
- Network A slashes 20% of operator's delegated stake
- Network B slashes 30% of operator's delegated stake (same block or epoch)
- **Does the vault have 50% of stake left, or 56%?** (sequential vs. concurrent)
- **Who gets slashed first if vault balance < total slashing amount?**
- **Is there a priority mechanism, or FIFO, or pro-rata?**

**Where to look:**
- Vault slashing logic: how does it handle multiple simultaneous slashing requests?
- VetoSlasher contract: does it queue slashing events or execute atomically?
- Network middleware: can two networks submit slashing in the same block?

**Potential invariant violation:**
> "Total slashing from correlated events must not exceed 100% of operator's delegated stake."  
> If broken → vault insolvent or loss externalized to depositors.

---

### **Q2: Loss Attribution to Depositors**

When slashing happens:
- Does the loss get distributed across ALL depositors in the vault?
- Or only depositors who delegated to that specific operator?
- Or only depositors who delegated to that specific network?

**Scenario:**
- Vault has $100M deposits
- $20M delegated to Operator X (serving Network A and Network B)
- Network A slashes $5M (25% of operator's $20M)
- **Question:** Who bears the $5M loss?
  - Option 1: All $100M depositors (dilution across vault)
  - Option 2: Only $20M who delegated to Operator X
  - Option 3: Only depositors who opted into Network A

**Where to look:**
- Vault withdrawal logic after slashing
- Share accounting in vault (does slashing reduce share value globally or locally?)
- Delegation tracking: is it per-network or per-operator?

**Potential invariant violation:**
> "Depositors who did NOT delegate to Network A should NOT bear Network A's slashing loss."  
> If broken → loss externalization / isolation failure.

---

### **Q3: Resolver Veto Coordination**

If two networks slash the same operator:
- Network A slashing request: veto window = 7 days
- Network B slashing request: veto window = 7 days (different resolver)
- **Can Resolver A veto Network A's slashing, but Resolver B approve Network B's?**
- **If yes:** Does Network B's slashing execute even if it shares the same operator as Network A?

**Scenario:**
- Operator X misbehaved for Network A (false positive, resolver vetoes)
- Operator X misbehaved for Network B (real breach, resolver approves)
- **Question:** Does the vault slash once (Network B only) or zero times (both vetoed)?
- **Failure mode:** If resolvers are independent, one network's veto might block another network's valid slashing

**Where to look:**
- VetoSlasher: does it track slashing requests per-network or per-operator?
- Resolver veto logic: is it per-request or global per operator?

**Potential invariant violation:**
> "A resolver for Network A should NOT be able to block slashing for Network B."  
> If broken → griefing attack or censorship.

---

### **Q4: Cascade Amplification**

If Network A slashing causes vault collateral to drop:
- Vault collateral drops 30% (from $100M to $70M)
- Network B's security requirement: "vault must have ≥$80M"
- **Does Network B automatically revoke delegation when vault drops below threshold?**
- **If yes:** Does this trigger further slashing from Network B (non-compliance penalty)?
- **If no:** Is Network B now under-secured without knowing it?

**Scenario:**
- Vault has $100M, delegates to Operator X for Network A ($50M) and Network B ($50M)
- Network A slashes $30M (operator breach)
- Vault now has $70M
- Network B's threshold: $80M minimum
- **Question:** Does Network B automatically exit? Or does it stay under-secured?
- **Failure mode:** Cascade where one network's slashing causes other networks to breach security thresholds

**Where to look:**
- Network security requirement enforcement (is it pull or push?)
- Vault collateral monitoring (does it automatically revoke delegation on threshold breach?)

**Potential invariant violation:**
> "A slashing event in Network A must not cause Network B to unknowingly operate under-secured."  
> If broken → systemic security failure.

---

## WHAT TO PRODUCE (step-by-step)

### **STEP 1: Read contracts (2 hours max)**

**Scope (in order of priority):**
1. `VaultStorage.sol` or equivalent — how slashing affects share accounting
2. `VetoSlasher.sol` — how veto window and multi-network slashing interact
3. `NetworkMiddleware.sol` or similar — how networks submit slashing requests
4. `OperatorRegistry.sol` or similar — how operators are tracked across networks

**DO NOT:**
- Read the entire codebase
- Audit for reentrancy, access control, etc. (out of scope)
- Write exploit PoCs yet

**DO:**
- Find the slashing execution logic
- Trace what happens when multiple slashing requests target the same operator
- Identify if there's a queue, ordering, or concurrency handling

**Output:** 1-page notes on "How Slashing Works Under Correlated Events"

---

### **STEP 2: Economic modeling (2 hours)**

**Build a scenario table:**

| Event | Vault Balance | Operator X Stake | Network A Slashing | Network B Slashing | Result |
|-------|---------------|------------------|--------------------|--------------------|--------|
| T=0 | $100M | $20M (delegated) | — | — | Normal |
| T=1 | $100M | $20M | Request $5M slash | — | Pending |
| T=2 | $100M | $20M | Request $5M slash | Request $6M slash | **QUESTION** |
| T=3 | ??? | ??? | ??? | ??? | **ANSWER HERE** |

**Questions to answer in the table:**
1. Does the vault slash $11M total (sequential) or something else?
2. Who bears the loss — all depositors or only those delegated to Operator X?
3. Can both slashing events execute if they exceed operator's total stake?

**Output:** 1 table showing the failure scenario numerically

---

### **STEP 3: Invariant definition (30 min)**

Write a single falsifiable invariant. Example:

> **Invariant_LossIsolation:**  
> "If a depositor delegates to Operator X for Network A only, they must NOT bear slashing losses from Network B breaches, even if Operator X serves both networks."

**Test:** Is this invariant enforced in code?

**Output:** 1 invariant + 1 test case (pass/fail)

---

### **STEP 4: Submission outline (1 hour)**

**Structure (Immunefi format):**

1. **Title** (12 words max)
2. **Summary** (non-technical, 3 sentences)
3. **Broken Invariant** (from Step 3)
4. **Failure Mechanism** (from Step 2 table)
5. **Impact** (who loses money, how much, probability)
6. **Why Users Cannot Mitigate**
7. **Why This Is CRITICAL** (map to Immunefi severity criteria)
8. **Proof of Concept** (economic model, not Solidity exploit)
9. **Mitigation** (how to fix without invalidating the finding)

**DO NOT write the full submission yet.** Just the outline.

**Output:** 1-page submission skeleton

---

## CRITICAL RULES

### **DO:**
- Focus on DESIGN gaps, not code bugs
- Model economically, not exploit in code
- Ask "who pays" not "how to steal"
- Use the Fluid H2 finding as a template (claim vs reality)

### **DO NOT:**
- Write Solidity exploits
- Audit for standard bugs (reentrancy, overflow, etc.)
- Spend >6 hours on this
- Submit anything to Immunefi yet (this is research phase)

### **SUCCESS CRITERIA:**

You've succeeded if you can answer:
1. **Is there a loss attribution gap when multiple networks slash the same operator?**
   - YES → proceed to submission
   - NO → document why not, move to next angle
2. **Can you quantify the loss with a numeric scenario?**
   - YES → CRITICAL tier likely
   - NO → rethink the angle

---

## CONTEXT (why this matters)

Symbiotic launched **6 days ago** (Jan 30, 2025). It's fresh. Private audits happened, but they focused on:
- Code correctness
- Standard exploits
- Single-network behavior

**Nobody has stress-tested:**
- Multi-network correlated slashing
- Loss attribution under simultaneous events
- Cascade effects across shared operators

This is the design-level blind spot. This is where the value is.

---

## TIMELINE

- **Hour 1-2:** Read contracts (VaultStorage, VetoSlasher, NetworkMiddleware)
- **Hour 3-4:** Build economic scenario table
- **Hour 5:** Define invariant + test
- **Hour 6:** Write submission outline

**Total:** 6 hours max.

If after 6 hours there's no clear finding → STOP. Document what you learned. Move to Jupiter Lend prep.

---

## FINAL NOTE

This is NOT a "find any bug" hunt.  
This is: **"Is loss attribution broken under correlated network breaches?"**

If the answer is YES → you have a CRITICAL Immunefi submission.  
If the answer is NO → you have clarity on a design assumption that's actually safe.

Both outcomes are valuable.

Go.
