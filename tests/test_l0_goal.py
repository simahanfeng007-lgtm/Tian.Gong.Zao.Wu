from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.goal import (
    GoalFailureCriteriaRef,
    GoalKind,
    GoalPriority,
    GoalRef,
    GoalState,
    GoalSuccessCriteriaRef,
)
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_goal_objects_construction_immutability_serialization_hash_and_enum_values():
    item = GoalRef(RefId("goal:" + "4" * 32), GoalKind.USER_REQUEST, GoalState.ACTIVE)
    success = GoalSuccessCriteriaRef(RefId("gsc:" + "5" * 32))
    failure = GoalFailureCriteriaRef(RefId("gfc:" + "6" * 32))
    priority = GoalPriority(3)
    try:
        item.state = GoalState.FAILED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("GoalRef allowed mutation")
    assert '"kind":"user_request"' in stable_json_dumps((item, success, failure, priority))
    assert len(stable_hash((item, success, failure, priority))) == 64
    assert [member.value for member in GoalKind] == [
        "user_request",
        "system_maintenance",
        "recovery",
        "learning",
        "exploration",
        "safety",
        "resource",
        "unknown",
    ]
    assert [member.value for member in GoalState] == [
        "proposed",
        "accepted",
        "active",
        "suspended",
        "blocked",
        "achieved",
        "failed",
        "abandoned",
        "archived",
        "unknown",
    ]
