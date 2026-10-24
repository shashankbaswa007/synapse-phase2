"""
Generator module initialization.

NOTE: HospitalSimulator is retained here for legacy compatibility mode (--mode hospital).
The canonical Phase 2 longitudinal simulation pipeline is executed via ExperimentRunner
(synapse_simulator.evaluation.experiment).
"""

from synapse_simulator.generator.hospital_generator import HospitalSimulator

__all__ = ["HospitalSimulator"]
