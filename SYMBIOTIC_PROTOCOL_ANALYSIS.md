# Symbiotic Protocol - Smart Contract Analysis

## Executive Summary

Symbiotic is a modular shared security protocol that enables decentralized networks to customize multi-asset restaking with flexible slashing and rewards mechanisms. The protocol consists of three core components: **Vault** (collateral management), **Delegator** (stake allocation), and **Slasher** (penalty enforcement).

---

## 1. VAULT IMPLEMENTATION - Collateral & Deposit Management

### Location: `symbioticfi/core/src/contracts/vault/`

#### Key Contracts:
- **VaultStorage.sol** - State management and epoch tracking
- **Vault.sol** - Core vault logic for deposits, withdrawals, slashing

### 1.1 VaultStorage - Core State Variables

**File:** `VaultStorage.sol`

```solidity
abstract contract VaultStorage is StaticDelegateCallable, IVaultStorage {
    using Checkpoints for Checkpoints.Trace256;
    
    // Role definitions
    bytes32 public constant DEPOSIT_WHITELIST_SET_ROLE = keccak256("DEPOSIT_WHITELIST_SET_ROLE");
    bytes32 public constant IS_DEPOSIT_LIMIT_SET_ROLE = keccak256("IS_DEPOSIT_LIMIT_SET_ROLE");
    bytes32 public constant DEPOSIT_LIMIT_SET_ROLE = keccak256("DEPOSIT_LIMIT_SET_ROLE");
    
    // Key state variables
    address public immutable DELEGATOR_FACTORY;
    address public immutable SLASHER_FACTORY;
    
    // Configuration
    address public collateral;              // Single ERC20 token per vault
    address public burner;                  // Handles penalized collateral
    uint48 public epochDurationInit;        // Epoch start timestamp
    uint48 public epochDuration;            // Length of each epoch
    
    // Delegation & Slashing setup
    address public delegator;
    bool public isDelegatorInitialized;
    address public slasher;
    bool public isSlasherInitialized;
    
    // Withdrawal management
    mapping(uint256 epoch => uint256 amount) public withdrawals;
    mapping(uint256 epoch => uint256 amount) public withdrawalShares;
    mapping(uint256 epoch => mapping(address account => uint256 amount)) public withdrawalSharesOf;
    mapping(uint256 epoch => mapping(address account => bool value)) public isWithdrawalsClaimed;
    
    // Internal checkpoints for historical lookups
    Checkpoints.Trace256 internal _activeShares;
    Checkpoints.Trace256 internal _activeStake;
    mapping(address account => Checkpoints.Trace256 shares) internal _activeSharesOf;
}
```

### 1.2 Epoch Management Functions

**File:** `VaultStorage.sol`

```solidity
/// @dev Calculates the epoch number for a given timestamp
function epochAt(uint48 timestamp) public view returns (uint256) {
    if (timestamp < epochDurationInit) {
        revert InvalidTimestamp();
    }
    return (timestamp - epochDurationInit) / epochDuration;
}

/// @dev Returns the current epoch
function currentEpoch() public view returns (uint256) {
    return (Time.timestamp() - epochDurationInit) / epochDuration;
}

/// @dev Historical stake/shares lookup at a specific timestamp
function activeStakeAt(uint48 timestamp, bytes memory hint) public view returns (uint256) {
    return _activeStake.upperLookupRecent(timestamp, hint);
}

function activeSharesOfAt(address account, uint48 timestamp, bytes memory hint) 
    public view returns (uint256) {
    return _activeSharesOf[account].upperLookupRecent(timestamp, hint);
}
```

### 1.3 Deposit/Withdrawal Lifecycle in Vault.sol

**File:** `Vault.sol`

