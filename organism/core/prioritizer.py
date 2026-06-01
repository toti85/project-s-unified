"""
Priority Engine - Ranks tasks using multi-metric scoring.

Scoring formula:
    score = (impact * 10) + (learning * 5) + (ev * 3) - effort

Uses heuristic estimators to evaluate tasks without ML.
"""

from typing import TypedDict
import math
from .observer import Task


class TaskScore(TypedDict):
    """Task with calculated priority score."""
    task_id: str
    description: str
    impact: float      # 0.0-1.0
    learning_value: float  # 0.0-1.0
    ev: float          # 0.0-1.0 (expected value)
    effort: float      # 1-10 numeric scale
    strategic_score: float  # 0-10 (structural improvement)
    rabbit_hole_risk: float  # 0-1 (speculative work penalty)
    score: float       # Final weighted score
    reason: str        # Explanation of score
    file: str          # Source file
    line: int          # Line number
    text: str          # Original TODO/FIXME text
    snippet: str       # Code context (3 lines before/after)
    context_tags: set  # Task context classification
    is_kill_list: bool  # Flagged for low leverage
    is_quick_win: bool  # Low effort, high impact
    why_not: str       # Reasons NOT to do this task
    issue_url: str     # GitHub/issue tracker URL if present
    priority: str      # 'TODO' or 'FIXME'
    is_quick_win: bool  # Low effort, high impact
    why_not: str       # Critical perspective
    is_kill_list: bool  # Low-leverage work (eliminate)


