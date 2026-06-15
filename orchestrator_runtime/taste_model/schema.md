# Taste Model — Mission Outcome Schema

Append-only log of mission execution outcomes used by Project-S to learn
from its own decisions. Every completed mission gets exactly one record.

---

## Record Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `mission_id` | string | ✓ | Mission identifier, e.g. `AO5_T42` |
| `date` | string | ✓ | Execution date, `YYYY-MM-DD` |
| `claimed_status` | enum | ✓ | What was declared at mission close |
| `actual_status` | enum | ✓ | Toti-validated ground truth |
| `model_used` | string | ✓ | Which model/executor ran the mission |
| `runtime_validated` | bool/string | ✓ | Whether runtime evidence was captured |
| `value_immediate` | int 1–5 | ✓ | Immediate value delivered (see scale) |
| `patterns` | list[str] | ✓ | Behavioural/outcome patterns (snake_case) |
| `notes` | string | ✓ | Free-form, max 200 chars |
| `logged_at` | ISO timestamp | ✓ | When record was written |

---

## `claimed_status` / `actual_status` Values

| Value | Meaning |
|---|---|
| `completed` | Mission fully done, all outputs delivered |
| `partial` / `partial_pass` | Some outputs missing or partial success |
| `draft_only` | Only a draft was produced, not executed |
| `draft_executed_as_t<N>` | Draft became next mission |
| `completed_but_no_push` | Done locally, not committed/pushed |
| `false_declaration` | Claimed done; evidence shows otherwise |
| `blocked` | External blocker prevented completion |
| `failed` | Mission failed with error |
| `deception` | Output intentionally misrepresented |

---

## Value Scale (1–5)

| Value | Meaning |
|---|---|
| 1 | Harmful or deceptive — negative trust impact |
| 2 | Minimal / draft quality — little immediate value |
| 3 | Useful but incomplete — partial value delivered |
| 4 | Solid — real value, no major gaps |
| 5 | Exceptional — milestone, proof, or trust-building |

---

## Pattern Naming Convention

- **snake_case**, descriptive, reusable across missions
- Examples: `surgical_edit`, `new_infrastructure`, `deception_detected_later`
- Patterns enable cross-mission trend queries
- New patterns are allowed; prefer reuse over invention

Common established patterns:
- `surgical_edit` — minimal, targeted code change
- `new_infrastructure` — creates new capability/module
- `autonomy_milestone` — advances autonomous execution
- `e2e_validation` — end-to-end proof, not just code
- `false_declaration` — claimed completion without evidence
- `real_code_fix` — actual lines changed (vs. claimed fix)
- `honest_correction` — self-correction of prior error
- `trust_verified_not_given` — trust earned through proof

---

## Append-Only Contract

**NEVER edit or delete existing rows.**

`mission_outcomes.jsonl` is a write-once ledger:
- Each line is a complete JSON record
- New records are always appended at EOF
- Corrections are made by appending a new record with a `correction_of` field
- The logger module enforces this contract at the file level
