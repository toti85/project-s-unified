"# AO3 Task JSON Schema Diagnosis

**Date:** 2026-05-28
**Status:** DIAGNOSIS COMPLETE

---

## A. Schema specifikáció helye / formátuma

**Fájl:** `orchestrator_runtime/cline_inbox/CLINE_HANDOFF_INSTRUCTIONS.md`

**A schema specifikáció KÉT külön protokollt ír le:**

### 1. INPUT protokoll (Cline → olvassa)

| Mező | Forrás fájl | Kötelező? |
|------|-------------|-----------|
| Task description | `next_prompt.md` | IGEN |
| Allowed sandbox directory | `next_prompt.md` | IGEN |
| Forbidden paths | `next_prompt.md` | IGEN |
| Required deliverables | `next_prompt.md` | IGEN |
| Test instructions | `next_prompt.md` | IGEN |
| Output/report location | `next_prompt.md` | IGEN |

**FONTOS:** A `CLINE_HANDOFF_INSTRUCTIONS.md` a `next_prompt.md`-t említi inputként, **NEM** a `task.json`-t!

### 2. OUTPUT protokoll (Cline → írja)

`orchestrator_runtime/cline_outbox/output_ready.json`:

```json
{
  "run_id": "FA1_XXX",
  "iteration": 1,
  "timestamp": "ISO 8601 timestamp",
  "status": "ready",
  "checksum": "first 16 chars of SHA-256 of last_output.md content"
}
```

**Kötelező mezők:** `run_id`, `iteration`, `timestamp`, `status`, `checksum`

---

## B. Generator helye / kódja

**Fájl:** `orchestrator_runtime/governance/orchestrator_bridge.py`
**Függvény:** `_generate_fa1_task_prompt(goal)` (line 129-162)

**Generált task.json schema:**

```python
return {
    "goal_id": goal_id,           # pl. "GOAL_007"
    "title": title,               # pl. "Generate MS-AO1 Progress Report"
    "risk": risk,                 # pl. "LOW"
    "prompt": prompt,             # FA1-style markdown prompt
    "sandbox_dir": "...",         # abszolút path sandbox-hoz
    "forbidden_paths": ["src/", "config/", "self_state.json"],
    "generated_at": _now(),       # ISO 8601 timestamp
}
```

**TÁROLÁS:** `orchestrator_runtime/cline_inbox/task.json` (atomic write: tmp → rename)

---

## C. Leftover task.json volt-e a cline_inbox-ban?

**NEM.** A `cline_inbox/` tartalom:

```
CLINE_HANDOFF_INSTRUCTIONS.md
next_prompt.md
prompt_ready.json
```

**Nincs `task.json` fájl.** A Copilot session előtt nem maradt vissza task.json.

**Lehetséges ok:** A task.json-t a bridge.py írta, de a Copilot session előtt már törölve lett (vagy soha nem jött létre, mert a bridge.py `--live` futás timeout-ot kapott és nem generált task.json-t a Copilot session idejére).

---

## D. Schema vs Generator eltérés — A MISMATCH

### 3 külön eltérés azonosítva:

### 1. FÁJL NÉV MISMATCH

| Várható (CLINE_HANDOFF_INSTRUCTIONS.md) | Tényleges (bridge.py) |
|------------------------------------------|----------------------|
| `next_prompt.md` | `task.json` |

**A CLINE_HANDOFF_INSTRUCTIONS.md a `next_prompt.md`-t említi inputként. A bridge.py `task.json`-t ír.**

### 2. `task_id` MEZŐ HIÁNYA

| Várható (output_ready.json schema) | Tényleges (task.json) |
|-------------------------------------|----------------------|
| `run_id` (output_ready.json-ban) | `goal_id` (task.json-ban) |

**A Copilot executor valószínűleg `task_id` mezőt keresett a task.json-ban, de a bridge.py `goal_id`-t használ.** Ez a NEEDS_HUMAN escalation okai lehet.

### 3. PROTOKOLL INKONZISTENCIA

| Komponens | Input fájl | Output fájl |
|-----------|-----------|-------------|
| CLINE_HANDOFF_INSTRUCTIONS.md | `next_prompt.md` | `output_ready.json` |
| bridge.py | `goal_queue.json` | `task.json` |
| prompt_ready.json | — | `run_id` mező |

**A `prompt_ready.json` (FA1 protokoll) és a `task.json` (AO3 protokoll) két külön handoff mechanizmus:**

| | FA1 (prompt_ready.json) | AO3 (task.json) |
|---|--------------------------|-----------------|
| Input | `next_prompt.md` | `task.json` |
| Metadata | `prompt_ready.json` | (nincs) |
| Output | `output_ready.json` | `output_ready.json` |
| ID mező | `run_id` | `goal_id` |

---

## E. Javasolt fix (TERV, nem implementáció)

### Fix 1: CLINE_HANDOFF_INSTRUCTIONS.md frissítése

A `next_prompt.md` hivatkozás mellé felvenni a `task.json` alternatívát:

```markdown
## 1. Read the Prompt

Read the prompt from ONE of:
- `orchestrator_runtime/cline_inbox/next_prompt.md` (FA1 protocol)
- `orchestrator_runtime/cline_inbox/task.json` (AO3 protocol) — use "prompt" field
```

### Fix 2: task.json schema kiegészítése

A `_generate_fa1_task_prompt()` return dict-jébe felvenni:

```python
return {
    "goal_id": goal_id,
    "task_id": goal_id,       # ALIAS — backward compat
    "run_id": goal_id,        # ALIAS — output_ready.json compat
    "title": title,
    ...
}
```

### Fix 3: prompt_ready.json szinkronizálása

Ha `task.json` létrejön, akkor `prompt_ready.json` is frissüljön:

```python
# After writing task.json
prompt_ready = {
    "run_id": goal_id,
    "iteration": 1,
    "timestamp": _now(),
    "status": "ready",
    "checksum": hashlib.sha256(task_data["prompt"].encode()).hexdigest()[:16],
    "consumed": False,
}
```

### Fix 4: Egységes ID mező

| Protokoll | ID mező | Megjegyzés |
|-----------|---------|-----------|
| FA1 | `run_id` | prompt_ready.json, output_ready.json |
| AO3 | `goal_id` | task.json |
| **Javasolt** | `goal_id` + `run_id` alias | Mindkét protokoll kompatibilis |

---

## Összefoglaló

| Kérdés | Válasz |
|--------|--------|
| A. Schema specifikáció helye | `CLINE_HANDOFF_INSTRUCTIONS.md` — `next_prompt.md` input, `output_ready.json` output |
| B. Generator helye | `orchestrator_bridge.py` `_generate_fa1_task_prompt()` — `task.json` output |
| C. Leftover task.json | NEM — nincs task.json a cline_inbox-ban |
| D. Schema mismatch | 3 eltérés: fájl név (next_prompt.md vs task.json), ID mező (run_id vs goal_id), protokoll inkonzisztencia |
| E. Javasolt fix | 4 lépés: instructions update, task.json alias mezők, prompt_ready.json sync, egységes ID |

**A NEEDS_HUMAN escalation valószínű ok:** A Copilot executor a `task.json` `task_id` vagy `run_id` mezőjét kereste, de a bridge.py csak `goal_id`-t ír. A hiányzó mező miatt a schema validáció sikertelen volt.
"