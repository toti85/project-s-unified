"""
Observer Module - Detects and monitors developer activity.

Capabilities:
- Scan repository changes (git diff)
- Extract TODO/FIXME annotations
- Read terminal command history
- Pattern detection for repetition
"""

import subprocess
import os
import re
import hashlib
from pathlib import Path
from typing import Optional, TypedDict
from dataclasses import dataclass, asdict, field
from datetime import datetime


class RepoChange(TypedDict):
    """Repository change metadata."""
    file: str
    lines_added: int
    lines_removed: int
    status: str  # 'modified', 'added', 'deleted'


class TodoItem(TypedDict):
    """TODO annotation found in source."""
    file: str
    line: int
    text: str
    priority: str  # 'TODO', 'FIXME'
    snippet: str  # 3 lines before/after context
    task_id: str  # Unique ID with sha1 hash
    issue_url: str  # GitHub/issue tracker URL if present, else empty


class TerminalPattern(TypedDict):
    """Detected pattern in terminal history."""
    command: str
    frequency: int
    last_seen: str


@dataclass
class Task:
    """Task representation for prioritization."""
    task_id: str
    description: str
    source: str  # 'todo', 'change', 'pattern'
    file: str = ""
    line: int = 0
    text: str = ""  # Original TODO/FIXME text
    snippet: str = ""  # Code context (3 lines before/after)
    source_path: str = ""  # Full relative path for filtering
    issue_url: str = ""  # GitHub/issue tracker URL if present
    metadata: dict = field(default_factory=dict)


@dataclass
class Observation:
    """Complete observation snapshot."""
    timestamp: str
    repo_changes: list[RepoChange]
    todos: list[TodoItem]
    terminal_patterns: list[TerminalPattern]
    repo_root: str
    
    def to_dict(self):
        """Convert to serializable dict."""
        return asdict(self)


