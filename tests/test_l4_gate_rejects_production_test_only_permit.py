from l4_phase2_builders import build_gate_input, full_permit, validate
from tiangong_kernel.l4_action_grounding import PermitValidationStatus


def test_l4_gate_rejects_production_test_only_permit_for_safety_chain_patch():
    result = validate(build_gate_input(permit=full_permit(test_only=True), production_path=True))
    assert result.status is PermitValidationStatus.TEST_ONLY_REJECTED
    assert result.allowed_for_grounding is False
