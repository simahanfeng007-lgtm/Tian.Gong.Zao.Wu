"""L3 第四阶段意图路径排序与前三阶段接线对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .intent_envelope import ActionIntentRef, IntentKind, ModelIntentRef, ToolIntentRef
from .intent_math import IntentMathResult
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind
from .orchestration_math_result import RankingOrder
from .orchestration_resume import ResumeAdviceKind
from .skill_visibility import SkillSelectionAdvice
from .tool_group_release_advice import ToolGroupReleaseAdvice


class IntentRouteKind(str, Enum):
    """意图路径类别。"""

    UNKNOWN = "unknown"
    CLARIFY_MODEL_INTENT = "clarify_model_intent"
    PREPARE_TOOL_INTENT_REVIEW = "prepare_tool_intent_review"
    PREPARE_ACTION_REVIEW = "prepare_action_review"
    DOWNGRADE_INTENT = "downgrade_intent"
    REJECT_INTENT_PATH = "reject_intent_path"
    RETRY_WITH_MORE_CONTEXT = "retry_with_more_context"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _route_score(candidate: "IntentRouteCandidate") -> float:
    return round(
        (candidate.readiness_score * 0.30)
        + (candidate.completeness_score * 0.24)
        + ((1.0 - candidate.ambiguity_score) * 0.18)
        + (candidate.continuity_score * 0.12)
        + (candidate.reversibility_score * 0.08)
        + ((1.0 - candidate.clarification_need_score) * 0.04)
        + ((1.0 - candidate.degrade_score) * 0.04),
        6,
    )


def _ref_sort_value(ref_value: TypedRef | None) -> str:
    if ref_value is None:
        return ""
    return ref_value.ref_id.value + ":" + ref_value.ref_type


@dataclass(frozen=True, slots=True)
class IntentRouteCandidate:
    """意图路径候选；只用于排序建议。"""

    route_ref: TypedRef
    route_kind: IntentRouteKind = IntentRouteKind.UNKNOWN
    intent_kind: IntentKind = IntentKind.UNKNOWN
    model_intent_ref: TypedRef | None = None
    tool_intent_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    readiness_score: float = 0.0
    completeness_score: float = 0.0
    ambiguity_score: float = 0.0
    continuity_score: float = 0.0
    reversibility_score: float = 0.0
    clarification_need_score: float = 0.0
    degrade_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "readiness_score",
            "completeness_score",
            "ambiguity_score",
            "continuity_score",
            "reversibility_score",
            "clarification_need_score",
            "degrade_score",
        ):
            _ensure_unit_interval(getattr(self, field_name), f"IntentRouteCandidate.{field_name}")
        for item in self.reason_codes:
            _ensure_short_text(item, "IntentRouteCandidate.reason_codes", 128)
        if self.advisory_only is not True:
            raise ValueError("IntentRouteCandidate.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentRouteCandidate.schema_version cannot be empty")

    @property
    def weighted_score_hint(self) -> float:
        return _route_score(self)


@dataclass(frozen=True, slots=True)
class IntentRouteRanking:
    """意图路径排序结果；不代表最终路径裁决。"""

    ranking_ref: TypedRef
    candidates: tuple[IntentRouteCandidate, ...] = field(default_factory=tuple)
    order: RankingOrder = RankingOrder.HIGHER_SCORE_FIRST
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _, value in self.target_scores:
            _ensure_unit_interval(value, "IntentRouteRanking.target_scores value")
        _ensure_unit_interval(self.confidence, "IntentRouteRanking.confidence")
        _ensure_short_text(self.reason_summary, "IntentRouteRanking.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentRouteRanking.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunIntentAdvice:
    advice_ref: TypedRef
    run_ref: TypedRef
    route_ranking: IntentRouteRanking
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "RunIntentAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("RunIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("RunIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskIntentAdvice:
    advice_ref: TypedRef
    task_ref: TypedRef
    model_intent: ModelIntentRef | None = None
    tool_intent: ToolIntentRef | None = None
    action_intent: ActionIntentRef | None = None
    route_ranking_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TaskIntentAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("TaskIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("TaskIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnIntentAdvice:
    advice_ref: TypedRef
    turn_ref: TypedRef
    model_intent: ModelIntentRef | None = None
    carryover_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TurnIntentAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("TurnIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("TurnIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepIntentAdvice:
    advice_ref: TypedRef
    step_ref: TypedRef
    tool_intent: ToolIntentRef | None = None
    action_intent: ActionIntentRef | None = None
    readiness_hint_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "StepIntentAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("StepIntentAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("StepIntentAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillIntentLinkAdvice:
    advice_ref: TypedRef
    skill_selection_advice: SkillSelectionAdvice
    model_intent_ref: TypedRef | None = None
    tool_intent_ref: TypedRef | None = None
    link_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.link_score, "SkillIntentLinkAdvice.link_score")
        _ensure_short_text(self.reason_summary, "SkillIntentLinkAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillIntentLinkAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillIntentLinkAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolGroupIntentLinkAdvice:
    advice_ref: TypedRef
    tool_group_release_advice: ToolGroupReleaseAdvice
    tool_intent_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    link_score: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.link_score, "ToolGroupIntentLinkAdvice.link_score")
        _ensure_short_text(self.reason_summary, "ToolGroupIntentLinkAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("ToolGroupIntentLinkAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("ToolGroupIntentLinkAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentResumeAdvice:
    advice_ref: TypedRef
    route_ranking: IntentRouteRanking
    advice_kind: ResumeAdviceKind = ResumeAdviceKind.RESUME_NEXT_STEP
    suggested_route_ref: TypedRef | None = None
    math_result_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "IntentResumeAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentResumeAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentResumeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentInterruptionAdvice:
    advice_ref: TypedRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.ACTIVE
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.WAITING
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "IntentInterruptionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentInterruptionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentInterruptionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentContinuityAdvice:
    advice_ref: TypedRef
    route_ranking: IntentRouteRanking
    math_result: IntentMathResult
    recommended_route_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "IntentContinuityAdvice.confidence")
        _ensure_short_text(self.reason_summary, "IntentContinuityAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentContinuityAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentContinuityAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IntentRouteProjection:
    projection_ref: TypedRef
    route_ranking_ref: TypedRef
    projected_model_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    projected_tool_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    projected_action_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l5_preparation_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    future_l4_preparation_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "IntentRouteProjection.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("IntentRouteProjection.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("IntentRouteProjection.schema_version cannot be empty")


def build_intent_route_ranking(
    ranking_ref: TypedRef,
    candidates: tuple[IntentRouteCandidate, ...],
    confidence: float = 0.8,
    reason_summary: str = "intent route ranking advice",
) -> IntentRouteRanking:
    """生成稳定意图路径排序建议。"""

    ordered = tuple(
        sorted(
            candidates,
            key=lambda candidate: (-candidate.weighted_score_hint, _ref_sort_value(candidate.route_ref)),
        )
    )
    target_scores = tuple((candidate.route_ref, candidate.weighted_score_hint) for candidate in ordered)
    top_route_ref = ordered[0].route_ref if ordered else None
    return IntentRouteRanking(
        ranking_ref=ranking_ref,
        candidates=ordered,
        target_scores=target_scores,
        top_route_ref=top_route_ref,
        confidence=confidence,
        reason_summary=reason_summary,
    )