class Observer:
    """
    Observes developer activity across filesystem, VCS, and terminal.
    Raises no exceptions—logs errors and returns partial data.
    """
    
    def __init__(self, repo_root: str, ignore_dirs: list[str] = None):
        """
        Initialize observer.
        
        Args:
            repo_root: Path to git repository root
            ignore_dirs: List of directory names to exclude from scanning
        """
        self.repo_root = Path(repo_root)
        if not self.repo_root.exists():
            raise ValueError(f"Repo root does not exist: {repo_root}")
        
        # Default directories to ignore
        if ignore_dirs is None:
            ignore_dirs = [
                'organism', '.git', 'venv', 'node_modules', '__pycache__',
                '.pytest_cache', '.venv', 'build', 'dist', '.tox', 'htmlcov',
                '.mypy_cache', '.idea', '.vscode', 'target', '.gradle',
                '.egg-info', '.coverage', '.pytest'
            ]
        self.ignore_dirs = set(ignore_dirs)
    
    def scan_repo_changes(self) -> list[RepoChange]:
        """
        Scan git diff to detect modified files and change counts.
        
        Returns:
            List of RepoChange dicts with file, status, and line counts
        """
        changes: list[RepoChange] = []
        
        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-status"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                status_code = parts[0]
                filepath = parts[1]
                
                # Map status codes
                status_map = {
                    'M': 'modified',
                    'A': 'added',
                    'D': 'deleted',
                    'R': 'renamed',
                    'C': 'copied'
                }
                status = status_map.get(status_code, 'unknown')
                
                # Get line counts via diff
                diff_result = subprocess.run(
                    ["git", "diff", "--unified=0", "--", filepath],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                lines_added = diff_result.stdout.count('\n+') - 1
                lines_removed = diff_result.stdout.count('\n-') - 1
                lines_added = max(0, lines_added)
                lines_removed = max(0, lines_removed)
                
                changes.append({
                    'file': filepath,
                    'lines_added': lines_added,
                    'lines_removed': lines_removed,
                    'status': status
                })
        
        except subprocess.TimeoutExpired:
            pass  # Return partial results
        except Exception:
            pass  # Return partial results
        
        return changes
    
    def extract_todos(self) -> list[TodoItem]:
        """
        Scan source files for TODO/FIXME annotations in actual code comments only.
        
        Matches:
        - Python comments: lines starting with '#'
        - JavaScript/TypeScript/Solidity: lines starting with '//'
        - NOT docstrings or plain text
        
        Also extracts issue URLs from comment text (e.g., github.com/owner/repo/issues/123)
        
        Returns:
            List of TodoItem dicts with file, line, text, priority, snippet, task_id, issue_url
        """
        todos: list[TodoItem] = []
        
        # File extensions to scan
        scan_extensions = {'.py', '.lua', '.ts', '.js', '.sol', '.tsx', '.jsx'}
        
        # Regex to extract issue URLs
        issue_url_pattern = re.compile(r'(https?://[^\s]+/issues/\d+)')
        
        try:
            # Scan repo root, but skip ignored directories
            for filepath in self.repo_root.rglob('*'):
                # Skip ignored directories
                if any(ignored in filepath.parts for ignored in self.ignore_dirs):
                    continue
                
                if not filepath.is_file() or filepath.suffix not in scan_extensions:
                    continue
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for line_num, line_text in enumerate(lines, 1):
                        # Only match actual code comments (anchored to line start, after whitespace)
                        # Python format: ^(\s*)#\s*(TODO|FIXME)
                        # JavaScript format: ^(\s*)//(TODO|FIXME)
                        
                        # Strip leading whitespace to check for comment start
                        stripped = line_text.lstrip()
                        
                        # Check if line is a Python comment with TODO/FIXME
                        py_match = None
                        js_match = None
                        
                        if stripped.startswith('#'):
                            py_match = re.match(r'#\s*(TODO|FIXME)[:\s]+(.*?)(?:\s*$)', stripped)
                        
                        # Check if line is a JavaScript/Solidity comment with TODO/FIXME
                        if stripped.startswith('//'):
                            js_match = re.match(r'//\s*(TODO|FIXME)[:\s]+(.*?)(?:\s*$)', stripped)
                        
                        match = py_match or js_match
                        if not match:
                            continue
                        
                        priority = match.group(1)  # 'TODO' or 'FIXME'
                        comment_text = match.group(2).strip()
                        
                        # Extract issue URL from comment text
                        issue_url = ""
                        url_match = issue_url_pattern.search(comment_text)
                        if url_match:
                            issue_url = url_match.group(1)
                        
                        # Extract snippet (3 lines before/after)
                        snippet_start = max(0, line_num - 4)
                        snippet_end = min(len(lines), line_num + 3)
                        snippet_lines = [
                            f"{i}: {lines[i-1].rstrip()}"
                            for i in range(snippet_start + 1, snippet_end + 1)
                        ]
                        snippet = "\n".join(snippet_lines)
                        
                        # Generate unique task ID with sha1 hash
                        hash_input = f"{filepath.name}:{line_num}:{comment_text}"
                        text_hash = hashlib.sha1(hash_input.encode()).hexdigest()[:8]
                        task_id = f"{priority.lower()}:{filepath.name}:{line_num}:{text_hash}"
                        
                        todos.append({
                            'file': str(filepath.relative_to(self.repo_root)),
                            'line': line_num,
                            'text': comment_text,
                            'priority': priority,
                            'snippet': snippet,
                            'task_id': task_id,
                            'issue_url': issue_url
                        })
                except Exception:
                    pass
        
        except Exception:
            pass
        
        return todos
    
    def read_terminal_history(self, max_commands: int = 50) -> list[TerminalPattern]:
        """
        Extract patterns from terminal command history.
        
        On Windows, tries to read PowerShell history.
        Returns frequency of repeated commands.
        
        Args:
            max_commands: Maximum commands to analyze
        
        Returns:
            List of TerminalPattern dicts sorted by frequency
        """
        patterns: list[TerminalPattern] = []
        
        try:
            # Windows PowerShell history location
            history_file = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt"
            
            if not history_file.exists():
                return []
            
            with open(history_file, 'r', encoding='utf-8', errors='ignore') as f:
                commands = [line.strip() for line in f.readlines() if line.strip()]
            
            # Get last N commands
            recent = commands[-max_commands:]
            
            # Count frequencies
            freq_map = {}
            for cmd in recent:
                # Normalize command (first word only for grouping)
                first_word = cmd.split()[0] if cmd else ""
                if first_word:
                    freq_map[first_word] = freq_map.get(first_word, 0) + 1
            
            # Build patterns for frequently repeated commands
            for cmd, count in sorted(freq_map.items(), key=lambda x: x[1], reverse=True):
                if count >= 2:  # Only report repeated commands
                    patterns.append({
                        'command': cmd,
                        'frequency': count,
                        'last_seen': datetime.now().isoformat()
                    })
        
        except Exception:
            pass  # Return partial results
        
        return patterns
    
    def observe(self) -> Observation:
        """
        Execute complete observation pass.
        
        Returns:
            Observation dict with all detected activity
        """
        return Observation(
            timestamp=datetime.now().isoformat(),
            repo_changes=self.scan_repo_changes(),
            todos=self.extract_todos(),
            terminal_patterns=self.read_terminal_history(),
            repo_root=str(self.repo_root)
        )
