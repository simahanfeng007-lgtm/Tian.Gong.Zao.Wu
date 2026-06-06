from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.actor import ActorKind, ActorRef
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_actor_ref_construction_immutability_serialization_hash_and_enum_values():
    item = ActorRef(RefId("actor:" + "1" * 32), ActorKind.USER)
    assert item.kind is ActorKind.USER
    try:
        item.kind = ActorKind.MODEL
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ActorRef allowed mutation")
    assert '"kind":"user"' in stable_json_dumps(item)
    assert len(stable_hash(item)) == 64
    assert [member.value for member in ActorKind] == [
        "user",
        "model",
        "system",
        "plugin",
        "adapter",
        "scheduler",
        "self_healing",
        "external",
        "unknown",
    ]
