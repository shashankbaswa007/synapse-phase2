"""
Department Handlers Module.

Provides modular lifecycle handlers for hospital departmental domains:
clinical encounters, finance/billing, laboratory testing, pharmacy, and radiology.
"""

from synapse_simulator.departments.base import BaseDepartmentHandler
from synapse_simulator.departments.clinical import ClinicalDepartmentHandler
from synapse_simulator.departments.finance import FinanceDepartmentHandler
from synapse_simulator.departments.laboratory import LaboratoryDepartmentHandler
from synapse_simulator.departments.pharmacy import PharmacyDepartmentHandler
from synapse_simulator.departments.radiology import RadiologyDepartmentHandler

__all__ = [
    "BaseDepartmentHandler",
    "ClinicalDepartmentHandler",
    "FinanceDepartmentHandler",
    "LaboratoryDepartmentHandler",
    "PharmacyDepartmentHandler",
    "RadiologyDepartmentHandler",
]

