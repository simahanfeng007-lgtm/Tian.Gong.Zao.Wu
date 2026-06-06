from dataclasses import FrozenInstanceError, is_dataclass
from enum import Enum
import inspect

import pytest

import tiangong_kernel.l2_state.boundary_state as boundary_state
import tiangong_kernel.l2_state.control_state as control_state
import tiangong_kernel.l2_state.environment_state as environment_state
import tiangong_kernel.l2_state.resource_state as resource_state
import tiangong_kernel.l2_state.risk_decision_state as risk_decision_state
import tiangong_kernel.l2_state.security_state as security_state
from tests.test_l2_phase4_serialization import build_phase4_objects


MODULES = (
    control_state,
    boundary_state,
    risk_decision_state,
    resource_state,
    environment_state,
    security_state,
)


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def test_l2_phase4_public_dataclasses_are_frozen_and_slotted():
    violations = []
    dataclasses = []
    for module in MODULES:
        for cls in _public_local_classes(module):
            if issubclass(cls, Enum):
                continue
            dataclasses.append(cls.__name__)
            if not is_dataclass(cls):
                violations.append((cls.__name__, "not_dataclass"))
                continue
            if not cls.__dataclass_params__.frozen:
                violations.append((cls.__name__, "not_frozen"))
            if "__slots__" not in cls.__dict__:
                violations.append((cls.__name__, "no_slots"))
    assert len(dataclasses) == 22
    assert violations == []


def test_l2_phase4_objects_reject_mutation():
    item = build_phase4_objects()["control"]
    with pytest.raises(FrozenInstanceError):
        item.summary = "changed"


def test_l2_phase4_tuple_defaults_are_not_shared_and_remain_tuples():
    first = build_phase4_objects()["constraint"]
    second = build_phase4_objects()["constraint"]
    assert isinstance(first.constraint_refs, tuple)
    assert first.constraint_refs is not second.constraint_refs
