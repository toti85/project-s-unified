# KINETIQ CONTRACT ARCHITECTURE MAPPING
**January 24, 2026 | Phase 0 Analysis Foundation**

---

## 📋 EXECUTIVE SUMMARY

**8 Core Contracts | 90+ State Variables | 5 Role Tiers | 3 Critical Paths**

The Kinetiq protocol is a **liquid staking system** for Hyperliquid validators. Core architecture:
- **Entry point:** StakingManager (deposits/withdrawals)
- **Token layer:** KHYPE (ERC-20 staked token)
- **Accounting:** StakingAccountant (exchange rates)
- **Validators:** ValidatorManager (delegation, rewards, slashing)
- **Oracles:** OracleManager + DefaultOracle (performance reporting)
- **Control:** PauserRegistry (emergency pause)

---

## 🔗 CONTRACT INTERACTION MAP

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERACTIONS                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    StakingManager (Core)     │
        │  - Deposits, Withdrawals     │
        │  - L1 Operations Queue       │
        │  - Delegation Management     │
        └──────────────────────────────┘
                  │          │          │
        ┌─────────┘          │          └──────────┐
        │                    │                     │
        ▼                    ▼                      ▼
   ┌─────────┐      ┌──────────────────┐      ┌──────────────┐
   │  KHYPE  │      │StakingAccountant │      │ValidatorMgr  │
   │ (Token) │      │ - Exchange Rate  │      │- Validators  │
   │         │      │ - Accounting     │      │- Rewards     │
   └─────────┘      └──────────────────┘      │- Slashing    │
                                               │- Delegation │
                                               └──────────────┘
                                                      │
                                        ┌─────────────┴──────────────┐
                                        │                            │
                                        ▼                            ▼
                                  ┌──────────────┐          ┌─────────────────┐
                                  │OracleManager │          │ DefaultOracle   │
                                  │- Validation  │◄────────►│ - Metric Store  │
                                  │- Aggregation │          │ - Audit Trail   │
                                  └──────────────┘          └─────────────────┘
                                        │
                                        ▼
                            ┌──────────────────────────┐
                            │    PauserRegistry        │
                            │  - Emergency Control     │
                            │  - All Contracts Tied    │
                            └──────────────────────────┘
```

---

## 📊 STATE VARIABLES BY CONTRACT

### **1. StakingManager (Core - 24 state vars)**

```
ACCOUNTING:
├─ totalStaked: uint256                    // Total HYPE staked
├─ totalClaimed: uint256                   // Total HYPE claimed/withdrawn
├─ totalQueuedWithdrawals: uint256         // Pending withdrawals
├─ hypeBuffer: uint256                     // Current liquidity buffer
├─ treasury: address                       // Fee recipient

PARAMETERS:
├─ targetBuffer: uint256                   // Target buffer size
├─ stakingLimit: uint256                   // Max stake (0=unlimited)
├─ minStakeAmount: uint256                 // Min per transaction
├─ maxStakeAmount: uint256                 // Max per transaction (0=unlimited)
├─ withdrawalDelay: uint256                // Withdrawal confirmation delay
├─ unstakeFeeRate: uint256                 // Fee in basis points (10 = 0.1%)

STATUS FLAGS:
├─ stakingPaused: bool                     // Staking pause state
├─ withdrawalPaused: bool                  // Withdrawal pause state
├─ whitelistEnabled: bool                  // Whitelist enforcement

MAPPINGS:
├─ nextWithdrawalId[user]: uint256         // Per-user withdrawal counter
├─ _withdrawalRequests[user][id]: WithdrawalRequest  // Withdrawal details
├─ _whitelist: EnumerableSet<address>     // Whitelisted users

CONTRACT REFERENCES:
├─ pauserRegistry: IPauserRegistry         // Pause control
├─ kHYPE: IKHYPE                           // Staked token
├─ validatorManager: IValidatorManager     // Validator ops
├─ stakingAccountant: IStakingAccountant   // Accounting
```

### **2. KHYPE (Token - 8 state vars)**

```
CORE:
├─ name: string                            // Token name
├─ symbol: string                          // Token symbol
├─ decimals: uint8 = 18                    // Decimal places
├─ totalSupply: uint256                    // Total minted

ROLES:
├─ minter: address                         // Can mint
├─ burner: address                         // Can burn
├─ admin: address                          // Admin role
├─ pauserRegistry: IPauserRegistry         // Pause control

