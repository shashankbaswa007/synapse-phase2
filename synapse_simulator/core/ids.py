"""
Deterministic identifier factory.

Replaces ``uuid.uuid4()`` for every simulation-generated identifier so that identical
seeds and configurations yield identical IDs (and therefore byte-identical datasets).

Design
------
* One monotonically increasing counter per ``(prefix, hex_length)`` key.
* The counter is passed through a seed-keyed *bijection* on ``[0, 16**length)``
  (multiply by an odd constant, add a seed/prefix-derived offset, modulo ``2**bits``).
  A bijection guarantees **uniqueness** for the first ``16**length`` IDs of a key,
  which a truncated hash/uuid does not (birthday collisions).
* IDs keep the legacy textual format: ``<prefix><hex of fixed length>``.

State is process-global because ID producers live in many places (pydantic default
factories, scenario constructors, handlers) that have no handle to the simulator.
``reset(seed)`` is called by ``SimulationBootstrapFactory.bootstrap`` so each simulator
starts from a clean, seed-determined state. Two simulators alive in one process share
the module state; run them sequentially (documented limitation).
"""

import hashlib
import itertools
from typing import Dict, Tuple

# Odd 64-bit constant (golden-ratio based): multiplication by an odd number is a
# bijection modulo any power of two.
_ODD_MULTIPLIER = 0x9E3779B97F4A7C15


class IdFactory:
    """Seeded, collision-free ID generator."""

    def __init__(self, seed: int = 0):
        self.seed = int(seed)
        self._counters: Dict[Tuple[str, int], int] = {}

    def new(self, prefix: str, length: int = 8) -> str:
        key = (prefix, length)
        n = self._counters.get(key, 0)
        bits = 4 * length
        modulus = 1 << bits
        if n >= modulus:
            raise OverflowError(f"ID space exhausted for prefix '{prefix}' with length {length}")
        self._counters[key] = n + 1
        digest = hashlib.sha256(f"{self.seed}|{prefix}|{length}".encode("utf-8")).digest()
        offset = int.from_bytes(digest[:8], "big") % modulus
        value = (n * _ODD_MULTIPLIER + offset) % modulus
        return f"{prefix}{value:0{length}x}"


_factory = IdFactory(0)

# Monotonic tie-break sequences used by the scheduler / queue / engine. They are
# registered here so a single ``reset`` call restores them all.
_sequences: Dict[str, "itertools.count"] = {}


def reset(seed: int = 0) -> None:
    """Re-seed the global ID factory and restart all tie-break sequences."""
    global _factory
    _factory = IdFactory(seed)
    for name in list(_sequences):
        _sequences[name] = itertools.count()


def new_id(prefix: str, length: int = 8) -> str:
    """Return the next deterministic ID, e.g. ``new_id('pat-', 8) -> 'pat-1f3a09bc'``."""
    return _factory.new(prefix, length)


def next_sequence(name: str) -> int:
    """Return the next value of the named monotonic sequence (starts at 0 after reset)."""
    seq = _sequences.get(name)
    if seq is None:
        seq = _sequences[name] = itertools.count()
    return next(seq)