```solidity
/**
 * DEPOSIT FLOW:
 * 1. User calls deposit(onBehalfOf, amount)
 * 2. Tokens transferred from user to vault
 * 3. Shares minted based on: ERC4626Math.previewDeposit(amount, activeShares, activeStake)
 * 4. Active stake and shares updated in checkpoints
 */
function deposit(address onBehalfOf, uint256 amount)
    public
    virtual
    nonReentrant
    returns (uint256 depositedAmount, uint256 mintedShares)
{
    if (onBehalfOf == address(0)) {
        revert InvalidOnBehalfOf();
    }
    
    // Deposit limit check
    if (isDepositLimit && activeStake() + depositedAmount > depositLimit) {
        revert DepositLimitReached();
    }

    uint256 activeStake_ = activeStake();
    uint256 activeShares_ = activeShares();

    // Standard ERC4626 share calculation
    mintedShares = ERC4626Math.previewDeposit(depositedAmount, activeShares_, activeStake_);

    // Update checkpoints for historical lookups
    _activeStake.push(Time.timestamp(), activeStake_ + depositedAmount);
    _activeShares.push(Time.timestamp(), activeShares_ + mintedShares);
    _activeSharesOf[onBehalfOf].push(Time.timestamp(), activeSharesOf(onBehalfOf) + mintedShares);
    
    emit Deposit(msg.sender, onBehalfOf, depositedAmount, mintedShares);
}

/**
 * WITHDRAWAL FLOW (2-stage process):
 * Stage 1: User requests withdrawal - amount marked as pending but REMAINS SLASHABLE
 * Stage 2: After next epoch ends - user claims funds (non-slashable)
 */
function withdraw(address claimer, uint256 amount)
    external
    nonReentrant
    returns (uint256 burnedShares, uint256 mintedShares)
{
    burnedShares = ERC4626Math.previewWithdraw(amount, activeShares(), activeStake());
    
    if (burnedShares > activeSharesOf(msg.sender)) {
        revert TooMuchWithdraw();
    }

    mintedShares = _withdraw(claimer, amount, burnedShares);
}

function _withdraw(address claimer, uint256 withdrawnAssets, uint256 burnedShares)
    internal
    virtual
    returns (uint256 mintedShares)
{
    // Burn active shares
    _activeSharesOf[msg.sender].push(
        Time.timestamp(), 
        activeSharesOf(msg.sender) - burnedShares
    );
    _activeShares.push(Time.timestamp(), activeShares() - burnedShares);
    _activeStake.push(Time.timestamp(), activeStake() - withdrawnAssets);

    // Add to next epoch's withdrawal queue (still slashable during this epoch)
    uint256 epoch = currentEpoch() + 1;
    uint256 withdrawals_ = withdrawals[epoch];
    uint256 withdrawalsShares_ = withdrawalShares[epoch];

    mintedShares = ERC4626Math.previewDeposit(
        withdrawnAssets, 
        withdrawalsShares_, 
        withdrawals_
    );

    withdrawals[epoch] = withdrawals_ + withdrawnAssets;
    withdrawalShares[epoch] = withdrawalsShares_ + mintedShares;
    withdrawalSharesOf[epoch][claimer] += mintedShares;

    emit Withdraw(msg.sender, claimer, withdrawnAssets, burnedShares, mintedShares);
}

/**
 * CLAIM FLOW:
 * - User can only claim from past epochs (epoch < currentEpoch())
 * - Once claimed, tokens cannot be re-slashed
 */
function claim(address recipient, uint256 epoch) 
    external nonReentrant returns (uint256 amount) 
{
    if (recipient == address(0)) {
        revert InvalidRecipient();
    }
    amount = _claim(epoch);
    IERC20(collateral).safeTransfer(recipient, amount);
    emit Claim(msg.sender, recipient, epoch, amount);
}

function _claim(uint256 epoch) internal returns (uint256 amount) {
    if (epoch >= currentEpoch()) {
        revert InvalidEpoch();  // Can't claim current or future epochs
    }

    if (isWithdrawalsClaimed[epoch][msg.sender]) {
        revert AlreadyClaimed();
    }

    amount = withdrawalsOf(epoch, msg.sender);

    if (amount == 0) {
        revert InsufficientClaim();
    }

    isWithdrawalsClaimed[epoch][msg.sender] = true;
}
```

### 1.4 Share Price Calculation

**File:** `Vault.sol` - Share Accounting

The vault implements standard ERC4626 accounting where:
- **Share Price = activeStake / activeShares** 

```solidity
/**
 * Calculate user's balance in collateral tokens from shares
 * Formula: (userShares * activeStake) / activeShares
 */
function activeBalanceOfAt(address account, uint48 timestamp, bytes calldata hints) 
    public view returns (uint256) 
{
    return ERC4626Math.previewRedeem(
        activeSharesOfAt(account, timestamp, activeBalanceOfHints.activeSharesOfHint),
        activeStakeAt(timestamp, activeBalanceOfHints.activeStakeHint),
        activeSharesAt(timestamp, activeBalanceOfHints.activeSharesHint)
    );
}

/**
 * Total slashable balance includes:
 * - Active balance (not withdrawn)
 * - Current epoch withdrawals (still slashable during epoch)
 * - Next epoch withdrawals (slashable until their deadline)
 */
function slashableBalanceOf(address account) external view returns (uint256) {
    uint256 epoch = currentEpoch();
    return activeBalanceOf(account) 
        + withdrawalsOf(epoch, account) 
        + withdrawalsOf(epoch + 1, account);
}
```

---

## 2. SLASHING EXECUTION LOGIC

### Location: `symbioticfi/core/src/contracts/slasher/`

#### Key Contracts:
- **BaseSlasher.sol** - Core slashing validation
- **Slasher.sol** - Instant execution slashing
- **VetoSlasher.sol** - Request-veto-execute pattern

### 2.1 BaseSlasher - Core Slashing Mechanism

**File:** `BaseSlasher.sol`

