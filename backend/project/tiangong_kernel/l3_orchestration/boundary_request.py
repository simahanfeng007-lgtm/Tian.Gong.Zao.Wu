"""L3 第五阶段边界审查纯请求对象。

本模块只表达未来 L5 边界层可能需要审查的请求、证据引用、上下文引用与需求提示。
它不实现权限裁决、风险放行、确认票据签发、租约授予、凭据读取或审计写入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ActionIntentRef, ModelIntentRef, ToolIntentRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class BoundaryRequestKind(str, Enum):
    """边界请求类别；只表示请求类型，不表示审查结果。"""

    BOUNDARY_CHECK = "boundary_check"
    RISK_REVIEW = "risk_review"
    PERMISSION_REVIEW = "permission_review"
    CONFIRMATION = "confirmation"
    LEASE = "lease"


class BoundaryRequestStatus(str, Enum):
    """边界请求编排状态。"""

    DRAFT = "draft"
    PREPARED = "prepared"
    WAITING_FOR_EVIDENCE = "waiting_for_evidence"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    READY_FOR_FUTURE_REVIEW = "ready_for_future_review"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class BoundaryEvidenceRef:
    """边界审查证据引用；不读取证据内容。"""

    evidence_ref: TypedRef
    evidence_kind_hint: str = "unknown"
    source_intent_ref: TypedRef | None = None
    summary: str = ""
    confidence: float = 0.0
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.evidence_kind_hint, "BoundaryEvidenceRef.evidence_kind_hint", 128)
        _ensure_short_text(self.summary, "BoundaryEvidenceRef.summary")
        _ensure_unit_interval(self.confidence, "BoundaryEvidenceRef.confidence")
        if not self.schema_version:
            raise ValueError("BoundaryEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryContextSnapshotRef:
    """边界上下文快照引用；不创建、不持久化快照。"""

    snapshot_ref: TypedRef
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    intent_ref: TypedRef | None = None
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.summary, "BoundaryContextSnapshotRef.summary")
        if not self.schema_version:
            raise ValueError("BoundaryContextSnapshotRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryRequirementHint:
    """未来边界审查需求提示；不触发审查。"""

    hint_ref: TypedRef
    requirement_kind: BoundaryRequestKind = BoundaryRequestKind.BOUNDARY_CHECK
    required_field_names: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[BoundaryEvidenceRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.required_field_names + self.reason_codes:
            _ensure_short_text(item, "BoundaryRequirementHint short fields", 128)
        _ensure_short_text(self.summary, "BoundaryRequirementHint.summary")
        _ensure_advisory(self.advisory_only, "BoundaryRequirementHint.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryRequirementHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CredentialRequirementHint:
    """未来凭据审查需求提示；不读取凭据。"""

    hint_ref: TypedRef
    credential_scope_hint: str = "not_required_yet"
    related_request_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.credential_scope_hint, "CredentialRequirementHint.credential_scope_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "CredentialRequirementHint.reason_codes", 128)
        _ensure_short_text(self.summary, "CredentialRequirementHint.summary")
        _ensure_advisory(self.advisory_only, "CredentialRequirementHint.advisory_only")
        if not self.schema_version:
            raise ValueError("CredentialRequirementHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AuditRequirementHint:
    """未来审计记录需求提示；不写审计。"""

    hint_ref: TypedRef
    audit_scope_hint: str = "future_boundary_review"
    related_request_ref: TypedRef | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.audit_scope_hint, "AuditRequirementHint.audit_scope_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "AuditRequirementHint.reason_codes", 128)
        _ensure_short_text(self.summary, "AuditRequirementHint.summary")
        _ensure_advisory(self.advisory_only, "AuditRequirementHint.advisory_only")
        if not self.schema_version:
            raise ValueError("AuditRequirementHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryCheckRequestRef:
    """边界检查请求引用；不表示边界结果。"""

    request_ref: TypedRef
    model_intent_ref: ModelIntentRef | None = None
    tool_intent_ref: ToolIntentRef | None = None
    action_intent_ref: ActionIntentRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    request_kind: BoundaryRequestKind = BoundaryRequestKind.BOUNDARY_CHECK
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("BoundaryCheckRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryCheckRequest:
    """面向未来 L5 的边界检查纯请求对象。"""

    request_ref: BoundaryCheckRequestRef
    requested_review_kinds: tuple[BoundaryRequestKind, ...] = field(default_factory=tuple)
    evidence_refs: tuple[BoundaryEvidenceRef, ...] = field(default_factory=tuple)
    context_snapshot_refs: tuple[BoundaryContextSnapshotRef, ...] = field(default_factory=tuple)
    requirement_hints: tuple[BoundaryRequirementHint, ...] = field(default_factory=tuple)
    credential_requirement_hint: CredentialRequirementHint | None = None
    audit_requirement_hint: AuditRequirementHint | None = None
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.requested_review_kinds:
            raise ValueError("BoundaryCheckRequest.requested_review_kinds cannot be empty")
        _ensure_short_text(self.reason_summary, "BoundaryCheckRequest.reason_summary")
        _ensure_advisory(self.request_only, "BoundaryCheckRequest.request_only")
        if not self.schema_version:
            raise ValueError("BoundaryCheckRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryCheckEnvelope:
    """边界检查请求信封；不执行提交。"""

    envelope_ref: TypedRef
    request: BoundaryCheckRequest
    status: BoundaryRequestStatus = BoundaryRequestStatus.DRAFT
    present_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    readiness_hint: float = 0.0
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.present_field_names + self.missing_field_names:
            _ensure_short_text(item, "BoundaryCheckEnvelope field names", 128)
        _ensure_unit_interval(self.readiness_hint, "BoundaryCheckEnvelope.readiness_hint")
        _ensure_short_text(self.reason_summary, "BoundaryCheckEnvelope.reason_summary")
        _ensure_advisory(self.request_only, "BoundaryCheckEnvelope.request_only")
        if not self.schema_version:
            raise ValueError("BoundaryCheckEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RiskReviewRequestRef:
    request_ref: TypedRef
    boundary_request_ref: TypedRef | None = None
    source_intent_ref: TypedRef | None = None
    risk_scope_hint: str = "orchestration_risk_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.risk_scope_hint, "RiskReviewRequestRef.risk_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("RiskReviewRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RiskReviewRequest:
    """风险审查纯请求对象；不做风险放行。"""

    request_ref: RiskReviewRequestRef
    risk_factor_hints: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[BoundaryEvidenceRef, ...] = field(default_factory=tuple)
    clarification_needed: bool = False
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.risk_factor_hints:
            _ensure_short_text(item, "RiskReviewRequest.risk_factor_hints", 128)
        _ensure_short_text(self.reason_summary, "RiskReviewRequest.reason_summary")
        _ensure_advisory(self.request_only, "RiskReviewRequest.request_only")
        if not self.schema_version:
            raise ValueError("RiskReviewRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PermissionReviewRequestRef:
    request_ref: TypedRef
    boundary_request_ref: TypedRef | None = None
    source_intent_ref: TypedRef | None = None
    permission_scope_hint: str = "future_permission_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.permission_scope_hint, "PermissionReviewRequestRef.permission_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("PermissionReviewRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PermissionReviewRequest:
    """权限审查纯请求对象；不做权限裁决。"""

    request_ref: PermissionReviewRequestRef
    required_permission_hints: tuple[str, ...] = field(default_factory=tuple)
    context_snapshot_refs: tuple[BoundaryContextSnapshotRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.required_permission_hints:
            _ensure_short_text(item, "PermissionReviewRequest.required_permission_hints", 128)
        _ensure_short_text(self.reason_summary, "PermissionReviewRequest.reason_summary")
        _ensure_advisory(self.request_only, "PermissionReviewRequest.request_only")
        if not self.schema_version:
            raise ValueError("PermissionReviewRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ConfirmationRequestRef:
    request_ref: TypedRef
    boundary_request_ref: TypedRef | None = None
    source_intent_ref: TypedRef | None = None
    confirmation_scope_hint: str = "future_user_confirmation"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.confirmation_scope_hint, "ConfirmationRequestRef.confirmation_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("ConfirmationRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ConfirmationRequest:
    """确认纯请求对象；不签发确认票据。"""

    request_ref: ConfirmationRequestRef
    confirmation_prompt_hints: tuple[str, ...] = field(default_factory=tuple)
    required_acknowledgement_hints: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.confirmation_prompt_hints + self.required_acknowledgement_hints:
            _ensure_short_text(item, "ConfirmationRequest short fields", 256)
        _ensure_short_text(self.reason_summary, "ConfirmationRequest.reason_summary")
        _ensure_advisory(self.request_only, "ConfirmationRequest.request_only")
        if not self.schema_version:
            raise ValueError("ConfirmationRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LeaseRequestRef:
    request_ref: TypedRef
    boundary_request_ref: TypedRef | None = None
    source_tool_group_ref: TypedRef | None = None
    lease_scope_hint: str = "future_tool_lease_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.lease_scope_hint, "LeaseRequestRef.lease_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("LeaseRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LeaseRequest:
    """租约纯请求对象；不授予真实租约。"""

    request_ref: LeaseRequestRef
    lease_subject_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requested_scope_hints: tuple[str, ...] = field(default_factory=tuple)
    duration_hint: str = "future_review_required"
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.lease_subject_refs:
            raise ValueError("LeaseRequest.lease_subject_refs cannot be empty")
        for item in self.requested_scope_hints:
            _ensure_short_text(item, "LeaseRequest.requested_scope_hints", 128)
        _ensure_short_text(self.duration_hint, "LeaseRequest.duration_hint", 128)
        _ensure_short_text(self.reason_summary, "LeaseRequest.reason_summary")
        _ensure_advisory(self.request_only, "LeaseRequest.request_only")
        if not self.schema_version:
            raise ValueError("LeaseRequest.schema_version cannot be empty")
