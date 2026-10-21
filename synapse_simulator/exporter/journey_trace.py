"""
Journey Trace Formatter: Produces human-readable causal execution traces for Patient Journeys.
"""

from typing import Dict, Any, List
from synapse_simulator.workflows.model import PatientJourney


class JourneyTraceFormatter:
    """Formats PatientJourney execution data into human-readable causal traces."""

    @staticmethod
    def format_journey_trace(journey: PatientJourney) -> str:
        lines = []
        lines.append("=================================================================")
        lines.append(f" PATIENT JOURNEY TRACE: {journey.journey_id}")
        lines.append("=================================================================")
        lines.append(f" Patient ID    : {journey.patient_id}")
        lines.append(f" Scenario ID   : {journey.scenario_id}")
        lines.append(f" Status        : {journey.status}")
        lines.append(f" Start Time    : {journey.start_time.isoformat()}")
        lines.append(f" End Time      : {journey.end_time.isoformat() if journey.end_time else 'Active'}")
        lines.append(f" Final Outcome : {journey.outcome}")
        lines.append("-----------------------------------------------------------------")
        lines.append(" Causal Step History:")
        lines.append("-----------------------------------------------------------------")

        for idx, step in enumerate(journey.trace_history, 1):
            lines.append(
                f" [{idx}] Time: {step.get('timestamp')} | Step: {step.get('step_id')} | "
                f"Action: {step.get('action_type')} | Rule: {step.get('rule')} | "
                f"Status: {step.get('status')} | Domain Event: {step.get('event_type')}"
            )

        lines.append("=================================================================\n")
        return "\n".join(lines)
