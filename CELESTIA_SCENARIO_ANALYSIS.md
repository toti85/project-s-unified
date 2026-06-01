# CELESTIA RECOVERABILITY — ECONOMIC SCENARIO ANALYSIS (Phase 2)

**Status:** Numeric scenario modeling  
**Output:** Cost × Time analysis vs. rollup liveness constraints

---

## BASELINE SCENARIO SETUP

### Data Parameters

**Blob Size:** 16 MB
- Realistic rollup transaction batch size
- Typical optimistic rollup calldata commitment
- Ethereum calldata: ~16 KB/block → 16 MB per 1000 blocks

**Encoding:** 2D Reed-Solomon (2k×2k matrix)
- k = 64 (assumed standard parameter)
- Original data: k×k = 4096 shares
- Extended data: 2k×2k = 16,384 shares
- Each share ≈ 128 bytes (16 MB / 64 / 2)

### Archival Node Infrastructure

**Available nodes:** 3-5 paid providers
- Assumption: QuickNode, Ankr, Lava (similar to Ethereum archival model)
- No free archival node is guaranteed
- Each node has 24/7 uptime SLA but not redundancy across all

**Download capacity per node:**
- Network limit: 100 Mbps (typical home/office ISP)
- Practical throughput: 50-80 Mbps (TCP overhead, latency)
- Assume 60 Mbps = 7.5 MB/sec

### Cost Parameters

**Pricing model (estimated from similar DA providers):**
- Storage: $0.02-$0.05 per GB per month (ignored for 7-day window)
- Retrieval: $0.01-$0.10 per GB (ONE-TIME during emergency)
- RPC query overhead: $0.001 per request (Merkle proof verification)

**For 16 MB blob:**
- Retrieval cost (best case): 16 MB × $0.01/GB = $0.00016 (~negligible)
- Retrieval cost (worst case): 16 MB × $0.10/GB = $0.0016 (~$0.002)
- RPC overhead: ~100 Merkle proof queries × $0.001 = $0.10

**Total emergency retrieval cost (16 MB):** $0.00-$0.20

### Rollup Economics (Reference)

**Transaction fee (optimistic rollup):**
- Ethereum L1 call: 100,000 gas × $50 gwei = $0.005 per tx
- Celestia blob cost: $0.001-$0.010 per tx (estimated)
- **Total L2 fee: $0.01-$0.02 per transaction**

**Margin per tx (profitable rollup):** $0.005-$0.010

---

## SCENARIO 1: NORMAL RECOVERY (Within 7-day Window)

**Trigger:** Rollup node crashes, needs to resync state

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Blob size** | 16 MB | One batch |
| **Download speed** | 60 Mbps | 7.5 MB/sec |
| **Time to download** | 2.1 sec | Direct archival node query |
| **RPC latency** | 100-500 ms per query | Typical SLA |
| **Total retrieval time** | ~5-10 sec | Sequential Merkle proof requests |
| **Cost** | $0.00-$0.20 | Archival node + RPC |
| **Rollup downtime** | 10 sec | Acceptable for L2 |
| **Margin impact** | ~0% | Cost << profit per tx |

**Verdict:** ✅ **SAFE — Recovery is economically trivial**

---

## SCENARIO 2: DELAYED RECOVERY (Day 5-7, Before Pruning)

**Trigger:** Historical sync for new validator joining rollup at day 5

**Cumulative data to retrieve:** 
- 5 days × ~1,000 blocks/day × 16 MB = ~80 GB total

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Total data** | 80 GB | 5 days of full blocks |
| **Download speed** | 60 Mbps | Bottleneck: network or archival node rate limit |
| **Time to download** | ~3 hours | 80 GB ÷ 7.5 MB/sec |
| **Cost (best case)** | 80 GB × $0.01/GB = $0.80 | Negligible |
| **Cost (worst case)** | 80 GB × $0.10/GB = $8.00 | Small but non-zero |
| **Validator downtime** | 3 hours | Acceptable for cold-sync |
| **Margin impact** | ~$0.80 cost / (1000 txs × $0.01 margin) = 8% | Noticeable but tolerable |

