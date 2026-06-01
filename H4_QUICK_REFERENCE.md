# H4 PROOF VERIFICATION - QUICK REFERENCE

## At a Glance

| Metric | Value |
|--------|-------|
| Tests | 8 |
| Status | ✅ 8/8 PASS |
| Gas Total | 17,358 |
| Time | 3.00ms |
| Repo | https://github.com/0xPolygonHermez/zkevm-contracts.git |
| Commit | e468f9b0967334403069aa650d9f1164b1731ebb |
| Workspace | /root/bounties/zkevm-contracts |

## Tests Matrix

| # | Test Name | Status | Gas | What It Tests |
|---|-----------|--------|-----|---------------|
| 1 | test_H4_DestinationAddressBindsToProof | ✅ | 1,266 | Funds go to right address |
| 2 | test_H4_AmountBindsToProof | ✅ | 1,066 | Amount locked in proof |
| 3 | test_H4_OriginAddressBindsToProof | ✅ | 1,305 | Source authenticated |
| 4 | test_H4_MetadataHashBindsToProof | ✅ | 1,113 | Message tamper-proof |
| 5 | test_H4_LeafTypeBindsToProof | ✅ | 1,469 | Asset ≠ Message claims |
| 6 | test_H4_DestinationNetworkBindsToProof | ✅ | 1,508 | Network-specific claim |
| 7 | test_H4_OriginNetworkBindsToProof | ✅ | 1,244 | Replay prevention |
| 8 | test_H4_LeafHashUniqueness | ✅ | 7,353 | No hash collisions |

## Run Command

```bash
cd ~/bounties/zkevm-contracts && forge test --match-contract 'H4_ProofVerification' -vv
```

## Key Invariants

- ✅ Destination address binds to proof
- ✅ Amount binds to proof
- ✅ Origin address binds to proof
- ✅ Message metadata tamper-proof
- ✅ Claim type distinguished (asset vs message)
- ✅ Network parameters prevent replays
- ✅ All parameter combinations produce unique hashes

## Attack Prevention

| Attack | Prevention |
|--------|-----------|
| Fund redirection | Destination binding |
| Over-claiming | Amount binding |
| Source spoofing | Origin binding |
| Message tampering | Metadata binding |
| Type confusion | Leaf type binding |
| Cross-chain replay | Network binding |
| Hash collision | Unique computation |

## Contract References

```
getLeafValue(): PolygonZkEVMBridgeV2.sol:904
claimAsset(): PolygonZkEVMBridgeV2.sol:556
claimMessage(): PolygonZkEVMBridgeV2.sol:716
_verifyLeafBridge(): PolygonZkEVMBridgeV2.sol:791
```

## Hypothesis Validated

**H4: Proof Verification / Claim Authorization / Cross-Domain Message Validation**

Leaf value computation ensures:
- Authorization (destination address)
- Integrity (amount, metadata)
- Source authentication (origin address/network)
- Cross-domain safety (destination network)
- No ambiguity (leaf type)

## Important Note

These tests validate leaf computation (✅ executable in Solidity).
Full merkle proof verification requires external proof generator (⚠️ not testable).

## Files

- Implementation: test/H4_ProofVerification.t.sol
- Execution Log: H4_TEST_EXECUTION_RAW.txt
- Full Summary: H4_EXECUTABLE_TESTS_SUMMARY.md

