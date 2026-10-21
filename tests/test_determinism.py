"""
Determinism / reproducibility tests (research-alignment Phase 0).

Contract: identical seed + configuration => byte-identical exported datasets,
independent of process, wall-clock, or PYTHONHASHSEED. A different seed must
produce different output (guards against the seed being silently ignored).
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from synapse_simulator.core import ids
from synapse_simulator.core.ids import IdFactory
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.exporter.csv_exporter import CSVExporter

REPO_ROOT = Path(__file__).resolve().parents[1]

# Executed in a child process so PYTHONHASHSEED can be varied.
_CHILD = """
import sys, hashlib
from pathlib import Path
from synapse_simulator.generator.hospital_generator import HospitalSimulator
from synapse_simulator.exporter.csv_exporter import CSVExporter
seed, n, out = int(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
sim = HospitalSimulator(random_seed=seed, enable_pubmed=True, offline_mode=True)
sim.spawn_patients(n)
sim.run(max_events=n * 150)
CSVExporter(sim.state_manager, sim.master_data_snapshot, sim.patient_contexts,
            sim.engine.committed_events, sim.journeys, sim.engine.trace_log,
            sim.metrics, out / 'phase2').export_simplified_dataset(target_dir=out)
for p in sorted(out.glob('*.csv')):
    print(p.name, hashlib.sha256(p.read_bytes()).hexdigest())
"""


def _generate(out: Path, seed: int, n: int = 40) -> None:
    sim = HospitalSimulator(random_seed=seed, enable_pubmed=True, offline_mode=True)
    sim.spawn_patients(n)
    sim.run(max_events=n * 150)
    CSVExporter(
        sim.state_manager, sim.master_data_snapshot, sim.patient_contexts,
        sim.engine.committed_events, sim.journeys, sim.engine.trace_log,
        sim.metrics, out / "phase2",
    ).export_simplified_dataset(target_dir=out)


def _digests(d: Path) -> dict:
    files = sorted(d.glob("*.csv"))
    assert files, f"no CSVs exported to {d}"
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


# ---------------------------------------------------------------- IdFactory unit tests

def test_id_factory_same_seed_same_sequence():
    a, b = IdFactory(7), IdFactory(7)
    assert [a.new("pat-", 8) for _ in range(50)] == [b.new("pat-", 8) for _ in range(50)]


def test_id_factory_different_seed_differs():
    assert [IdFactory(1).new("pat-", 8) for _ in range(5)] != [IdFactory(2).new("pat-", 8) for _ in range(5)]


def test_id_factory_format_matches_legacy():
    v = IdFactory(0).new("pat-", 8)
    assert v.startswith("pat-") and len(v) == len("pat-") + 8
    int(v[4:], 16)  # valid hex


def test_id_factory_is_collision_free_over_full_small_space():
    """Bijection property: the whole 16**3 space is hit exactly once (a truncated hash/uuid would collide)."""
    f = IdFactory(123)
    seen = {f.new("x-", 3) for _ in range(16 ** 3)}
    assert len(seen) == 16 ** 3
    with pytest.raises(OverflowError):
        f.new("x-", 3)


def test_id_factory_unique_at_cohort_scale():
    f = IdFactory(42)
    n = 200_000
    assert len({f.new("evt-", 10) for _ in range(n)}) == n


def test_prefix_streams_are_independent():
    f = IdFactory(5)
    assert f.new("pat-", 8) != f.new("rx-", 8)


def test_module_reset_restarts_ids_and_sequences():
    ids.reset(9)
    first = [ids.new_id("pat-", 8), ids.next_sequence("t")]
    ids.new_id("pat-", 8); ids.next_sequence("t")
    ids.reset(9)
    assert [ids.new_id("pat-", 8), ids.next_sequence("t")] == first


# ---------------------------------------------------------------- end-to-end

def test_same_seed_in_process_is_byte_identical(tmp_path):
    _generate(tmp_path / "a", seed=42)
    _generate(tmp_path / "b", seed=42)
    da, db = _digests(tmp_path / "a"), _digests(tmp_path / "b")
    assert da.keys() == db.keys()
    mismatched = [k for k in da if da[k] != db[k]]
    assert not mismatched, f"non-reproducible files: {mismatched}"


def test_different_seed_changes_output(tmp_path):
    _generate(tmp_path / "a", seed=42)
    _generate(tmp_path / "b", seed=43)
    assert _digests(tmp_path / "a")["patients.csv"] != _digests(tmp_path / "b")["patients.csv"]


def _child(out: Path, seed: int, hashseed: str, n: int = 40) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": hashseed}
    res = subprocess.run(
        [sys.executable, "-c", _CHILD, str(seed), str(n), str(out)],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=300,
    )
    assert res.returncode == 0, res.stderr[-2000:]
    return dict(line.split() for line in res.stdout.splitlines() if line.endswith(tuple("0123456789abcdef")) and ".csv" in line)


def test_reproducible_across_processes_and_hash_seeds(tmp_path):
    """Catches dict/set iteration-order leaks, which one process cannot reveal."""
    d1 = _child(tmp_path / "p1", 42, "1")
    d2 = _child(tmp_path / "p2", 42, "98765")
    assert d1 and d1 == d2
