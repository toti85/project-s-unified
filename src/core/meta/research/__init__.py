"""
Bug Bounty Research Pipeline - Uses Meta Layer for research orchestration.
No new architecture. No real hacking tools. Pure research workflow via MetaController.
"""

from .research_goal import ResearchGoal
from .research_state import ResearchState
from .research_loop import ResearchLoop, ResearchResult

__all__ = [
    "ResearchGoal",
    "ResearchState",
    "ResearchLoop",
    "ResearchResult",
]
