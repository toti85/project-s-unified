# Polygon zkEVM Bridge Smart Contracts - Comprehensive Report

**Date:** January 25, 2026  
**Repository:** [agglayer/agglayer-contracts](https://github.com/agglayer/agglayer-contracts) (evolved from 0xPolygonHermez/zkevm-contracts)  
**Note:** The original 0xPolygonHermez/zkevm-contracts repository has evolved into the agglayer-contracts project under [agglayer](https://github.com/agglayer).

---

## Executive Summary

The Polygon zkEVM Bridge is a sophisticated cross-chain messaging protocol enabling secure asset and message transfers between Ethereum mainnet and the Polygon zkEVM Layer 2 solution. The architecture includes core bridge contracts, exit root mechanisms, message passing infrastructure, and verifier components.

---

## 1. Core Bridge Contracts

### 1.1 Main Bridge Contracts

| Contract | Location | Purpose | Status |
|----------|----------|---------|--------|
| **PolygonZkEVMBridge.sol** | `/contracts/` | V1 bridge implementation for asset and message transfers between L1 and L2 | Legacy (superseded by V2) |
| **PolygonZkEVMBridgeV2.sol** | `/contracts/v2/` | Enhanced bridge with improved architecture and security features | **Current - Active** |
| **PolygonZkEVM.sol** | `/contracts/` | Core rollup contract managing state transitions and proof verification | Active |
| **PolygonZkEVMTimelock.sol** | `/contracts/` | Timelock mechanism for governance and contract upgrades | Active |

### 1.2 Bridge Functionality

**PolygonZkEVMBridgeV2.sol** provides:
- Cross-chain asset transfers (ETH and ERC20 tokens)
- Arbitrary message passing between L1 and L2
- Native bridge functionality for wrapped tokens
- Token-wrapped bridge support for custom token bridges
- Pause/unpause mechanisms for emergency scenarios

---

## 2. Exit Root Contracts

Exit roots form the critical infrastructure for verifying exits from the rollup to mainnet.

### 2.1 Exit Root Contracts

| Contract | Location | Purpose | Status |
|----------|----------|---------|--------|
| **PolygonZkEVMGlobalExitRoot.sol** | `/contracts/` | V1 exit root aggregation on Ethereum mainnet | Legacy |
| **PolygonZkEVMGlobalExitRootV2.sol** | `/contracts/v2/` | V2 enhanced exit root with improved verification mechanisms | **Current - Active** |
| **PolygonZkEVMGlobalExitRootL2.sol** | `/contracts/` | L2-side exit root contract for zkEVM chain | Active |
| **IBasePolygonZkEVMGlobalExitRoot.sol** | `/contracts/interfaces/` | Base interface defining exit root functionality | Reference |

### 2.2 Exit Root Functionality

- Aggregates state roots from rollup proofs
- Manages Merkle tree of exit leaves
- Verifies withdrawal proofs
- Coordinates L1-L2 state synchronization
- Maintains exit root history for proof verification

---

## 3. Interface Contracts & Abstractions

### 3.1 Critical Interfaces

| Interface | File | Purpose |
|-----------|------|---------|
| **IPolygonZkEVMBridge.sol** | `/contracts/interfaces/` | Defines bridge contract ABI and standards |
| **IBridgeMessageReceiver.sol** | `/contracts/interfaces/` | Enables contracts to receive cross-chain messages |
| **IPolygonZkEVMGlobalExitRoot.sol** | `/contracts/interfaces/` | Defines exit root operations and state queries |
| **IBasePolygonZkEVMGlobalExitRoot.sol** | `/contracts/interfaces/` | Base interface for exit root functionality |
| **IPolygonZkEVMErrors.sol** | `/contracts/interfaces/` | Consolidated error definitions for gas optimization |
| **IVerifierRollup.sol** | `/contracts/interfaces/` | Proof verifier interface for rollup proofs |

### 3.2 Message Passing Implementation

**IBridgeMessageReceiver Interface:**
```solidity
- Interface for contracts receiving bridge messages
- Implements onMessageReceived() callback function
- Enables programmable cross-chain interactions
- Standard for L2 dApps to receive L1 messages
```

---

## 4. Ancillary Contracts

### 4.1 Verifier Contracts

| Contract | Location | Purpose |
|----------|----------|---------|
| **FflonkVerifier** | `/contracts/verifiers/` | zk-SNARK verifier for Fflonk proof system |
| **Proof Verifier Contracts** | Generated from PIL/Rom | Auto-generated contracts from rollup constraints |

### 4.2 Supporting Infrastructure

| Component | Location | Purpose |
|-----------|----------|---------|
| **PolygonRollupManager.sol** | `/contracts/v2/` | Manages multiple rollup deployments |
| **AggLayerGateway.sol** | `/contracts/v2/` | AggLayer interoperability gateway |
| **Lib directory** | `/contracts/lib/` | Utility libraries and helpers |
| **Mocks directory** | `/contracts/mocks/` | Testing utilities and mock contracts |

---

## 5. Deployment Information

### 5.1 Ethereum Mainnet Deployments

| Contract | Address | Chain |
|----------|---------|-------|
| **PolygonRollupManager** | `0x5132A183E9F3CB7C848b0AAC5Ae0c4f0491B7aB2` | Ethereum Mainnet |
| **PolygonZkEVMBridgeV2** | `0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe` | Ethereum Mainnet |
| **PolygonZkEVMGlobalExitRootV2** | `0x580bda1e7A0CFAe92Fa7F6c20A3794F169CE3CFb` | Ethereum Mainnet |
| **FflonkVerifier** | `0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9` | Ethereum Mainnet |
| **PolygonZkEVMDeployer** | `0xCB19eDdE626906eB1EE52357a27F62dd519608C2` | Ethereum Mainnet |
| **PolygonZkEVMTimelock** | `0xEf1462451C30Ea7aD8555386226059Fe837CA4EF` | Ethereum Mainnet |

### 5.2 Polygon zkEVM Chain Deployments

| Contract | Address | Chain |
|----------|---------|-------|
| **PolygonZkEVMBridgeV2** | `0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe` | Polygon zkEVM |
| **PolygonZkEVMTimelock** | `0xBBa0935Fa93Eb23de7990b47F0D96a8f75766d13` | Polygon zkEVM |

### 5.3 Deployment Structure

```
/deployment/
├── helpers/           # Deployment helper utilities
├── testnet/           # Testnet-specific deployments
└── v2/                # V2 contract deployments
```

---

## 6. Audit & Security

### 6.1 Security Audits

The codebase has undergone multiple professional security audits:

| Auditor | Report | Scope | Status |
|---------|--------|-------|--------|
| **Hexens** | `Hexens_Polygon_zkEVM_PUBLIC_27.02.23.pdf` | Bridge and core contracts | Completed |
| **Sigma Prime** | `Sigma Prime - Polygon - LXLY Banana - Security Assessment Report - 2.0.pdf` | Bridge infrastructure | Completed |
| **Sigma Prime** | `Sigma_Prime_Polygon_LXLY_Bridge_Security_Assessment_Report.pdf` | Bridge-specific assessment | Completed |
| **Sigma Prime** | `Sigma_Prime_Polygon_LXLY_Sovereign_Chains_Security_Assessment_Report_v2_0.pdf` | Sovereign chains implementation | Completed |
| **Sigma Prime** | `Sigma_Prime_Polygon_AggLayer_v0.3.0_Smart_Contract_Updates_Security_Assessment_Report_v2_1.pdf` | AggLayer v0.3.0 updates | Completed |
| **Sigma Prime** | `Sigma_Prime_Polygon_PR_478_Changes_Security_Assessment_Report_v2_0.pdf` | PR #478 migration changes | Completed |
| **Sigma Prime** | `Sigma_Prime_Polygon_Polygon_LXLY_UpgradeableWrappedTokens_Security_Assessment_Report_v2_0.pdf` | Wrapped token upgrades | Completed |
| **Spearbit** | `zkEVM-bridge-Spearbit-27-March.pdf` | Bridge security assessment | Completed |

**Audit Location:** `/audits/`

### 6.2 Audit Coverage Details

**Sigma Prime Audits** (Most Comprehensive):
- Architecture review and threat modeling
- Code quality and best practices analysis
- Smart contract vulnerability assessment
- Gas optimization review
- Compliance with industry standards

**Historical Audits:**
- Hexens (2023): Early protocol security review
- Spearbit (2023): Bridge-specific security assessment

---

## 7. Contract Architecture & Design Patterns

### 7.1 Key Design Features

1. **Proxy Pattern**
   - Upgradeable architecture using UUPS proxies
   - Governance-controlled upgrades
   - Timelock for upgrade safety

2. **Message Passing**
   - Generic message passing between chains
   - Callback mechanism via IBridgeMessageReceiver
   - Message ordering guarantees

3. **Exit Root Mechanism**
   - Merkle tree-based proof verification
   - Aggregated state roots from proofs
   - Atomic exit verification

4. **Token Management**
   - Native ETH and ERC20 support
   - Wrapped token bridge for exotic assets
   - Token-wrapped bridge for custom implementations

5. **Governance**
   - PolygonZkEVMTimelock for upgrade delays
   - Multi-signature admin controls
   - Emergency pause mechanisms

### 7.2 Security Features

- **Reentrancy Protection:** Checks-effects-interactions pattern
- **Rate Limiting:** Message batching and processing limits
- **Access Control:** Role-based permissions
- **Formal Verification:** Some components with mathematical proofs
- **Circuit-level Verification:** Zero-knowledge proofs for state transitions

---

## 8. Contract Dependency Map

```
PolygonZkEVMBridgeV2.sol
├── IPolygonZkEVMBridge.sol (interface)
├── PolygonZkEVMGlobalExitRootV2.sol (dependency)
├── IBridgeMessageReceiver.sol (callback interface)
└── IPolygonZkEVMErrors.sol (error definitions)

PolygonZkEVMGlobalExitRootV2.sol
├── IPolygonZkEVMGlobalExitRoot.sol
├── IBasePolygonZkEVMGlobalExitRoot.sol
└── IPolygonZkEVMErrors.sol

PolygonRollupManager.sol
├── IVerifierRollup.sol
├── PolygonZkEVMGlobalExitRootV2.sol
└── Verifier contracts

PolygonZkEVM.sol (L2 Rollup)
├── PolygonZkEVMGlobalExitRootL2.sol
└── Exit proof mechanisms
```

---

## 9. Repository Structure

```
agglayer-contracts/
├── contracts/
│   ├── PolygonZkEVM.sol              (Core rollup)
│   ├── PolygonZkEVMBridge.sol        (V1 - Legacy)
│   ├── PolygonZkEVMGlobalExitRoot.sol (V1 - Legacy)
│   ├── PolygonZkEVMGlobalExitRootL2.sol
│   ├── PolygonZkEVMTimelock.sol
│   ├── interfaces/
│   │   ├── IPolygonZkEVMBridge.sol
│   │   ├── IBridgeMessageReceiver.sol
│   │   ├── IPolygonZkEVMGlobalExitRoot.sol
│   │   ├── IBasePolygonZkEVMGlobalExitRoot.sol
│   │   ├── IPolygonZkEVMErrors.sol
│   │   └── IVerifierRollup.sol
│   ├── v2/
│   │   ├── PolygonZkEVMBridgeV2.sol  (Current)
│   │   ├── PolygonZkEVMGlobalExitRootV2.sol (Current)
│   │   ├── PolygonRollupManager.sol
│   │   ├── AggLayerGateway.sol
│   │   ├── interfaces/
│   │   ├── sovereignChains/
│   │   ├── aggchains/
│   │   └── consensus/
│   ├── verifiers/
│   │   ├── FflonkVerifier.sol
│   │   └── [Auto-generated verifier contracts]
│   ├── lib/
│   ├── mocks/
│   └── deployment/
├── audits/
│   ├── Hexens_Polygon_zkEVM_PUBLIC_27.02.23.pdf
│   ├── Sigma_Prime_*.pdf (multiple versions)
│   └── zkEVM-bridge-Spearbit-27-March.pdf
├── deployment/
│   ├── helpers/
│   ├── testnet/
│   └── v2/
├── docs/
├── test/
├── package.json
├── hardhat.config.ts
└── README.md
```

---

## 10. Key Metrics & Specifications

### 10.1 Technology Stack

| Component | Version/Type |
|-----------|--------------|
| Solidity | 0.8.20+ |
| Framework | Hardhat / Foundry |
| Proof System | Fflonk (Fast Fourier Transform-based) |
| Verification | SNARK-based zero-knowledge proofs |

### 10.2 Contract Specifications

| Specification | Details |
|---------------|---------|
| **Bridge Functionality** | Cross-chain message & asset transfer |
| **Message Format** | Arbitrary data with 32-byte nonce |
| **Proof System** | Fflonk zero-knowledge proofs |
| **State Root** | Merkle tree based |
| **Exit Verification** | Merkle proof based |
| **Fee Mechanism** | Dynamic gas-based pricing |

---

## 11. Audit Scope & Out-of-Scope Items

### 11.1 Typically Audited Components

✅ **In Scope:**
- Bridge contract logic and state management
- Exit root verification mechanisms
- Message passing infrastructure
- Access control and permission models
- Emergency pause mechanisms
- Token handling and transfer logic
- Proof verification logic
- Cross-chain synchronization

### 11.2 Typically Out-of-Scope

⚠️ **Often Out-of-Scope:**
- Zero-knowledge circuit security (handled separately)
- Proof generation system
- zkEVM machine implementations
- Consensus layer mechanisms
- Network-level security
- Off-chain infrastructure

---

## 12. Version History & Evolution

### 12.1 Major Versions

| Version | Status | Key Features | Notes |
|---------|--------|--------------|-------|
| **V1** | Deprecated | Initial bridge implementation | Legacy, superseded by V2 |
| **V2** | **Current** | Enhanced architecture, improved security | Active mainnet deployment |
| **V3** | In development | AggLayer integration, sovereign chains | Feature branch development |

### 12.2 Recent Enhancements

- AggLayer integration for multi-chain messaging
- Sovereign chains support
- Enhanced token wrapping mechanisms
- Improved proof verification efficiency

---

## 13. Testing & Verification

### 13.1 Test Infrastructure

```
tests/
├── unit tests (Hardhat)
├── integration tests
├── fuzz testing
└── security-focused test cases
```

### 13.2 Verification Tools

- **Hardhat:** Smart contract development and testing
- **Foundry:** High-speed contract testing and verification
- **Slither:** Static analysis
- **Mythril:** Bytecode analysis
- **Contract verification:** Etherscan verification support

---

## 14. Integration Points

### 14.1 Consuming Contracts Must Implement

```solidity
interface IBridgeMessageReceiver {
    function onMessageReceived(
        address originAddress,
        uint32 originNetwork,
        bytes calldata data
    ) external payable;
}
```

### 14.2 Common Integration Patterns

1. **Simple ETH Transfer**
   - Call bridge.bridgeAsset() with ETH amount

2. **ERC20 Transfer**
   - Approve token → Call bridge.bridgeAsset()

3. **Message Passing**
   - Implement IBridgeMessageReceiver
   - Call bridge.sendMessage()
   - Receive via onMessageReceived callback

---

## 15. Security Considerations & Best Practices

### 15.1 For Bridge Users

- Always verify destination address before bridging
- Use timelock-protected upgrades
- Monitor for bridge pause events
- Verify proof authenticity before exit
- Implement slippage protection for token swaps

### 15.2 For Integrators

- Implement IBridgeMessageReceiver correctly
- Handle reentrancy in message receivers
- Validate cross-chain message authenticity
- Implement timeout mechanisms
- Test on testnet before mainnet

### 15.3 Known Limitations

- Exit delays due to rollup proof finality (typically ~1 week)
- Message ordering guarantees within batches only
- No atomic cross-chain transactions
- Wrapped token bridge requires custom implementation per token

---

## 16. Resources & Documentation

### 16.1 Official Links

- **Repository:** https://github.com/agglayer/agglayer-contracts
- **Original:** https://github.com/0xPolygonHermez/zkevm-contracts
- **Deployment Verification:** `/verifyMainnetDeployment/verifyDeployment.md`
- **Proof Verifier Verification:** `/verifyMainnetDeployment/verifyMainnetProofVerifier.md`

### 16.2 Useful Commands

```bash
# Install dependencies
npm install

# Run tests
npm run test

# Deploy on Hardhat
npm run deploy:ZkEVM:hardhat

# Run contract verification
npm run verify

# Access Prisma Studio (if using Prisma ORM)
npm run prisma:studio
```

---

## Appendix A: Contract Quick Reference

### Core Contracts
- `PolygonZkEVMBridgeV2.sol` - Primary bridge implementation
- `PolygonZkEVMGlobalExitRootV2.sol` - Exit verification
- `PolygonRollupManager.sol` - Rollup management
- `PolygonZkEVMTimelock.sol` - Upgrade governance

### Key Interfaces
- `IPolygonZkEVMBridge.sol` - Bridge ABI
- `IBridgeMessageReceiver.sol` - Message receiver pattern
- `IPolygonZkEVMGlobalExitRoot.sol` - Exit root ABI

### Deployment Details
- **Mainnet Bridge:** `0x2a3DD3EB832aF982ec71669E178424b10Dca2EDe`
- **Exit Root:** `0x580bda1e7A0CFAe92Fa7F6c20A3794F169CE3CFb`
- **Verification:** Multiple Sigma Prime audits completed

---

## Document Metadata

- **Last Updated:** January 25, 2026
- **Information Source:** GitHub repositories and official documentation
- **Audit Information:** Current as of document date
- **Deployment Addresses:** Ethereum Mainnet verified addresses

---

*This report provides a comprehensive overview of the Polygon zkEVM Bridge architecture. For the latest updates, contract code, and deployment information, refer to the official agglayer-contracts GitHub repository.*
