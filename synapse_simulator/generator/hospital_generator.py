"""
Legacy Discrete-Event Hospital Operational Simulator Engine (Stage 7 Workflow Integration).

NOTE: Retained for backward compatibility mode (`generate_synthetic_data.py --mode hospital`)
and historical regression testing.
The canonical Phase 2 active system is the Synthea-inspired longitudinal population
simulator executed via ExperimentRunner (synapse_simulator.evaluation.experiment).
"""

import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.scheduler import FutureActionScheduler
from synapse_simulator.core.event_queue import EventQueue, SimulationEvent
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.engine.orchestrator import ExecutionPipeline
from synapse_simulator.core.simulation_engine import SimulationEngine
from synapse_simulator.state.models import DecisionStatus

from synapse_simulator.workflows.model import PatientJourney, JourneyStatus
from synapse_simulator.workflows.coordinator import WorkflowCoordinator
from synapse_simulator.workflows.templates import get_all_scenario_workflows

from synapse_simulator.departments.clinical import ClinicalDepartmentHandler
from synapse_simulator.departments.pharmacy import PharmacyDepartmentHandler
from synapse_simulator.departments.laboratory import LaboratoryDepartmentHandler
from synapse_simulator.departments.radiology import RadiologyDepartmentHandler
from synapse_simulator.departments.finance import FinanceDepartmentHandler

from synapse_simulator.scenarios.scen_v1_01_opd import OutpatientRoutineScenario
from synapse_simulator.scenarios.scen_v1_02_diagnostic import DiagnosticInvestigationScenario
from synapse_simulator.scenarios.scen_v1_03_allergy import DrugAllergySafetyHoldScenario
from synapse_simulator.scenarios.scen_v1_04_inventory import InventoryDepletionScenario

from synapse_simulator.knowledge.loader import MedicalKnowledgeBase
from synapse_simulator.datagen.master_data import MasterDataGenerator
from synapse_simulator.datagen.patient_generator import PatientProfileGenerator
from synapse_simulator.datagen.clinical_generator import ClinicalEntityGenerator
from synapse_simulator.datagen.diagnostic_generator import DiagnosticGenerator
from synapse_simulator.datagen.billing_generator import BillingGenerator
from synapse_simulator.datagen.models import PatientContext
from synapse_simulator.generator.factory import SimulationBootstrapFactory
from synapse_simulator.core.ids import new_id


