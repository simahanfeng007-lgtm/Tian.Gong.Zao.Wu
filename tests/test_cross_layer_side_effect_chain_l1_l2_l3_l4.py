from dataclasses import replace

from l3_phase1_builders import typed
from l4_phase2_builders import build_gate_input, full_permit, validate
from tiangong_kernel.l1_ports import ApprovalRequest, EffectAuthorizationRequest
from tiangong_kernel.l2_state import L2StateIdentity, L2StateKind, L2StateStatus, SideEffectGovernanceChainState
from tiangong_kernel.l3_orchestration import SideEffectExecutionReadinessFlow
from tiangong_kernel.l4_action_grounding import L3SafetyChainRef, PermitValidationStatus


def test_cross_layer_side_effect_chain_l1_l2_l3_l4_refs_only():
    approval_request = ApprovalRequest(request_ref=typed(1, "approval_request"))
    effect_request = EffectAuthorizationRequest(request_ref=typed(2, "effect_authorization_request"))
    state = SideEffectGovernanceChainState(
        L2StateIdentity(state_ref=typed(3, "side_effect_state"), kind=L2StateKind.BOUNDARY),
        L2StateStatus(),
        chain_ref=typed(4, "side_effect_chain"),
        action_intent_ref=typed(5, "action_intent"),
    )
    flow = SideEffectExecutionReadinessFlow(safety_chain_ref=state.chain_ref, input_refs=(approval_request.request_ref, effect_request.request_ref))
    safety = L3SafetyChainRef(safety_chain_ref=typed(6, "safety_chain"), source_action_intent_ref=state.action_intent_ref)
    gate_input = replace(build_gate_input(permit=full_permit()), live_action_requested=True, safety_chain_ref=safety.safety_chain_ref)
    result = validate(gate_input)
    assert flow.dispatch_enabled is False
    assert safety.l4_authorized_action is False
    assert result.status is PermitValidationStatus.ACCEPTED
    assert result.l4_authorized_action is False
