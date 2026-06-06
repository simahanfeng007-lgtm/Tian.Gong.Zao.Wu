from collections import Counter

from l3_phase7_builders import build_l3_phase7_objects
from l3_phase8_builders import build_l3_phase8_objects
import tiangong_kernel.l3_orchestration as l3


PHASE8_EXPORTS = {
    "OrchestrationProjection",
    "OrchestrationComponentIndex",
    "OrchestrationMathCatalog",
    "L3ToL4HandoffEnvelope",
    "L3ToL5HandoffEnvelope",
    "L3ToL6HandoffEnvelope",
    "L3ClosureCheckResult",
    "L3FinalFreezeReadinessReport",
}


def test_l3_phase8_objects_import_and_previous_phase_builders_still_work():
    phase7 = build_l3_phase7_objects()
    phase8 = build_l3_phase8_objects()
    assert phase7["validation_request"].request_only is True
    assert phase8["projection"].projection_only is True
    assert phase8["l4_envelope"].handoff_only is True
    assert phase8["l5_envelope"].handoff_only is True
    assert phase8["l6_envelope"].handoff_only is True


def test_l3_phase8_public_exports_are_present_and_not_duplicated():
    exported = set(l3.__all__)
    assert PHASE8_EXPORTS.issubset(exported)
    counts = Counter(l3.__all__)
    assert [name for name, count in counts.items() if count > 1] == []
    for name in PHASE8_EXPORTS:
        assert hasattr(l3, name)