```solidity
abstract contract BaseSlasher is Entity, StaticDelegateCallable, 
    ReentrancyGuardUpgradeable, IBaseSlasher {
    
    using Checkpoints for Checkpoints.Trace256;
    using Subnetwork for bytes32;

    // Constants
    uint256 public constant BURNER_GAS_LIMIT = 150_000;
    uint256 public constant BURNER_RESERVE = 20_000;

    // Immutable addresses
    address public immutable VAULT_FACTORY;
    address public immutable NETWORK_MIDDLEWARE_SERVICE;
    
    // Mutable state
    address public vault;
    bool public isBurnerHook;

    // Core slashing state: tracks cumulative slashes per operator per network
    mapping(bytes32 subnetwork => mapping(address operator => uint48 value)) 
        public latestSlashedCaptureTimestamp;
    
    mapping(bytes32 subnetwork => mapping(address operator => Checkpoints.Trace256 amount)) 
        internal _cumulativeSlash;

    /**
     * CRITICAL: Calculate slashable stake at a specific timestamp
     * 
     * Slashable stake = stakeAt(captureTimestamp) - (cumulativeSlash(now) - cumulativeSlashAt(captureTimestamp))
     * 
     * This bounds slashing: you cannot slash more than was guaranteed at capture time,
     * even if other networks have already slashed the same operator.
     */
    function _slashableStake(
        bytes32 subnetwork, 
        address operator, 
        uint48 captureTimestamp, 
        bytes memory hints
    )
        internal
        view
        returns (uint256 slashableStake_, uint256 stakeAmount)
    {
        SlashableStakeHints memory slashableStakeHints;
        if (hints.length > 0) {
            slashableStakeHints = abi.decode(hints, (SlashableStakeHints));
        }

        // Timestamp validation: must be within current epoch
        if (
            captureTimestamp < Time.timestamp() - IVault(vault).epochDuration() 
            || captureTimestamp >= Time.timestamp()
            || captureTimestamp < latestSlashedCaptureTimestamp[subnetwork][operator]
        ) {
            return (0, 0);
        }

        // Get stake at capture time from delegator
        stakeAmount = IBaseDelegator(IVault(vault).delegator())
            .stakeAt(subnetwork, operator, captureTimestamp, slashableStakeHints.stakeHints);

        // Calculate remaining slashable amount after prior slashes
        // CRUCIAL: slashes are subtracted only from the period AFTER capture timestamp
        slashableStake_ = stakeAmount
            - Math.min(
                cumulativeSlash(subnetwork, operator)
                    - cumulativeSlashAt(subnetwork, operator, captureTimestamp,
                        slashableStakeHints.cumulativeSlashFromHint),
                stakeAmount
            );
    }

    /**
     * Track cumulative slashing to enforce bounds on future requests
     * Each slash updates the cumulative total for that operator-network pair
     */
    function _updateCumulativeSlash(
        bytes32 subnetwork, 
        address operator, 
        uint256 amount
    ) internal {
        _cumulativeSlash[subnetwork][operator].push(
            Time.timestamp(), 
            cumulativeSlash(subnetwork, operator) + amount
        );
    }

    /**
     * Notify delegator and vault of slash
     * Delegator handles stake updates; vault handles active balance updates
     */
    function _delegatorOnSlash(
        bytes32 subnetwork,
        address operator,
        uint256 amount,
        uint48 captureTimestamp,
        bytes memory data
    ) internal {
        IBaseDelegator(IVault(vault).delegator())
            .onSlash(
                subnetwork,
                operator,
                amount,
                captureTimestamp,
                abi.encode(GeneralDelegatorData({slasherType: TYPE, data: data}))
            );
    }

    function _vaultOnSlash(uint256 amount, uint48 captureTimestamp) internal {
        IVault(vault).onSlash(amount, captureTimestamp);
    }

    /**
     * Gas-safe call to burner hook for custom collateral handling
     */
    function _burnerOnSlash(
        bytes32 subnetwork, 
        address operator, 
        uint256 amount, 
        uint48 captureTimestamp
    ) internal {
        if (isBurnerHook) {
            address burner = IVault(vault).burner();
            bytes memory calldata_ = abi.encodeCall(
                IBurner.onSlash, 
                (subnetwork, operator, amount, captureTimestamp)
            );

            if (gasleft() < BURNER_RESERVE + BURNER_GAS_LIMIT * 64 / 63) {
                revert InsufficientBurnerGas();
            }

            assembly ("memory-safe") {
                pop(call(BURNER_GAS_LIMIT, burner, 0, add(calldata_, 0x20), 
                    mload(calldata_), 0, 0))
            }
        }
    }
}
```

### 2.2 Slasher - Instant Execution

**File:** `Slasher.sol`

