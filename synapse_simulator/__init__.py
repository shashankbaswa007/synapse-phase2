"""
SYNAPSE Phase 2 — Synthea-Inspired Longitudinal Synthetic Healthcare Simulation System.

Provides an agentic, longitudinal healthcare data generation and patient trajectory
simulation engine tailored to Indian demographic, clinical, and epidemiological characteristics.

Canonical Entry Points:
    - ExperimentRunner: Programmatic coordinator for longitudinal cohort generation and evaluation.
    - ClinicalModuleRunner: Executes declarative YAML disease state machines over time.
    - DatasetAuditor: Structural and referential integrity auditor for exported CSV datasets.
    - DatasetEvaluator: Quantitative clinical and demographic fidelity evaluator.
    - DatasetValidationGate: Enforces fail-fast validation before promoting datasets to publication.
    - CSVExporter: Serializes validated in-memory simulation entities to normalized relational CSVs.
"""

__version__ = "2.0.0"

from synapse_simulator.evaluation.experiment import (
    ExperimentRunner,
    ExperimentConfig,
)
from synapse_simulator.modules.engine import ClinicalModuleRunner
from synapse_simulator.modules.loader import load_clinical_module
from synapse_simulator.population.loader import (
    load_population_profile,
    PopulationSampler,
)
from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
from synapse_simulator.exporter.csv_exporter import CSVExporter
from synapse_simulator.validation.dataset_auditor import DatasetAuditor
from synapse_simulator.validation.validation_gate import DatasetValidationGate
from synapse_simulator.evaluation.evaluator import DatasetEvaluator

# Legacy hospital operational prototype
from synapse_simulator.generator.hospital_generator import HospitalSimulator

__all__ = [
    "__version__",
    "ExperimentRunner",
    "ExperimentConfig",
    "ClinicalModuleRunner",
    "load_clinical_module",
    "load_population_profile",
    "PopulationSampler",
    "PatientProfileGenerator",
    "CSVExporter",
    "DatasetAuditor",
    "DatasetValidationGate",
    "DatasetEvaluator",
    "HospitalSimulator",
]
