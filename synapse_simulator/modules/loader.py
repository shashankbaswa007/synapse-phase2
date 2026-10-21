"""
Clinical module loader.
"""

from pathlib import Path
from typing import Dict, List
import yaml

from synapse_simulator.modules.models import ClinicalModule


def load_clinical_module(module_path: Path) -> ClinicalModule:
    """Load and validate a ClinicalModule YAML file."""
    if not module_path.exists():
        raise FileNotFoundError(f"Module file not found at {module_path}")

    with open(module_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    if not isinstance(raw_data, dict):
        raise ValueError(f"Invalid YAML in {module_path}: expected dictionary root")

    return ClinicalModule.model_validate(raw_data)


def load_all_clinical_modules(modules_dir: Path) -> List[ClinicalModule]:
    """Scan a directory and load all clinical module YAMLs."""
    modules = []
    if not modules_dir.exists():
        return modules

    for path in sorted(modules_dir.glob("*.yaml")):
        modules.append(load_clinical_module(path))
    return modules
