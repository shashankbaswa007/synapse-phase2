"""
Rule Repository: Loads YAML rule files and indexes SynapseRule objects in memory.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml
from synapse_simulator.rules.models import SynapseRule


class RuleRepository:
    """Loads, validates, and indexes rules from YAML files."""

    def __init__(self, rules_directory: Optional[Path] = None):
        self.rules_directory = rules_directory or Path(__file__).parent.parent.parent / "config" / "rules"
        self.rules: Dict[str, SynapseRule] = {}
        # In-memory index: action_type -> List[SynapseRule]
        self._action_index: Dict[str, List[SynapseRule]] = {}

    def load_rules(self) -> int:
        """Scan directory recursively and load all YAML rule files."""
        self.rules.clear()
        self._action_index.clear()

        if not self.rules_directory.exists():
            return 0

        for root, _, files in os.walk(self.rules_directory):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    file_path = Path(root) / file
                    self._load_yaml_file(file_path)

        self._build_indexes()
        return len(self.rules)

    def register_rule(self, rule: SynapseRule) -> None:
        """Register a single rule in memory."""
        self.rules[rule.rule_id] = rule
        self._index_single_rule(rule)

    def get_rule_by_id(self, rule_id: str) -> Optional[SynapseRule]:
        return self.rules.get(rule_id)

    def find_applicable_rules(self, action_type: str, department_id: str, scenario_id: str) -> List[SynapseRule]:
        """Find candidate rules matching action_type, department, and scenario."""
        candidates = self._action_index.get(action_type, []) + self._action_index.get("*", [])
        matching_rules = []

        for rule in candidates:
            # Check department scope (if empty, matches all)
            if rule.departments and department_id not in rule.departments and "*" not in rule.departments:
                continue
            # Check scenario scope (if empty, matches all)
            if rule.scenarios and scenario_id not in rule.scenarios and "*" not in rule.scenarios:
                continue
            matching_rules.append(rule)

        return matching_rules

    def _load_yaml_file(self, file_path: Path) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    return

                # Support single rule or list of rules per YAML file
                rule_list = data if isinstance(data, list) else [data]
                for item in rule_list:
                    rule = SynapseRule.model_validate(item)
                    self.rules[rule.rule_id] = rule
        except Exception as e:
            print(f"Warning: Failed to load rule file {file_path}: {e}")

    def _build_indexes(self) -> None:
        for rule in self.rules.values():
            self._index_single_rule(rule)

    def _index_single_rule(self, rule: SynapseRule) -> None:
        action_type = rule.preconditions.action_type or "*"
        if action_type not in self._action_index:
            self._action_index[action_type] = []
        if rule not in self._action_index[action_type]:
            self._action_index[action_type].append(rule)