```solidity
contract Slasher is BaseSlasher, ISlasher {
    
    /**
     * IMMEDIATE SLASHING: Network middleware calls slash() directly
     * 
     * Flow:
     * 1. Validate capture timestamp is within current epoch
     * 2. Get slashable stake from delegator (ensures operator has adequate stake)
     * 3. Cap slash amount by slashable stake
     * 4. Update cumulative slashes to enforce bounds for future requests
     * 5. Notify delegator and vault
     * 6. Transfer penalized collateral to burner
     */
    function slash(
        bytes32 subnetwork, 
        address operator,
        uint256 amount, 
        uint48 captureTimestamp, 
        bytes calldata hints
    )
        external
        nonReentrant
        onlyNetworkMiddleware(subnetwork)
        returns (uint256 slashedAmount)
    {
        SlashHints memory slashHints;
        if (hints.length > 0) {
            slashHints = abi.decode(hints, (SlashHints));
        }

        // Timestamp must be fresh: within current epoch
        if (captureTimestamp < Time.timestamp() - IVault(vault).epochDuration() 
            || captureTimestamp >= Time.timestamp()) {
            revert InvalidCaptureTimestamp();
        }

        // Get slashable amount at this capture timestamp
        (uint256 slashableStake_, uint256 stakeAt) =
            _slashableStake(subnetwork, operator, captureTimestamp, 
                slashHints.slashableStakeHints);
        
        slashedAmount = Math.min(amount, slashableStake_);
        
        if (slashedAmount == 0) {
            revert InsufficientSlash();
        }

        // Update tracking for this operator-network pair
        _updateLatestSlashedCaptureTimestamp(subnetwork, operator, captureTimestamp);
        _updateCumulativeSlash(subnetwork, operator, slashedAmount);

        // Propagate to delegator and vault
        _delegatorOnSlash(
            subnetwork,
            operator,
            slashedAmount,
            captureTimestamp,
            abi.encode(ISlasher.DelegatorData({
                slashableStake: slashableStake_, 
                stakeAt: stakeAt
            }))
        );

        _vaultOnSlash(slashedAmount, captureTimestamp);
        _burnerOnSlash(subnetwork, operator, slashedAmount, captureTimestamp);

        emit Slash(subnetwork, operator, slashedAmount, captureTimestamp);
    }
}
```

---

## 3. VetoSlasher - Veto & Resolver Mechanism

### Location: `symbioticfi/core/src/contracts/slasher/VetoSlasher.sol`

