# CRYPTO BOUNTY HUNTING - OPERATIONAL GUIDE

**Status:** POC Functional (3/3 tests pass)
**Target:** Uniswap V3 Core
**Platform:** Immunefi
**Bounty:** $500-$100,000
**Timeline:** 2-3 weeks intensive work

---

## ARCHITECTURE

```
Project Structure:
├── hardhat-poc/              # Working Hardhat project
│   ├── contracts/            # Solidity contracts
│   │   ├── MockUniswapV3Pool.sol    (reentrancy guard)
│   │   └── FlashSwapAttacker.sol    (exploit contract)
│   ├── test/
│   │   └── reentrancy.test.js       (3 passing tests)
│   └── artifacts/            # Compiled ABIs + bytecode
│
├── memory/bounty_audits/uniswap-v3-core/  # Real Uniswap V3 repo
│   ├── contracts/
│   │   ├── UniswapV3Pool.sol        (TARGET)
│   │   ├── LiquidityMath.sol        (Precision target)
│   │   └── SwapMath.sol             (Math target)
│   └── test/                        (Reference)
│
└── docs/
    └── OPERATIONAL_GUIDE.md         (This file)
```

---

## EXECUTION PHASES

### PHASE 1: RECONNAISSANCE (DONE)
- [x] Repository downloaded
- [x] Contracts analyzed
- [x] 5 vulnerability candidates identified
- [x] Mock POC created & tested

### PHASE 2: SEPOLIA TESTING (NEXT)
**Timeline:** 2-3 days
**Goal:** Test real Uniswap V3 contracts on Sepolia

Steps:
1. Deploy Uniswap V3Factory + Pool to Sepolia
2. Initialize with test token pair
3. Run attack contracts against real code
4. Document all findings

Tools needed:
- Hardhat + Ethers.js
- Uniswap V3 Periphery (Router)
- Sepolia testnet RPC
- Testnet ETH (from faucet)

### PHASE 3: VULNERABILITY CONFIRMATION (3-5 days)
**Goal:** Reproduce real vulnerability

If found:
1. Create minimal POC
2. Document attack flow
3. Calculate impact/severity
4. Prepare report

### PHASE 4: BOUNTY SUBMISSION (1 day)
1. Write Immunefi report
2. Include POC code + comments
3. Explain remediation
4. Submit via Immunefi form

---

## VULNERABILITY HIERARCHY

### Priority 1: REENTRANCY (Highest Reward)
- **Target:** UniswapV3Pool.swap() callback
- **Attack:** Nested call during callback execution
- **Reward:** $50K-$100K
- **Effort:** Medium
- **POC Status:** Mock test passes ✓

### Priority 2: PRECISION LOSS (High Reward)
- **Target:** LiquidityMath operations
- **Attack:** Dust amounts, rounding errors
- **Reward:** $5K-$20K
- **Effort:** Medium
- **POC Status:** Need to test edge cases

### Priority 3: ORACLE MANIPULATION (High Reward)
- **Target:** Flash loan + price impact
- **Attack:** Manipulate TWAP oracle
- **Reward:** $10K-$50K
- **Effort:** High
- **POC Status:** Needs Sepolia integration

### Priority 4: TICK OVERFLOW (Medium Reward)
- **Target:** TickBitmap operations
- **Attack:** Integer overflow conditions
- **Reward:** $10K-$25K
- **Effort:** High
- **POC Status:** Needs mapping analysis

---

## CRITICAL CONTRACTS

**UniswapV3Pool.sol (35.5 KB)**
- Main target
- Swap, mint, burn, collect functions
- Callback handling
- Liquidity management

**LiquidityMath.sol**
- Critical math operations
- Precision edge cases
- Rounding behavior

**SwapMath.sol**
- Price calculations
- Token amount conversions
- Overflow potential

---

## SEPOLIA DEPLOYMENT CHECKLIST

- [ ] Testnet wallet created
- [ ] ETH from faucet (2+ ETH needed)
- [ ] Hardhat configured for Sepolia
- [ ] Uniswap V3 Core contracts deployed
- [ ] Factory initialized
- [ ] Pool created with test tokens
- [ ] Attacker contract deployed
- [ ] Test run against real contracts
- [ ] Results documented

---

## SUCCESS CRITERIA

**Minimum:** Find 1 medium-severity issue → $1K-$5K
**Target:** Find high-severity issue → $5K-$50K
**Excellent:** Find critical vulnerability → $50K-$100K

---

## REALISTIC TIMELINE

```
Week 1:
- Day 1-2: Sepolia setup + deployment (4 hrs)
- Day 3-4: Manual code analysis (8 hrs)
- Day 5-6: Edge case testing (8 hrs)
- Day 7: Report preparation (4 hrs)
Total: 24 hours invested

Week 2-3:
- Detailed POC development
- Multiple attack vectors tested
- Vulnerability confirmation
- Report writing

Expected: Bounty submission by end of Week 2
```

---

## RESOURCES

**Hardhat:** `./hardhat-poc/` (ready to use)
**Uniswap V3:** `./memory/bounty_audits/uniswap-v3-core/`
**Documentation:** `./docs/` (this folder)
**Tests:** All 3/3 passing ✓

**Online Resources:**
- Uniswap V3 Whitepaper
- Immunefi: https://immunefi.com/bounty/uniswap/
- Hardhat Docs: https://hardhat.org/
- Ethers.js: https://docs.ethers.org/

---

## FINANCIAL SUMMARY

**Investment:** 30-50 hours over 2-3 weeks
**Expected Return:** $5K-$100K
**ROI:** $100-$3,333/hour
**Risk:** None (testnet only, responsible disclosure)

---

## NEXT IMMEDIATE ACTION

1. Ensure you have Node.js + npm installed
2. cd hardhat-poc && npm install (already done)
3. Get Sepolia testnet RPC (free: Infura/Alchemy)
4. Get testnet ETH from faucet
5. Configure .env with RPC URL
6. Begin Sepolia testing tomorrow

**Current Status:** POC functional, ready for real testing
