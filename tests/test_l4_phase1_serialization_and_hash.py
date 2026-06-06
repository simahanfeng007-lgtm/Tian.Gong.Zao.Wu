from l3_phase1_builders import typed
from l4_phase1_builders import build_l4_phase1_objects
from tiangong_kernel.l4_action_grounding import (
    ActionGroundingSerialization,
    action_grounding_stable_hash,
    action_grounding_stable_json,
    action_grounding_to_primitive,
)


def test_l4_phase1_basic_objects_have_stable_serialization():
    objects = build_l4_phase1_objects()
    payload = {
        "identity": objects["identity"],
        "intake": objects["intake"],
        "disabled": objects["disabled"],
        "projection": objects["projection"],
    }
    primitive = action_grounding_to_primitive(payload)
    stable_json = action_grounding_stable_json(payload)
    stable_hash = action_grounding_stable_hash(payload)
    assert primitive["identity"]["schema_version"] == "0.1"
    assert stable_json == action_grounding_stable_json(payload)
    assert stable_hash == action_grounding_stable_hash(payload)
    assert len(stable_hash) == 64


def test_l4_phase1_serialization_snapshot_object_is_stable():
    objects = build_l4_phase1_objects()
    snapshot = ActionGroundingSerialization.from_value(
        serialization_ref=typed(4020, "l4_serialization"),
        target_ref=objects["result"].result_ref,
        value=objects["result"],
    )
    assert snapshot.serialization_only is True
    assert snapshot.stable_hash_value == action_grounding_stable_hash(objects["result"])
