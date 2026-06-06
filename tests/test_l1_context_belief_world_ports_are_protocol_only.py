from __future__ import annotations

from inspect import isabstract

import pytest

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.context_belief_world_ports import (
    BeliefEventPrecedenceBoundary,
    BeliefStateReference,
    BeliefStateReferencePort,
    ContextPollutionBoundary,
    ContextSafetyBoundary,
    ContextSafetyBoundaryPort,
    InstructionEligibilityBoundary,
    ModelOutputDemotionBoundary,
    ToolOutputDemotionBoundary,
    WorldStateReference,
    WorldStateReferencePort,
)


def _ref(suffix: int, ref_type: str = "context_belief_world") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_l1_context_belief_world_boundaries_are_protocol_only() -> None:
    belief = BeliefStateReference(_ref(1), evidence_refs=(_ref(2),), event_refs=(_ref(3),))
    precedence = BeliefEventPrecedenceBoundary(_ref(4), event_ref=_ref(5), belief_ref=belief.belief_ref)
    world = WorldStateReference(_ref(6), observation_refs=(_ref(7),), evidence_refs=(_ref(8),), trust_boundary_ref=_ref(9))
    pollution = ContextPollutionBoundary(_ref(10), taint_refs=(_ref(11),))
    tool_demotion = ToolOutputDemotionBoundary(_ref(12), tool_result_ref=_ref(13))
    model_demotion = ModelOutputDemotionBoundary(_ref(14), tool_result_ref=_ref(15))
    instruction = InstructionEligibilityBoundary(_ref(16), source_ref=_ref(17))
    context = ContextSafetyBoundary(_ref(18), pollution_boundary_ref=pollution.boundary_ref, instruction_boundary_ref=instruction.boundary_ref)

    assert belief.reference_only is True
    assert belief.cannot_override_event is True
    assert precedence.event_precedes_belief is True
    assert precedence.belief_overrides_event is False
    assert world.syncs_real_world is False
    assert pollution.allows_polluted_context is False
    assert tool_demotion.untrusted_output is True
    assert tool_demotion.system_instruction_eligible is False
    assert model_demotion.context_injection_allowed is False
    assert instruction.requires_l5_boundary_review is True
    assert context.assembles_context is False
    assert isabstract(ContextSafetyBoundaryPort)
    assert isabstract(BeliefStateReferencePort)
    assert isabstract(WorldStateReferencePort)

    with pytest.raises(ValueError):
        BeliefEventPrecedenceBoundary(_ref(19), event_ref=_ref(20), belief_ref=_ref(21), belief_overrides_event=True)
