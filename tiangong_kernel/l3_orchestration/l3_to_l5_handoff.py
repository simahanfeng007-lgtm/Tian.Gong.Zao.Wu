"""L3 → L5 边界层交接接口冻结对象。

本模块只表达未来 L5 需要消费的边界请求、引用、准备度摘要和冻结说明。
它不做真实权限、风险、确认、租约、凭据或审计处理。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .boundary_request import BoundaryCheckRequest, ConfirmationRequest, LeaseRequest, PermissionReviewRequest, RiskReviewRequest
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_flag(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class BoundaryDecisionRef:
    """未来 L5 返回的边界结论引用；不是 L3 裁决。"""

    decision_ref: TypedRef
    source_request_ref: TypedRef | None = None
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.ref_only, "BoundaryDecisionRef.ref_only")
        if not self.schema_version:
            raise ValueError("BoundaryDecisionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PolicyDecisionRef:
    """未来 L5 策略结论引用；不是 L3 策略引擎。"""

    decision_ref: TypedRef
    policy_hint: str = "future_policy_result_ref"
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.policy_hint, "PolicyDecisionRef.policy_hint", 128)
        _ensure_flag(self.ref_only, "PolicyDecisionRef.ref_only")
        if not self.schema_version:
            raise ValueError("PolicyDecisionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DenialReasonRef:
    """未来 L5 拒绝原因引用；不是 L3 拒绝动作。"""

    reason_ref: TypedRef
    source_request_ref: TypedRef | None = None
    reason_hint: str = "future_l5_reason_ref"
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_hint, "DenialReasonRef.reason_hint", 128)
        _ensure_flag(self.ref_only, "DenialReasonRef.ref_only")
        if not self.schema_version:
            raise ValueError("DenialReasonRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5BoundaryRequestBundle:
    """未来 L5 边界请求束；不提交裁决。"""

    bundle_ref: TypedRef
    boundary_requests: tuple[BoundaryCheckRequest, ...] = field(default_factory=tuple)
    risk_review_requests: tuple[RiskReviewRequest, ...] = field(default_factory=tuple)
    permission_review_requests: tuple[PermissionReviewRequest, ...] = field(default_factory=tuple)
    confirmation_requests: tuple[ConfirmationRequest, ...] = field(default_factory=tuple)
    lease_requests: tuple[LeaseRequest, ...] = field(default_factory=tuple)
    request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    bundle_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.bundle_only, "L3ToL5BoundaryRequestBundle.bundle_only")
        if not self.schema_version:
            raise ValueError("L3ToL5BoundaryRequestBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5BoundaryRefBundle:
    """未来 L5 回传引用束。"""

    bundle_ref: TypedRef
    boundary_decision_refs: tuple[BoundaryDecisionRef, ...] = field(default_factory=tuple)
    policy_decision_refs: tuple[PolicyDecisionRef, ...] = field(default_factory=tuple)
    denial_reason_refs: tuple[DenialReasonRef, ...] = field(default_factory=tuple)
    request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.ref_only, "L3ToL5BoundaryRefBundle.ref_only")
        if not self.schema_version:
            raise ValueError("L3ToL5BoundaryRefBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5BoundaryReadinessSummary:
    """边界请求准备度摘要；不等同放行。"""

    summary_ref: TypedRef
    request_bundle_ref: TypedRef | None = None
    readiness_score: float = 0.0
    evidence_sufficiency_score: float = 0.0
    missing_requirement_hints: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_score, "L3ToL5BoundaryReadinessSummary.readiness_score")
        _ensure_unit_interval(self.evidence_sufficiency_score, "L3ToL5BoundaryReadinessSummary.evidence_sufficiency_score")
        for item in self.missing_requirement_hints + self.reason_codes:
            _ensure_short_text(item, "L3ToL5BoundaryReadinessSummary text", 128)
        _ensure_flag(self.advisory_only, "L3ToL5BoundaryReadinessSummary.advisory_only")
        if not self.schema_version:
            raise ValueError("L3ToL5BoundaryReadinessSummary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5NonDecisionGuarantee:
    """L3 不裁决保证。"""

    guarantee_ref: TypedRef
    guarantee_items: tuple[str, ...] = ("no_permission_result", "no_risk_result", "no_ticket_issue", "no_lease_grant")
    confidence: float = 1.0
    guarantee_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.guarantee_items:
            _ensure_short_text(item, "L3ToL5NonDecisionGuarantee.guarantee_items", 128)
        _ensure_unit_interval(self.confidence, "L3ToL5NonDecisionGuarantee.confidence")
        _ensure_flag(self.guarantee_only, "L3ToL5NonDecisionGuarantee.guarantee_only")
        if not self.schema_version:
            raise ValueError("L3ToL5NonDecisionGuarantee.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5ExpectedConsumerNote:
    """未来 L5 消费方说明。"""

    note_ref: TypedRef
    expected_consumer_hint: str = "future_l5_boundary_layer"
    required_input_hints: tuple[str, ...] = ("BoundaryCheckRequest", "RiskReviewRequest", "PermissionReviewRequest", "ConfirmationRequest", "LeaseRequest")
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.expected_consumer_hint, "L3ToL5ExpectedConsumerNote.expected_consumer_hint", 128)
        for item in self.required_input_hints:
            _ensure_short_text(item, "L3ToL5ExpectedConsumerNote.required_input_hints", 128)
        _ensure_flag(self.note_only, "L3ToL5ExpectedConsumerNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL5ExpectedConsumerNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5InterfaceFreezeNote:
    """L3 → L5 接口冻结说明。"""

    note_ref: TypedRef
    frozen_object_names: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "L3 to L5 interface is request/ref based."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.frozen_object_names:
            _ensure_short_text(item, "L3ToL5InterfaceFreezeNote.frozen_object_names", 128)
        _ensure_short_text(self.summary, "L3ToL5InterfaceFreezeNote.summary")
        _ensure_flag(self.note_only, "L3ToL5InterfaceFreezeNote.note_only")
        if not self.schema_version:
            raise ValueError("L3ToL5InterfaceFreezeNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5CompatibilityCheckResult:
    """L3 → L5 交接兼容检查结果。"""

    result_ref: TypedRef
    checked_object_names: tuple[str, ...] = field(default_factory=tuple)
    missing_object_names: tuple[str, ...] = field(default_factory=tuple)
    compatibility_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.checked_object_names + self.missing_object_names:
            _ensure_short_text(item, "L3ToL5CompatibilityCheckResult names", 128)
        _ensure_unit_interval(self.compatibility_score, "L3ToL5CompatibilityCheckResult.compatibility_score")
        _ensure_flag(self.report_only, "L3ToL5CompatibilityCheckResult.report_only")
        if not self.schema_version:
            raise ValueError("L3ToL5CompatibilityCheckResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L5PlanningPrerequisiteNote:
    """L5 策划前置说明。"""

    note_ref: TypedRef
    prerequisite_hints: tuple[str, ...] = ("read_l3_boundary_freeze", "keep_decision_outside_l3")
    summary: str = "Future L5 planning must consume request objects and return refs."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.prerequisite_hints:
            _ensure_short_text(item, "L5PlanningPrerequisiteNote.prerequisite_hints", 128)
        _ensure_short_text(self.summary, "L5PlanningPrerequisiteNote.summary")
        _ensure_flag(self.note_only, "L5PlanningPrerequisiteNote.note_only")
        if not self.schema_version:
            raise ValueError("L5PlanningPrerequisiteNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L5BoundaryOpenQuestionNote:
    """L5 边界开放问题说明。"""

    note_ref: TypedRef
    question_hints: tuple[str, ...] = field(default_factory=tuple)
    summary: str = "Open questions are planning notes only."
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.question_hints:
            _ensure_short_text(item, "L5BoundaryOpenQuestionNote.question_hints", 128)
        _ensure_short_text(self.summary, "L5BoundaryOpenQuestionNote.summary")
        _ensure_flag(self.note_only, "L5BoundaryOpenQuestionNote.note_only")
        if not self.schema_version:
            raise ValueError("L5BoundaryOpenQuestionNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ToL5HandoffEnvelope:
    """L3 → L5 交接信封。"""

    envelope_ref: TypedRef
    request_bundle: L3ToL5BoundaryRequestBundle | None = None
    ref_bundle: L3ToL5BoundaryRefBundle | None = None
    readiness_summary: L3ToL5BoundaryReadinessSummary | None = None
    non_decision_guarantee: L3ToL5NonDecisionGuarantee | None = None
    expected_consumer_note: L3ToL5ExpectedConsumerNote | None = None
    freeze_note: L3ToL5InterfaceFreezeNote | None = None
    flow_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    side_effect_governance_chain_ref: TypedRef | None = None
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    handoff_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_flag(self.handoff_only, "L3ToL5HandoffEnvelope.handoff_only")
        if not self.schema_version:
            raise ValueError("L3ToL5HandoffEnvelope.schema_version cannot be empty")
