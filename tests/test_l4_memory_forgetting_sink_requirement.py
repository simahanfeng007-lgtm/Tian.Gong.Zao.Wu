from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_action_grounding.cognitive_sink_hint import ActionResultCognitiveSinkHint
from tiangong_kernel.l4_execution import L4_L6_SURFACES
from tiangong_kernel.l4_execution.l4_to_l6_forgetting_sink_requirement import L4ToL6ForgettingSinkRequirement
from tiangong_kernel.l4_execution.l4_to_l6_memory_sink_requirement import L4ToL6MemorySinkRequirement


def _ref(suffix: int, ref_type: str = "l4_memory_sink") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l4_l6_surfaces_include_memory_forgetting_sinks() -> None:
    for surface in (
        "memory_sink",
        "forgetting_sink",
        "retrieval_sink",
        "learning_sink",
        "affective_feedback_sink",
        "privacy_retention_sink",
    ):
        assert surface in L4_L6_SURFACES


def test_l4_memory_and_forgetting_requirements_do_not_implement_l6() -> None:
    memory = L4ToL6MemorySinkRequirement(_ref(1), memory_candidate_refs=(_ref(2),))
    forgetting = L4ToL6ForgettingSinkRequirement(_ref(3), forgetting_intent_refs=(_ref(4),), tombstone_refs=(_ref(5),))
    hint = ActionResultCognitiveSinkHint(_ref(6), memory_candidate_refs=(_ref(7),), forgetting_intent_refs=(_ref(8),))

    assert memory.requirement_only is True
    assert memory.writes_memory is False
    assert memory.implements_memory_system is False
    assert forgetting.requirement_only is True
    assert forgetting.executes_forgetting is False
    assert forgetting.deletes_memory is False
    assert hint.advisory_only is True
    assert hint.ref_only is True
    assert hint.writes_memory is False
    assert hint.executes_forgetting is False

    with pytest.raises(ValueError):
        L4ToL6MemorySinkRequirement(_ref(9), writes_memory=True)
    with pytest.raises(ValueError):
        L4ToL6ForgettingSinkRequirement(_ref(10), executes_forgetting=True)
