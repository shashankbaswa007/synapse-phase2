"""
Base Scenario definition class.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Tuple
from synapse_simulator.core.event_queue import SimulationEvent, EventQueue
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.core.ids import new_id


class BaseScenario(ABC):
    """Abstract base class for scenario setup and initial state generation."""

    scenario_id: str = "SCEN-BASE"
    name: str = "Base Scenario"
    description: str = ""

    def __init__(self, instance_index: int = 1):
        self.scenario_instance_id = new_id(f"{self.scenario_id}-inst-{instance_index}-", 6)
        self.patient_journey_id = new_id("pj-", 8)
        self.correlation_id = new_id("corr-", 8)
        self.patient_id = new_id("pat-", 8)
        self.appointment_id = new_id("apt-", 8)
        self.prescription_id = new_id("rx-", 8)
        self.batch_id = new_id("batch-", 8)
        self.lab_order_id = new_id("lab-", 8)
        self.rad_order_id = new_id("rad-", 8)
        self.invoice_id = f"inv-{self.patient_journey_id[3:]}"

    @abstractmethod
    def setup_initial_state(self, state_manager: StateManager) -> None:
        """Initialize required entity state snapshots in StateManager."""
        pass

    @abstractmethod
    def generate_initial_events(self, start_time: datetime) -> SimulationEvent:
        """Create entry-point simulation event to trigger scenario execution."""
        pass

    def create_patient_profile(self, patient_gen: Any) -> Any:
        """Create patient profile using generator (polymorphically overridden by scenario subclasses)."""
        return patient_gen.generate_patient()

    def should_force_conflict(self) -> bool:
        """Whether this scenario intentionally forces a clinical conflict (LSP hook)."""
        return False
