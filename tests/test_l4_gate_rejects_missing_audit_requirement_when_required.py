from l4_phase2_builders import build_gate_input, full_permit, validate
from tiangong_kernel.l4_action_grounding import PermitValidationStatus


def test_l4_gate_rejects_missing_audit_requirement_when_required_for_safety_chain_patch():
    result = validate(build_gate_input(permit=full_permit(), audit_required=True))
    assert result.status is PermitValidationStatus.REJECTED
    assert result.allowed_for_grounding is False
    assert "audit requirement ref is missing" in result.boundary_feedback_summary