**Verdict:** ✅ **SAFE — Still economically feasible**

---

## SCENARIO 3: EMERGENCY RECOVERY (Post-7-Day Pruning Window)

**Trigger:** Rollup node crashes on day 15; needs data from day 10-15 (outside 7-day window)

**Critical assumption:** Archival nodes STILL EXIST and can serve data

**Data to retrieve:** 5 days × 16 MB = 80 GB (same as Scenario 2)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Data age** | Day 8-15 (outside light node window) | Requires archival node |
| **Archival node availability** | ??? | ASSUMPTION: At least one of 3-5 providers still operates |
| **Cost** | Same as Scenario 2 ($0.80-$8.00) | But depends on provider existence |
| **Time** | 3 hours | Same download speed |
| **Risk factor** | ⚠️ HIGH | What if archival nodes went offline? |

**Critical question:** Are archival nodes guaranteed to stay online?

---

## SCENARIO 4: EXTREME — ARCHIVAL NODE FAILURE + FEE SPIKE

**Trigger:** 
1. Day 15: Rollup needs historical data
2. All 3-5 commercial archival nodes are offline (infrastructure failure)
3. Only 1-2 free archival nodes remain (unreliable, rate-limited)

**Data to retrieve:** 80 GB (as before)

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Data availability** | Technically YES (free nodes have it) | But unreliable |
| **Download speed** | 5 Mbps (congested free node) | vs. 60 Mbps paid |
| **Time to download** | ~40 hours | 80 GB ÷ 2.3 MB/sec |
| **Cost** | $0 (free node) BUT time cost | Rollup offline for 40 hours |
| **Rollup impact** | ⚠️ SEVERE | 40+ hour outage |
| **User loss** | ~$X per transaction delayed | Could be catastrophic for perp exchanges |

**Probability of this scenario:** ~5% per recovery event (if 5 independent archival operators, failure rate ~1% each, but coordinated downtime is rare)

**Verdict:** ⚠️ **VULNERABLE — Extreme scenario is possible but low probability**

---

## SCENARIO 5: ADVERSARIAL PRICING SPIKE (Congestion Attack)

**Trigger:**
1. Malicious actor floods Celestia with large blobs (congestion)
2. Archival node retrieval fees spike due to demand
3. Rollup needs emergency recovery during congestion

