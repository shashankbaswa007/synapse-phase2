"""
Data Exporter: Serializes simulation transactions, state snapshots, and telemetry to files.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


class DataExporter:
    """Exports synthetic hospital simulation results to JSON/CSV files."""

    @staticmethod
    def export_to_json(output_dir: Path, summary_data: Dict[str, Any], filename: str = "simulation_summary.json") -> Path:
        """Export simulation metrics and state snapshots to a JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, default=str)

        return file_path