STANDARD ERC20:
├─ balanceOf[account]: uint256             // User balances
├─ allowance[owner][spender]: uint256      // Spend approvals
├─ nonces[owner]: uint256                  // Permit nonces
```

### **3. StakingAccountant (Accounting - 10 state vars)**

```
ACCOUNTING:
├─ totalHYPEStaked: uint256                // Global stake total
├─ totalHYPEClaimed: uint256               // Global claim total
├─ uniqueTokenCount: uint256               // Number of unique kHYPE tokens

AUTHORIZATION:
├─ authorizedStakingManagers: Set<address> // Approved staking managers
├─ kHYPETokens: Map<StakingManager → IKHYPE> // Token per manager

HELPER:
├─ pauserRegistry: IPauserRegistry         // Pause control
```

### **4. ValidatorManager (Validator Ops - 18 state vars)**

```
VALIDATORS:
├─ validators: Set<address>                // Active validator list
├─ validatorInfo[addr]: ValidatorInfo      // Per-validator state
│   ├─ balance: uint256                    // Validator balance
│   ├─ delegatedStakingManager: address    // Who can operate validator
│   └─ rebalanceableAmount: uint256        // Available for rebalancing

PERFORMANCE:
├─ totalRewards: uint256                   // Accumulated rewards
├─ totalSlashing: uint256                  // Accumulated slashing
├─ pendingRewards[validator]: uint256      // Per-validator pending
├─ pendingSlashing[validator]: uint256     // Per-validator pending

PARAMETERS:
├─ maxValidators: uint256                  // Limit on validators
├─ minValidatorBalance: uint256            // Minimum per validator
├─ maxRewardPercentage: uint256            // Reward cap (basis points)
├─ maxSlashingPercentage: uint256          // Slash cap (basis points)

DELEGATION:
├─ delegations: Map<StakingManager → Validator>  // Who stakes where

EXTERNAL:
├─ l1Write: IL1Write                       // Hyperliquid L1 interface
├─ pauserRegistry: IPauserRegistry         // Pause control
```

### **5. OracleManager (Oracle Aggregation - 14 state vars)**

```
ORACLE DATA:
├─ oracleAdapters: Set<address>            // Authorized oracle adapters
├─ oracleActive[adapter]: bool             // Adapter enabled flag
├─ minValidOracles: uint256                // Minimum votes for validity
├─ reportedMetrics: Map<Validator → Metrics> // Latest metrics

BOUNDS & FRESHNESS:
├─ maxPerformanceBound: uint256            // Upper reward limit
├─ minPerformanceBound: int256             // Lower slash limit
├─ minUpdateInterval: uint256              // Min time between updates
├─ lastUpdateTime[validator]: uint256      // Last report timestamp

SANITY CHECKING:
├─ sanityChecker: address                  // Checker contract
├─ suspiciousValidators: Set<address>      // Flagged for review

EXTERNAL:
├─ validatorManager: IValidatorManager     // Report destination
├─ pauserRegistry: IPauserRegistry         // Pause control
```

### **6. DefaultOracle (Metric Storage - 4 state vars)**

```
STORAGE:
├─ metrics: Map<Validator → PerformanceMetric> // Historical metrics
│   ├─ reward: uint256
│   ├─ slashing: uint256
│   ├─ timestamp: uint256
│   └─ reportingEntity: address
├─ auditTrail: Array<AuditEntry>          // Full history
├─ oracleManager: address                 // Write permission

HELPER:
├─ pauserRegistry: IPauserRegistry        // Pause control
```

### **7. PauserRegistry (Emergency Control - 6 state vars)**

```
PAUSE STATE:
├─ pauserRole: address                     // Can pause
├─ unpauser: address                       // Can unpause
├─ isPaused: Map<Contract → bool>          // Pause state per contract
├─ pauseAll: bool                          // Global pause flag

