from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l3_orchestration.belief_world_context_transition import (
    BeliefEventPrecedenceAdvice,
    BeliefUpdateAdvice,
    ContextPollutionReviewAdvice,
    ModelResultContextDemotionAdvice,
    ToolResultContextDemotionAdvice,
    WorldStateReconciliationAdvice,
)


def _ref(suffix: int, ref_type: str = "context_belief_world") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l3_belief_world_context_advices_are_advisory_only() -> None:
    advices = (
        BeliefUpdateAdvice(_ref(1), belief_ref=_ref(2), evidence_refs=(_ref(3),)),
        BeliefEventPrecedenceAdvice(_ref(4), event_ref=_ref(5), belief_ref=_ref(6)),
        WorldStateReconciliationAdvice(_ref(7), world_state_ref=_ref(8)),
        ContextPollutionReviewAdvice(_ref(9), taint_refs=(_ref(10),)),
        ToolResultContextDemotionAdvice(_ref(11), tool_result_ref=_ref(12)),
        ModelResultContextDemotionAdvice(_ref(13), model_result_ref=_ref(14)),
    )

    for advice in advices:
        assert advice.advisory_only is True
        assert advice.ref_only is True
        assert advice.writes_l2_state is False
        assert advice.assembles_context is False
        assert advice.emits_instruction is False
        assert advice.belief_overrides_event is False

    assert advices[4].system_instruction_eligible is False
    assert advices[5].context_injection_allowed is False

    with pytest.raises(ValueError):
        BeliefUpdateAdvice(_ref(15), emits_instruction=True)
