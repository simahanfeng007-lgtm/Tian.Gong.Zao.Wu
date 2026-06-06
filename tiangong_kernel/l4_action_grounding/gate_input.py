"""L4 第二阶段动作落地门控输入。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .audit_requirement import AuditRequirementRef
from .boundary_ref import BoundaryDecisionRef, ConfirmationTicketRef, LeaseRef, PolicyDecisionRef
from .context import ActionGroundingContext
from .credential_ref import CredentialHandleRef
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true
from .permit_ref import ActionPermitRef
from .permit_scope import PermitScope
from .request_intake import ActionRequestIntake
from .resource_limit_ref import ResourceLimitRef


@dataclass(frozen=True, slots=True)
class ActionGroundingGateInput:
    """动作落地门控输入；仅承载 L3 请求与未来 L5 许可引用。"""

    gate_input_ref: TypedRef
    intake: ActionRequestIntake
    context: ActionGroundingContext
    requested_scope: PermitScope
    permit_ref: ActionPermitRef | None = None
    boundary_decision_ref: BoundaryDecisionRef | None = None
    policy_decision_ref: PolicyDecisionRef | None = None
    confirmation_ticket_ref: ConfirmationTicketRef | None = None
    lease_ref: LeaseRef | None = None
    credential_handle_ref: CredentialHandleRef | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    resource_limit_ref: ResourceLimitRef | None = None
    safety_chain_ref: TypedRef | None = None
    transaction_requirement_ref: TypedRef | None = None
    secret_privacy_guard_ref: TypedRef | None = None
    event_requirement_ref: TypedRef | None = None
    event_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    responsibility_chain_ref: TypedRef | None = None
    provenance_ref: TypedRef | None = None
    tamper_evidence_ref: TypedRef | None = None
    integrity_chain_ref: TypedRef | None = None
    effect_intent_ref: TypedRef | None = None
    sandbox_policy_ref: TypedRef | None = None
    data_governance_refs: tuple[TypedRef, ...] = ()
    privacy_boundary_refs: tuple[TypedRef, ...] = ()
    disclosure_boundary_refs: tuple[TypedRef, ...] = ()
    trust_boundary_refs: tuple[TypedRef, ...] = ()
    capability_token_ref: TypedRef | None = None
    revocation_ref: TypedRef | None = None
    credential_status_ref: TypedRef | None = None
    explicit_token_revoked: bool = False
    explicit_credential_revoked: bool = False
    production_path: bool = False
    boundary_required: bool = False
    lease_required: bool = False
    credential_required: bool = False
    audit_required: bool = False
    resource_limit_required: bool = False
    event_required: bool = False
    evidence_required: bool = False
    responsibility_required: bool = False
    provenance_required: bool = False
    tamper_required: bool = False
    integrity_required: bool = False
    data_governance_required: bool = False
    disclosure_boundary_required: bool = False
    live_action_requested: bool = False
    gate_input_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.gate_input_only, "ActionGroundingGateInput.gate_input_only")
        ensure_schema_version(self.schema_version, "ActionGroundingGateInput.schema_version")

    @property
    def source_request_ref(self) -> TypedRef | None:
        return self.intake.source_request_ref


ExecutionGateInput = ActionGroundingGateInput