AUTHORIZATION:
├─ authorizedContracts: Set<address>       // Can be paused
```

### **8. DefaultAdapter (Oracle Bridge - 2 state vars)**

```
REFERENCES:
├─ oracleManager: IOracleManager           // Destination
├─ pauserRegistry: IPauserRegistry         // Pause control
```

---

## 👥 ROLE-BASED ACCESS CONTROL MATRIX

| Role | Function | Contract | Who Can Call |
|------|----------|----------|--------------|
| **ADMIN** | initialize() | All | Only once (proxy) |
| **ADMIN** | grantRole() | All | Deployer |
| | | | |
| **MANAGER** | pause()/unpause() | All except KHYPE | MANAGER_ROLE holders |
| **MANAGER** | setMaxStakeAmount() | StakingManager | MANAGER_ROLE |
| **MANAGER** | setStakingLimit() | StakingManager | MANAGER_ROLE |
| **MANAGER** | setUnstakeFeeRate() | StakingManager | MANAGER_ROLE |
| **MANAGER** | setTargetBuffer() | StakingManager | MANAGER_ROLE |
| **MANAGER** | activateValidator() | ValidatorManager | MANAGER_ROLE |
| **MANAGER** | deactivateValidator() | ValidatorManager | MANAGER_ROLE |
| **MANAGER** | authorizeOracleAdapter() | OracleManager | MANAGER_ROLE |
| **MANAGER** | setMinValidOracles() | OracleManager | MANAGER_ROLE |
| **MANAGER** | setMaxPerformanceBound() | OracleManager | MANAGER_ROLE |
| | | | |
| **OPERATOR** | executeL1Operations() | StakingManager | OPERATOR_ROLE |
| **OPERATOR** | queueL1Operations() | StakingManager | OPERATOR_ROLE |
| **OPERATOR** | generatePerformance() | OracleManager | OPERATOR_ROLE |
| **OPERATOR** | reportRewardEvent() | ValidatorManager | ORACLE_MANAGER_ROLE |
| **OPERATOR** | reportSlashingEvent() | ValidatorManager | ORACLE_MANAGER_ROLE |
| | | | |
| **MINTER** | mint() | KHYPE | StakingManager only |
| **BURNER** | burn() | KHYPE | StakingManager only |
| | | | |
| **PUBLIC** | stake() | StakingManager | Any (if whitelisted) |
| **PUBLIC** | queueWithdrawal() | StakingManager | Any (if whitelisted) |
| **PUBLIC** | confirmWithdrawal() | StakingManager | Any |
| **PUBLIC** | kHYPEToHYPE() | StakingAccountant | Any |
| **PUBLIC** | HYPEToKHYPE() | StakingAccountant | Any |

---

## 🔀 CRITICAL EXECUTION PATHS

### **PATH 1: DEPOSIT FLOW**
```
User sends HYPE (ETH) →
  1. StakingManager.stake() [public, nonReentrant]
     - Check: whitelist (if enabled)
     - Check: staking not paused
     - Check: amount within min/max bounds
     
  2. StakingAccountant.HYPEToKHYPE(amount)
     - Calculate: exchange ratio
     - Return: kHYPE amount to mint
     
  3. KHYPE.mint(user, kHYPEAmount)
     - Update: totalSupply
     - Update: balanceOf[user]
     - Emit: Transfer event
     
  4. StakingManager internal updates
     - Update: totalStaked += amount
     - Update: hypeBuffer += amount
     - Emit: StakeReceived event

Result: User gets kHYPE, balance updated
Gas: ~150K typical
Dependencies: KHYPE, StakingAccountant, ValidatorManager (delegation check)
```

### **PATH 2: WITHDRAWAL FLOW (2-step)**
```
Step A: User queues withdrawal →
  1. StakingManager.queueWithdrawal(kHYPEAmount) [public, nonReentrant]
     - Check: whitelist (if enabled)
     - Check: withdrawal not paused
     - Calculate: unstake fee = kHYPEAmount × unstakeFeeRate
     - Transfer: kHYPE from user to StakingManager
     
  2. StakingAccountant.kHYPEToHYPE(postFeeKHYPE)
     - Calculate: HYPE equivalent
     - Return: amount to withdraw
     
  3. ValidatorManager.getDelegation()
     - Check: validator is available
     - Prepare: rebalancing if needed
     
  4. StakingManager records withdrawal request
     - Store: WithdrawalRequest[user][id]
     - Update: totalQueuedWithdrawals
     - Emit: WithdrawalQueued event

Step B: User confirms withdrawal (after delay) →
  1. StakingManager.confirmWithdrawal(withdrawalId) [public, nonReentrant]
     - Check: withdrawal delay elapsed
     - Retrieve: stored WithdrawalRequest
     - Check: contract has balance
     
  2. Transfer ETH to user
     - (bool success, ) = payable(user).call{value}("")
     - Emit: WithdrawalConfirmed event

