from dataclasses import is_dataclass
from enum import Enum
import inspect

import tiangong_kernel.l2_state.base_state as base_state
import tiangong_kernel.l2_state.state_boundary as state_boundary
import tiangong_kernel.l2_state.state_delta as state_delta
import tiangong_kernel.l2_state.state_identity as state_identity
import tiangong_kernel.l2_state.state_invariant as state_invariant
import tiangong_kernel.l2_state.state_snapshot as state_snapshot
import tiangong_kernel.l2_state.state_status as state_status


MODULES = (
    base_state,
    state_identity,
    state_status,
    state_boundary,
    state_snapshot,
    state_delta,
    state_invariant,
)


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def test_l2_phase1_public_state_dataclasses_are_frozen_and_slotted():
    violations = []
    seen = []
    for module in MODULES:
        for cls in _public_local_classes(module):
            if issubclass(cls, Enum):
                continue
            seen.append(cls.__name__)
            if not is_dataclass(cls):
                violations.append((cls.__name__, "not_dataclass"))
                continue
            if not cls.__dataclass_params__.frozen:
                violations.append((cls.__name__, "not_frozen"))
            if "__slots__" not in cls.__dict__:
                violations.append((cls.__name__, "no_slots"))
    assert set(seen) == {
        "L2StateMetadata",
        "L2StateRecord",
        "L2StateIdentity",
        "L2StateStatus",
        "L2StateBoundary",
        "L2SnapshotSummary",
        "L2StateSnapshot",
        "L2DeltaEntry",
        "L2StateDelta",
        "L2StateInvariant",
        "L2InvariantCheck",
    }
    assert violations == []