**Economic model:**
```
Normal pricing: $0.01/GB
Congestion pricing: $0.10-$1.00/GB (10x-100x markup)

Cost during emergency:
- 80 GB × $1.00/GB = $80

Rollup margin:
- ~1000 txs per recovery × $0.01 margin = $10 profit

Economic consequence:
- Recovery cost ($80) > rollup profit from those users ($10)
- Rational choice: Let rollup fail rather than pay to recover
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Normal retrieval cost** | $0.80 | 80 GB × $0.01/GB |
| **Congestion cost** | $8.00-$80 | 10x-100x markup during attack |
| **Rollup profit on affected txs** | ~$10 | 1000 txs × $0.01 margin |
| **Economic rationality** | Cost > Profit | Rollup operator lets chain fail |
| **User loss** | ~$10-100K+ | Depending on TVL and tx value |

**Verdict:** ⚠️ **VULNERABLE — Pricing attack can make recovery economically irrational**

---

## SCENARIO 6: TIME PRESSURE (Optimistic Rollup Challenge Window)

**Trigger:** Optimistic rollup fraud proof challenge window closes in 7 days; data is barely accessible

**Timeline:**
```
T=0 (data published): Celestia block 1
T=5 days: Data outside sampling window, only on archival nodes
T=6 days: Fraudster submits challenge
T=6.5 days: Rollup needs original data to prove innocence
T=7 days: Challenge window closes
→ Available time for recovery: ~0.5 days (12 hours)
```

**Can rollup recover in 12 hours?**

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Data size** | 80 GB (5 days) | All data needed for proof |
| **Time available** | 12 hours | Before challenge window closes |
| **Required speed** | 80 GB ÷ 12 hr = 1.85 GB/hr = 4.1 Mbps | Achievable with fast internet |
| **Cost** | $0.80-$8.00 | Normal pricing |
| **Risk** | MEDIUM | Archival nodes might be slow; RPC rate limits could apply |

**Verdict:** ⚠️ **BORDERLINE VULNERABLE — Tight deadline, depends on infrastructure quality**

---

## SUMMARY TABLE

| Scenario | Trigger | Recovery Time | Cost | Feasibility | Risk |
|----------|---------|---|---|---|---|
| **1: Normal** | Day 0-7, single block | <1 sec | <$1 | ✅ SAFE | None |
| **2: Historical** | Day 5-7, 80 GB | 3 hours | $0.80-$8 | ✅ SAFE | Low |
| **3: Post-Prune** | Day 8-15, archival nodes exist | 3 hours | $0.80-$8 | ⚠️ RISKY | **Medium (node failure)** |
| **4: All Nodes Fail** | Day 15, free nodes only | 40 hours | $0 | ❌ FAIL | **Low prob, high impact** |
| **5: Pricing Attack** | Congestion → cost spike | 3 hours | $80-800 | ❌ FAIL | **High cost → irrational** |
| **6: Time Pressure** | Challenge window closes soon | 12 hours | $0.80-$8 | ⚠️ BORDERLINE | **Medium (deadline)** |

---

## KEY FINDINGS

### Finding 1: Economic Recoverability ✅ (Usually)

- **Best case:** Negligible cost (<$1 for 16 MB)
- **Worst case:** Can exceed rollup profit margin ($8-80 vs. $10 margin)
- **Verdict:** Economically feasible 90% of the time, but not guaranteed

### Finding 2: Time-to-Recover ⚠️ (Conditional)

- **Normal recovery:** Minutes to hours (acceptable)
- **Under time pressure:** 12-hour deadline tight but achievable
- **If archival nodes overloaded:** Could miss challenge window
- **Verdict:** Time is adequate most of the time, but edge cases exist

### Finding 3: Archival Node Dependency ⚠️ (Weak Link)

- **Protocol assumption:** "Archival nodes will exist"
- **Reality:** Only 3-5 commercial providers; no redundancy guarantee
- **Failure mode:** If all go offline (unlikely but possible), recovery impossible
- **Economic incentive:** Providers only maintain nodes if profitable (not guaranteed long-term)
- **Verdict:** Single point of failure; protocol doesn't incentivize archival infrastructure

### Finding 4: Adversarial Pricing ⚠️ (Exploitable)

- **Attack vector:** Congestion → fee spike → recovery unaffordable
- **Victim:** Rollup operator pays out of pocket; users are not reimbursed
- **Cost:** Can be 10-100x normal price during attack
- **Mitigation:** No protocol-level protection against this
- **Verdict:** Economic incentive misalignment; DA-valid but unrecoverable via pricing

### Finding 5: No Slashing for Archival Failure ❌

- **Current design:** Validators are slashed for DA failures (sampling)
- **Not slashed for:** Recovery failures (archival infrastructure)
- **Gap:** Responsibility is on rollups, but no compensation mechanism
- **Verdict:** Loss externalization; rollups bear all recovery risk

---

## NEXT PHASE: FORMAL INVARIANT TEST

**Invariant to test:**
```
Invariant_Recoverability:
If DA sampling passes at time T,
then a rollup can reconstruct full data within:
  - Time budget: 7 days (before pruning) or 12 hours (if time-pressured)
  - Cost budget: < $10 (less than expected rollup profit margin)
  with high probability (>90%)
```

**Expected result:** FAIL (archival infrastructure not guaranteed)
