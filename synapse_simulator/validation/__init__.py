"""
Validation package for SYNAPSE Phase 2.
Provides dataset auditing, referential integrity verification, population sanity checks,
and the mandatory fail-fast publication validation gate.
"""

from synapse_simulator.validation.dataset_auditor import DatasetAuditor
from synapse_simulator.validation.validation_gate import (
    DatasetValidationGate,
    DatasetValidationError,
    GateResult,
)
from synapse_simulator.validation.integrity_auditor import IntegrityAuditor
from synapse_simulator.validation.consistency_checker import ConsistencyChecker
from synapse_simulator.validation.population_validator import PopulationValidator
from synapse_simulator.validation.document_validator import DocumentValidator

__all__ = [
    "DatasetAuditor",
    "DatasetValidationGate",
    "DatasetValidationError",
    "GateResult",
    "IntegrityAuditor",
    "ConsistencyChecker",
    "PopulationValidator",
    "DocumentValidator",
]