class HospitalSimulator:
    """Orchestrates workflow-driven synthetic hospital patient journeys and cross-department execution."""

    def __init__(
        self,
        random_seed: int = 42,
        start_time: Optional[datetime] = None,
        enable_pubmed: bool = True,
        pubmed_store_dir: Optional[Any] = None,
        offline_mode: bool = True,
    ):
        # Delegate component instantiation and wiring to SimulationBootstrapFactory (SRP/DIP)
        SimulationBootstrapFactory.bootstrap(
            sim=self,
            random_seed=random_seed,
            start_time=start_time,
            enable_pubmed=enable_pubmed,
            pubmed_store_dir=pubmed_store_dir,
            offline_mode=offline_mode,
        )

        # Journeys registry
        self.journeys: List[PatientJourney] = []

        # Metrics telemetry
        self.metrics: Dict[str, Any] = {
            "total_patients": 0,
            "total_events_processed": 0,
            "decisions_allowed": 0,
            "decisions_blocked": 0,
            "rule_hits": {},
            "events_emitted_types": {},
            "journey_outcomes": {},
        }

    def _setup_department_handlers(self) -> None:
        """Delegate department handler registration to factory."""
        SimulationBootstrapFactory.wire_department_handlers(self)

    def spawn_patients(self, patient_count: int = 20) -> List[str]:
        """Generate and schedule N synthetic patient scenario journeys using WorkflowCoordinator."""
        scenario_ids = ["SCEN-V1-01", "SCEN-V1-02", "SCEN-V1-03", "SCEN-V1-04"]
        scenario_classes = [
            OutpatientRoutineScenario,
            DiagnosticInvestigationScenario,
            DrugAllergySafetyHoldScenario,
            InventoryDepletionScenario,
        ]

        instance_ids = []
        for i in range(patient_count):
            idx = i % len(scenario_ids)
            scen_id = scenario_ids[idx]
            scen_cls = scenario_classes[idx]

            scen_inst = scen_cls(instance_index=i + 1)

            # 1. Generate Patient Profile Dynamically (polymorphic LSP hook)
            if hasattr(scen_inst, "create_patient_profile"):
                patient_context = scen_inst.create_patient_profile(self.patient_gen)
            elif scen_id == "SCEN-V1-03":
                patient_context = self.patient_gen.generate_patient(force_allergy="Penicillin")
            else:
                patient_context = self.patient_gen.generate_patient()
                
            # Assign scenario context IDs to the patient
            patient_context.patient_id = scen_inst.patient_id
            patient_context.scenario_id = scen_id

            # Select clinical diagnosis and medication treatment with PubMed evidence
            # For SCEN-V1-03 (Penicillin allergy safety hold), select an infection diagnosis indicated for antibiotics
            if scen_id == "SCEN-V1-03":
                infection_candidates = [
                    d for d in self.kb.diagnoses
                    if d.code in ("J06.9", "J18.9", "N39.0")
                ]
                diagnosis = self.rng.choice(infection_candidates) if infection_candidates else self.clinical_gen.select_diagnosis(patient_context)
            else:
                diagnosis = self.clinical_gen.select_diagnosis(patient_context)

            patient_context.diagnosis_code = diagnosis.code
            patient_context.diagnosis_name = diagnosis.name

            force_conflict = (
                scen_inst.should_force_conflict()
                if hasattr(scen_inst, "should_force_conflict")
                else (scen_id == "SCEN-V1-03")
            )
            patient_context.force_conflict = force_conflict
            treatment, is_conflict = self.clinical_gen.select_medication(
                patient_context, diagnosis, force_conflict=force_conflict
            )

            self.patient_contexts[scen_inst.patient_id] = patient_context

            # Let scenario setup its base requirements, but datagen will override/populate rich data
            scen_inst.setup_initial_state(self.state_manager)
            
            # Override patient name in state manager from the generated profile
            self.state_manager.set_entity_state(
                "patient.patients",
                scen_inst.patient_id,
                {
                    "patient_id": scen_inst.patient_id,
                    "name": patient_context.name,
                    "allergies": patient_context.allergies,
                    "status": "Active",
                }
            )

            staggered_start = self.clock.now() + timedelta(minutes=i * 5)

            # Initialize clinical encounter entity in StateManager
            enc_id = f"enc-{scen_inst.patient_journey_id[3:]}"
            patient_context.encounter_id = enc_id
            self.state_manager.set_entity_state(
                "clinical.encounters",
                enc_id,
                {
                    "encounter_id": enc_id,
                    "patient_id": scen_inst.patient_id,
                    "journey_id": scen_inst.patient_journey_id,
                    "status": "Active",
                    "start_time": staggered_start.isoformat(),
                    "end_time": None,
                },
            )

            # Pre-seed prescription entity in StateManager with selected treatment provenance
            rx_id = getattr(scen_inst, "prescription_id", new_id("rx-", 6))
            rx_data = self.clinical_gen.generate_prescription_data(
                patient_context, rx_id, enc_id, treatment, is_conflict
            )
            self.state_manager.set_entity_state("pharmacy.prescriptions", rx_id, rx_data)

            # Ensure lab, radiology, and invoice states have unique IDs and are associated with encounter_id and patient_id
            lab_id = getattr(scen_inst, "lab_order_id", new_id("lab-", 8))
            rad_id = getattr(scen_inst, "rad_order_id", new_id("rad-", 8))
            inv_id = getattr(scen_inst, "invoice_id", new_id("inv-", 8))

            diag_entry = self.kb.get_diagnosis_by_code(patient_context.diagnosis_code)
            lab_options = diag_entry.lab_tests if (diag_entry and diag_entry.lab_tests) else ["CBC"]
            chosen_lab = self.rng.choice(lab_options) if lab_options else "CBC"

            imaging_options = diag_entry.imaging if (diag_entry and diag_entry.imaging) else ["X-Ray_Chest"]
            chosen_rad = self.rng.choice(imaging_options) if imaging_options else "X-Ray_Chest"
            modality_display = {
                "X-Ray_Chest": "Chest X-Ray",
                "X-Ray_Lumbar_Spine": "Lumbar Spine X-Ray",
                "CT_Head": "CT Head",
                "CT_Abdomen": "CT Abdomen",
            }.get(chosen_rad, chosen_rad)

            self.state_manager.set_entity_state(
                "laboratory.laboratory_orders",
                lab_id,
                {
                    "lab_order_id": lab_id,
                    "patient_id": scen_inst.patient_id,
                    "encounter_id": enc_id,
                    "journey_id": scen_inst.patient_journey_id,
                    "test_type": chosen_lab,
                    "test_name": chosen_lab,
                    "status": "Ordered",
                    "ordered_at": staggered_start.isoformat(),
                    "created_at": staggered_start.isoformat(),
                    "completed_at": None,
                },
            )

            self.state_manager.set_entity_state(
                "radiology.radiology_orders",
                rad_id,
                {
                    "rad_order_id": rad_id,
                    "patient_id": scen_inst.patient_id,
                    "encounter_id": enc_id,
                    "journey_id": scen_inst.patient_journey_id,
                    "modality": modality_display,
                    "status": "Ordered",
                    "ordered_at": staggered_start.isoformat(),
                    "created_at": staggered_start.isoformat(),
                    "completed_at": None,
                },
            )

            self.state_manager.set_entity_state(
                "finance.invoices",
                inv_id,
                {
                    "invoice_id": inv_id,
                    "patient_id": scen_inst.patient_id,
                    "encounter_id": enc_id,
                    "journey_id": scen_inst.patient_journey_id,
                    "status": "Draft",
                    "total_amount": 500.0,
                    "created_at": None,
                },
            )

            journey = PatientJourney(
                journey_id=scen_inst.patient_journey_id,
                patient_id=scen_inst.patient_id,
                scenario_id=scen_id,
                scenario_instance_id=scen_inst.scenario_instance_id,
                correlation_id=scen_inst.correlation_id,
                start_time=staggered_start,
                entity_references={
                    "patient.patients": scen_inst.patient_id,
                    "clinical.appointments": scen_inst.appointment_id,
                    "clinical.encounters": enc_id,
                    "pharmacy.prescriptions": rx_id,
                    "pharmacy.inventory_batches": getattr(scen_inst, "batch_id", new_id("batch-", 6)),
                    "laboratory.laboratory_orders": lab_id,
                    "radiology.radiology_orders": rad_id,
                    "finance.invoices": inv_id,
                },
            )

            self.journeys.append(journey)
            self.coordinator.start_journey(journey, start_time=staggered_start)
            instance_ids.append(scen_inst.scenario_instance_id)

        self.metrics["total_patients"] += patient_count
        return instance_ids

    def run(self, max_events: int = 1000, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute discrete event simulation loop until queue is empty or max_events reached."""
        processed_count = 0

        while processed_count < max_events and (self.scheduler.size() > 0 or not self.event_queue.is_empty()):
            # Peek next item
            next_evt = self.event_queue.peek()
            next_action_time = self.scheduler.peek_next_due_time()

            if not next_evt and not next_action_time:
                break

            evt_time = next_evt.scheduled_at if next_evt else None

            if evt_time and (not next_action_time or evt_time <= next_action_time):
                # Process simulation event
                event = self.event_queue.pop()
                if not event:
                    break
                processed_count += 1
                self.clock.advance_to(event.scheduled_at)
                actions = self.dispatcher.dispatch(event)
                for req in actions:
                    self.scheduler.schedule_action(req, scheduled_at=self.clock.now(), causation_depth=event.causation_depth)
            else:
                # Process due action
                self.clock.advance_to(next_action_time)
                due_actions = self.scheduler.get_due_actions(next_action_time)
                for saction in due_actions:
                    processed_count += 1
                    result, domain_event = self.engine._process_scheduled_action(saction)

                    # Update metrics
                    if result.decision.status == DecisionStatus.ALLOWED:
                        self.metrics["decisions_allowed"] += 1
                    else:
                        self.metrics["decisions_blocked"] += 1

                    winning_rule = result.decision.winning_rule_id
                    if winning_rule:
                        self.metrics["rule_hits"][winning_rule] = self.metrics["rule_hits"].get(winning_rule, 0) + 1

                    # Advance PatientJourney if action belonged to a journey
                    action = saction.action_request
                    journey_id = action.payload.get("journey_id")
                    step_id = action.payload.get("step_id")
                    if journey_id and step_id and domain_event:
                        self.coordinator.advance_journey(
                            journey_id=journey_id,
                            current_step_id=step_id,
                            decision=result.decision,
                            event=domain_event,
                            current_time=self.clock.now(),
                        )
                        # Close clinical encounter if journey finishes
                        journey = self.coordinator.active_journeys.get(journey_id)
                        if journey and journey.status in (JourneyStatus.COMPLETED, JourneyStatus.BLOCKED):
                            enc_id = f"enc-{journey_id[3:]}"
                            enc_state = self.state_manager.get_entity_state("clinical.encounters", enc_id)
                            if enc_state:
                                enc_state["status"] = "Closed"
                                current_dt = self.clock.now()
                                st_val = enc_state.get("start_time")
                                st_dt = datetime.fromisoformat(st_val) if isinstance(st_val, str) else st_val
                                if st_dt and current_dt <= st_dt:
                                    current_dt = st_dt + timedelta(minutes=15)
                                enc_state["end_time"] = current_dt.isoformat()
                                if not journey.end_time or journey.end_time < current_dt:
                                    journey.end_time = current_dt
                                self.state_manager.set_entity_state("clinical.encounters", enc_id, enc_state)

        # Pre-index events by journey_id for O(1) lookup
        from collections import defaultdict
        events_by_journey = defaultdict(list)
        for e in self.engine.committed_events:
            if e.patient_journey_id:
                events_by_journey[e.patient_journey_id].append(e)

        # Ensure any remaining encounters have consistent end_time and positive duration
        for j in self.journeys:
            enc_id = f"enc-{j.journey_id[3:]}"
            enc_state = self.state_manager.get_entity_state("clinical.encounters", enc_id)
            if enc_state:
                st_val = enc_state.get("start_time")
                st_dt = datetime.fromisoformat(st_val) if isinstance(st_val, str) else st_val
                journey_events = events_by_journey.get(j.journey_id, [])
                if journey_events:
                    latest_evt_time = max(e.timestamp for e in journey_events)
                else:
                    latest_evt_time = st_dt + timedelta(minutes=15) if st_dt else self.clock.now()

                if st_dt and latest_evt_time <= st_dt:
                    latest_evt_time = st_dt + timedelta(minutes=15)

                if not enc_state.get("end_time") or datetime.fromisoformat(enc_state["end_time"]) < latest_evt_time:
                    enc_state["end_time"] = latest_evt_time.isoformat()

                enc_end_dt = datetime.fromisoformat(enc_state["end_time"])
                if not j.end_time or j.end_time < enc_end_dt:
                    j.end_time = enc_end_dt

                if j.status in (JourneyStatus.COMPLETED, JourneyStatus.BLOCKED):
                    enc_state["status"] = "Closed"
                self.state_manager.set_entity_state("clinical.encounters", enc_id, enc_state)

        # Collect final journey metrics
        for j in self.journeys:
            outcome = j.outcome
            self.metrics["journey_outcomes"][outcome] = self.metrics["journey_outcomes"].get(outcome, 0) + 1

        self.metrics["total_events_processed"] += processed_count
        self.metrics["final_simulation_time"] = self.clock.now().isoformat()

        # Persist events, documents, and CSV datasets if output_dir is provided
        if output_dir:
            from pathlib import Path
            from synapse_simulator.exporter.document_generator import DocumentGenerator
            from synapse_simulator.exporter.event_logger import EventLogger
            from synapse_simulator.exporter.lineage_mapper import LineageMapper
            from synapse_simulator.validation.consistency_checker import ConsistencyChecker
            from synapse_simulator.exporter.csv_exporter import CSVExporter

            base_out = Path(output_dir)
            out_path = base_out / "phase2" if base_out.name != "phase2" else base_out

            # 1. Event logging
            event_logger = EventLogger(out_path)
            event_logger.persist_events(self.engine.committed_events)

            # 2. Document generation
            doc_gen = DocumentGenerator(self.state_manager, self.engine.committed_events, out_path)
            generated_docs = doc_gen.generate_all()

            # 3. Lineage mapping
            mapper = LineageMapper(out_path)
            lineage_map_path = mapper.generate_map(self.engine.committed_events, generated_docs)

            # 4. Consistency & Data Integrity Check
            checker = ConsistencyChecker(
                self.state_manager,
                self.engine.committed_events,
                generated_docs,
                lineage_map_path,
                out_path
            )
            checker.check_all()

            # 5. Export structured CSV files
            csv_exporter = CSVExporter(
                state_manager=self.state_manager,
                master_data=self.master_data_snapshot,
                patient_contexts=self.patient_contexts,
                committed_events=self.engine.committed_events,
                journeys=self.journeys,
                trace_log=self.engine.trace_log,
                metrics=self.metrics,
                output_dir=out_path,
            )
            exported_csvs = csv_exporter.export_all()
            self.metrics["exported_csv_files"] = list(exported_csvs.keys())

        return self.metrics
