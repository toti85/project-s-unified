# Dev Organism - Project-S-LIVE

A **living development environment** that observes developer activity, prioritizes tasks using multi-metric scoring, and proposes actionable work.

## Core Design Principles

- **Observability First**: Detects changes, TODOs, patterns without intrusion
- **Intelligent Prioritization**: Multi-metric scoring (impact, learning value, expected value, effort)
- **Human-Centered**: Proposals only—no autonomous execution
- **Evidence-Driven**: All decisions logged for learning and audit
- **Production-Grade**: No toy code, typed Python, defensive implementation

## Architecture

```
organism/
├── core/
│   ├── observer.py        # Detects activity (git, TODOs, terminal)
│   ├── prioritizer.py     # Multi-metric scoring engine
│   ├── proposer.py        # Generates proposals
│   └── loop.py            # Orchestrates pipeline
├── modules/
│   └── taste_model.py     # Lightweight learning system
├── ui/
│   └── dashboard.py       # HTTP dashboard (standard library only)
└── evidence/
    ├── decisions.jsonl    # User approval/rejection log
    ├── outcomes.jsonl     # Task completion outcomes
    └── top_proposals.md   # Latest proposals
```

## Quick Start

### 1. Run a Single Observation Cycle

```bash
python -m organism.core.loop --repo .
```

This will:
1. **Observe** git changes, TODOs, terminal patterns
2. **Prioritize** using multi-metric scoring
3. **Propose** top 5 tasks with reasoning
4. **Save** proposals to `organism/evidence/top_proposals.md`

### 2. View Proposals

Open `organism/evidence/top_proposals.md` to see:
- Task descriptions
- Why it matters (impact, learning, confidence)
- Suggested next actions
- Risk assessment (🟢 low, 🟡 medium, 🔴 high)

### 3. Record Decisions

Approve a task:
```bash
python -m organism.core.loop --approve todo_0
```

Reject:
```bash
python -m organism.core.loop --reject todo_0
```

Defer:
```bash
python -m organism.core.loop --defer todo_0
```

## Web Dashboard

Start the interactive dashboard:

```bash
python -m organism.ui.dashboard .
```

Then open http://localhost:8765 in your browser.

**Dashboard features:**
- 🔍 Run observation cycles on-demand
- 📋 View generated proposals
- 📊 Track decision history
- 🔗 RESTful API endpoints

## Scoring Formula

```
score = (impact × 10) + (learning × 5) + (ev × 3) - effort
```

### Metrics

| Metric | Range | Definition |
|--------|-------|------------|
| **Impact** | 0.0-1.0 | How much does completing this improve the codebase? |
| **Learning Value** | 0.0-1.0 | How much will we learn from this work? |
| **Expected Value (EV)** | 0.0-1.0 | Confidence that this work will succeed |
| **Effort** | 0.0-1.0 | Estimated implementation complexity |

### Heuristic Estimators

**Impact** (things that increase it):
- FIXME items → 1.0
- Security/architecture tasks → 0.9
- Bug fixes → 0.85
- Changes to critical files → varies by file
- Repeated patterns → 0.7

**Learning Value** (things that increase it):
- Core module changes → 0.85
- Architecture tasks → 0.8
- Refactoring → varies
- Repeated patterns → 0.2 (less to learn)

**Expected Value** (confidence):
- FIXME items → 0.85 (likely solves a real problem)
- Pattern automation → 0.8 (high success rate)
- TODOs → 0.55 (moderate clarity)

**Effort** (things that increase cost):
- FIXME items → 0.8 (problems are hard)
- Code changes → 0.7 (risky)
- TODOs → 0.3 (comments are lightweight)
- Automation → 0.4 (scripting)

## API Reference

### GET /

Renders the web dashboard.

### GET /api/observe

Runs a complete observation cycle.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-02-15T...",
  "tasks_collected": 12,
  "top_proposals": [...],
  "taste_stats": {
    "total": 5,
    "approved": 3,
    "rejected": 1,
    "deferred": 1,
    "approval_rate": 0.6
  }
}
```

### GET /api/proposals

Returns latest proposals in Markdown format.

### GET /api/decisions

Returns decision history statistics.

### GET /api/observations

Returns raw observation data (changes, TODOs, patterns).

### POST /api/decide

Record a user decision.

**Body:**
```json
{
  "task_id": "todo_0",
  "action": "approve"
}
```

**Actions:** `approve`, `reject`, `defer`

## Taste Model (Learning)

The taste model learns from user decisions to adjust future scoring:

- **Approved task** → +0.2 score boost for similar tasks
- **Rejected task** → -0.3 score penalty
- **Deferred task** → -0.1 urgency decay

Decisions are logged to `organism/evidence/decisions.jsonl` in JSONL format for easy analysis and replay.

## Evidence & Audit Trail

All decisions and outcomes are logged:

### decisions.jsonl
```json
{"task_id": "todo_0", "action": "approve", "timestamp": "2026-02-15T..."}
{"task_id": "change_1", "action": "reject", "timestamp": "2026-02-15T..."}
```

### run_latest.txt
Latest complete observation cycle results with all metrics.

## Implementation Notes

### No External Dependencies

Uses **only Python standard library** except for:
- Optional: FastAPI (for dashboard, but we use pure `http.server` instead)

### Error Handling

All components are defensive:
- Git operations → catches and returns partial results
- File I/O → graceful fallbacks
- Terminal history → skips if not available
- Scoring → always produces a score, even with missing data

### Production-Grade Code

- **Typed**: Full type hints throughout
- **Documented**: Docstrings on all classes and methods
- **Testable**: Pure functions, dependency injection
- **Observable**: Detailed logging, evidence trail
- **Safe**: No destructive operations without approval

## Workflow Example

1. **Morning check-in:**
   ```bash
   python -m organism.core.loop --repo . --top 5
   ```

2. **Review proposals:**
   - Open `organism/evidence/top_proposals.md`
   - Scan "Why it matters" for each task
   - Identify quick wins vs. strategic work

3. **Make decisions:**
   ```bash
   python -m organism.core.loop --approve todo_2  # Highest priority
   python -m organism.core.loop --defer todo_4    # Not now
   ```

4. **Do the work**

5. **Log outcome:**
   - The taste model adapts
   - Next cycle's scores reflect your choices
   - Learning compounds over time

## Future Work (v0.2+)

- [ ] Pattern matching for similar task clustering
- [ ] Outcome logging (when you complete a task)
- [ ] Advanced taste model (Bayesian updates)
- [ ] Multi-developer organism (team decisions)
- [ ] Integration with issue trackers
- [ ] Continuous background observation

## Contributing

This is a research project. Pull requests welcome for:
- Additional observation sources
- Improved heuristics
- Better UI/UX
- Integration examples

## License

Part of Project-S-LIVE research fork.
