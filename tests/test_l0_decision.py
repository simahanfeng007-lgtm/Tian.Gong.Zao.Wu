from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.decision import Decision, DecisionKind, DecisionReason, DecisionRef
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.time import Timestamp


def test_decision_objects_construction_immutability_serialization_hash_and_enum_values():
    ref = DecisionRef(RefId("decision:" + "f" * 32), DecisionKind.REVIEW)
    reason = DecisionReason("needs_review", evidence_refs=(TypedRef(RefId("risk:" + "1" * 32), "risk"),))
    item = Decision(ref, DecisionKind.REVIEW, Timestamp(10), reason)
    try:
        item.kind = DecisionKind.ALLOW
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Decision allowed mutation")
    assert '"kind":"review"' in stable_json_dumps(item)
    assert len(stable_hash(item)) == 64
    assert [member.value for member in DecisionKind] == ["allow", "warn", "review", "block", "defer", "unknown"]
