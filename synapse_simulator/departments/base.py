"""
Base Department Handler abstract class.
"""

from abc import ABC, abstractmethod
from typing import List
from synapse_simulator.core.event_queue import SimulationEvent
from synapse_simulator.state.models import ActionRequest


class BaseDepartmentHandler(ABC):
    """Abstract base class for departmental event handlers."""

    department_name: str = "base"

    @abstractmethod
    def handle_event(self, event: SimulationEvent) -> List[ActionRequest]:
        """Convert incoming simulation event into actionable domain ActionRequests."""
        pass