class PriorityEngine:
    """
    Multi-metric task prioritization.
    
    Evaluates impact, learning value, expected value, and effort
    to rank work by strategic value.
    """
    
    def __init__(self):
        """Initialize priority engine."""
        self.critical_files = {
            'core/observer.py': 2.0,
            'core/prioritizer.py': 2.0,
            'core/proposer.py': 2.0,
            'core/loop.py': 1.8,
            'modules/taste_model.py': 1.5,
            'ui/dashboard.py': 1.2,
        }
        self.high_impact_keywords = {
            'FIXME': 1.0,
            'security': 0.9,
            'bug': 0.85,
            'crash': 0.95,
            'performance': 0.7,
            'TODO': 0.6,
            'refactor': 0.5,
        }
    
    def estimate_impact(self, task: Task) -> float:
        """
        Estimate impact of completing this task (0.0-1.0).
        
        Heuristics:
        - HEAVILY PENALIZE organism/ and other ignored dirs (-0.95 impact)
        - FIXME items: high impact (0.8-1.0)
        - Critical file paths (core/*, ui/*): 0.7+ base impact
        - Keywords (security, crash, data loss, critical): +0.2 bonus
        - Documentation/README: lower impact (0.2-0.4)
        """
        # CRITICAL: Heavily penalize organism/ directory
        ignored_dirs = {'organism', '.git', 'venv', 'node_modules', '__pycache__'}
        if any(ignored in task.file.lower() for ignored in ignored_dirs):
            return 0.05  # Almost no impact—these are internal tool tasks
        
        impact = 0.5  # Baseline for TODOs
        
        # File location matters
        if task.file:
            file_lower = task.file.lower()
            # Critical system files (in user's project, not organism/)
            if 'core/' in file_lower and 'organism' not in file_lower:
                impact = 0.95
            elif 'src/' in file_lower or 'lib/' in file_lower:
                impact = 0.85
            elif 'ui/' in file_lower and 'organism' not in file_lower:
                impact = 0.75
            elif 'modules/' in file_lower and 'organism' not in file_lower:
                impact = 0.7
            elif 'docs/' in file_lower or 'readme' in file_lower:
                impact = 0.25
            else:
                impact = 0.5
        
        # High-impact keywords add bonus
        text_combined = (task.text + " " + task.description).lower()
        impact_keywords = ['fixme', 'critical', 'crash', 'security', 'data loss', 'broken', 'error']
        if any(kw in text_combined for kw in impact_keywords):
            impact = min(1.0, impact + 0.2)
        
        return min(1.0, impact)
    
    def estimate_effort(self, task: Task) -> float:
        """
        Estimate effort to complete (1-10 scale, NOT 0.0-1.0).
        
        Heuristics:
        - Simple fixes (typo, doc, comment, rename): 1-2
        - Medium items (implement missing feature, fix bug): 3-5
        - Hard items (refactor, rewrite, architecture, async, threading): 6-8
        - Major effort (system redesign, large refactoring): 8-10
        
        Returns numeric 1-10 (used with subtraction in score formula).
        """
        effort = 4  # Default medium effort
        
        text_combined = (task.text + " " + task.description).lower()
        
        # Easy tasks: typo, doc, comment, rename, TODO cleanup
        easy_keywords = ['typo', 'doc', 'comment', 'rename', 'clean up', 'remove', 'add docstring']
        if any(kw in text_combined for kw in easy_keywords):
            effort = 2
        # Hard tasks: major refactoring, architecture, async/threading
        elif any(kw in text_combined for kw in ['refactor', 'rewrite', 'architecture', 'redesign', 'async', 'thread', 'cache']):
            effort = 7
        # Medium-easy: simple fixing
        elif 'fix' in text_combined and 'FIXME' not in task.text:
            effort = 3
        # Standard TODO
        elif 'TODO' in task.text:
            effort = 4
        # FIXME usually harder
        elif 'FIXME' in task.text:
            effort = 6
        
        return min(10, effort)
    
    def estimate_learning_value(self, task: Task) -> float:
        """
        Estimate learning/knowledge gain (0.0-1.0).
        
        Heuristics:
        - Core system modules (observer, prioritizer, loop): 0.8-1.0
        - Subsystem keywords (fastapi, git, dashboard, taste_model): 0.4-0.7
        - Architecture/design tasks: 0.75-0.85
        - Bug fixes and optimization: 0.5-0.7
        - Documentation/cleanup: 0.1-0.3
        """
        learning = 0.3  # Baseline knowledge gain
        
        # File location learning
        if task.file:
            file_lower = task.file.lower()
            if 'core/observer.py' in file_lower or 'core/prioritizer.py' in file_lower or 'core/loop.py' in file_lower:
                learning = 0.9
            elif 'core/' in file_lower:
                learning = 0.8
            elif 'taste_model' in file_lower or 'dashboard' in file_lower:
                learning = 0.65
            elif 'modules/' in file_lower:
                learning = 0.6
            elif 'ui/' in file_lower:
                learning = 0.5
            elif 'docs/' in file_lower or 'readme' in file_lower:
                learning = 0.15
        
        # Subsystem keywords (architecture, integration points)
        text_combined = (task.text + " " + task.description).lower()
        subsystem_keywords = ['fastapi', 'git', 'dashboard', 'taste_model', 'observer', 'prioritizer', 'proposer']
        if any(kw in text_combined for kw in subsystem_keywords):
            learning = max(learning, 0.65)
        
        # Architecture/design keywords
        if any(kw in text_combined for kw in ['architecture', 'design', 'pattern', 'refactor']):
            learning = max(learning, 0.75)
        
        return min(1.0, learning)
    
    def estimate_ev(self, task: Task) -> float:
        """
        Estimate expected value (probability of high outcome).
        
        Evidence-based heuristics:
        - If issue_url present: ev = 0.65 (already discussed/tracked)
        - If file contains "/test/" and FIXME: +0.15 bonus
        - If text has timeout|crash|broken|failing: +0.10
        - If text has future|complicated|implement: ev = 0.35 (speculative)
        - Otherwise: standard heuristics
        
        Clamps to 0.05..0.95
        """
        ev = 0.55  # Baseline
        
        text_combined = (task.text + " " + task.description).lower()
        
        # Evidence-based adjustments
        if task.issue_url:
            ev = 0.65  # Issue tracked = higher confidence
        
        # Test file FIXME = higher confidence
        if '/test/' in task.file.lower() and task.metadata.get('priority') == 'FIXME':
            ev += 0.15
        
        # Critical failure keywords
        if any(kw in text_combined for kw in ['timeout', 'crash', 'broken', 'failing']):
            ev += 0.10
        
        # Speculative/future work = lower confidence
        if any(kw in text_combined for kw in ['future', 'complicated', 'implement in the future']):
            ev = 0.35
        
        # Standard keyword-based adjustments (if not already overridden)
        elif 'fixme' in text_combined:
            ev = max(ev, 0.80)  # FIXMEs are usually proven issues
        elif 'TODO' in task.text and 'verify' in text_combined:
            ev = max(ev, 0.60)  # Verification is testable
        
        return max(0.05, min(0.95, ev))  # Clamp to 0.05..0.95
    
    def estimate_strategic_score(self, task: Task) -> float:
        """
        Estimate strategic value: does completing this make the developer structurally stronger?
        
        Returns 0-10 score (not normalized).
        
        HIGH (7-10): Security, rounding, exploit, precision, architecture, automation, infra, tools, perf
        MEDIUM (4-6): Refactor, timeout config, reliability, testing
        LOW (0-3): Docs, rename, cosmetic, workaround, maintenance
        """
        text_combined = (task.text + " " + task.description).lower()
        
        # HIGH strategic value
        high_keywords = ['security', 'rounding', 'exploit', 'precision', 'architecture', 
                        'automation', 'infrastructure', 'reusable', 'tool', 'performance']
        if any(kw in text_combined for kw in high_keywords):
            return 8.5
        
        # MEDIUM strategic value
        medium_keywords = ['refactor', 'timeout', 'config', 'reliability', 'test', 'verify', 'optimize']
        if any(kw in text_combined for kw in medium_keywords):
            return 5.5
        
        # LOW strategic value (workarounds, docs, renames)
        low_keywords = ['doc', 'comment', 'rename', 'cosmetic', 'workaround', 'maintenance']
        if any(kw in text_combined for kw in low_keywords):
            return 2.0
        
        # Default = medium
        return 4.5
    
    def estimate_rabbit_hole_risk(self, task: Task) -> float:
        """
        Estimate risk of open-ended speculative work (rabbit hole) — v2 AGGRESSIVE.
        
        Returns 0-1 penalty score. Prefers false positives over false negatives.
        Strategy: Default to MEDIUM, only drop to LOW for truly bounded work.
        
        HIGH RISK (0.6-0.9): deployment, migration, upgrade, architecture, full test setup,
                             hardhat, ethers, infra, rewrite, implement in future
        MEDIUM (0.3-0.5): Default for unclassified work; refactor, configurable, etc
        LOW: bounded bug, rounding check, precision test, small config (explicit safe keywords)
        """
        text_combined = (task.text + " " + task.description).lower()
        
        # LOW RISK SAFETY VALVE (0.0-0.2) — only specific bounded cases
        # These are explicit markers of safe, bounded work
        low_risk_keywords = [
            'rounding',
            'precision',
            'dust amount',
            'edge case',
            'boundary',
            'verify test',
            'check error',
            'small',
            'rename',
            'comment',
            'fix typo',
            'add comment',
            'update comment',
            'fix formatting',
            'simple fix',
            'bounded bug',
        ]
        
        for keyword in low_risk_keywords:
            if keyword in text_combined:
                return 0.1  # Very low risk for explicitly bounded work
        
        # HIGH RISK (0.6-0.9) — aggressive detection
        high_risk_keywords = [
            'deployment',
            'migration',
            'upgrade',
            'architecture',
            'implement in the future',
            'full test setup',
            'hardhat',
            'ethers',
            'infra',
            'rewrite',
            'redesign',
            'major refactor',
            'rearchitect',
            'infrastructure',
            'system-wide',
        ]
        
        for keyword in high_risk_keywords:
            if keyword in text_combined:
                return 0.7  # Consistent HIGH (0.6-0.9 range)
        
        # MEDIUM RISK (0.3-0.5) — DEFAULT for everything else
        # Anything with these patterns gets MEDIUM instead of default LOW
        medium_risk_keywords = [
            'refactor',
            'configurable',
            'conditions',
            'complicated',
            'timeout',
            'handle',
            'implement',
            'improve',
            'investigate',
            'integration',
            'integration test',
            'setup',
            'configure',
            'consolidate',
        ]
        
        for keyword in medium_risk_keywords:
            if keyword in text_combined:
                return 0.4  # Consistent MEDIUM (0.3-0.5 range)
        
        # DEFAULT: If no keywords matched, still default to MEDIUM (0.4)
        # This increases caution (as requested) to catch hidden complexity
        return 0.4
    
    def detect_kill_list_candidate(self, task: Task, strategic: float, learning: float, context_tags: set = None) -> bool:
        """
        Detect low-leverage work for elimination.
        
        Kill criteria (ALL must be true):
        - strategic_score <= 4 (not architecturally important)
        - learning <= 0.3 (minimal growth opportunity)
        - no exploit/security relevance
        - matches kill keywords: rename, comment, format, cosmetic, docs
        
        PROTECTION: Never kill tasks tagged as "evidence_support"
        These are critical for proving the exploit exists (test, verify, check results, dust testing).
        
        Returns True if this is kill-list material.
        Prefers false positives (better to kill useful work than optimize mediocre).
        """
        if context_tags is None:
            context_tags = set()
        
        # PROTECT: evidence-supporting tasks are never killed (test, verify, check)
        if "evidence_support" in context_tags:
            return False
        
        text_combined = (task.text + " " + task.description).lower()
        
        # Check if has security/exploit relevance (save from kill)
        protective_keywords = ['security', 'exploit', 'vulnerability', 'breach', 'attack', 'hack']
        for keyword in protective_keywords:
            if keyword in text_combined:
                return False  # Protected from kill list
        
        # Strategic score must be low
        if strategic > 4:
            return False
        
        # Learning must be minimal
        if learning > 0.3:
            return False
        
        # Low-leverage keywords (rename, comments, format, cosmetic, docs)
        kill_keywords = [
            'rename',
            'comment',
            'formatting',
            'cosmetic',
            'doc',
            'readme',
            'typo',
            'whitespace',
            'indentation',
            'style',
            'lint',
            'grammar',
            'spelling',
        ]
        
        for keyword in kill_keywords:
            if keyword in text_combined:
                return True  # Kill it
        
        return False
    
    def classify_task_context(self, task: Task) -> set:
        """
        Classify task context to protect exploit-evidence work.
        
        Returns set of context tags:
        - "exploit_context": file contains "exploit" OR snippet contains "exploit" OR mentions precision/rounding issues
        - "evidence_support": text contains "test", "verify", "check", "dust", "results", "amounts"
        - "maintenance": text contains "rename", "comment", "doc", "deprecated", "style", "formatting"
        - "infra_rabbit": text contains "deploy", "hardhat", "ethers", "migration", "upgrade"
        
        These tags protect tasks from inappropriate kill-listing.
        """
        tags = set()
        text_combined = (task.text + " " + task.description + " " + task.snippet).lower()
        file_path = (task.file + " " + task.source_path).lower()
        
        # Exploit context: file path contains "exploit" OR snippet mentions precision/rounding
        if "exploit" in file_path or "exploit" in text_combined:
            tags.add("exploit_context")
        if "precision" in text_combined or "rounding" in text_combined or "dust" in text_combined:
            tags.add("exploit_context")
        
        # Evidence support: test/verify/check related tasks
        evidence_keywords = ["test", "verify", "check results", "check if", "dust amount", "amounts"]
        for kw in evidence_keywords:
            if kw in text_combined:
                tags.add("evidence_support")
                break
        
        # Maintenance: low-value work that should be deferred
        maintenance_keywords = ["rename", "comment", "doc", "documentation", "deprecated", "style", "formatting", "cosmetic"]
        for kw in maintenance_keywords:
            if kw in text_combined:
                tags.add("maintenance")
                break
        
        # Infrastructure rabbit holes: deployment/migration tasks
        infra_keywords = ["deploy", "hardhat", "ethers", "migration", "upgrade", "integration"]
        for kw in infra_keywords:
            if kw in text_combined:
                tags.add("infra_rabbit")
                break
        
        return tags
    
    def calculate_score(self, task: Task) -> tuple:
        """
        Calculate final priority score with strategic intelligence.
        
        Formula:
            score = (impact * 8) + (strategic * 10) + (learning * 4) + (ev * 3) 
                    - effort - (rabbit_hole_risk * 8) + quick_win_bonus
        
        Kill list detection happens but does NOT affect final score.
        Instead, it flags the task for critical "Why NOT" reasoning.
        
        Returns:
            (final_score, strategic_score, rabbit_hole_risk, is_quick_win, is_kill_list)
        """
        impact = self.estimate_impact(task)
        learning = self.estimate_learning_value(task)
        ev = self.estimate_ev(task)
        effort = self.estimate_effort(task)
        strategic = self.estimate_strategic_score(task)
        rabbit_hole = self.estimate_rabbit_hole_risk(task)
        
        # Core score with strategy as dominant factor
        score = (impact * 8) + (strategic * 10) + (learning * 4) + (ev * 3) - effort
        
        # Penalize rabbit holes heavily
        score -= rabbit_hole * 8
        
        # Quick win bonus: low effort + high impact = momentum boost
        is_quick_win = effort <= 2 and impact >= 0.70
        if is_quick_win:
            score += 15
        
        # Kill list detection: flag for visibility
        # Classify context FIRST (needed for kill list protection)
        context_tags = self.classify_task_context(task)
        is_kill_list = self.detect_kill_list_candidate(task, strategic, learning, context_tags)
        
        return score, strategic, rabbit_hole, is_quick_win, is_kill_list, context_tags
    
    def rank(self, tasks: list[Task], top_n: int = 5) -> list[TaskScore]:
        """
        Rank tasks by priority score using strategic intelligence.
        
        Args:
            tasks: List of Task objects to rank
            top_n: Return top N tasks
        
        Returns:
            Sorted list of TaskScore objects (highest priority first)
        """
        scored: list[TaskScore] = []
        
        for task in tasks:
            score, strategic, rabbit_hole, is_quick_win, is_kill_list, context_tags = self.calculate_score(task)
            impact = self.estimate_impact(task)
            learning = self.estimate_learning_value(task)
            ev = self.estimate_ev(task)
            effort = self.estimate_effort(task)
            
            # Generate human-readable reason
            reasons = []
            if strategic >= 7:
                reasons.append(f"high strategic value ({strategic:.1f}/10)")
            if impact >= 0.8:
                reasons.append(f"high impact ({impact:.2f})")
            if is_quick_win:
                reasons.append("quick win opportunity")
            if ev >= 0.75:
                reasons.append(f"high confidence ({ev:.2f})")
            
            reason = "; ".join(reasons) if reasons else "balanced trade-offs"
            
            # Generate "Why NOT" critical perspective
            why_not_reasons = []
            if is_kill_list:
                why_not_reasons.append("LOW LEVERAGE: Do NOT spend time unless blocking another task")
            if rabbit_hole >= 0.6:
                why_not_reasons.append("HIGH RISK: Multi-day rabbit hole with unclear scope")
            elif rabbit_hole >= 0.4:
                why_not_reasons.append("MEDIUM RISK: Potential scope creep and complexity")
            if strategic <= 3:
                why_not_reasons.append("Does not strengthen architecture")
            if learning <= 0.3:
                why_not_reasons.append("Limited learning opportunity")
            if ev <= 0.5:
                why_not_reasons.append("Uncertain outcome")
            
            why_not = "; ".join(why_not_reasons) if why_not_reasons else "Low-risk, bounded work"
            
            scored.append({
                'task_id': task.task_id,
                'description': task.description,
                'impact': impact,
                'learning_value': learning,
                'ev': ev,
                'effort': effort,
                'strategic_score': strategic,
                'rabbit_hole_risk': rabbit_hole,
                'score': score,
                'reason': reason,
                'file': task.file,
                'line': task.line,
                'text': task.text,
                'snippet': task.snippet,
                'issue_url': task.issue_url,
                'priority': task.metadata.get('priority', 'TODO'),
                'is_quick_win': is_quick_win,
                'is_kill_list': is_kill_list,
                'context_tags': context_tags,
                'why_not': why_not
            })
        
        # Sort by score descending
        ranked = sorted(scored, key=lambda x: x['score'], reverse=True)
        
        return ranked[:top_n]
