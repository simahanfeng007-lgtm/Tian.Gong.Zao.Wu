from __future__ import annotations

from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l1_ports.context_belief_world_ports import BeliefEventPrecedenceBoundary, ToolOutputDemotionBoundary
from tiangong_kernel.l2_state.belief_state import BeliefEventPrecedenceState
from tiangong_kernel.l2_state.context_safety_state import MemoryInjectionBoundaryState
from tiangong_kernel.l2_state.state_identity import L2StateIdentity, L2StateKind
from tiangong_kernel.l2_state.state_status import L2StateStatus, L2StateStatusKind
from tiangong_kernel.l3_orchestration.belief_world_context_transition import ToolResultContextDemotionAdvice
from tiangong_kernel.l4_action_grounding.context_safety_projection import L4ToolOutputContextProjection


def _ref(suffix: int, ref_type: str = "context_belief_world") -> TypedRef:
    return TypedRef(RefId(f"ref:{suffix:032x}"), ref_type)


def test_tool_result_and_memory_injection_cannot_become_system_instruction() -> None:
    event_ref = _ref(1, "event")
    belief_ref = _ref(2, "belief")
    tool_result_ref = _ref(3, "tool_result")
    l1_boundary = BeliefEventPrecedenceBoundary(_ref(4), event_ref=event_ref, belief_ref=belief_ref)
    l1_demotion = ToolOutputDemotionBoundary(_ref(5), tool_result_ref=tool_result_ref)
    l2_precedence = BeliefEventPrecedenceState(
        identity=L2StateIdentity(_ref(6, "l2_state"), L2StateKind.MEMORY_CONTEXT),
        status=L2StateStatus(L2StateStatusKind.DECLARED),
        belief_ref=belief_ref,
        event_refs=(event_ref,),
    )
    l2_memory_boundary = MemoryInjectionBoundaryState(
        identity=L2StateIdentity(_ref(7, "l2_state"), L2StateKind.MEMORY_CONTEXT),
        status=L2StateStatus(L2StateStatusKind.DECLARED),
        memory_refs=(_ref(8, "memory"),),
        boundary_status="not_reviewed",
    )
    l3_demotion = ToolResultContextDemotionAdvice(_ref(9), tool_result_ref=tool_result_ref)
    l4_projection = L4ToolOutputContextProjection(_ref(10), tool_result_ref=tool_result_ref, taint_ref=_ref(11))

    assert l1_boundary.belief_overrides_event is False
    assert l1_demotion.system_instruction_eligible is False
    assert l1_demotion.context_injection_allowed is False
    assert l2_precedence.overrides_event_fact is False
    assert l2_memory_boundary.injected is False
    assert l3_demotion.emits_instruction is False
    assert l3_demotion.system_instruction_eligible is False
    assert l4_projection.system_instruction_eligible is False
    assert l4_projection.context_injection_allowed is False