```solidity
contract VetoSlasher is BaseSlasher, IVetoSlasher {
    using Math for uint256;
    using SafeCast for uint256;
    using Checkpoints for Checkpoints.Trace208;

    // Immutable
    address public immutable NETWORK_REGISTRY;

    // Dynamic resolver per subnetwork (can change between epochs)
    mapping(bytes32 subnetwork => Checkpoints.Trace208 value) internal _resolver;

    // Slash request queue
    SlashRequest[] public slashRequests;

    // Configuration
    uint48 public vetoDuration;                  // How long resolvers can veto (must < epoch duration)
    uint256 public resolverSetEpochsDelay;       // Minimum epochs before new resolver takes effect

    /**
     * SLASH REQUEST STRUCTURE
     */
    struct SlashRequest {
        bytes32 subnetwork;
        address operator;
        uint256 amount;
        uint48 captureTimestamp;
        uint48 vetoDeadline;                    // Time until which veto is allowed
        bool completed;                          // Execution or veto already occurred
    }

    /**
     * REQUEST PHASE: Network submits slash request
     * 
     * Requirements:
     * 1. captureTimestamp must allow time for veto + execution within epoch
     * 2. amount capped by slashable stake
     * 3. Request added to queue with vetoDeadline = now + vetoDuration
     */
    function requestSlash(
        bytes32 subnetwork,
        address operator,
        uint256 amount,
        uint48 captureTimestamp,
        bytes calldata hints
    ) 
        external nonReentrant
        onlyNetworkMiddleware(subnetwork) 
        returns (uint256 slashIndex) 
    {
        RequestSlashHints memory requestSlashHints;
        if (hints.length > 0) {
            requestSlashHints = abi.decode(hints, (RequestSlashHints));
        }

        // Stricter timestamp check: must leave time for veto + execution
        if (captureTimestamp < Time.timestamp() + vetoDuration - IVault(vault).epochDuration()
            || captureTimestamp >= Time.timestamp()) {
            revert InvalidCaptureTimestamp();
        }

        // Cap by slashable stake
        amount = Math.min(
            amount, 
            slashableStake(subnetwork, operator, captureTimestamp,
                requestSlashHints.slashableStakeHints)
        );
        
        if (amount == 0) {
            revert InsufficientSlash();
        }

        uint48 vetoDeadline = Time.timestamp() + vetoDuration;

        slashIndex = slashRequests.length;
        slashRequests.push(
            SlashRequest({
                subnetwork: subnetwork,
                operator: operator,
                amount: amount,
                captureTimestamp: captureTimestamp,
                vetoDeadline: vetoDeadline,
                completed: false
            })
        );

        emit RequestSlash(slashIndex, subnetwork, operator, amount, captureTimestamp, vetoDeadline);
    }

    /**
     * VETO PHASE: Resolver can veto request during veto window
     * 
     * Conditions:
     * 1. Resolver must exist at capture timestamp (knew about this operator then)
     * 2. Resolver must still exist now (hasn't been removed)
     * 3. Must be called before vetoDeadline
     * 4. Only the resolver address can veto
     */
    function vetoSlash(uint256 slashIndex, bytes calldata hints)
        external nonReentrant
    {
        VetoSlashHints memory vetoSlashHints;
        if (hints.length > 0) {
            vetoSlashHints = abi.decode(hints, (VetoSlashHints));
        }

        if (slashIndex >= slashRequests.length) {
            revert SlashRequestNotExist();
        }

        SlashRequest storage request = slashRequests[slashIndex];

        // Get resolver at capture and current time
        address captureResolver = resolverAt(
            request.subnetwork, 
            request.captureTimestamp,
            vetoSlashHints.captureResolverHint
        );
        
        address currentResolver = resolverAt(
            request.subnetwork, 
            Time.timestamp() - 1,
            vetoSlashHints.currentResolverHint
        );

        // Both resolvers must exist
        if (captureResolver == address(0) || currentResolver == address(0)) {
            revert NoResolver();
        }

        // Only resolver can veto (no consensus mechanism - single point of review)
        if (msg.sender != captureResolver) {
            revert NotResolver();
        }

        // Must be within veto window
        if (request.vetoDeadline <= Time.timestamp()) {
            revert VetoPeriodEnded();
        }

        // Mark as completed (blocks execution)
        if (request.completed) {
            revert SlashRequestCompleted();
        }

        request.completed = true;

        emit VetoSlash(slashIndex, msg.sender);
    }

    /**
     * EXECUTION PHASE: After veto period, execute slash if not vetoed
     * 
     * Conditions for success:
     * 1. No resolver at capture OR no resolver now → execute immediately
     * 2. Resolver exists both times AND veto period has ended → execute
     * 3. Capture timestamp still within epoch
     */
    function executeSlash(uint256 slashIndex, bytes calldata hints)
        external
        nonReentrant
        returns (uint256 slashedAmount)
    {
        ExecuteSlashHints memory executeSlashHints;
        if (hints.length > 0) {
            executeSlashHints = abi.decode(hints, (ExecuteSlashHints));
        }

        if (slashIndex >= slashRequests.length) {
            revert SlashRequestNotExist();
        }

        SlashRequest storage request = slashRequests[slashIndex];

        _checkNetworkMiddleware(request.subnetwork);

        // Check veto conditions
        address captureResolver = resolverAt(
            request.subnetwork, 
            request.captureTimestamp,
            executeSlashHints.captureResolverHint
        );
        
        address currentResolver = resolverAt(
            request.subnetwork, 
            Time.timestamp() - 1,
            executeSlashHints.currentResolverHint
        );

        // If resolver exists at BOTH capture and now, must wait for veto period
        if (captureResolver != address(0) && currentResolver != address(0) 
            && request.vetoDeadline > Time.timestamp()) {
            revert VetoPeriodNotEnded();
        }

        // Capture timestamp cannot be too old (must be within epoch)
        if (Time.timestamp() - request.captureTimestamp > IVault(vault).epochDuration()) {
            revert SlashPeriodEnded();
        }

        // Get fresh slashable stake
        (uint256 slashableStake_, uint256 stakeAt) =
            _slashableStake(
                request.subnetwork, 
                request.operator,
                request.captureTimestamp, 
                executeSlashHints.slashableStakeHints
            );
        
        slashedAmount = Math.min(request.amount, slashableStake_);
        
        if (slashedAmount == 0) {
            revert InsufficientSlash();
        }

        // Prevent double execution
        if (request.completed) {
            revert SlashRequestCompleted();
        }

        request.completed = true;

        // Same execution as Slasher
        _updateLatestSlashedCaptureTimestamp(
            request.subnetwork, 
            request.operator, 
            request.captureTimestamp
        );
        _updateCumulativeSlash(request.subnetwork, request.operator, slashedAmount);

        _delegatorOnSlash(
            request.subnetwork,
            request.operator,
            slashedAmount,
            request.captureTimestamp,
            abi.encode(IVetoSlasher.DelegatorData({
                slashableStake: slashableStake_, 
                stakeAt: stakeAt,
                slashIndex: slashIndex
            }))
        );

        _vaultOnSlash(slashedAmount, request.captureTimestamp);
        _burnerOnSlash(request.subnetwork, request.operator, slashedAmount, 
            request.captureTimestamp);

        emit ExecuteSlash(slashIndex, slashedAmount);
    }

    /**
     * RESOLVER MANAGEMENT: Set address that can veto slashes for a subnetwork
     * 
     * Key feature: New resolver only becomes active after `resolverSetEpochsDelay` epochs
     * This gives stakers time to exit if they don't trust the new resolver
     */
    function setResolver(uint96 identifier, address resolver_, bytes calldata hints)
        external nonReentrant
    {
        SetResolverHints memory setResolverHints;
        if (hints.length > 0) {
            setResolverHints = abi.decode(hints, (SetResolverHints));
        }

        // Only networks can set resolvers
        if (!IRegistry(NETWORK_REGISTRY).isEntity(msg.sender)) {
            revert NotNetwork();
        }

        address vault_ = vault;
        bytes32 subnetwork = (msg.sender).subnetwork(identifier);

        (bool exists, uint48 latestTimestamp,) = _resolver[subnetwork].latestCheckpoint();
        
        if (exists) {
            if (latestTimestamp > Time.timestamp()) {
                // Future-dated checkpoint - replace it
                _resolver[subnetwork].pop();
            } else if (resolver_ == address(uint160(_resolver[subnetwork].latest()))) {
                // No change
                revert AlreadySet();
            }

            // New resolver takes effect after resolverSetEpochsDelay epochs
            if (resolver_ != address(uint160(_resolver[subnetwork].latest()))) {
                _resolver[subnetwork].push(
                    (IVault(vault_).currentEpochStart() + 
                     resolverSetEpochsDelay * IVault(vault_).epochDuration())
                    .toUint48(),
                    uint160(resolver_)
                );
            }
        } else {
            if (resolver_ == address(0)) {
                revert AlreadySet();
            }

            // First resolver takes effect immediately
            _resolver[subnetwork].push(Time.timestamp(), uint160(resolver_));
        }

        emit SetResolver(subnetwork, resolver_);
    }
}
```

