"""L3 副作用安全链路 Flow。

本模块只表达 ActionIntent 到 L4 Gate 前的安全链路请求、引用与不变量。
它不调用 L4/L5/L6，不执行、不裁决、不签发、不写状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


def _ensure_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _ensure_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class SideEffectSafetyFlowBase:
    """副作用安全 Flow 基础对象，只保存引用。"""

    flow_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    input_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    request_only: bool = True
    advisory_only: bool = True
    ref_only: bool = True
    no_execution: bool = True
    no_decision: bool = True
    no_persistence: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.request_only, "SideEffectSafetyFlowBase.request_only")
        _ensure_true(self.advisory_only, "SideEffectSafetyFlowBase.advisory_only")
        _ensure_true(self.ref_only, "SideEffectSafetyFlowBase.ref_only")
        _ensure_true(self.no_execution, "SideEffectSafetyFlowBase.no_execution")
        _ensure_true(self.no_decision, "SideEffectSafetyFlowBase.no_decision")
        _ensure_true(self.no_persistence, "SideEffectSafetyFlowBase.no_persistence")
        if not self.schema_version:
            raise ValueError("SideEffectSafetyFlowBase.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ActionToEffectSafetyFlow(SideEffectSafetyFlowBase):
    effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    side_effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RiskPolicyBoundaryFlow(SideEffectSafetyFlowBase):
    risk_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    policy_reference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class LeaseApprovalFlow(SideEffectSafetyFlowBase):
    lease_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    approval_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lease_granted: bool = False
    approval_confirmed: bool = False

    def __post_init__(self) -> None:
        SideEffectSafetyFlowBase.__post_init__(self)
        _ensure_false(self.lease_granted, "LeaseApprovalFlow.lease_granted")
        _ensure_false(self.approval_confirmed, "LeaseApprovalFlow.approval_confirmed")


@dataclass(frozen=True, slots=True)
class SecretPrivacyGuardFlow(SideEffectSafetyFlowBase):
    secret_guard_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    privacy_guard_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    plain_secret_visible: bool = False
    external_disclosure_authorized: bool = False

    def __post_init__(self) -> None:
        SideEffectSafetyFlowBase.__post_init__(self)
        _ensure_false(self.plain_secret_visible, "SecretPrivacyGuardFlow.plain_secret_visible")
        _ensure_false(self.external_disclosure_authorized, "SecretPrivacyGuardFlow.external_disclosure_authorized")


@dataclass(frozen=True, slots=True)
class TransactionCompensationFlow(SideEffectSafetyFlowBase):
    transaction_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    compensation_plan_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    commit_performed: bool = False
    rollback_performed: bool = False

    def __post_init__(self) -> None:
        SideEffectSafetyFlowBase.__post_init__(self)
        _ensure_false(self.commit_performed, "TransactionCompensationFlow.commit_performed")
        _ensure_false(self.rollback_performed, "TransactionCompensationFlow.rollback_performed")


@dataclass(frozen=True, slots=True)
class AuditEvidenceRequirementFlow(SideEffectSafetyFlowBase):
    audit_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_write_performed: bool = False

    def __post_init__(self) -> None:
        SideEffectSafetyFlowBase.__post_init__(self)
        _ensure_false(self.audit_write_performed, "AuditEvidenceRequirementFlow.audit_write_performed")


@dataclass(frozen=True, slots=True)
class EffectAuthorizationFlow(SideEffectSafetyFlowBase):
    authorization_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    authorization_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    grants_permission: bool = False

    def __post_init__(self) -> None:
        SideEffectSafetyFlowBase.__post_init__(self)
        _ensure_false(self.grants_permission, "EffectAuthorizationFlow.grants_permission")


@dataclass(frozen=True, slots=True)
class SideEffectExecutionReadinessFlow(SideEffectSafetyFlowBase):
    safety_chain_ref: TypedRef | None = None
    l4_gate_input_ref: TypedRef | None = None
    dispatch_enabled: bool = False

    def __post_init__(self) -> None:
        SideEffectSafetyFlowBase.__post_init__(self)
        _ensure_false(self.dispatch_enabled, "SideEffectExecutionReadinessFlow.dispatch_enabled")


@dataclass(frozen=True, slots=True)
class SideEffectDispatchRequiresBoundaryBundleInvariant:
    invariant_ref: TypedRef | None = None
    boundary_bundle_required: bool = True
    invariant_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.boundary_bundle_required, "SideEffectDispatchRequiresBoundaryBundleInvariant.boundary_bundle_required")
        _ensure_true(self.invariant_only, "SideEffectDispatchRequiresBoundaryBundleInvariant.invariant_only")


@dataclass(frozen=True, slots=True)
class SideEffectDispatchRequiresAuditRequirementInvariant:
    invariant_ref: TypedRef | None = None
    audit_requirement_required: bool = True
    invariant_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.audit_requirement_required, "SideEffectDispatchRequiresAuditRequirementInvariant.audit_requirement_required")
        _ensure_true(self.invariant_only, "SideEffectDispatchRequiresAuditRequirementInvariant.invariant_only")


@dataclass(frozen=True, slots=True)
class SideEffectDispatchRequiresLeaseOrDenialInvariant:
    invariant_ref: TypedRef | None = None
    lease_or_denial_required: bool = True
    invariant_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.lease_or_denial_required, "SideEffectDispatchRequiresLeaseOrDenialInvariant.lease_or_denial_required")
        _ensure_true(self.invariant_only, "SideEffectDispatchRequiresLeaseOrDenialInvariant.invariant_only")


@dataclass(frozen=True, slots=True)
class SideEffectDispatchRequiresSecretPrivacyGuardInvariant:
    invariant_ref: TypedRef | None = None
    secret_privacy_guard_required: bool = True
    invariant_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.secret_privacy_guard_required, "SideEffectDispatchRequiresSecretPrivacyGuardInvariant.secret_privacy_guard_required")
        _ensure_true(self.invariant_only, "SideEffectDispatchRequiresSecretPrivacyGuardInvariant.invariant_only")


@dataclass(frozen=True, slots=True)
class SideEffectDispatchRequiresTransactionCompensationPlanInvariant:
    invariant_ref: TypedRef | None = None
    transaction_compensation_plan_required: bool = True
    invariant_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(
            self.transaction_compensation_plan_required,
            "SideEffectDispatchRequiresTransactionCompensationPlanInvariant.transaction_compensation_plan_required",
        )
        _ensure_true(self.invariant_only, "SideEffectDispatchRequiresTransactionCompensationPlanInvariant.invariant_only")


@dataclass(frozen=True, slots=True)
class NoExecutionDispatchWithoutSafetyChainInvariant:
    invariant_ref: TypedRef | None = None
    safety_chain_required: bool = True
    invariant_only: bool = True
    l3_dispatch_enabled: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_true(self.safety_chain_required, "NoExecutionDispatchWithoutSafetyChainInvariant.safety_chain_required")
        _ensure_true(self.invariant_only, "NoExecutionDispatchWithoutSafetyChainInvariant.invariant_only")
        _ensure_false(self.l3_dispatch_enabled, "NoExecutionDispatchWithoutSafetyChainInvariant.l3_dispatch_enabled")
