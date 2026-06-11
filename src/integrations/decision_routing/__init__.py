"""
Decision Routing - True Golden Age Advanced Decision Router
-----------------------------------------------------------
"""

try:
    from .base_router import router_registry, DecisionRouterRegistry, BaseDecisionRouter, DecisionResult, DecisionType, DecisionStatus
    from .advanced_router import AdvancedDecisionRouter
    ADVANCED_DECISION_ROUTER_AVAILABLE = True
except ImportError as e:
    ADVANCED_DECISION_ROUTER_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Advanced decision router not available: {e}")

__all__ = [
    "ADVANCED_DECISION_ROUTER_AVAILABLE",
    "router_registry",
    "DecisionRouterRegistry",
    "AdvancedDecisionRouter",
    "BaseDecisionRouter",
    "DecisionResult",
    "DecisionType",
    "DecisionStatus"
]

# Bootstrap: register AdvancedDecisionRouter in the global registry
if ADVANCED_DECISION_ROUTER_AVAILABLE:
    _router_instance = AdvancedDecisionRouter()
    router_registry.register_router(_router_instance, is_default=True)