---

## 4. VAULT SLASHING - How Vault Handles Slashes

### File: `Vault.sol` - onSlash() function

```solidity
/**
 * VAULT SLASHING: Called by Slasher after slash is approved
 * 
 * Key insight: Slashing affects BOTH active stake and future withdrawals
 * The split is proportional to their slashable amounts
 * 
 * @param amount The amount to slash
 * @param captureTimestamp The timestamp this slash references
 * @return slashedAmount The actual amount slashed (may be less than requested)
 */
function onSlash(uint256 amount, uint48 captureTimestamp)
    external nonReentrant returns (uint256 slashedAmount) 
{
    if (msg.sender != slasher) {
        revert NotSlasher();
    }

    uint256 currentEpoch_ = currentEpoch();
    uint256 captureEpoch = epochAt(captureTimestamp);

    // Capture must be recent (not older than one epoch)
    if ((currentEpoch_ > 0 && captureEpoch < currentEpoch_ - 1) ||
        captureEpoch > currentEpoch_) {
        revert InvalidCaptureEpoch();
    }

    uint256 activeStake_ = activeStake();
    uint256 nextWithdrawals = withdrawals[currentEpoch_ + 1];

    if (captureEpoch == currentEpoch_) {
        /**
         * CASE 1: Slash on current epoch
         * 
         * Slashable = activeStake + withdrawals from NEXT epoch only
         * (Previous epoch's withdrawals are already safe - outside the guarantee)
         */
        uint256 slashableStake = activeStake_ + nextWithdrawals;
        slashedAmount = Math.min(amount, slashableStake);
        
        if (slashedAmount > 0) {
            // Proportional distribution between active and next epoch withdrawals
            uint256 activeSlashed = slashedAmount.mulDiv(activeStake_, slashableStake);
            uint256 nextWithdrawalsSlashed = slashedAmount - activeSlashed;

            _activeStake.push(Time.timestamp(), activeStake_ - activeSlashed);
            withdrawals[currentEpoch_ + 1] = nextWithdrawals - nextWithdrawalsSlashed;
        }
    } else {
        /**
         * CASE 2: Slash on previous epoch (within 1 epoch window)
         * 
         * Slashable = activeStake + current epoch withdrawals + next epoch withdrawals
         * More complex distribution since we're slashing past guarantees
         */
        uint256 withdrawals_ = withdrawals[currentEpoch_];
        uint256 slashableStake = activeStake_ + withdrawals_ + nextWithdrawals;
        slashedAmount = Math.min(amount, slashableStake);
        
        if (slashedAmount > 0) {
            // Proportional split across three pools
            uint256 activeSlashed = slashedAmount.mulDiv(activeStake_, slashableStake);
            uint256 nextWithdrawalsSlashed = slashedAmount.mulDiv(nextWithdrawals, slashableStake);
            uint256 withdrawalsSlashed = slashedAmount - activeSlashed - nextWithdrawalsSlashed;

            // Adjustment: if current epoch withdrawals insufficient, take from next
            if (withdrawals_ < withdrawalsSlashed) {
                nextWithdrawalsSlashed += withdrawalsSlashed - withdrawals_;
                withdrawalsSlashed = withdrawals_;
            }

            _activeStake.push(Time.timestamp(), activeStake_ - activeSlashed);
            withdrawals[currentEpoch_ + 1] = nextWithdrawals - nextWithdrawalsSlashed;
            withdrawals[currentEpoch_] = withdrawals_ - withdrawalsSlashed;
        }
    }

    // Transfer penalized collateral to burner
    if (slashedAmount > 0) {
        IERC20(collateral).safeTransfer(burner, slashedAmount);
    }

    emit OnSlash(amount, captureTimestamp, slashedAmount);
}
```

---

## 5. SHARE PRICE & LOSS ATTRIBUTION

