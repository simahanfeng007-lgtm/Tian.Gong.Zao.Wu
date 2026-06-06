from __future__ import annotations

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l4_action_grounding.context_safety_projection import (
    L4ContextSafetyProjection,
    L4ModelOutputContextProjection,
    L4ObservationBeliefWorldProjection,
    L4ToolOutputContextProjection,
)


def _ref(suffix: int, ref_type: str = "context_projection") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l4_context_safety_projection_defaults_are_non_instructional() -> None:
    projections = (
        L4ContextSafetyProjection(_ref(1), source_ref=_ref(2), taint_ref=_ref(3)),
        L4ToolOutputContextProjection(_ref(4), tool_result_ref=_ref(5), evidence_ref=_ref(6)),
        L4ModelOutputContextProjection(_ref(7), model_result_ref=_ref(8), evidence_ref=_ref(9)),
        L4ObservationBeliefWorldProjection(_ref(10), observation_ref=_ref(11), belief_candidate_refs=(_ref(12),), world_state_candidate_refs=(_ref(13),)),
    )

    for projection in projections:
        assert projection.untrusted_output is True
        assert projection.instruction_eligible is False
        assert projection.system_instruction_eligible is False
        assert projection.context_injection_allowed is False
        assert projection.requires_l5_boundary_review is True
        assert projection.requires_l6_context_assembler is True
        assert projection.l4_writes_l2 is False
        assert projection.l4_updates_belief_state is False
        assert projection.l4_updates_world_state is False
        assert projection.stores_plain_output is False

    with pytest.raises(ValueError):
        L4ToolOutputContextProjection(_ref(14), real_tool_called=True)
    with pytest.raises(ValueError):
        L4ModelOutputContextProjection(_ref(15), context_injection_allowed=True)
