"""
Simulation Clock: Manages simulated time progression and timestamping.
"""

from datetime import datetime, timedelta
from typing import Optional


class SimulationClock:
    """Manages virtual simulation time advancement."""

    def __init__(self, start_time: Optional[datetime] = None):
        self._current_time: datetime = start_time or datetime(2026, 1, 1, 8, 0, 0)

    @property
    def current_time(self) -> datetime:
        return self._current_time

    def now(self) -> datetime:
        return self._current_time

    def advance_to(self, target_time: datetime) -> datetime:
        """Advance clock to specified datetime (must be >= current_time)."""
        if target_time < self._current_time:
            raise ValueError(f"Cannot rewind simulation clock from {self._current_time} to {target_time}")
        self._current_time = target_time
        return self._current_time

    def advance_by_seconds(self, seconds: float) -> datetime:
        """Advance clock by N seconds."""
        if seconds < 0:
            raise ValueError("Time step must be non-negative")
        self._current_time += timedelta(seconds=seconds)
        return self._current_time

    def advance_by_minutes(self, minutes: float) -> datetime:
        """Advance clock by N minutes."""
        return self.advance_by_seconds(minutes * 60)
