from l4_phase2_builders import (
    audit_requirement,
    build_gate_input,
    confirmation_boundary,
    confirmation_ticket,
    credential,
    denied_boundary,
    expired_lease,
    full_permit,
    granted_boundary,
    mismatched_scope,
    resource_limit,
    validate,
)
from tiangong_kernel.l4_action_grounding import PermitValidationStatus


def test_l4_phase2_missing_permit_ref_returns_standard_failure():
    result = validate(build_gate_input(permit=None))
    assert result.status is PermitValidationStatus.REJECTED
    assert result.allowed_for_grounding is False
    assert result.normalized_failure is not None
    assert result.real_action_performed is False


def test_l4_phase2_malformed_permit_returns_malformed_failure():
    result = validate(build_gate_input(permit=full_permit(scope=None)))
    assert result.status is PermitValidationStatus.MALFORMED
    assert result.validation_result.reason.value == "permit_malformed"


def test_l4_phase2_expired_permit_returns_expired_failure():
    result = validate(build_gate_input(permit=full_permit(expired=True)))
    assert result.status is PermitValidationStatus.REJECTED
    assert "expired" in result.boundary_feedback_summary


def test_l4_phase2_scope_mismatch_returns_scope_mismatch_failure():
    result = validate(build_gate_input(permit=full_permit(scope=mismatched_scope())))
    assert result.status is PermitValidationStatus.REJECTED
    assert result.validation_result.reason.value == "scope_mismatch"


def test_l4_phase2_boundary_denied_returns_boundary_failure():
    boundary = denied_boundary()
    result = validate(build_gate_input(permit=full_permit(boundary=boundary), boundary=boundary))
    assert result.status is PermitValidationStatus.REJECTED
    assert result.validation_result.reason.value == "boundary_denied"


def test_l4_phase2_confirmation_required_does_not_auto_confirm():
    result = validate(build_gate_input(permit=full_permit(boundary=confirmation_boundary()), boundary=confirmation_boundary()))
    assert result.status is PermitValidationStatus.CONFIRMATION_REQUIRED
    assert result.allowed_for_grounding is False
    assert result.l4_authorized_action is False
    assert result.normalized_failure is None


def test_l4_phase2_confirmation_ticket_required_does_not_auto_confirm():
    ticket = confirmation_ticket(required=True, confirmed=False)
    result = validate(build_gate_input(permit=full_permit(confirmation_ticket=ticket), confirmation_ticket_ref=ticket))
    assert result.status is PermitValidationStatus.CONFIRMATION_REQUIRED
    assert result.allowed_for_grounding is False
    assert result.l4_authorized_action is False


def test_l4_phase2_lease_missing_or_expired_does_not_auto_extend():
    result = validate(build_gate_input(permit=full_permit(), lease_required=True))
    assert result.status is PermitValidationStatus.REJECTED
    assert result.validation_result.reason.value == "lease_unavailable"
    result_expired = validate(build_gate_input(permit=full_permit(lease=expired_lease()), lease=expired_lease(), lease_required=True), offset=10)
    assert result_expired.status is PermitValidationStatus.REJECTED


def test_l4_phase2_credential_audit_resource_missing_are_failures():
    credential_result = validate(build_gate_input(permit=full_permit(), credential_required=True))
    audit_result = validate(build_gate_input(permit=full_permit(), audit_required=True), offset=10)
    resource_result = validate(build_gate_input(permit=full_permit(), resource_limit_required=True), offset=20)
    assert credential_result.validation_result.reason.value == "credential_unavailable"
    assert audit_result.validation_result.reason.value == "audit_requirement_missing"
    assert resource_result.validation_result.reason.value == "resource_limit_unavailable"


def test_l4_phase2_accepted_means_structural_grounding_not_l4_authorization():
    permit = full_permit(
        boundary=granted_boundary(),
        credential=credential(),
        audit=audit_requirement(),
        resource=resource_limit(),
    )
    result = validate(
        build_gate_input(
            permit=permit,
            boundary=granted_boundary(),
            credential=credential(),
            audit=audit_requirement(),
            resource=resource_limit(),
            boundary_required=True,
            credential_required=True,
            audit_required=True,
            resource_limit_required=True,
        )
    )
    assert result.status is PermitValidationStatus.ACCEPTED
    assert result.allowed_for_grounding is True
    assert result.l4_authorized_action is False
    assert result.validation_result.l4_authorized_action is False
    assert result.permit_consumption_summary.l4_consumed_real_resource is False


def test_l4_phase2_resource_exceeded_is_not_consumed():
    result = validate(build_gate_input(permit=full_permit(resource=resource_limit("exceeded")), resource=resource_limit("exceeded")))
    assert result.status is PermitValidationStatus.REJECTED
    assert result.normalized_failure is not None
    assert "exceeded" in result.boundary_feedback_summary
