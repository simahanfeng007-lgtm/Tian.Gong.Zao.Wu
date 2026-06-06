from l3_phase1_builders import typed
from l4_phase1_builders import build_l4_phase1_objects
from tiangong_kernel.l4_action_grounding import (
    ActionGroundingGateInput,
    ActionGroundingGateValidator,
    ActionPermitRef,
    AuditRequirementRef,
    BoundaryDecisionRef,
    BoundaryDecisionStatus,
    ConfirmationTicketRef,
    CredentialHandleRef,
    LeaseRef,
    PermitActionRef,
    PermitExpiry,
    PermitIssuerRef,
    PermitScope,
    PermitSubjectRef,
    ResourceLimitRef,
)


def phase2_refs(offset: int = 0):
    return {
        "gate_input_ref": typed(5000 + offset, "l4_gate_input"),
        "gate_result_ref": typed(5001 + offset, "l4_gate_result"),
        "validation_result_ref": typed(5002 + offset, "l4_validation_result"),
        "validation_trace_ref": typed(5003 + offset, "l4_validation_trace"),
        "failure_ref": typed(5004 + offset, "l4_gate_failure"),
        "consumption_ref": typed(5005 + offset, "permit_consumption"),
    }


def requested_scope():
    return PermitScope(
        action_scope=("tool_call",),
        resource_scope=("workspace_ref",),
        environment_scope=("local_test_env",),
    )


def broader_scope():
    return PermitScope(
        action_scope=("tool_call", "dry_run"),
        resource_scope=("workspace_ref", "docs_ref"),
        environment_scope=("local_test_env",),
    )


def mismatched_scope():
    return PermitScope(action_scope=("network_call",), resource_scope=("external_net",), environment_scope=("prod_env",))


def full_permit(
    *,
    scope="__default__",
    expired: bool = False,
    test_only: bool = False,
    boundary=None,
    confirmation_ticket=None,
    lease=None,
    credential=None,
    audit=None,
    resource=None,
):
    permit_scope = broader_scope() if scope == "__default__" else scope
    return ActionPermitRef(
        permit_ref=typed(5010, "future_l5_permit"),
        scope=permit_scope,
        expiry=PermitExpiry("2099-01-01T00:00:00Z", explicit_expired=expired),
        issuer_ref=PermitIssuerRef(typed(5011, "future_l5_issuer")),
        subject_ref=PermitSubjectRef(typed(5012, "permit_subject")),
        action_ref=PermitActionRef(typed(5013, "permit_action")),
        boundary_decision_ref=boundary,
        confirmation_ticket_ref=confirmation_ticket,
        lease_ref=lease,
        credential_handle_ref=credential,
        audit_requirement_ref=audit,
        resource_limit_ref=resource,
        test_only=test_only,
    )


def build_gate_input(
    *,
    permit=None,
    production_path: bool = False,
    boundary=None,
    boundary_required: bool = False,
    confirmation_ticket_ref=None,
    lease=None,
    lease_required: bool = False,
    credential=None,
    credential_required: bool = False,
    audit=None,
    audit_required: bool = False,
    resource=None,
    resource_limit_required: bool = False,
):
    phase1 = build_l4_phase1_objects(include_permit=False)
    return ActionGroundingGateInput(
        gate_input_ref=typed(5020, "l4_gate_input"),
        intake=phase1["intake"],
        context=phase1["context"],
        requested_scope=requested_scope(),
        permit_ref=permit,
        boundary_decision_ref=boundary,
        confirmation_ticket_ref=confirmation_ticket_ref,
        lease_ref=lease,
        credential_handle_ref=credential,
        audit_requirement_ref=audit,
        resource_limit_ref=resource,
        production_path=production_path,
        boundary_required=boundary_required,
        lease_required=lease_required,
        credential_required=credential_required,
        audit_required=audit_required,
        resource_limit_required=resource_limit_required,
    )


def validator():
    return ActionGroundingGateValidator(validator_ref=typed(5030, "l4_gate_validator"))


def validate(gate_input, offset: int = 0):
    refs = phase2_refs(offset)
    return validator().validate(
        gate_input,
        gate_result_ref=refs["gate_result_ref"],
        validation_result_ref=refs["validation_result_ref"],
        validation_trace_ref=refs["validation_trace_ref"],
        failure_ref=refs["failure_ref"],
        permit_consumption_ref=refs["consumption_ref"],
    )


def granted_boundary(scope=None):
    return BoundaryDecisionRef(
        decision_ref=typed(5040, "boundary_decision"),
        decision_status=BoundaryDecisionStatus.GRANTED,
        scope=scope or broader_scope(),
    )


def denied_boundary():
    return BoundaryDecisionRef(decision_ref=typed(5041, "boundary_denied"), decision_status=BoundaryDecisionStatus.DENIED)


def confirmation_boundary():
    return BoundaryDecisionRef(
        decision_ref=typed(5042, "boundary_confirmation"),
        decision_status=BoundaryDecisionStatus.CONFIRMATION_REQUIRED,
    )


def valid_lease():
    return LeaseRef(lease_ref=typed(5050, "lease_ref"))


def expired_lease():
    return LeaseRef(lease_ref=typed(5051, "lease_ref"), explicit_expired=True)


def credential(scope=None):
    return CredentialHandleRef(handle_ref=typed(5060, "credential_handle"), scope=scope or broader_scope())


def audit_requirement():
    return AuditRequirementRef(requirement_ref=typed(5070, "audit_requirement"))


def resource_limit(availability_hint="referenced", scope=None):
    return ResourceLimitRef(limit_ref=typed(5080, "resource_limit"), scope=scope or broader_scope(), availability_hint=availability_hint)


def confirmation_ticket(required=True, confirmed=False):
    return ConfirmationTicketRef(
        ticket_ref=typed(5090, "confirmation_ticket"),
        confirmation_required=required,
        confirmed_by_l5=confirmed,
    )
