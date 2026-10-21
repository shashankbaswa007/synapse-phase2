"""
Core module initialization for Event-Driven Simulation Engine.
"""

from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.event_queue import SimulationEvent, EventQueue
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.core.interfaces import IClock, IScheduler, IEventQueue, IEventDispatcher

__all__ = [
    "SimulationClock",
    "SimulationEvent",
    "EventQueue",
    "EventDispatcher",
    "IClock",
    "IScheduler",
    "IEventQueue",
    "IEventDispatcher",
]
