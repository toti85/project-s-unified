UNIFIED DIFF PATCH:
==================

See: memory/output/target_dims_poc.patch

Changes:
1) avail/e2e/Cargo.toml: Add serde_json, sha2, hex dependencies
2) avail/e2e/src/tests/test_target_dims_poc.rs: NEW FILE (219 lines)


TEST EXECUTION COMMAND:
=======================

From avail-da/avail/ directory:

cargo test -p e2e test_target_dims_mismatch -- --nocapture

Alternative (with full output):

cargo test -p e2e test_target_dims_mismatch -- --nocapture --test-threads=1


EXPECTED OUTPUT BEHAVIOR:
========================

On success:
- Test runs without panic
- stderr shows:
  * "Proof1 (hardcoded 16,64): NN bytes"
  * "Proof2 (real dims Rx C): NN bytes"
  * "MISMATCH: Proofs differ..." OR "NO_DIFF: Proofs are identical..."
- File created: memory/output/target_dims_poc_proof.json
- JSON contains result field: "MISMATCH_OBSERVED" | "NO_OBSERVABLE_EFFECT" | "ERROR"

On failure (test panic):
- JSON artifact written before panic
- error field populated with failure reason
- result field set to "ERROR"


JSON ARTIFACT STRUCTURE:
=======================

{
  "timestamp": 1735315200,
  "real_dims": {
    "rows": 4,
    "cols": 8
  },
  "hardcoded_dims": {
    "rows": 16,
    "cols": 64
  },
  "proof1": {
    "len": 48,
    "hash": "abc123..."
  },
  "proof2": {
    "len": 48,
    "hash": "def456..."
  },
  "verify1": "generated" | "failed",
  "verify2": "generated" | "failed",
  "result": "MISMATCH_OBSERVED" | "NO_OBSERVABLE_EFFECT" | "ERROR",
  "error": "none" | "[error details]"
}


PROOF-GRADE CHARACTERISTICS:
============================

✓ Deterministic: Same seed, same grid size, same cell, reproducible output
✓ Minimal changes: Only 3 deps + 1 new test file added, zero existing tests modified
✓ Evidence artifact: JSON with dimensions, proof hashes, verification results
✓ Clear failure mode: If grid creation fails, JSON written with ERROR status before panic
✓ Dimension comparison: Hardcoded (16,64) vs computed real dims from 8x8 grid input
✓ Observable comparison: Proof byte length, hash, verification state
✓ No claims: Output only "MISMATCH_OBSERVED" or "NO_OBSERVABLE_EFFECT", no severity assigned
