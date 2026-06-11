"""L3 第七阶段恢复与回滚纯编排对象。

本模块只表达恢复请求、回滚建议与可逆性提示，不修改文件、不调用命令、
不触发真实恢复流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class RecoveryFlowKind(str, Enum):
    UNKNOWN = "unknown"
    REQUEST_RECOVERY_REVIEW = "request_recovery_review"
    REQUEST_ROLLBACK_REVIEW = "request_rollback_review"
    WAIT_FOR_STABLE_EVIDENCE = "wait_for_stable_evidence"
    FALLBACK_TO_SAFE_STATE = "fallback_to_safe_state"


class RecoveryEnvelopeStatus(str, Enum):
    DRAFT = "draft"
    READY_FOR_ADVICE = "ready_for_advice"
    NEEDS_PRECONDITION = "needs_precondition"
    NEEDS_REVIEW = "needs_review"


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
class RecoveryRequestRef:
    request_ref: TypedRef
    source_failure_ref: TypedRef | None = None
    request_kind_hint: str = "future_recovery_review"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.request_kind_hint, "RecoveryRequestRef.request_kind_hint", 128)
        if not self.schema_version:
            raise ValueError("RecoveryRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryTargetRef:
    target_ref: TypedRef
    target_kind_hint: str = "unknown"
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.target_kind_hint, "RecoveryTargetRef.target_kind_hint", 128)
        _ensure_short_text(self.summary, "RecoveryTargetRef.summary")
        _ensure_advisory(self.ref_only, "RecoveryTargetRef.ref_only")
        if not self.schema_version:
            raise ValueError("RecoveryTargetRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryRequirementHint:
    hint_ref: TypedRef
    requirement_kind_hint: str = "future_recovery_requirement"
    required_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.requirement_kind_hint, "RecoveryRequirementHint.requirement_kind_hint", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "RecoveryRequirementHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RecoveryRequirementHint.advisory_only")
        if not self.schema_version:
            raise ValueError("RecoveryRequirementHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryPreconditionHint:
    hint_ref: TypedRef
    precondition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_hint, "RecoveryPreconditionHint.readiness_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "RecoveryPreconditionHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RecoveryPreconditionHint.advisory_only")
        if not self.schema_version:
            raise ValueError("RecoveryPreconditionHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryRequest:
    request_ref: RecoveryRequestRef
    target_refs: tuple[RecoveryTargetRef, ...] = field(default_factory=tuple)
    requirement_hints: tuple[RecoveryRequirementHint, ...] = field(default_factory=tuple)
    precondition_hints: tuple[RecoveryPreconditionHint, ...] = field(default_factory=tuple)
    requested_scope_hint: str = "future_recovery_scope"
    reason_summary: str = ""
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.requested_scope_hint, "RecoveryRequest.requested_scope_hint", 128)
        _ensure_short_text(self.reason_summary, "RecoveryRequest.reason_summary")
        _ensure_advisory(self.request_only, "RecoveryRequest.request_only")
        if not self.schema_version:
            raise ValueError("RecoveryRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryEnvelope:
    envelope_ref: TypedRef
    request: RecoveryRequest
    status: RecoveryEnvelopeStatus = RecoveryEnvelopeStatus.DRAFT
    related_validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    present_field_names: tuple[str, ...] = field(default_factory=tuple)
    missing_field_names: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.present_field_names + self.missing_field_names:
            _ensure_short_text(item, "RecoveryEnvelope field names", 128)
        _ensure_short_text(self.reason_summary, "RecoveryEnvelope.reason_summary")
        _ensure_advisory(self.ref_only, "RecoveryEnvelope.ref_only")
        if not self.schema_version:
            raise ValueError("RecoveryEnvelope.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryFlowAdvice:
    advice_ref: TypedRef
    envelope: RecoveryEnvelope
    flow_kind: RecoveryFlowKind = RecoveryFlowKind.UNKNOWN
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "RecoveryFlowAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "RecoveryFlowAdvice.confidence")
        _ensure_advisory(self.advisory_only, "RecoveryFlowAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RecoveryFlowAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryScoreBase:
    score_ref: TypedRef
    value: float = 0.0
    confidence: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.value, f"{self.__class__.__name__}.value")
        _ensure_unit_interval(self.confidence, f"{self.__class__.__name__}.confidence")
        for item in self.reason_codes:
            _ensure_short_text(item, f"{self.__class__.__name__}.reason_codes", 128)
        _ensure_advisory(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryReadinessScore(RecoveryScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class RollbackNeedScore(RecoveryScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class ReversibilityScore(RecoveryScoreBase):
    pass


@dataclass(frozen=True, slots=True)
class RecoveryStateTransitionAdvice:
    advice_ref: TypedRef
    recovery_request_ref: TypedRef
    suggested_status: str = "recovery_advice_ready"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.suggested_status, "RecoveryStateTransitionAdvice.suggested_status", 128)
        for item in self.reason_codes:
            _ensure_short_text(item, "RecoveryStateTransitionAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "RecoveryStateTransitionAdvice.confidence")
        _ensure_advisory(self.advisory_only, "RecoveryStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RecoveryStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RollbackTargetRef:
    target_ref: TypedRef
    target_kind_hint: str = "future_reversible_target"
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.target_kind_hint, "RollbackTargetRef.target_kind_hint", 128)
        _ensure_advisory(self.ref_only, "RollbackTargetRef.ref_only")
        if not self.schema_version:
            raise ValueError("RollbackTargetRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RollbackPreconditionHint:
    hint_ref: TypedRef
    required_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_hint, "RollbackPreconditionHint.readiness_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "RollbackPreconditionHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RollbackPreconditionHint.advisory_only")
        if not self.schema_version:
            raise ValueError("RollbackPreconditionHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RollbackImpactHint:
    hint_ref: TypedRef
    impact_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    impact_level_hint: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.impact_level_hint, "RollbackImpactHint.impact_level_hint")
        for item in self.reason_codes:
            _ensure_short_text(item, "RollbackImpactHint.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RollbackImpactHint.advisory_only")
        if not self.schema_version:
            raise ValueError("RollbackImpactHint.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RollbackAdvice:
    advice_ref: TypedRef
    target_refs: tuple[RollbackTargetRef, ...] = field(default_factory=tuple)
    precondition_hints: tuple[RollbackPreconditionHint, ...] = field(default_factory=tuple)
    impact_hints: tuple[RollbackImpactHint, ...] = field(default_factory=tuple)
    rollback_need_score: RollbackNeedScore | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "RollbackAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "RollbackAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RollbackAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ReversibilityReviewAdvice:
    advice_ref: TypedRef
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reversibility_score: ReversibilityScore | None = None
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "ReversibilityReviewAdvice.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "ReversibilityReviewAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ReversibilityReviewAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryFallbackAdvice:
    advice_ref: TypedRef
    fallback_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "RecoveryFallbackAdvice.reason_codes", 128)
        _ensure_unit_interval(self.confidence, "RecoveryFallbackAdvice.confidence")
        _ensure_advisory(self.advisory_only, "RecoveryFallbackAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("RecoveryFallbackAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryRouteCandidate:
    route_ref: TypedRef
    route_kind: RecoveryFlowKind = RecoveryFlowKind.UNKNOWN
    score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.score, "RecoveryRouteCandidate.score")
        for item in self.reason_codes:
            _ensure_short_text(item, "RecoveryRouteCandidate.reason_codes", 128)
        if not self.schema_version:
            raise ValueError("RecoveryRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryRouteRanking:
    ranking_ref: TypedRef
    candidates: tuple[RecoveryRouteCandidate, ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.candidates:
            expected = max(self.candidates, key=lambda item: item.score).route_ref
            if self.top_route_ref is not None and self.top_route_ref != expected:
                raise ValueError("RecoveryRouteRanking.top_route_ref must match highest score")
        _ensure_short_text(self.reason_summary, "RecoveryRouteRanking.reason_summary")
        _ensure_advisory(self.advisory_only, "RecoveryRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("RecoveryRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryResultRef:
    result_ref: TypedRef
    recovery_request_ref: TypedRef | None = None
    result_kind_hint: str = "future_recovery_result"
    summary: str = ""
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.result_kind_hint, "RecoveryResultRef.result_kind_hint", 128)
        _ensure_short_text(self.summary, "RecoveryResultRef.summary")
        _ensure_advisory(self.ref_only, "RecoveryResultRef.ref_only")
        if not self.schema_version:
            raise ValueError("RecoveryResultRef.schema_version cannot be empty")


def build_recovery_route_ranking(ranking_ref: TypedRef, candidates: tuple[RecoveryRouteCandidate, ...]) -> RecoveryRouteRanking:
    ordered = tuple(sorted(candidates, key=lambda item: (-item.score, item.route_ref.ref_id.value)))
    top = ordered[0].route_ref if ordered else None
    return RecoveryRouteRanking(ranking_ref=ranking_ref, candidates=ordered, top_route_ref=top, reason_summary="recovery route ranking is deterministic advice only")
