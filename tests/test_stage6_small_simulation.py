"""
Stage 6 Integration Test: Small Time-Driven Simulation with Step-by-Step Causal Trace Verification.
"""

from datetime import datetime
from synapse_simulator.core.clock import SimulationClock
from synapse_simulator.core.scheduler import FutureActionScheduler
from synapse_simulator.core.event_queue import EventQueue, SimulationEvent
from synapse_simulator.core.dispatcher import EventDispatcher
from synapse_simulator.state.state_manager import StateManager
from synapse_simulator.rules.repository import RuleRepository
from synapse_simulator.rules.rule_engine import RuleEngine
from synapse_simulator.core.simulation_engine import SimulationEngine
from synapse_simulator.departments.clinical import ClinicalDepartmentHandler
from synapse_simulator.departments.pharmacy import PharmacyDepartmentHandler
from synapse_simulator.scenarios.scen_v1_01_opd import OutpatientRoutineScenario
from synapse_simulator.scenarios.scen_v1_03_allergy import DrugAllergySafetyHoldScenario


def test_small_time_driven_simulation_trace():
    # Setup core Stage 6 engine components
    clock = SimulationClock(datetime(2026, 1, 1, 8, 0, 0))
    scheduler = FutureActionScheduler()
    event_queue = EventQueue()
    dispatcher = EventDispatcher()
    state_manager = StateManager()

    repo = RuleRepository()
    repo.load_rules()
    rule_engine = RuleEngine(repo)

    # Register handlers
    clinical_h = ClinicalDepartmentHandler()
    pharmacy_h = PharmacyDepartmentHandler()
    dispatcher.register_handler("PatientArrived", clinical_h.handle_event)
    dispatcher.register_handler("EncounterStarted", pharmacy_h.handle_event)
    dispatcher.register_handler("PrescriptionVerified", pharmacy_h.handle_event)

    engine = SimulationEngine(
        clock=clock,
        scheduler=scheduler,
        event_queue=event_queue,
        dispatcher=dispatcher,
        state_manager=state_manager,
        rule_engine=rule_engine,
    )

    # Spawn 2 patients: 1 Routine OPD, 1 Drug Allergy Hold
    scen_opd = OutpatientRoutineScenario(instance_index=1)
    scen_opd.setup_initial_state(state_manager)
    evt_opd = scen_opd.generate_initial_events(datetime(2026, 1, 1, 8, 0, 0))
    event_queue.push(evt_opd)

    scen_allergy = DrugAllergySafetyHoldScenario(instance_index=2)
    scen_allergy.setup_initial_state(state_manager)
    evt_allergy = scen_allergy.generate_initial_events(datetime(2026, 1, 1, 8, 15, 0))
    event_queue.push(evt_allergy)

    # Execute simulation until completion
    committed_events = engine.run_until(max_events=100)

    # Verify execution output
    assert len(committed_events) > 0
    assert len(engine.trace_log) > 0

    print("\n--- STEP-BY-STEP SIMULATION EXECUTION TRACE ---")
    for step in engine.trace_log:
        print(f"[{step['time']}] ACTION: {step['action']} | TARGET: {step['target_entity']} | RULE: {step['rule_winning']} | STATUS: {step['status']} | EVENT: {step['domain_event']}")

    # Verify at least one ALLOWED event and at least one BLOCKED event occurred
    statuses = [step["status"] for step in engine.trace_log]
    assert "ALLOWED" in statuses
    assert "BLOCKED" in statuses

    # Verify clock advanced past 8:00 AM
    assert clock.now() >= datetime(2026, 1, 1, 8, 15, 0)
