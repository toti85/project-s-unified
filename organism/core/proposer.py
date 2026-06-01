"""
Proposer Module - Generates actionable proposals from prioritized tasks.

Creates human-readable recommendations with context, reasoning, and risk assessment.
No AI calls—template-based generation.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from .prioritizer import TaskScore


class Proposer:
    """
    Generates proposals from prioritized tasks.
    
    Each proposal includes:
    - WHY the task matters
    - Suggested action
    - Risk level assessment
    - Evidence trail
    """
    
    def __init__(self, evidence_dir: Path):
        """
        Initialize proposer.
        
        Args:
            evidence_dir: Path to evidence directory
        """
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.proposals_file = self.evidence_dir / "top_proposals.md"
    
    def _cluster_by_issue(self, tasks: list[TaskScore]) -> dict:
        """
        Cluster tasks by issue_url for consolidated proposals.
        
        Returns:
            Dict mapping cluster_id -> list of tasks
            Tasks without issue_url get individual clusters
        """
        clusters = {}
        
        for task in tasks:
            if task['issue_url']:
                # Create cluster ID from issue URL
                hash_input = task['issue_url']
                cluster_hash = hashlib.sha1(hash_input.encode()).hexdigest()[:8]
                cluster_id = f"issue:{cluster_hash}"
            else:
                # Individual task gets its own cluster
                cluster_id = f"task:{task['task_id']}"
            
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(task)
        
        return clusters
    
    def _rabbit_hole_level(self, risk: float) -> str:
        """Convert rabbit hole risk (0-1) to readable level."""
        if risk >= 0.5:
            return "HIGH"
        if risk >= 0.3:
            return "MEDIUM"
        return "LOW"
    
    def _categorize_resistance_reason(self, task: TaskScore) -> str:
        """
        Generate intelligent resistance reason based on task content.
        
        Categories:
        1. blocked_by_dependency - Tasks referencing future events (Once, After, When)
        2. high_scope_uncertainty - Tasks with vague verbs (Fix this, Investigate, Check)
        3. infra_ops_distraction - Infrastructure/deployment tasks
        4. rabbit_hole_general - Default high-risk reason
        
        Returns: Human-readable reason string
        """
        text = (task.get('text', '') + ' ' + task.get('file', '')).lower()
        
        # Category 1: Blocked by external dependency
        if any(trigger in text for trigger in ['once ', 'after ', 'when ']):
            if any(blocker in text for blocker in ['deployed', 'created', 'available', 'complete', 'ready']):
                return "Blocked by dependency; postpone until prerequisite completes."
        
        # Category 2: High scope uncertainty (vague task scope)
        task_title = task.get('text', '').lower()
        if any(vague in task_title for vague in ['fix this', 'investigate', 'check if', 'check the', 'consider', 'look at']):
            return "High scope uncertainty; postpone until clearer requirements."
        
        # Category 3: Infrastructure/ops distraction
        if any(infra_term in text for infra_term in ['deploy', 'migration', 'infrastructure', 'ci/cd', 'ci cd', 'ops ', 'devops', 'release']):
            return "Infrastructure distraction; postpone until core work completes."
        
        # Default: Rabbit hole risk
        return "High rabbit-hole risk; postpone until higher-confidence work completes."
    
    def _is_evidence_task(self, task: TaskScore) -> bool:
        """
        Detect if task is critical for evidence/validation.
        
        Returns True if task matches evidence patterns.
        """
        text = (task.get('text', '') + ' ' + task.get('file', '')).lower()
        
        evidence_patterns = [
            'test with dust',
            'verify rounding',
            'check results',
            'validate',
            'confirm vulnerability',
            'evidence',
            'proof of concept',
            'poc',
        ]
        
        return any(pattern in text for pattern in evidence_patterns)
    
    def _get_deferral_count(self, task_id: str) -> int:
        """
        Count how many times a task has been deferred.
        
        Reads decisions.jsonl and counts 'defer' actions for the task_id.
        """
        decisions_file = self.evidence_dir / "decisions.jsonl"
        
        if not decisions_file.exists():
            return 0
        
        deferral_count = 0
        try:
            with open(decisions_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        decision = json.loads(line)
                        if decision.get('task_id') == task_id and decision.get('action') == 'defer':
                            deferral_count += 1
                    except json.JSONDecodeError:
                        continue
        except (IOError, OSError):
            pass
        
        return deferral_count
    
    def _apply_evidence_escalation(self, tasks: list[TaskScore]) -> list[TaskScore]:
        """
        Boost evidence tasks that have been deferred 2+ times.
        
        Returns: Modified task list with escalation applied
        """
        escalated_tasks = []
        
        for task in tasks:
            task_copy = dict(task)  # Create a copy to avoid mutating original
            
            # Check if this is an evidence task that's been deferred
            if self._is_evidence_task(task):
                deferral_count = self._get_deferral_count(task.get('task_id', ''))
                
                if deferral_count >= 2:
                    # BOOST: Add +50 to priority score
                    original_score = task_copy.get('score', 0)
                    task_copy['score'] = original_score + 50
                    
                    # PIN: Mark as escalated
                    task_copy['evidence_escalated'] = True
                    task_copy['escalation_reason'] = f"Evidence task escalated after {deferral_count} deferrals"
                    task_copy['original_score'] = original_score
            
            escalated_tasks.append(task_copy)
        
        return escalated_tasks
    
    def _risk_assessment(self, task: TaskScore) -> str:
        """
        Assess risk level of executing this task.
        
        Returns: 'low', 'medium', 'high'
        """
        # Effort is now 1-10 numeric scale
        # High risk: high effort + unknown outcome
        if task['effort'] >= 7 and task['ev'] < 0.5:
            return "high"
        
        # Medium risk: medium effort or moderate uncertainty
        if task['effort'] >= 4 or task['ev'] < 0.7:
            return "medium"
        
        # Low risk: low effort + high EV
        return "low"
    
    def _select_resistance_tasks(self, all_tasks: list[TaskScore], max_resistance: int = 3, debug: bool = False) -> list[tuple]:
        """
        Select up to N tasks to 'resist' - push back on execution.
        
        Resistance criteria (in priority order):
        1. Highest rabbit_hole_risk (>= 0.6) - speculative tasks that distract
        2. Maintenance tasks with low strategic (<=4) - low-value when priority exists  
        3. Duplicate high-effort issues (same URL, lower score) - work already tracked
        
        CRITICAL PROTECTION: Never resist tasks with evidence_support context or is_kill_list=true.
        
        Returns list of (task, reason) tuples up to max_resistance items.
        """
        # Filter out protected tasks before consideration
        candidates = [
            t for t in all_tasks
            if not t.get('is_kill_list', False)
            and 'evidence_support' not in t.get('context_tags', set())
        ]
        
        if debug:
            print(f"[DEBUG] Resistance: {len(all_tasks)} total, {len(candidates)} after filtering")
        
        resist_candidates = []
        seen_task_ids = set()
        
        # Criterion 1: High rabbit hole risk (>= 0.6)
        high_risk = sorted(
            [t for t in candidates if t.get('rabbit_hole_risk', 0) >= 0.6],
            key=lambda t: (t.get('rabbit_hole_risk', 0), t.get('score', 0)),
            reverse=True
        )
        
        for task in high_risk:
            task_id = task.get('task_id')
            if task_id not in seen_task_ids and len(resist_candidates) < max_resistance:
                reason = self._categorize_resistance_reason(task)
                resist_candidates.append((task, reason))
                seen_task_ids.add(task_id)
        
        # Criterion 2: Maintenance tasks with low strategic value
        maintenance = sorted(
            [t for t in candidates if 'maintenance' in t.get('context_tags', set()) and t.get('strategic_score', 0) <= 4],
            key=lambda t: t.get('score', 0),
            reverse=True
        )
        
        for task in maintenance:
            task_id = task.get('task_id')
            if task_id not in seen_task_ids and len(resist_candidates) < max_resistance:
                reason = self._categorize_resistance_reason(task)
                resist_candidates.append((task, reason))
                seen_task_ids.add(task_id)
        
        # Criterion 3: Duplicate issues (same URL, lower score)
        url_groups = {}
        for t in candidates:
            url = t.get('issue_url', '')
            if url:
                if url not in url_groups:
                    url_groups[url] = []
                url_groups[url].append(t)
        
        for url, url_tasks in url_groups.items():
            if len(url_tasks) > 1:
                sorted_by_score = sorted(url_tasks, key=lambda t: t.get('score', 0), reverse=True)
                for dup_task in sorted_by_score[1:]:
                    task_id = dup_task.get('task_id')
                    if task_id not in seen_task_ids and len(resist_candidates) < max_resistance:
                        reason = self._categorize_resistance_reason(dup_task)
                        resist_candidates.append((dup_task, reason))
                        seen_task_ids.add(task_id)
                        break
        
        return resist_candidates[:max_resistance]
    
    def _generate_why(self, task: TaskScore) -> str:
        """Generate "WHY this matters" narrative."""
        impact = task['impact']
        learning = task['learning_value']
        ev = task['ev']
        
        why_parts = []
        
        if impact >= 0.8:
            why_parts.append(f"**Impact**: This change affects {impact*100:.0f}% of the critical path.")
        elif impact >= 0.6:
            why_parts.append(f"**Impact**: Medium-to-high impact ({impact*100:.0f}%).")
        
        if learning >= 0.8:
            why_parts.append(f"**Learning**: Completing this will deepen understanding of core systems.")
        elif learning >= 0.6:
            why_parts.append(f"**Learning**: Good opportunity to learn system internals.")
        
        if ev >= 0.75:
            why_parts.append(f"**Confidence**: High likelihood ({ev*100:.0f}%) of positive outcome.")
        
        return "\n".join(why_parts) if why_parts else "Addresses identified task in development pipeline."
    
    def _generate_action(self, task: TaskScore) -> str:
        """
        Generate suggested next action by task category (dev-coach style).
        
        Categories:
        - FIXME + (timeout/connection) => config/refactor steps
        - FIXME + (complicated/conditions/implement in future) => spec-first steps
        - TODO + (verify/test) => concrete test steps
        - Other FIXME => debug flow
        - Other TODO => implementation flow
        """
        text_combined = (task['text'] + " " + task['description']).lower()
        is_fixme = task['priority'].upper() == 'FIXME'
        
        # ===== FIXME: TIMEOUT/CONNECTION ISSUES =====
        if is_fixme and any(kw in text_combined for kw in ['timeout', 'connection']):
            return ("1. **Review configuration** — Check timeout values and connection limits\n"
                   "2. **Identify refactoring opportunity** — Should this be configurable?\n"
                   "3. **Extract to property/constant** — Move hardcoded value to config\n"
                   "4. **Test with edge cases** — Verify behavior at timeout boundaries")
        
        # ===== FIXME: COMPLICATED CONDITIONS/FUTURE WORK =====
        if is_fixme and any(kw in text_combined for kw in ['complicated', 'conditions', 'implement in the future']):
            return ("1. **Clarify requirements** — Document all conditions that apply\n"
                   "2. **Sketch the design** — How should this work when implemented?\n"
                   "3. **Break into phases** — What's MVP vs. future-nice-to-have?\n"
                   "4. **Propose implementation plan** — When and how to tackle this?")
        
        # ===== FIXME: GENERAL DEBUGGING FLOW =====
        if is_fixme:
            return ("1. **Read FIXME context** — Review the comment and surrounding code\n"
                   "2. **Identify root cause** — Understand why it's broken or problematic\n"
                   "3. **Implement fix** — Write targeted correction\n"
                   "4. **Test thoroughly** — Verify fix doesn't break other functionality")
        
        # ===== TODO: VERIFICATION/TESTING =====
        if 'verify' in text_combined or 'test' in text_combined:
            return ("1. **Identify test cases** — Dust amounts, rounding errors, edge cases\n"
                   "2. **Write test code** — Implement concrete test scenarios\n"
                   "3. **Run and observe** — What fails? What passes?\n"
                   "4. **Document findings** — Capture results for future reference")
        
        # ===== TODO: REFACTORING =====
        if 'refactor' in text_combined or 'rewrite' in text_combined:
            return ("1. **Map current implementation** — Document how it works now\n"
                   "2. **Design improved structure** — Sketch the new approach\n"
                   "3. **Refactor incrementally** — Test after each small change\n"
                   "4. **Remove old code** — Clean up once new version is stable")
        
        # ===== TODO: PERFORMANCE/SECURITY =====
        if any(kw in text_combined for kw in ['security', 'performance', 'optimize']):
            return ("1. **Measure current state** — Get baseline metrics\n"
                   "2. **Identify bottleneck** — Use profiler or security analyzer\n"
                   "3. **Implement improvement** — Apply optimization\n"
                   "4. **Verify improvement** — Confirm metrics improved")
        
        # ===== TODO: DOCUMENTATION =====
        if any(kw in text_combined for kw in ['doc', 'comment', 'clarify']):
            return ("1. **Read existing documentation** — Understand current state\n"
                   "2. **Identify gaps** — What's unclear or missing?\n"
                   "3. **Update documentation** — Add clarity and examples\n"
                   "4. **Verify completeness** — Test that docs match implementation")
        
        # ===== TODO: GENERIC IMPLEMENTATION =====
        return ("1. **Read the TODO context** — Understand the requirement\n"
               "2. **Plan the implementation** — Break down into steps\n"
               "3. **Implement incrementally** — Code + test in small pieces\n"
               "4. **Request review** — Get feedback before merging")
    
    def _generate_proposal_md(self, tasks: list[TaskScore], all_tasks: list[TaskScore] = None) -> str:
        """
        Generate markdown proposal document with issue clustering.
        
        Groups related tasks by issue URL for consolidated action planning.
        
        Args:
            tasks: Top prioritized tasks
        
        Returns:
            Markdown text
        """
        # Apply evidence escalation to boost critical tasks deferred multiple times
        tasks = self._apply_evidence_escalation(tasks)
        
        # Re-sort after escalation to put boosted tasks higher
        tasks = sorted(tasks, key=lambda t: t['score'], reverse=True)
        
        lines = [
            "# Dev Organism - Task Proposals",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "⚠️ **MANUAL APPROVAL REQUIRED** — Organism proposes, you decide.",
            "",
            "---",
            ""
        ]
        
        # Cluster tasks by issue URL
        clusters = self._cluster_by_issue(tasks)
        
        # Process each cluster — score szerinti csökkenő sorrend (legmagasabb score-ú cluster előre)
        def _cluster_best_score(item):
            return max(t['score'] for t in item[1])

        cluster_num = 0
        for cluster_id, cluster_tasks in sorted(clusters.items(), key=_cluster_best_score, reverse=True):
            cluster_num += 1
            
            # Sort tasks in cluster by score
            cluster_tasks = sorted(cluster_tasks, key=lambda t: t['score'], reverse=True)
            
            # Use highest-scoring task as primary
            primary_task = cluster_tasks[0]
            issue_url = primary_task['issue_url']
            
            # Determine cluster title
            if issue_url:
                title = f"[Issue] {issue_url.split('/issues/')[-1]}"
            else:
                original_text = primary_task['text'][:60] if primary_task['text'] else "Task"
                title = f"{original_text}..."
            
            risk = self._risk_assessment(primary_task)
            risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}[risk]
            
            # Add escalation marker if evidence task was escalated
            escalation_marker = ""
            if primary_task.get('evidence_escalated', False):
                escalation_marker = " 🔴 ESCALATED"
            
            lines.extend([
                f"## [{cluster_num}] {title}{escalation_marker} {risk_emoji}",
                ""
            ])
            
            # Show escalation reason if applicable
            if primary_task.get('evidence_escalated', False):
                original_score = primary_task.get('original_score', 0)
                current_score = primary_task.get('score', 0)
                boost = current_score - original_score
                lines.extend([
                    f"**Escalation**: {primary_task.get('escalation_reason', 'Evidence task escalated')}",
                    f"**Score Boost**: +{boost:.0f} (original: {original_score:.2f})",
                    "",
                ])
            
            # Show issue URL if present
            if issue_url:
                lines.extend([
                    f"**Issue**: [{issue_url}]({issue_url})",
                    ""
                ])
            
            # List all affected locations
            lines.extend([
                "**Locations**:",
                ""
            ])
            for task in cluster_tasks:
                file_location = f"{task['file']}:{task['line']}" if task['file'] else "unknown"
                task_text = task['text'][:50] if task['text'] else task['description'][:50]
                lines.append(f"- `{file_location}` — {task_text}")
            
            lines.extend(["", "**Priority Score**: " + ", ".join([f"{t['score']:.2f}" for t in cluster_tasks[:2]]), ""])
            
            # Show why this matters
            lines.extend([
                "### Why This Matters",
                ""
            ])
            
            # Special section for escalated evidence tasks
            if primary_task.get('evidence_escalated', False):
                lines.extend([
                    "⚠️ **CRITICAL EVIDENCE TASK** — Research momentum depends on validation.",
                    "",
                    "This evidence-critical task has been deferred multiple times.",
                    "Proceeding now is essential for confirming vulnerability and maintaining research progress.",
                    "",
                ])
            
            lines.append(self._generate_why(primary_task))
            lines.append("")
            
            # Show code context for primary task
            if primary_task['snippet']:
                lines.extend([
                    "### Code Context (Primary Location)",
                    "",
                    "```python",
                    primary_task['snippet'].rstrip(),
                    "```",
                    ""
                ])
            
            # Consolidated action plan
            lines.extend([
                "### Consolidated Action Plan",
                "",
                self._generate_action(primary_task),
                ""
            ])
            
            # Show metrics
            rabbit_hole_level = self._rabbit_hole_level(primary_task['rabbit_hole_risk'])
            quick_win_badge = "✅ YES" if primary_task['is_quick_win'] else "No"
            
            lines.extend([
                "### Intelligence Metrics",
                "",
                f"- **Strategic Score**: {primary_task['strategic_score']:.1f}/10",
                f"- **Rabbit Hole Risk**: {rabbit_hole_level} ({primary_task['rabbit_hole_risk']:.2f})",
                f"- **Quick Win**: {quick_win_badge}",
                "",
                "### Task Metrics",
                "",
                f"- Impact: {primary_task['impact']*100:.0f}%",
                f"- Learning Value: {primary_task['learning_value']*100:.0f}%",
                f"- Expected Value: {primary_task['ev']*100:.0f}%",
                f"- Estimated Effort: {primary_task['effort']:.1f}/10",
                f"- Risk Level: {risk.upper()}",
                f"- Related Items: {len(cluster_tasks)}",
                "",
                "### Why NOT Do This?",
                "",
                f"{primary_task['why_not']}",
                "",
                "---",
                ""
            ])
        
        # Extract and show kill-list tasks (low-leverage work to avoid)
        # Use is_kill_list flag from prioritizer (which includes protection logic)
        kill_list_tasks = []
        for t in tasks:
            # Use the is_kill_list flag from prioritizer that respects context_tags protection
            if t.get('is_kill_list', False):
                kill_list_tasks.append(t)
        
        if kill_list_tasks:
            lines.extend([
                "",
                "======================",
                "🚫 STRATEGIC KILL LIST",
                "======================",
                "",
                "**Low-leverage work — Do NOT spend time here unless blocking another task.**",
                ""
            ])
            
            for i, task in enumerate(kill_list_tasks, 1):
                lines.extend([
                    f"### [{i}] {task['text'][:60]}...",
                    "",
                    f"**File**: {task['file']}:{task['line']}",
                    f"**Score**: {task['score']:.2f} (after penalty)",
                    "",
                    "**Why Flagged**:",
                    f"- Strategic value too low ({task['strategic_score']:.1f}/10)",
                    f"- Minimal learning opportunity ({task['learning_value']*100:.0f}%)",
                    f"- No exploit/security relevance",
                    "",
                    "**Examples of kill-list work**:",
                    "- Rename variables or functions",
                    "- Add/update comments and documentation",
                    "- Code formatting and style changes",
                    "- Cosmetic refactoring",
                    "- Grammar/spelling fixes",
                    "",
                    ""
                ])
        
        # Extract and render resistance tasks (strategic pushback on certain work)
        # This does NOT remove tasks, but explains why organism is cautious about them
        # Use all_tasks for selection if provided, to find timing objections even to tier-2 work
        resistance_candidate_pool = all_tasks if all_tasks is not None else tasks
        resistance_with_reasons = self._select_resistance_tasks(resistance_candidate_pool, max_resistance=3, debug=False)
        if resistance_with_reasons:
            lines.extend([
                "",
                "===========================",
                "🚧 STRATEGIC RESISTANCE",
                "(DO NOT DO NOW)",
                "===========================",
                "",
                "**The organism strategically opposes doing these tasks NOW.** This is not rejection—it's timing.",
                "These tasks matter, but should be deferred until higher-confidence work completes.",
                ""
            ])
            
            for i, (task, reason) in enumerate(resistance_with_reasons, 1):
                lines.extend([
                    f"### [{i}] {task['text'][:60]}...",
                    "",
                    f"**Location**: {task['file']}:{task['line']}",
                    f"**Priority Score**: {task['score']:.2f} | Rabbit Hole: {self._rabbit_hole_level(task.get('rabbit_hole_risk', 0))} ({task.get('rabbit_hole_risk', 0):.2f})",
                    "",
                    f"**Organism says**: {reason}",
                    ""
                ])
        
        lines.extend([
            "## Approval Instructions",
            "",
            "**To approve a proposal:**",
            "```",
            "python organism/core/loop.py --approve <task_id>",
            "```",
            "",
            "**To reject a proposal:**",
            "```",
            "python organism/core/loop.py --reject <task_id>",
            "```",
            "",
            "**To defer a proposal:**",
            "```",
            "python organism/core/loop.py --defer <task_id>",
            "```",
            "",
            "Decisions are logged to `evidence/decisions.jsonl` for taste model training.",
        ])
        
        return "\n".join(lines)
    
    def generate(self, tasks: list[TaskScore], all_tasks: list[TaskScore] = None) -> Path:
        """
        Generate proposal document from ranked tasks.
        
        Args:
            tasks: Top prioritized tasks from PriorityEngine (proposals section)
            all_tasks: All ranked tasks (for resistance selector to find timing issues)
        
        Returns:
            Path to generated proposals file
        """
        md_content = self._generate_proposal_md(tasks, all_tasks=all_tasks)
        
        # Write to evidence directory
        self.proposals_file.write_text(md_content, encoding='utf-8')
        
        return self.proposals_file