### How Loss is Distributed

**Key Principle: Loss is GLOBAL, spread across ALL depositors equally (by share basis)**

```
BEFORE SLASH:
- Total activeStake = 1000 tokens
- Total activeShares = 100 shares
- Share price = 1000 / 100 = 10 tokens/share

AFTER SLASH (500 tokens slashed):
- Total activeStake = 500 tokens
- Total activeShares = 100 shares (unchanged)
- New share price = 500 / 100 = 5 tokens/share

RESULT: All depositors' shares lost 50% of value
- User A with 10 shares: had 100 tokens → now has 50 tokens
- User B with 20 shares: had 200 tokens → now has 100 tokens
```

### Implementation in Vault.sol

```solidity
/**
 * Share-based loss: When vault activeStake decreases, all share holders
 * experience proportional loss based on ERC4626 accounting
 */
function activeBalanceOfAt(address account, uint48 timestamp, bytes calldata hints) 
    public view returns (uint256) 
{
    // balance = (userShares / totalShares) * totalStake
    return ERC4626Math.previewRedeem(
        activeSharesOfAt(account, timestamp, hints),
        activeStakeAt(timestamp, hints),      // Total slashable stake
        activeSharesAt(timestamp, hints)      // Total shares
    );
}

/**
 * Loss is atomic and simultaneous for all accounts
 * No per-delegator accounting - only per-vault accounting
 * This means loss is global across the entire vault
 */
```

---

## 6. MULTI-NETWORK COORDINATION

### Location: `symbioticfi/core/src/contracts/delegator/NetworkRestakeDelegator.sol`

```solidity
/**
 * NETWORK RESTAKE DELEGATOR: Allocates stake across multiple networks
 * 
 * Key feature: Single vault stake is divided across networks
 * by curator-set shares and network limits
 */
contract NetworkRestakeDelegator is BaseDelegator, INetworkRestakeDelegator {
    using Checkpoints for Checkpoints.Trace256;
    
    // Per-network configuration
    mapping(bytes32 subnetwork => Checkpoints.Trace256 value) internal _networkLimit;
    mapping(bytes32 subnetwork => Checkpoints.Trace256 shares) 
        internal _totalOperatorNetworkShares;
    mapping(bytes32 subnetwork => mapping(address operator => Checkpoints.Trace256 shares)) 
        internal _operatorNetworkShares;

    /**
     * STAKE ALLOCATION FORMULA:
     * 
     * operatorStakeInNetwork = 
     *   (operatorShares / totalOperatorShares) 
     *   * min(vaultActiveStake, networkLimit)
     * 
     * Example:
     * - Vault stake: 1000 tokens
     * - Network A limit: 600 tokens
     * - Network B limit: 500 tokens
     * - Operator X shares: 50% (among operators in Network A)
     * 
     * Operator X's stake in Network A:
     *   = 0.5 * min(1000, 600) = 0.5 * 600 = 300 tokens
     * 
     * Operator X's stake in Network B:
     *   = (0 if not in B) or pro-rata if allocated to B
     */
    function _stakeAt(
        bytes32 subnetwork,
        address operator,
        uint48 timestamp,
        bytes memory hints
    )
        internal
        view
        override
        returns (uint256, bytes memory)
    {
        StakeHints memory stakesHints;
        if (hints.length > 0) {
            stakesHints = abi.decode(hints, (StakeHints));
        }

        uint256 totalOperatorNetworkSharesAt_ =
            totalOperatorNetworkSharesAt(subnetwork, timestamp,
                stakesHints.totalOperatorNetworkSharesHint);
        
        if (totalOperatorNetworkSharesAt_ == 0) {
            return (0, stakesHints.baseHints);
        }

        // Calculate operator's share of the network's allocation
        return (
            operatorNetworkSharesAt(subnetwork, operator, timestamp,
                    stakesHints.operatorNetworkSharesHint)
                .mulDiv(
                    Math.min(
                        IVault(vault).activeStakeAt(timestamp, stakesHints.activeStakeHint),
                        networkLimitAt(subnetwork, timestamp, stakesHints.networkLimitHint)
                    ),
                    totalOperatorNetworkSharesAt_
                ),
            stakesHints.baseHints
        );
    }
}
```

### Multi-Network Slashing Coordination

