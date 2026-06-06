"""L3 第三阶段 ToolGroup 解析、释放与租约编排建议对象。

本模块只表达工具组解析和释放建议，不解析真实工具组，不释放真实工具，不授予真实租约。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind
from .orchestration_math_result import RankingOrder


class ToolGroupAdviceKind(str, Enum):
    """工具组编排建议类别。"""

    UNKNOWN = "unknown"
    RESOLVE = "resolve"
    RELEASE = "release"
    MINIMAL_RELEASE = "minimal_release"
    LEASE_REQUEST = "lease_request"
    STATE_TRANSITION = "state_transition"


class ToolGroupReasonCode(str, Enum):
    """工具组建议解释码。"""

    SUFFICIENT_FOR_INTENT = "sufficient_for_intent"
    MINIMAL_EXPOSURE = "minimal_exposure"
    MISSING_REQUIRED_TOOL = "missing_required_tool"
    HIGH_EXPOSURE_COST = "high_exposure_cost"
    NEED_L5_REVIEW = "need_l5_review"
    UNKNOWN = "unknown"


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ref_sort_value(ref_value: TypedRef | None) -> str:
    if ref_value is None:
        return ""
    return ref_value.ref_id.value + ":" + ref_value.ref_type


def _release_candidate_score(candidate: "ToolGroupReleaseCandidate") -> float:
    return round(
        (candidate.sufficiency_score * 0.34)
        + (candidate.minimality_score * 0.28)
        + (candidate.readiness_score * 0.2)
        + ((1.0 - candidate.exposure_cost_score) * 0.18),
        6,
    )


@dataclass(frozen=True, slots=True)
class ToolGroupResolveRequestRef:
    """工具组解析请求引用。"""

    request_ref: TypedRef
    skill_ref: TypedRef | None = None
    source_advice_ref: TypedRef | None = None
    requested_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requested_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("ToolGroupResolveRequestRef.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupResolveRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupReleaseCandidate:
    """工具组释放候选；只保存引用和评分事实。"""

    candidate_ref: TypedRef
    tool_group_ref: TypedRef
    skill_ref: TypedRef | None = None
    tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    optional_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    minimality_score: float = 0.0
    sufficiency_score: float = 0.0
    exposure_cost_score: float = 0.0
    readiness_score: float = 0.0
    reason_codes: tuple[ToolGroupReasonCode, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.minimality_score, "ToolGroupReleaseCandidate.minimality_score")
        _ensure_unit_interval(self.sufficiency_score, "ToolGroupReleaseCandidate.sufficiency_score")
        _ensure_unit_interval(self.exposure_cost_score, "ToolGroupReleaseCandidate.exposure_cost_score")
        _ensure_unit_interval(self.readiness_score, "ToolGroupReleaseCandidate.readiness_score")
        if any(not isinstance(code, ToolGroupReasonCode) for code in self.reason_codes):
            raise ValueError("ToolGroupReleaseCandidate.reason_codes must use ToolGroupReasonCode")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupReleaseCandidate.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupReleaseCandidate.schema_version cannot be empty")

    @property
    def weighted_score_hint(self) -> float:
        """返回确定性工具组释放排序提示值。"""

        return _release_candidate_score(self)


@dataclass(frozen=True, slots=True)
class ToolGroupReleaseRanking:
    """工具组释放候选排序。"""

    ranking_ref: TypedRef
    candidates: tuple[ToolGroupReleaseCandidate, ...] = field(default_factory=tuple)
    order: RankingOrder = RankingOrder.HIGHER_SCORE_FIRST
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_tool_group_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _, value in self.target_scores:
            _ensure_unit_interval(value, "ToolGroupReleaseRanking.target_scores value")
        _ensure_unit_interval(self.confidence, "ToolGroupReleaseRanking.confidence")
        _ensure_short_text(self.reason_summary, "ToolGroupReleaseRanking.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupReleaseRanking.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupReleaseRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupReleaseAdvice:
    """工具组释放建议；不释放真实工具。"""

    advice_ref: TypedRef
    resolve_request_ref: ToolGroupResolveRequestRef
    release_ranking: ToolGroupReleaseRanking
    advice_kind: ToolGroupAdviceKind = ToolGroupAdviceKind.RELEASE
    suggested_tool_group_ref: TypedRef | None = None
    release_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advice_kind is not ToolGroupAdviceKind.RELEASE:
            raise ValueError("ToolGroupReleaseAdvice.advice_kind must be RELEASE")
        _ensure_short_text(self.reason_summary, "ToolGroupReleaseAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupReleaseAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupReleaseAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupMinimalReleaseAdvice:
    """最小充分工具组释放建议。"""

    advice_ref: TypedRef
    tool_group_ref: TypedRef
    kept_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    omitted_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    minimality_score: float = 0.0
    sufficiency_score: float = 0.0
    reason_codes: tuple[ToolGroupReasonCode, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.minimality_score, "ToolGroupMinimalReleaseAdvice.minimality_score")
        _ensure_unit_interval(self.sufficiency_score, "ToolGroupMinimalReleaseAdvice.sufficiency_score")
        if any(not isinstance(code, ToolGroupReasonCode) for code in self.reason_codes):
            raise ValueError("ToolGroupMinimalReleaseAdvice.reason_codes must use ToolGroupReasonCode")
        _ensure_short_text(self.reason_summary, "ToolGroupMinimalReleaseAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupMinimalReleaseAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupMinimalReleaseAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupLeaseAdvice:
    """工具组租约编排建议；只表达租约请求提示，不授予真实租约。"""

    advice_ref: TypedRef
    tool_group_ref: TypedRef
    tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    lease_request_ref: TypedRef | None = None
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    requested_scope_hint: str = "l3_advisory_only"
    requested_duration_hint: str = "unspecified"
    required_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.requested_scope_hint, "ToolGroupLeaseAdvice.requested_scope_hint", 128)
        _ensure_short_text(self.requested_duration_hint, "ToolGroupLeaseAdvice.requested_duration_hint", 128)
        _ensure_short_text(self.reason_summary, "ToolGroupLeaseAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupLeaseAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupLeaseAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupStateTransitionAdvice:
    """工具组编排状态转移建议；不写入状态。"""

    advice_ref: TypedRef
    tool_group_ref: TypedRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "ToolGroupStateTransitionAdvice.transition_score")
        _ensure_short_text(self.reason_summary, "ToolGroupStateTransitionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupStateTransitionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupStateTransitionAdvice.schema_version cannot be empty")


def build_tool_group_release_ranking(
    ranking_ref: TypedRef,
    candidates: tuple[ToolGroupReleaseCandidate, ...],
    confidence: float = 0.8,
    reason_summary: str = "tool group release ranking advice",
) -> ToolGroupReleaseRanking:
    """生成稳定工具组释放排序建议。"""

    ordered = tuple(
        sorted(
            candidates,
            key=lambda item: (-_release_candidate_score(item), _ref_sort_value(item.tool_group_ref), _ref_sort_value(item.candidate_ref)),
        )
    )
    target_scores = tuple((item.tool_group_ref, _release_candidate_score(item)) for item in ordered)
    top_ref = ordered[0].tool_group_ref if ordered else None
    return ToolGroupReleaseRanking(
        ranking_ref=ranking_ref,
        candidates=ordered,
        order=RankingOrder.HIGHER_SCORE_FIRST,
        target_scores=target_scores,
        top_tool_group_ref=top_ref,
        confidence=confidence,
        reason_summary=reason_summary,
    )
