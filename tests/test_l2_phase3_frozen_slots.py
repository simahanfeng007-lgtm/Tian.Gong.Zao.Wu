from dataclasses import FrozenInstanceError, is_dataclass
from enum import Enum
import inspect
import pytest

import tiangong_kernel.l2_state.action_effect_state as action_effect_state
import tiangong_kernel.l2_state.model_state as model_state
import tiangong_kernel.l2_state.skill_state as skill_state
import tiangong_kernel.l2_state.tool_group_state as tool_group_state
import tiangong_kernel.l2_state.tool_intent_state as tool_intent_state
from tests.test_l2_phase3_serialization import build_phase3_chain


MODULES = (
    skill_state,
    tool_group_state,
    tool_intent_state,
    model_state,
    action_effect_state,
)


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def test_l2_phase3_public_dataclasses_are_frozen_and_slotted():
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
    assert len(dataclasses) == 16
    assert violations == []


def test_l2_phase3_objects_reject_mutation():
    item = build_phase3_chain()["tool_intent"]
    with pytest.raises(FrozenInstanceError):
        item.argument_digest = "changed"


def test_l2_phase3_tuple_defaults_are_not_shared_and_remain_tuples():
    first = build_phase3_chain()["tool_declaration"]
    second = build_phase3_chain()["tool_declaration"]
    assert isinstance(first.required_tool_refs, tuple)
    assert first.required_tool_refs is not second.required_tool_refs