```solidity
/**
 * CROSS-NETWORK SLASHING ORDERING
 * 
 * When a single operator is slashed by multiple networks:
 * 1. Slashes share the same collateral (same vault = same backing)
 * 2. Cumulative slashes are tracked per operator-network pair
 * 3. Each network's slashing request is BOUNDED by:
 *    - Remaining guarantee: slashableStake = stakeAt(captureTime) 
 *                                - (cumulativeSlash(now) - cumulativeSlash(captureTime))
 * 
 * SCENARIO:
 * - Vault has 1000 tokens backing 3 networks
 * - Operator has:
 *   - Network A stake: 400 tokens (guaranteed)
 *   - Network B stake: 300 tokens (guaranteed)
 *   - Network C stake: 300 tokens (guaranteed)
 * 
 * SLASHING SEQUENCE:
 * 1. Network A slashes 200 tokens
 *    → Vault reduces active stake: 1000 → 800
 *    → But operator's Network A guarantee remains 400 (bounded by capture)
 * 
 * 2. Network B slashes 150 tokens
 *    → Vault reduces: 800 → 650
 *    → Operator still has 300 guaranteed in B (captured earlier)
 *    → But actual slashed in B may be less if vault depleted
 * 
 * 3. Network C's ability to slash is now REDUCED
 *    → Only 350 tokens left in vault (650 - 300 for B guarantee)
 *    → Even though Network C has 300 guarantee, actual slash depends on vault balance
 * 
 * KEY INSIGHT: Slashing is per-capture-timestamp bounded, but the actual amount
 * executed depends on cumulative slashes from ALL networks
 */
```

### Delegator's onSlash() Callback

```solidity
/**
 * File: BaseDelegator.sol
 * 
 * When a slash occurs, delegator's onSlash is called
 * This allows custom hooks to update per-network stake tracking
 */
function onSlash(
    bytes32 subnetwork, 
    address operator, 
    uint256 amount, 
    uint48 captureTimestamp, 
    bytes memory data
)
    external
    nonReentrant
{
    if (msg.sender != IVault(vault).slasher()) {
        revert NotSlasher();
    }

    address hook_ = hook;
    if (hook_ != address(0)) {
        // Call optional hook for custom handling
        bytes memory calldata_ =
            abi.encodeCall(
                IDelegatorHook.onSlash, 
                (subnetwork, operator, amount, captureTimestamp, data)
            );

        if (gasleft() < HOOK_RESERVE + HOOK_GAS_LIMIT * 64 / 63) {
            revert InsufficientHookGas();
        }

        assembly ("memory-safe") {
            pop(call(HOOK_GAS_LIMIT, hook_, 0, add(calldata_, 0x20), 
                mload(calldata_), 0, 0))
        }
    }

    emit OnSlash(subnetwork, operator, amount, captureTimestamp);
}
```

---

## 7. RELAY CONTRACTS - Network Middleware & Settlement

### Location: `symbioticfi/relay-contracts/src/modules/`

**Key Modules:**

```
1. VotingPowerProvider
   - Tracks operator voting power based on vault stakes
   - Extensions: OperatorsWhitelist, OperatorVaults, SharedVaults
   - Integrates with Symbiotic Core for stake data

2. KeyRegistry
   - Manages operator signing keys (BLS, ECDSA)
   - Associates operators with their verification credentials

3. Settlement
   - Verifies quorum signatures over finalized validator sets
   - Maintains validator set headers per epoch
   - Supports BLS and ZK verification

4. ValSetDriver
   - Derives validator sets from voting power
   - Maintains on-chain validator set state
   - Used for off-chain signature aggregation
```

### Network Middleware Integration Pattern

```solidity
/**
 * Network middleware calls slashing through this pattern:
 * 
 * 1. Observe misbehavior (e.g., double-signing, non-participation)
 * 2. Verify it against the operator set at a specific epoch
 * 3. Call slasher with reference to capture timestamp
 * 
 * Example from SumTask.sol (test network):
 */

// Verify that result was signed by required quorum
if (!settlement.verifyQuorumSigAt(
    abi.encode(keccak256(abi.encode(taskId, result))),  // Message
    settlement.getRequiredKeyTagFromValSetHeaderAt(epoch),  // Key types
    settlement.getQuorumThresholdFromValSetHeaderAt(epoch), // Threshold
    proof,
    epoch,
    new bytes(0)
)) {
    revert InvalidQuorumSignature();
}

// If verification fails, network can slash the operator set
// by calling slasher.requestSlash() or slasher.slash()
```

---

## SUMMARY TABLE: Loss Attribution & Multi-Network Handling

| Aspect | Implementation |
|--------|-----------------|
| **Loss Attribution** | Global across vault (share-based) |
| **Per-Depositor Loss** | (userShares / totalShares) × slashedAmount |
| **Per-Delegator Loss** | Not tracked per-delegator; only per-vault |
| **Cross-Network Slashing** | Ordered sequentially; bounded by capture guarantees |
| **Slashing Bounds** | slashableStake(capture) - priorSlashes ≤ stakeAt(capture) |
| **Veto Mechanism** | Resolver can veto before execution deadline |
| **Multi-Network Order** | First-come-first-served; each slash reduces vault balance |
| **Network Coordination** | Delegator divides vault stake by limits & shares |
| **Guarantee Period** | One vault epoch (unchangeable once captured) |

---

## Key References

**Symbiotic Core Repository:**
- https://github.com/symbioticfi/core

**Relay Contracts:**
- https://github.com/symbioticfi/relay-contracts

**Documentation:**
- https://docs.symbiotic.fi/learn

**Example Network (Super Sum):**
- https://github.com/symbioticfi/symbiotic-super-sum
