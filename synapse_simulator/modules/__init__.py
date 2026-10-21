"""
Clinical Module Framework for SYNAPSE Phase 2.
Implements Synthea Generic Module Framework with 7 control states, 11 clinical states,
and 4 transition types, fully integrated with discrete-event scheduling.
"""

from synapse_simulator.modules.models import (
    ClinicalModule,
    ControlType,
    ClinicalType,
    TransitionType,
)
from synapse_simulator.modules.engine import ClinicalModuleRunner

__all__ = [
    "ClinicalModule",
    "ControlType",
    "ClinicalType",
    "TransitionType",
    "ClinicalModuleRunner",
]
