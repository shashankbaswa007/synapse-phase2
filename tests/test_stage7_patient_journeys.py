"""
Stage 7 Integration Test: 10-Patient Small-Scale Validation with Readable Journey Traces.
"""

from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.exporter.journey_trace import JourneyTraceFormatter


def test_ten_patient_small_scale_validation():
    sim = HospitalSimulator(random_seed=42)
    sim.spawn_patients(patient_count=10)

    metrics = sim.run(max_events=500)

    assert metrics["total_patients"] == 10
    assert metrics["decisions_allowed"] > 0
    assert metrics["decisions_blocked"] > 0
    assert len(sim.journeys) == 10

    # Print trace output for several journeys to demonstrate end-to-end correctness
    print("\n" + JourneyTraceFormatter.format_journey_trace(sim.journeys[0]))
    print("\n" + JourneyTraceFormatter.format_journey_trace(sim.journeys[2]))

    # Verify no orphan records (every journey has non-empty trace history)
    for j in sim.journeys:
        assert len(j.trace_history) > 0
