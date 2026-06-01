#!/usr/bin/env python3
"""
Dev Organism Quick Start

This script demonstrates how to use the Dev Organism system.
"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from organism.core.loop import DevOrganism
from organism.core.observer import Observer
from organism.ui.dashboard import Dashboard


def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║          DEV ORGANISM - Project-S-LIVE Research Fork           ║
║                                                                ║
║   A living development environment that OBSERVES, PRIORITIZES ║
║   TASKS, and PROPOSES actions. Explicit human approval only.  ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize the organism
    repo_root = str(project_root)
    evidence_dir = str(project_root / 'organism' / 'evidence')

    # --- RISK_003 fix: bővített ignore_dirs scope-szűréshez ---
    # Observer default ignore_dirs (observer.py-ból másolva, nem módosítva)
    default_ignores = [
        'organism', '.git', 'venv', 'node_modules', '__pycache__',
        '.pytest_cache', '.venv', 'build', 'dist', '.tox', 'htmlcov',
        '.mypy_cache', '.idea', '.vscode', 'target', '.gradle',
        '.egg-info', '.coverage', '.pytest',
    ]
    # Külső repók — nem a Project-S része, false positive-ok forrása
    external_repos = [
        'tbtc-v2',
        'fluid-solana-programs',
        'tbtc-hunt',
        'bounty',
        'rujira-bounty',
    ]
    # Adat / log mappák + archív kód — szintén false positive-ok forrása
    noise_dirs = [
        'memory',        # jsonl logok
        'logs',          # szöveges logok
        'pending_goals', # bridge kimenet
        'archiv',        # archív Project-S kód (docs/archiv/)
        'archive',       # alternatív elnevezés (memory/state/archive/)
        '_old',          # legacy mintázat
        '_deprecated',   # explicit deprecation
        'backup',        # backup mappák
        'backups',       # backup mappák (plural)
    ]
    all_ignore_dirs = default_ignores + external_repos + noise_dirs

    organism = DevOrganism(repo_root, evidence_dir)
    # Observer újrapéldányosítása a bővített ignore_dirs listával
    # (DevOrganism konstruktora nem fogad ignore_dirs paramétert)
    organism.observer = Observer(repo_root, ignore_dirs=all_ignore_dirs)
    # --- RISK_003 fix vége ---
    
    print("\n[1/3] Running observation cycle...\n")
    result = organism.run_once(top_n=5)
    
    print("\n" + "="*65)
    print(f"✓ {result['tasks_collected']} tasks collected")
    print(f"✓ {len(result['top_proposals'])} proposals generated")
    print(f"\nProposals saved to: {result['proposals_file']}")
    print("="*65)
    
    if result['top_proposals']:
        print("\nTop 5 Prioritized Tasks:\n")
        for idx, task in enumerate(result['top_proposals'], 1):
            print(f"[{idx}] {task['description'][:70]}")
            print(f"    Score: {task['score']:.1f} | {task['reason']}")
            print()
    
    print("\nNext steps:")
    print("  1. Review proposals: cat organism/evidence/top_proposals.md")
    print("  2. Approve a task:   python -m organism.core.loop --approve <task_id>")
    print("  3. Launch dashboard: python -m organism.ui.dashboard .")
    print("     Then open: http://localhost:8765")
    print()


if __name__ == '__main__':
    main()
