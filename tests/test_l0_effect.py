from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.effect import (
    EffectBoundaryRef,
    EffectImpact,
    EffectIntent,
    EffectKind,
    EffectRef,
    EffectResultRef,
    EffectReversibility,
    EffectState,
)
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_effect_objects_construction_immutability_serialization_hash_and_enum_values():
    ref = EffectRef(RefId("effect:" + "b" * 32), EffectKind.WRITE)
    result = EffectResultRef(RefId("result:" + "c" * 32), "effect_result")
    boundary = EffectBoundaryRef(RefId("boundary:" + "d" * 32), "effect_boundary")
    impact = EffectImpact("bounded")
    item = EffectIntent(
        ref,
        EffectKind.WRITE,
        target_ref=TypedRef(RefId("content:" + "e" * 32), "content"),
        result_ref=result,
        reversibility=EffectReversibility.COMPENSATABLE,
        impact=impact,
        boundary_ref=boundary,
    )
    try:
        item.state = EffectState.SUCCEEDED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("EffectIntent allowed mutation")
    assert '"kind":"write"' in stable_json_dumps(item)
    assert len(stable_hash(item)) == 64
    assert [member.value for member in EffectKind] == [
        "read",
        "write",
        "delete",
        "execute",
        "send",
        "modify_state",
        "allocate_resource",
        "release_resource",
        "spawn",
        "terminate",
        "observe",
        "unknown",
    ]
    assert [member.value for member in EffectState] == [
        "proposed",
        "under_review",
        "authorized",
        "rejected",
        "leased",
        "running",
        "succeeded",
        "failed",
        "rolled_back",
        "compensated",
        "expired",
        "cancelled",
        "unknown",
    ]
