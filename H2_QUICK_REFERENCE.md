# H2 STATE TRANSITION - QUICK REFERENCE

## At a Glance

| Metric | Value |
|--------|-------|
| Tests | 5 |
| Status | ✅ 5/5 PASS |
| Gas Total | 117,459 |
| Time | 5.61ms |
| Repo | https://github.com/0xPolygonHermez/zkevm-contracts.git |
| Commit | e468f9b0967334403069aa650d9f1164b1731ebb |
| Workspace | /root/bounties/zkevm-contracts |

## Tests Matrix

| # | Test Name | Status | Gas | What It Tests |
|---|-----------|--------|-----|---------------|
| 1 | test_H2_SingleClaimMarkedInBitmap | ✅ | 22,798 | Claim state persisted |
| 2 | test_H2_DoubleClaim_Reverts | ✅ | 25,577 | Double-claim prevented |
| 3 | test_H2_IndependentLeavesIsolated | ✅ | 23,310 | Bitmap isolation |
| 4 | test_H2_LeafValueDeterminism | ✅ | 1,957 | Hash determinism |
| 5 | test_H2_ClaimSequenceFlexibility | ✅ | 23,417 | Out-of-order claims work |

## Run Command

```bash
cd ~/bounties/zkevm-contracts && forge test --match-contract 'H2_StateTransition' -vv
```

## Key Invariants

- ✅ claimedBitMap prevents double-claiming
- ✅ Claim marking is atomic (bitmap XOR)
- ✅ Leaf hashes are deterministic
- ✅ Bitmap bits don't collide
- ✅ Claims work in any order

## Contract References

```
claimedBitMap: PolygonZkEVMBridgeV2.sol:80
_setAndCheckClaimed(): PolygonZkEVMBridgeV2.sol:1019
isClaimed(): PolygonZkEVMBridgeV2.sol:995
getLeafValue(): PolygonZkEVMBridgeV2.sol:904
```

## Hypothesis Validated

**H2: State Transition / Double-Claim / Replay / Finalization Gating**

State transitions in bridge are:
- Atomic (can't be interrupted)
- Deterministic (reproducible)
- Protected against replays (bitmap nullifier)
- Protected against double-claims (AlreadyClaimed revert)

## Files

- Implementation: test/H2_StateTransition.t.sol
- Execution Log: H2_TEST_EXECUTION_RAW.txt
- Full Summary: H2_EXECUTABLE_TESTS_SUMMARY.md

