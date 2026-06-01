# EXECUTION PATHS ANALYSIS

Status: Mapping Only (No Refactoring Recommendations Yet)
Generated: 2026-02-18

## Three Active Execution Paths

### PATH 1: STANDARD PATH (Pre-Meta, Still Active)

```
Entry Point: startup.py or super_intelligent_launcher.py
    ↓
super_intelligent_ai.py (main AI interface)
    ↓
strategic_overlay.py (strategy decisions)
    ↓
orchestration/workflow_engine.py or langgraph_engine.py
    ↓
tool execution (browser, file, system tools)
    ↓
state/persistent_state_manager.py (state updates)
    ↓
Output: task results
```

**Status**: ACTIVE (working)  
**Stability**: MEDIUM (complex orchestration)  
**Test Coverage**: PARTIAL  
**Health**: ?UNCLEAR (not recently tested)

**What Still Works**:
- Super intelligent AI interface
- Strategic overlay decisions
- Tool execution and chaining
- State persistence
- Multi-tool coordination

**What Is Partially Broken**:
- LangGraph integration (unclear if used)
- Orchestrator variants (multiple untested paths)
- Browser automation tool selection (5 versions)
- Workflow restart/recovery

**What Is Redundant**:
- Two orchestration engines (workflow_engine.py vs langgraph_engine.py)
- Multiple tool registry locations
- Strategy_council vs meta_controller (responsibility unclear)

**Should NEVER Be Removed**:
- super_intelligent_ai.py - core interface
- state management - persistent data
- tool registry - tool execution backbone
- strategic_overlay.py - decision making


### PATH 2: META PATH (New, Most Tested)

```
Entry Point: organism/core/loop.py (--repo . --top 20)
    ↓
observer.py (detect tasks from code)
    ↓
prioritizer.py (rank tasks, classify context, check evidence)
    ↓
taste_model.py (load decision history)
    ↓
proposer.py (generate proposals with escalation + intelligent reasons)
    ↓
Output: top_proposals.md with:
  - Evidence tasks escalated (+50 if deferred 2x)
  - Strategic resistance with context-aware reasons
  - Kill list eliminated for evidence tasks
```

**Status**: ACTIVE (recently implemented)  
**Stability**: HIGH (comprehensive testing)  
**Test Coverage**: COMPREHENSIVE (+10 test files)  
**Health**: EXCELLENT (evidence escalation verified)

**What Still Works**:
- Task observation from code comments
- Priority scoring with machine learning
- Evidence task protection (no kill list)
- Deferral tracking in decisions.jsonl
- Escalation mechanism (+50 boost after 2 deferrals)
- Intelligent resistance categorization (3 categories)
- Strategic filtering (exclude kill-list, evidence-support)

**What Is Robust**:
- Evidence detection (8 patterns)
- Context tagging (exploit_context, evidence_support, maintenance, infra_rabbit)
- Resistance selection (up to 3 tasks with proper reasons)
- Proposal generation with escalation markers

**No Known Breakage**:
- This path is well-tested and production-ready

**Should NEVER Be Removed**:
- organism/ - core meta layer
- decision tracking - taste model foundation
- evidence protection - critical for research integrity
- prioritization - core value


### PATH 3: RESEARCH PATH (Experimental)

```
Entry Point: src/core/meta/research/research_loop.py
    ↓
research_goal.py (define exploration goals)
    ↓
research_state.py (track state)
    ↓
learning iteration (explore, evaluate, improve)
    ↓
Output: learned models, improved goals
```

**Status**: EXPERIMENTAL (research phase)  
**Stability**: LOW (ongoing development)  
**Test Coverage**: BASIC  
**Health**: UNKNOWN (not production-tested)

**What Is In Development**:
- Self-improving mechanisms
- Goal refinement
- Knowledge extraction

**Risk Factors**:
- Unknown convergence properties
- No production validation
- Dependency chain unclear

**Decision**: Keep alive for research, do not integrate into critical paths


### PATH 4: LANGGRAPH V2 PATH (Status Unclear)

```
Entry Point: src/core/orchestration/langgraph_engine.py
    ↓
LangGraph runtime setup
    ↓
Node execution graph
    ↓
Result aggregation
```

**Status**: POSSIBLY_BROKEN (unknown if used)  
**Stability**: UNKNOWN  
**Test Coverage**: UNKNOWN  
**Health**: ??NEEDS_AUDIT

**Critical Questions**:
- Is LangGraph still used in any production path?
- Are there tests that validate it?
- What is the fallback if it breaks?
- Should it be marked deprecated?

**Action Required**: AUDIT BEFORE USING


## Path Cross-Referencing

### Standard Path Dependencies
- Requires: super_intelligent_ai.py, orchestration/, tools/
- Depends on: state management, tool registry
- Used by: startup.py, super_intelligent_launcher.py
- Tested by: test_meta_integration.py, test_real_execution.py

### Meta Path Dependencies
- Requires: organism/ (standalone)
- Depends on: decisions.jsonl (can create)
- Used by: organism/core/loop.py (CLI)
- Tested by: test_evidence_escalation_comprehensive.py, test_resistance_selector.py, +8 more

### Research Path Dependencies
- Requires: src/core/meta/research/
- Depends on: unknown (incomplete analysis)
- Used by: research only
- Tested by: test_research_loop.py (basic)

### LangGraph Path Dependencies
- Requires: LangGraph library + langgraph_engine.py
- Depends on: unclear
- Used by: UNKNOWN (AUDIT NEEDED)
- Tested by: UNKNOWN


## Convergence Analysis

**Are the paths converging?**

- **Standard → Meta**: Possible convergence. Meta layer is younger and more advanced. Standard path should eventually feed tasks to meta.
- **Meta → Research**: No convergence yet. Research operates independently.
- **All paths**: No unified convergence shown. Multiple execution paradigms still coexist.

**Convergence Risks**:
1. Task ownership ambiguity (who decides priorities?)
2. Data flow ambiguity (where does state flow?)
3. Tool registry conflicts (which tools are active in which path?)
4. Decision conflicts (multiple decision-makers)

**Convergence Safety**:
- Meta path shows clear ownership (organism layer)
- Standard path still controls AI decisions
- Research path is isolated
- No documented conflicts (yet)

---

## Summary Table

| Path | Entry | Status | Stability | Health | Critical? |
|------|-------|--------|-----------|--------|-----------|
| Standard | super_intelligent_ai.py | ACTIVE | MEDIUM | UNCLEAR | YES |
| Meta | organism/core/loop.py | ACTIVE | HIGH | GOOD | YES |
| Research | research_loop.py | EXPERIMENTAL | LOW | UNKNOWN | NO |
| LangGraph | langgraph_engine.py | UNKNOWN | UNKNOWN | UNKNOWN | ?? |

---

## Read-Only Observations

1. **Meta path is more mature** than standard path in terms of testing and clarity
2. **Standard path is still active** and handles production workloads
3. **Research path is isolated** and doesn't affect production
4. **LangGraph status is ambiguous** - needs audit
5. **No single "canonical" path** - system is multi-paradigm

---

Last Updated: 2026-02-18
Scope: Complete execution mapping
Status: ANALYSIS ONLY
