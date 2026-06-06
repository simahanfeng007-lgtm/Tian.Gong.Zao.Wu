from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.action import ActionIntent, ActionKind, ActionRef, ActionState
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_action_objects_construction_immutability_serialization_hash_and_enum_values():
    ref = ActionRef(RefId("action:" + "9" * 32), ActionKind.REQUEST_EFFECT)
    item = ActionIntent(ref, ActionKind.REQUEST_EFFECT, target_ref=TypedRef(RefId("effect:" + "a" * 32), "effect"))
    try:
        item.state = ActionState.COMPLETED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ActionIntent allowed mutation")
    assert '"kind":"request_effect"' in stable_json_dumps(item)
    assert len(stable_hash(item)) == 64
    assert [member.value for member in ActionKind] == ["final", "ask_user", "request_effect", "refuse", "noop", "unknown"]
