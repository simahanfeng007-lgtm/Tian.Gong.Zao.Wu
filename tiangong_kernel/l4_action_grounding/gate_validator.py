"""L4 第二阶段动作落地门控结构校验器。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .boundary_failure import BoundaryDeniedFailure, BoundaryExpiredFailure, BoundaryMissingFailure, BoundaryScopeMismatchFailure
from .boundary_ref import BoundaryDecisionStatus
from .gate_input import ActionGroundingGateInput
from .gate_result import ActionGroundingGateResult
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_failure import (
    AuditRequirementMissingFailure,
    CredentialScopeMismatchFailure,
    CredentialUnavailableFailure,
    LeaseUnavailableFailure,
    PermitExpiredFailure,
    PermitMalformedFailure,
    PermitMissingFailure,
    PermitScopeMismatchFailure,
    PermitTestOnlyMisuseFailure,
    ResourceLimitExceededFailure,
    ResourceLimitUnavailableFailure,
)
from .permit_ref import PermitConsumptionRef
from .permit_validation import PermitValidationReason, PermitValidationResult, PermitValidationStatus, PermitValidationTrace


@dataclass(frozen=True, slots=True)
class ActionGroundingGateValidator:
    """只做 permit/ref 的结构校验，不做政策、风险或授权裁决。"""

    validator_ref: TypedRef
    structural_validation_only: bool = True
    l4_permission_decision_made: bool = False
    l4_risk_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.structural_validation_only, "ActionGroundingGateValidator.structural_validation_only")
        ensure_false(self.l4_permission_decision_made, "ActionGroundingGateValidator.l4_permission_decision_made")
        ensure_false(self.l4_risk_decision_made, "ActionGroundingGateValidator.l4_risk_decision_made")
        ensure_schema_version(self.schema_version, "ActionGroundingGateValidator.schema_version")

    def validate(
        self,
        gate_input: ActionGroundingGateInput,
        *,
        gate_result_ref: TypedRef,
        validation_result_ref: TypedRef,
        validation_trace_ref: TypedRef,
        failure_ref: TypedRef,
        permit_consumption_ref: TypedRef | None = None,
    ) -> ActionGroundingGateResult:
        checked_steps: list[str] = []

        def rejected(status: PermitValidationStatus, reason: PermitValidationReason, failure_obj, summary: str) -> ActionGroundingGateResult:
            checked_steps.append(reason.value)
            trace = PermitValidationTrace(trace_ref=validation_trace_ref, checked_step_names=tuple(checked_steps))
            validation = PermitValidationResult(
                result_ref=validation_result_ref,
                status=status,
                reason=reason,
                allowed_for_grounding=False,
                structurally_accepted_for_grounding=False,
                reason_summary=summary,
                validation_trace=trace,
            )
            return ActionGroundingGateResult(
                gate_result_ref=gate_result_ref,
                status=status,
                allowed_for_grounding=False,
                validation_result=validation,
                normalized_failure=failure_obj.to_action_failure(),
                boundary_feedback_summary=summary,
            )

        permit = gate_input.permit_ref
        if permit is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.PERMIT_MISSING,
                PermitMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "future L5 permit ref is missing",
            )
        checked_steps.append("permit_ref_present")

        if not permit.is_structurally_complete:
            return rejected(
                PermitValidationStatus.MALFORMED,
                PermitValidationReason.PERMIT_MALFORMED,
                PermitMalformedFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "future L5 permit ref is structurally incomplete",
            )
        checked_steps.append("permit_structure_complete")

        if gate_input.production_path and permit.test_only:
            return rejected(
                PermitValidationStatus.TEST_ONLY_REJECTED,
                PermitValidationReason.TEST_ONLY_MISUSE,
                PermitTestOnlyMisuseFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "test-only permit cannot be used on production path",
            )
        checked_steps.append("test_only_isolated")

        if gate_input.live_action_requested and gate_input.safety_chain_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.PERMIT_MISSING,
                PermitMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "safety_chain_ref is missing for live action request",
            )
        checked_steps.append("safety_chain_ref_checked")

        production_resource_required = gate_input.production_path or gate_input.resource_limit_required
        production_audit_required = gate_input.production_path or gate_input.audit_required
        production_boundary_required = gate_input.production_path or gate_input.boundary_required
        production_event_required = gate_input.production_path or gate_input.event_required
        production_evidence_required = gate_input.production_path or gate_input.evidence_required
        production_responsibility_required = gate_input.production_path or gate_input.responsibility_required
        production_provenance_required = gate_input.production_path or gate_input.provenance_required

        if permit.expiry is not None and permit.expiry.is_expired:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.PERMIT_EXPIRED,
                PermitExpiredFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "future L5 permit ref is explicitly expired",
            )
        checked_steps.append("permit_not_explicitly_expired")

        if permit.scope is not None and not permit.scope.structurally_covers(gate_input.requested_scope):
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.SCOPE_MISMATCH,
                PermitScopeMismatchFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "future L5 permit scope does not structurally cover requested scope",
            )
        checked_steps.append("permit_scope_structurally_matches")

        boundary = gate_input.boundary_decision_ref or permit.boundary_decision_ref
        if production_boundary_required and boundary is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.PERMIT_MISSING,
                BoundaryMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "boundary decision ref is missing",
            )
        if boundary is not None:
            if boundary.is_expired:
                return rejected(
                    PermitValidationStatus.REJECTED,
                    PermitValidationReason.PERMIT_EXPIRED,
                    BoundaryExpiredFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                    "boundary decision ref is expired",
                )
            if boundary.scope is not None and not boundary.scope.structurally_covers(gate_input.requested_scope):
                return rejected(
                    PermitValidationStatus.REJECTED,
                    PermitValidationReason.SCOPE_MISMATCH,
                    BoundaryScopeMismatchFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                    "boundary decision scope does not structurally cover requested scope",
                )
            if boundary.decision_status is BoundaryDecisionStatus.DENIED:
                return rejected(
                    PermitValidationStatus.REJECTED,
                    PermitValidationReason.BOUNDARY_DENIED,
                    BoundaryDeniedFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                    "boundary decision ref explicitly denies grounding",
                )
            if boundary.decision_status is BoundaryDecisionStatus.CONFIRMATION_REQUIRED:
                trace = PermitValidationTrace(trace_ref=validation_trace_ref, checked_step_names=tuple(checked_steps + ["confirmation_required"]))
                validation = PermitValidationResult(
                    result_ref=validation_result_ref,
                    status=PermitValidationStatus.CONFIRMATION_REQUIRED,
                    reason=PermitValidationReason.CONFIRMATION_REQUIRED,
                    allowed_for_grounding=False,
                    reason_summary="confirmation is required by boundary decision ref",
                    validation_trace=trace,
                )
                return ActionGroundingGateResult(
                    gate_result_ref=gate_result_ref,
                    status=PermitValidationStatus.CONFIRMATION_REQUIRED,
                    allowed_for_grounding=False,
                    validation_result=validation,
                    boundary_feedback_summary="confirmation is required; L4 does not confirm",
                )
        checked_steps.append("boundary_ref_checked")

        ticket = gate_input.confirmation_ticket_ref or permit.confirmation_ticket_ref
        if ticket is not None and ticket.confirmation_required and not ticket.confirmed_by_l5:
            trace = PermitValidationTrace(trace_ref=validation_trace_ref, checked_step_names=tuple(checked_steps + ["confirmation_ticket_required"]))
            validation = PermitValidationResult(
                result_ref=validation_result_ref,
                status=PermitValidationStatus.CONFIRMATION_REQUIRED,
                reason=PermitValidationReason.CONFIRMATION_REQUIRED,
                allowed_for_grounding=False,
                reason_summary="confirmation ticket ref requires confirmation",
                validation_trace=trace,
            )
            return ActionGroundingGateResult(
                gate_result_ref=gate_result_ref,
                status=PermitValidationStatus.CONFIRMATION_REQUIRED,
                allowed_for_grounding=False,
                validation_result=validation,
                boundary_feedback_summary="confirmation ticket is required; L4 does not issue or confirm tickets",
            )

        lease = gate_input.lease_ref or permit.lease_ref
        if gate_input.lease_required and (lease is None or lease.is_expired):
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.LEASE_UNAVAILABLE,
                LeaseUnavailableFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "lease ref is unavailable or explicitly expired",
            )
        checked_steps.append("lease_ref_checked")

        credential = gate_input.credential_handle_ref or permit.credential_handle_ref
        if gate_input.credential_required and credential is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.CREDENTIAL_UNAVAILABLE,
                CredentialUnavailableFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "credential handle ref is unavailable",
            )
        if credential is not None and credential.scope is not None and not credential.scope.structurally_covers(gate_input.requested_scope):
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.CREDENTIAL_UNAVAILABLE,
                CredentialScopeMismatchFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "credential handle scope does not structurally cover requested scope",
            )
        checked_steps.append("credential_ref_checked")

        resource = gate_input.resource_limit_ref or permit.resource_limit_ref
        if production_resource_required and resource is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.RESOURCE_LIMIT_UNAVAILABLE,
                ResourceLimitUnavailableFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "resource limit ref is unavailable",
            )
        if resource is not None and resource.availability_hint in {"exceeded", "blocked", "unavailable"}:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.RESOURCE_LIMIT_UNAVAILABLE,
                ResourceLimitExceededFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "resource limit ref reports exceeded or unavailable status",
            )
        checked_steps.append("resource_limit_ref_checked")

        audit = gate_input.audit_requirement_ref or permit.audit_requirement_ref
        if production_audit_required and audit is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "audit requirement ref is missing",
            )
        checked_steps.append("audit_requirement_ref_checked")

        if production_event_required and gate_input.event_ref is None and gate_input.event_requirement_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "event ref or event requirement ref is missing",
            )
        checked_steps.append("event_ref_checked")

        if production_evidence_required and gate_input.evidence_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "evidence ref is missing",
            )
        checked_steps.append("evidence_ref_checked")

        if production_responsibility_required and gate_input.responsibility_chain_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "responsibility chain ref is missing",
            )
        checked_steps.append("responsibility_ref_checked")

        if production_provenance_required and gate_input.provenance_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "provenance ref is missing",
            )
        checked_steps.append("provenance_ref_checked")

        if gate_input.tamper_required and gate_input.tamper_evidence_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "tamper evidence ref is missing",
            )
        checked_steps.append("tamper_ref_checked")

        if gate_input.integrity_required and gate_input.integrity_chain_ref is None:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.AUDIT_REQUIREMENT_MISSING,
                AuditRequirementMissingFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "integrity chain ref is missing",
            )
        checked_steps.append("integrity_ref_checked")

        if gate_input.data_governance_required and not gate_input.data_governance_refs:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.CREDENTIAL_UNAVAILABLE,
                CredentialUnavailableFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "data governance refs are missing",
            )
        checked_steps.append("data_governance_refs_checked")

        if gate_input.disclosure_boundary_required and not gate_input.disclosure_boundary_refs:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.CREDENTIAL_UNAVAILABLE,
                CredentialUnavailableFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "disclosure boundary refs are missing",
            )
        checked_steps.append("disclosure_boundary_refs_checked")

        if gate_input.explicit_token_revoked or gate_input.explicit_credential_revoked:
            return rejected(
                PermitValidationStatus.REJECTED,
                PermitValidationReason.CREDENTIAL_UNAVAILABLE,
                CredentialUnavailableFailure(failure_ref=failure_ref, source_request_ref=gate_input.source_request_ref),
                "token or credential is explicitly revoked by boundary signal",
            )
        checked_steps.append("revocation_refs_checked")

        trace = PermitValidationTrace(trace_ref=validation_trace_ref, checked_step_names=tuple(checked_steps + ["structure_accepted"]))
        validation = PermitValidationResult(
            result_ref=validation_result_ref,
            status=PermitValidationStatus.ACCEPTED,
            reason=PermitValidationReason.STRUCTURE_ACCEPTED,
            allowed_for_grounding=True,
            structurally_accepted_for_grounding=True,
            reason_summary="future L5 permit ref is structurally acceptable for grounding",
            validation_trace=trace,
        )
        consumption = PermitConsumptionRef(permit_consumption_ref) if permit_consumption_ref is not None else None
        return ActionGroundingGateResult(
            gate_result_ref=gate_result_ref,
            status=PermitValidationStatus.ACCEPTED,
            allowed_for_grounding=True,
            validation_result=validation,
            permit_consumption_summary=consumption,
            audit_requirement_ref=audit,
            boundary_feedback_ref=boundary.decision_ref if boundary is not None else None,
            boundary_feedback_summary="structure accepted; this is not L4 authorization",
        )


ExecutionGateValidator = ActionGroundingGateValidator
