"""
Simulator configuration settings.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field


class SimulatorSettings(BaseModel):
    project_name: str = "SYNAPSE Synthetic Hospital Simulator"
    version: str = "1.0.0"
    environment: str = Field(default_factory=lambda: os.getenv("SYNAPSE_ENV", "development"))
    rules_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "config" / "rules")
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/synapse_v1"))
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    default_random_seed: int = 42
    outbox_batch_size: int = 500
    max_causation_depth: int = 10


settings = SimulatorSettings()
