from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.risk import RiskLevel, RiskRef, RiskSignal, RiskView
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps


def test_risk_objects_construction_immutability_serialization_hash_and_enum_values():
    ref = RiskRef(RefId("risk:" + "2" * 32), RiskLevel.A3_ELEVATED)
    signal = RiskSignal(RiskLevel.A3_ELEVATED, source_ref=TypedRef(RefId("signal:" + "3" * 32), "signal"), confidence=0.8)
    item = RiskView(ref, RiskLevel.A3_ELEVATED, signals=(signal,))
    try:
        item.level = RiskLevel.A5_CRITICAL
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("RiskView allowed mutation")
    assert '"level":"a3_elevated"' in stable_json_dumps(item)
    assert len(stable_hash(item)) == 64
    assert [member.value for member in RiskLevel] == [
        "a0_safe",
        "a1_low",
        "a2_normal",
        "a3_elevated",
        "a4_review_required",
        "a5_critical",
        "unknown",
    ]
