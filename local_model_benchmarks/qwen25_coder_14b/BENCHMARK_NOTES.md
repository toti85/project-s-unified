# BENCHMARK_NOTES.md — Qwen2.5-Coder-14B Local Cline Benchmark

**Date:** 2026-05-22  
**Model:** Qwen2.5-Coder-14B-Instruct-Q4_K_M (GGUF, Q4_K_M)  
**Endpoint:** http://46.253.140.72:8098 (llama.cpp Vulkan, Tesla M60)  
**Context window:** 4096 tokens  
**Inference speed (baseline):** ~11–12.5 tok/s  

---

## Task 1 — Explain the Code

**Prompt:** "Read sample_buggy_code.py and explain what it does."  
**Start time:** _to be filled_  
**End time:** _to be filled_  
**Tokens out:** _  
**Speed (tok/s):** _  

### Response Summary
_(paste model response here)_

### Evaluation
- [ ] Correctly identified `read_config` purpose  
- [ ] Correctly identified `count_words` purpose  
- [ ] Correctly identified `calculate_average` purpose  
- [ ] No hallucinated functions or methods  
- **Verdict:** PASS / FAIL  

---

## Task 2 — Identify Bugs (Read-Only)

**Prompt:** "Identify all bugs and risks in sample_buggy_code.py. Do NOT suggest file edits yet."  
**Start time:** _  
**End time:** _  
**Tokens out:** _  

### Response Summary
_(paste model response here)_

### Evaluation
- [ ] BUG 1 found: unclosed file handle / resource leak in `read_config`  
- [ ] BUG 2 found: `split(" ")` logic bug in `count_words` (double-space creates empty token)  
- [ ] BUG 3 found: ZeroDivisionError on empty list in `calculate_average`  
- [ ] Did NOT attempt to edit files  
- [ ] No false positives (hallucinated bugs)  
- **Bugs found:** _ / 3  
- **Verdict:** PASS / FAIL  

---

## Task 3 — Fix and Test

**Prompt:** "Fix all identified bugs in sample_buggy_code.py. Provide the complete corrected file."  
**Start time:** _  
**End time:** _  
**Tokens out:** _  

### Model Output (fixed code)
_(saved as sample_fixed_code.py)_

### Test Run (before fix)
```
FAILED test_count_words_double_space  (returns 3, expected 2)
FAILED test_count_words_triple_space  (returns 7, expected 3)
FAILED test_calculate_average_empty   (ZeroDivisionError not ValueError)
PASSED test_count_words_normal
PASSED test_count_words_single
PASSED test_count_words_empty
PASSED test_count_words_none
PASSED test_calculate_average_normal
PASSED test_calculate_average_single
```

### Test Run (after applying model fix)
_(pytest output here)_

### Evaluation
- [ ] All 3 bugs fixed correctly  
- [ ] No regressions on previously-passing tests  
- [ ] Modified ONLY sandbox files  
- [ ] Correction cycles needed: _  
- **Verdict:** PASS / FAIL  

---

## Sandbox Isolation Check

- [ ] No files outside `local_model_benchmarks\qwen25_coder_14b\` were touched  
- [ ] No destructive shell commands issued  
- [ ] No hallucinated external dependencies  

---

## Summary

| Metric | Value |
|--------|-------|
| Task 1 (Explain) | PASS / FAIL |
| Task 2 (Bug ID) | _ / 3 bugs found |
| Task 3 (Fix+Test) | PASS / FAIL |
| Correction cycles | _ |
| Total elapsed | _ min |
| Hallucinations | _ |
| Unsafe file access | Yes / No |
| **Final verdict** | **usable / supervised / not usable** |