Result: User gets ETH back, kHYPE burned, fees to treasury
Gas: ~200K typical (combined)
Dependencies: KHYPE, StakingAccountant, ValidatorManager
```

### **PATH 3: VALIDATOR PERFORMANCE UPDATE (Via Oracle)**
```
Oracle reports performance →
  1. OracleManager.generatePerformance(validator) [OPERATOR_ROLE]
     - Aggregate: metrics from multiple oracle adapters
     - Validate: consensus (minValidOracles met)
     - Sanity check: bounds within limits
     
  2. DefaultOracle retrieves historical metric
     - Get: latest ValidatorMetric[validator]
     - Calculate: delta from baseline
     
  3. OracleManager → ValidatorManager
     - Report: reportRewardEvent() OR reportSlashingEvent()
     - Store: pendingRewards/Slashing[validator]
     - Update: totalRewards/totalSlashing
     
  4. Next stake() call includes rewards
     - ValidatorManager.totalRewards() is consulted
     - Exchange ratio recalculated: (totalStaked + rewards - claims) / kHYPE
     - New stakers get diluted by rewards

Result: Protocol's exchange rate reflects performance
Gas: ~100K typical
Dependencies: OracleManager, DefaultOracle, ValidatorManager
```

---

## 🔗 CALL DEPENDENCY GRAPH

```
StakingManager (HUB)
├─→ KHYPE
│   └─→ PauserRegistry (isPaused check)
├─→ StakingAccountant
│   └─→ Exchange rate calculation
├─→ ValidatorManager
│   ├─→ Delegation queries
│   ├─→ Reward aggregation
│   ├─→ Rebalancing logic
│   └─→ L1Write interface (sends to Hyperliquid)
├─→ PauserRegistry
│   └─→ Pause state checks

OracleManager
├─→ DefaultOracle
│   └─→ Historical metrics storage
├─→ ValidatorManager
│   └─→ Reward/slashing reports
├─→ Multiple OracleAdapters
│   └─→ Consensus voting
└─→ PauserRegistry

ValidatorManager
├─→ L1Write interface
│   └─→ Hyperliquid L1 contract
├─→ Validator delegation tracking
└─→ Reward/slashing calculations

All Contracts
└─→ PauserRegistry
    └─→ Emergency pause capability
```

---

## ⚠️ CRITICAL STATE DEPENDENCIES

**These state changes are INTERDEPENDENT - changing one affects others:**

1. **Exchange Rate Triangle:**
   ```
   totalStaked (StakingManager)
        ↓
   StakingAccountant.totalHYPEStaked
        ↓
   Exchange Ratio = (totalStaked + rewards - claims) / kHYPE.totalSupply
        ↓
   KHYPE.mint() amount depends on exchange rate
   ```

2. **Withdrawal Queue Cascade:**
   ```
   queueWithdrawal() reduces buffer
        ↓
   Buffer drops below targetBuffer
        ↓
   Triggers rebalancing in ValidatorManager
        ↓
   L1 operations queued
        ↓
   executeL1Operations() pulls from validators
   ```

3. **Reward Accumulation Loop:**
   ```
   Oracle reports rewards
        ↓
   ValidatorManager.totalRewards increases
        ↓
   Exchange ratio recalculated (HYPE/kHYPE increases)
        ↓
   New stake() gets less kHYPE per HYPE (diluted)
   ```

---

## 🔍 CROSS-CONTRACT VULNERABILITIES TO CHECK

**Phase 0 Hypothesis Areas:**

1. **Exchange Rate Manipulation**
   - Can HYPE/kHYPE ratio be arbitraged?
   - Are rewards/slashing properly reflected?
   - Is rounding consistent across paths?

2. **Withdrawal Queue Dynamics**
   - Can users front-run withdrawals?
   - Is fee calculation correct for all cases?
   - Buffer depletion scenarios?

3. **Validator State Consistency**
   - Can validator balances diverge from L1?
   - Slashing race conditions?
   - Rebalancing edge cases?

4. **Oracle Aggregation**
   - Can minority oracle manipulate consensus?
   - Stale data windows?
   - Bounds checking correctness?

5. **Role-Based Access**
   - Can MANAGER_ROLE prevent OPERATOR_ROLE actions?
   - Pause() state exploitability?
   - Role assumption safety?

---

**MAPPING COMPLETE | Ready for Phase 0 Hypothesis Definition**

This architecture forms the **baseline for 5 targeted hypotheses** to test in Phase 0.

