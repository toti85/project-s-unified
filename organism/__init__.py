"""Dev Organism - Living development environment for Project-S-LIVE."""

from .core.loop import DevOrganism
from .core.observer import Observer, Observation
from .core.prioritizer import PriorityEngine, TaskScore
from .core.proposer import Proposer
from .modules.taste_model import TasteModel, Decision
from .ui.dashboard import Dashboard

__version__ = "0.1.0"
__all__ = [
    "DevOrganism",
    "Observer",
    "Observation",
    "PriorityEngine",
    "TaskScore",
    "Proposer",
    "TasteModel",
    "Decision",
    "Dashboard",
]
