# CELESTIA DATA RECOVERABILITY ANALYSIS

**Date:** February 4, 2026  
**Target:** "Data availability implies data recoverability" invariant  
**Scope:** Economic, systemic, and bandwidth constraints (NOT cryptography)  
**Status:** PHASE 1 — Architecture Research Complete

---

## CELESTIA ARCHITECTURE SUMMARY (From Docs)

### Core Design

1. **Data Availability Sampling (DAS)**
   - 2D Reed-Solomon encoding: block data → k×k shares → 2k×2k extended matrix
   - Light nodes sample random coordinates (NOT all data)
   - High probability guarantee: if enough unique shares sampled, data is available

2. **Namespaced Merkle Trees (NMTs)**
   - Applications fetch only their namespace
   - Proof of completeness included

3. **Data Retrievability (Recent Change — v6, Jan 2026)**
   - **Light nodes:** 7-day rolling window (prune older data)
   - **Archival nodes:** Store complete history
   - **Critical:** "Archival nodes serving historical data for free is not guaranteed"
   - **Rollup responsibility:** Store their own historical data

### Slashing / Penalties

**Current:** No explicit validator slashing for DA failure found in docs.

---

## RESEARCH QUESTIONS

### Q1: Economic Recoverability

**Question:** Can DA sampling pass but full blob reconstruction cost exceed economic limits?

**Scenario to test:**
```
- Blob size: 16 MB (realistic for rollup)
- Available archival nodes: 3-5 (fee-based)
- Cost per GB retrieval: $0.01-$0.10 (estimated market rate)
- Time budget: 1 hour to 7 days (depends on rollup liveness)
```

**Economic limit:** If reconstruction cost > (rollup's margin per transaction × expected transactions in downtime), it's "affordable failure" but not practically recoverable.

### Q2: Time-to-Recover vs. Rollup Liveness

**Question:** Can DA be available but too slow to prevent rollup failure?

**Comparison:**
- Optimistic rollup timeout: 7-14 days to challenge fraud proof
- ZK rollup: must prove within same epoch (~12 hours)
- Data recovery from archival nodes: ??? (depends on service quality)

**Risk:** If recovery takes longer than rollup's liveness assumption, rollup fails.

### Q3: Adversarial Withholding

**Question:** Can adversaries exploit fee markets or publishing delays to make DA technically valid but practically unusable?

**Scenarios:**
- Malicious archival node operator: delay serving data during congestion
- Network congestion: exponential fee spike during emergency retrieval
- Collusion: archival nodes coordinate withholding

### Q4: Slashing / Penalty Mismatch

**Question:** Who pays if DA is valid but rollup fails?

**Current state:** 
- No explicit DA validator slashing for recovery failures (from docs)
- Rollups must store their own data
- **Gap:** If data is DA-valid but *inaccessible*, who is responsible?

---

## KEY ARCHITECTURAL ASSUMPTIONS (To Test)

1. **Assumption 1:** Archival nodes will exist and remain operational
   - **Reality:** No guarantee; may require paid services
   - **Cost:** Unknown market rate (assumed $0.01-$0.10/GB)

2. **Assumption 2:** Full data recovery is always possible if DAS passed
   - **Reality:** Only if k×k unique shares were sampled (from docs)
   - **Gap:** What if sampling was insufficient? (probably rare, but not impossible)

3. **Assumption 3:** Recovery time is acceptable for rollup liveness
   - **Reality:** Depends on archival node infrastructure quality
   - **Gap:** No SLA guarantees in protocol

4. **Assumption 4:** Rollups bear full responsibility for historical data storage
   - **Reality:** Protocol does NOT guarantee retrievability after 7 days
   - **Implication:** Economic burden is shifted from protocol to rollups

---

## PHASE 1 SUMMARY

**What Celestia Does Well:**
- ✅ DAS enables light nodes to verify availability without full download
- ✅ NMTs enable per-app data fetching
- ✅ Archival nodes *can* store data indefinitely

**Critical Gaps Found:**
- ⚠️ **No guaranteed retrievability past 7 days** (depends on archival nodes)
- ⚠️ **No pricing guarantee** for archival data access (could spike during emergency)
- ⚠️ **No explicit slashing** if archival infrastructure fails
- ⚠️ **Rollup bears responsibility** for storage (deferred to application layer)

**Verdict so far:** "Data available" ≠ "Data recoverable" if archival infrastructure is weak.

---

## NEXT PHASES

**Phase 2:** Economic scenario (cost × time × probability model)  
**Phase 3:** Formal invariant test (Pass/Fail)  
**Phase 4:** Conclusion (SAFE or VULNERABLE)

**Time allocated:** 3 more hours (45 min each)
