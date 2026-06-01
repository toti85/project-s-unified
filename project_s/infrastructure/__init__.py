"""
Project-S Infrastructure Module

Provides infrastructure management capabilities including server control
via HPE iLO 4 Redfish API.
"""

from .ilo_controller import ILOController

__all__ = ["ILOController"]
