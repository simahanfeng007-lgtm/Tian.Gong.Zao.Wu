from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.plan import PlanKind, PlanOriginRef, PlanPriority, PlanRef, PlanState
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_plan_objects_construction_immutability_serialization_hash_and_enum_values():
    item = PlanRef(RefId("plan:" + "7" * 32), PlanKind.CHECKLIST, PlanState.PROPOSED)
    origin = PlanOriginRef(TypedRef(RefId("goal:" + "8" * 32), "goal"))
    priority = PlanPriority(2)
    try:
        item.state = PlanState.ACTIVE
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("PlanRef allowed mutation")
    assert '"kind":"checklist"' in stable_json_dumps((item, origin, priority))
    assert len(stable_hash((item, origin, priority))) == 64
    assert [member.value for member in PlanKind] == [
        "sequential",
        "checklist",
        "hierarchical",
        "dag",
        "parallel",
        "narrative",
        "pseudocode",
        "recovery",
        "unknown",
    ]
    assert [member.value for member in PlanState] == [
        "draft",
        "proposed",
        "approved",
        "active",
        "paused",
        "blocked",
        "revising",
        "completed",
        "failed",
        "abandoned",
        "archived",
        "unknown",
    ]
