from dataclasses import replace

from l4_phase2_builders import build_gate_input, full_permit, validate
from tiangong_kernel.l4_action_grounding import PermitValidationStatus


def test_l4_gate_rejects_live_action_without_safety_chain_ref():
    gate_input = replace(build_gate_input(permit=full_permit()), live_action_requested=True)
    result = validate(gate_input)
    assert result.status is PermitValidationStatus.REJECTED
    assert result.allowed_for_grounding is False
    assert "safety_chain_ref is missing" in result.boundary_feedback_summary
