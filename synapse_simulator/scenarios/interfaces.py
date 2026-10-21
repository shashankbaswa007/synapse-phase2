"""
Scenario Protocols: Defines contracts for polymorphic scenario execution and profile hooks (LSP).
"""

from typing import Protocol, runtime_checkable, Any
from datetime import datetime
from synapse_simulator.core.event_queue import SimulationEvent


@runtime_checkable
class IScenarioProfileHook(Protocol):
    """Protocol for scenario-level profile customization and initial state setup."""

    scenario_id: str

    def create_patient_profile(self, patient_gen: Any) -> Any:
        ...

    def should_force_conflict(self) -> bool:
        ...

    def setup_initial_state(self, state_manager: Any) -> None:
        ...

    def generate_initial_events(self, start_time: datetime) -> SimulationEvent:
        ...
