from dataclasses import FrozenInstanceError, is_dataclass
from enum import Enum
import inspect
import pytest

import tiangong_kernel.l2_state.agent_state as agent_state
import tiangong_kernel.l2_state.continuity_state as continuity_state
import tiangong_kernel.l2_state.goal_plan_state as goal_plan_state
import tiangong_kernel.l2_state.run_state as run_state
import tiangong_kernel.l2_state.state_lifecycle as state_lifecycle
import tiangong_kernel.l2_state.task_state as task_state
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state import L2StateIdentity, L2StateStatus


MODULES = (
    agent_state,
    run_state,
    task_state,
    goal_plan_state,
    state_lifecycle,
    continuity_state,
)


def _public_local_classes(module):
    for _, value in inspect.getmembers(module, inspect.isclass):
        if value.__module__ == module.__name__ and not value.__name__.startswith("_"):
            yield value


def _identity() -> L2StateIdentity:
    return L2StateIdentity(TypedRef(RefId("ref:00000000000000000000000000000001"), "l2_state"))


def test_l2_phase2_public_dataclasses_are_frozen_and_slotted():
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
        "AgentHealthState",
        "AgentState",
        "RunProgressState",
        "RunState",
        "TaskProgressState",
        "TaskState",
        "GoalPlanState",
        "LifecycleState",
        "ContinuityState",
        "CheckpointContinuityState",
        "RecoveryContinuityState",
    }
    assert violations == []


def test_l2_phase2_objects_reject_mutation():
    item = agent_state.AgentState(identity=_identity(), status=L2StateStatus())
    with pytest.raises(FrozenInstanceError):
        item.schema_version = "0.2"
