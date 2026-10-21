"""
Master Data Generator: Generates hospital reference data (departments, staff, rooms, inventory).
Runs ONCE per simulation run. All patient journeys reference this shared master data.
"""

import uuid
import random
from typing import List, Optional
from datetime import datetime, timedelta

from faker import Faker

from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.knowledge.models import MasterDataConfig
from synapse_simulator.datagen.models import (
    StaffProfile,
    RoomRecord,
    InventorySnapshot,
    MasterDataSnapshot,
)
from synapse_simulator.state.state_manager import StateManager


class MasterDataGenerator:
    """Generates deterministic hospital master data from configuration."""

    def __init__(self, knowledge_base: MedicalKnowledgeBase, rng: random.Random):
        self.kb = knowledge_base
        self.rng = rng
        self.fake = Faker()
        Faker.seed(rng.randint(0, 2**31))
        self.config: MasterDataConfig = knowledge_base.master_data_config

    def generate(self) -> MasterDataSnapshot:
        """Generate complete master data snapshot."""
        snapshot = MasterDataSnapshot()

        # 1. Generate departments (directly from config, they are reference data)
        for dept in self.config.departments:
            snapshot.departments.append({
                "department_id": dept.id,
                "name": dept.name,
                "type": dept.type,
                "floor": dept.floor,
            })

        # 2. Generate staff
        staff = self._generate_staff()
        snapshot.staff = staff
        snapshot.doctors = [s for s in staff if s.role == "doctor"]
        snapshot.pharmacists = [s for s in staff if s.role == "pharmacist"]
        snapshot.lab_technicians = [s for s in staff if s.role in ("lab_technician", "pathologist")]

        # 3. Generate rooms
        snapshot.rooms = self._generate_rooms()

        # 4. Generate initial inventory batches
        snapshot.inventory = self._generate_inventory()
        snapshot.drug_batch_index = {inv.drug_name: inv.batch_id for inv in snapshot.inventory}

        return snapshot

    def seed_state_manager(self, state_manager: StateManager, snapshot: MasterDataSnapshot) -> None:
        """Seed StateManager with generated master data inventory batches."""
        for inv in snapshot.inventory:
            state_manager.set_entity_state(
                "pharmacy.inventory_batches",
                inv.batch_id,
                {
                    "batch_id": inv.batch_id,
                    "drug_name": inv.drug_name,
                    "drug_class": inv.drug_class,
                    "quantity_available": inv.quantity_available,
                    "quantity_initial": inv.quantity_initial,
                    "unit_cost": inv.unit_cost,
                    "status": inv.status,
                },
            )

    def _generate_staff(self) -> List[StaffProfile]:
        """Generate staff profiles from department config."""
        staff: List[StaffProfile] = []
        specializations = self.config.specializations or ["General Medicine"]

        for dept in self.config.departments:
            sc = dept.staff

            # Doctors
            for i in range(sc.doctors):
                staff.append(StaffProfile(
                    staff_id=f"doc-{dept.id.lower()}-{i+1:03d}",
                    name=f"Dr. {self.fake.last_name()}",
                    role="doctor",
                    department_id=dept.id,
                    specialization=self.rng.choice(specializations),
                    qualification="MBBS, MD",
                ))

            # Nurses
            for i in range(sc.nurses):
                staff.append(StaffProfile(
                    staff_id=f"nur-{dept.id.lower()}-{i+1:03d}",
                    name=self.fake.name(),
                    role="nurse",
                    department_id=dept.id,
                    qualification="BSc Nursing",
                ))

            # Pharmacists
            for i in range(sc.pharmacists):
                staff.append(StaffProfile(
                    staff_id=f"phm-{dept.id.lower()}-{i+1:03d}",
                    name=f"Phm. {self.fake.last_name()}",
                    role="pharmacist",
                    department_id=dept.id,
                    qualification="B.Pharm",
                ))

            # Lab technicians
            for i in range(sc.lab_technicians):
                staff.append(StaffProfile(
                    staff_id=f"lab-{dept.id.lower()}-{i+1:03d}",
                    name=self.fake.name(),
                    role="lab_technician",
                    department_id=dept.id,
                    qualification="DMLT",
                ))

            # Pathologists
            for i in range(sc.pathologists):
                staff.append(StaffProfile(
                    staff_id=f"path-{dept.id.lower()}-{i+1:03d}",
                    name=f"Dr. {self.fake.last_name()}",
                    role="pathologist",
                    department_id=dept.id,
                    qualification="MD Pathology",
                ))

            # Radiologists
            for i in range(sc.radiologists):
                staff.append(StaffProfile(
                    staff_id=f"rad-{dept.id.lower()}-{i+1:03d}",
                    name=f"Dr. {self.fake.last_name()}",
                    role="radiologist",
                    department_id=dept.id,
                    qualification="MD Radiology",
                ))

            # Rad technicians
            for i in range(sc.rad_technicians):
                staff.append(StaffProfile(
                    staff_id=f"radt-{dept.id.lower()}-{i+1:03d}",
                    name=self.fake.name(),
                    role="rad_technician",
                    department_id=dept.id,
                    qualification="B.Sc Radiology",
                ))

            # Billing clerks
            for i in range(sc.billing_clerks):
                staff.append(StaffProfile(
                    staff_id=f"fin-{dept.id.lower()}-{i+1:03d}",
                    name=self.fake.name(),
                    role="billing_clerk",
                    department_id=dept.id,
                    qualification="B.Com",
                ))

        return staff

    def _generate_rooms(self) -> List[RoomRecord]:
        """Generate room records from department config."""
        rooms: List[RoomRecord] = []
        for dept in self.config.departments:
            for i in range(dept.rooms.count):
                rooms.append(RoomRecord(
                    room_id=f"{dept.rooms.prefix}-{i+1:03d}",
                    room_name=f"{dept.name} Room {i+1}",
                    department_id=dept.id,
                    floor=dept.floor,
                    room_type="consultation" if dept.type == "clinical" else dept.type,
                ))
        return rooms

    def _generate_inventory(self) -> List[InventorySnapshot]:
        """Generate initial inventory batches from config."""
        batches: List[InventorySnapshot] = []
        for inv_cfg in self.config.initial_inventory:
            batches.append(InventorySnapshot(
                batch_id=f"batch-{inv_cfg.drug_name.lower().replace(' ', '_')}-{uuid.uuid4().hex[:6]}",
                drug_name=inv_cfg.drug_name,
                drug_class=inv_cfg.drug_class,
                quantity_available=inv_cfg.batch_quantity,
                quantity_initial=inv_cfg.batch_quantity,
                unit_cost=inv_cfg.unit_cost,
                status="Active",
            ))
        return batches
