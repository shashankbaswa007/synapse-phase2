"""
Pydantic data models for Stage 9 Document Metadata and Statuses.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PRESCRIPTION = "Prescription"
    INVOICE = "Invoice"
    LAB_REPORT = "LabReport"
    RAD_REPORT = "RadReport"
    DISCHARGE_SUMMARY = "DischargeSummary"


class DocumentStatus(str, Enum):
    FINAL = "FINAL"
    REVISED = "REVISED"
    CANCELLED = "CANCELLED"


class DocumentMetadata(BaseModel):
    """Authority metadata for a single generated hospital document."""
    document_id: str
    document_type: DocumentType
    patient_id: str
    patient_journey_id: str
    scenario_id: str
    source_entity_table: str
    source_entity_id: str
    source_action_id: str
    source_event_id: str
    created_at: datetime
    document_version: str = "1.0.0"
    document_status: DocumentStatus = DocumentStatus.FINAL
    file_path: str
    checksum: str
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
