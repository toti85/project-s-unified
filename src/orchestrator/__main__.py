"""
__main__.py — Allow running orchestrator as a module

Usage:
    python -m orchestrator.cli --help
    python -m orchestrator.cli list-runs
    python -m orchestrator.cli status
    python -m orchestrator.cli run-loop --auto --max-iterations 2
"""

from .cli import main

if __name__ == "__main__":
    main()