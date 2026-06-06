"""L3 第三阶段 Skill / ToolGroup 路径排序与前两阶段接线对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_continuity import ContinuityEvaluationSet
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind
from .orchestration_math_result import RankingOrder
from .orchestration_resume import ResumeAdviceKind
from .skill_tool_math import SkillToolMathResult
from .skill_visibility import SkillActivationAdvice, SkillDisplayAdvice, SkillSelectionAdvice
from .tool_group_release_advice import ToolGroupReleaseAdvice


class SkillToolRouteKind(str, Enum):
    """Skill / ToolGroup 路径类别。"""

    UNKNOWN = "unknown"
    DISPLAY_ONLY = "display_only"
    SELECT_AND_PREPARE = "select_and_prepare"
    PREPARE_TOOL_GROUP = "prepare_tool_group"
    WAIT_FOR_REVIEW = "wait_for_review"
    PAUSE_FOR_CLARIFICATION = "pause_for_clarification"


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


@dataclass(frozen=True, slots=True)
class SkillToolRouteCandidate:
    """Skill 与工具组组合路径候选。"""

    route_ref: TypedRef
    route_kind: SkillToolRouteKind = SkillToolRouteKind.UNKNOWN
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    skill_score: float = 0.0
    tool_group_score: float = 0.0
    continuity_score: float = 0.0
    exposure_cost: float = 0.0
    reversibility_score: float = 0.0
    stability_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "skill_score",
            "tool_group_score",
            "continuity_score",
            "exposure_cost",
            "reversibility_score",
            "stability_score",
        ):
            _ensure_unit_interval(getattr(self, field_name), f"SkillToolRouteCandidate.{field_name}")
        if any(len(item) > 128 for item in self.reason_codes):
            raise ValueError("SkillToolRouteCandidate.reason_codes entries must be short")
        if self.advisory_only is not True:
            raise ValueError("SkillToolRouteCandidate.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolRouteCandidate.schema_version cannot be empty")

    @property
    def weighted_score_hint(self) -> float:
        """返回路径排序提示值。"""

        return round(
            (self.skill_score * 0.24)
            + (self.tool_group_score * 0.22)
            + (self.continuity_score * 0.18)
            + (self.reversibility_score * 0.14)
            + (self.stability_score * 0.14)
            + ((1.0 - self.exposure_cost) * 0.08),
            6,
        )


@dataclass(frozen=True, slots=True)
class SkillToolRouteRanking:
    """Skill / ToolGroup 路径排序。"""

    ranking_ref: TypedRef
    route_candidates: tuple[SkillToolRouteCandidate, ...] = field(default_factory=tuple)
    order: RankingOrder = RankingOrder.HIGHER_SCORE_FIRST
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _, value in self.target_scores:
            _ensure_unit_interval(value, "SkillToolRouteRanking.target_scores value")
        _ensure_unit_interval(self.confidence, "SkillToolRouteRanking.confidence")
        _ensure_short_text(self.reason_summary, "SkillToolRouteRanking.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolRouteRanking.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolRouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunSkillDisplayAdvice:
    """Run 级 Skill 直显建议接线。"""

    advice_ref: TypedRef
    run_ref: TypedRef
    display_advice: SkillDisplayAdvice
    continuity_evaluation_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "RunSkillDisplayAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("RunSkillDisplayAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("RunSkillDisplayAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskSkillSelectionAdvice:
    """Task 级 Skill 选择建议接线。"""

    advice_ref: TypedRef
    task_ref: TypedRef
    selection_advice: SkillSelectionAdvice
    route_ranking_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TaskSkillSelectionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("TaskSkillSelectionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("TaskSkillSelectionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TurnSkillActivationAdvice:
    """Turn 级 Skill 激活建议接线。"""

    advice_ref: TypedRef
    turn_ref: TypedRef
    activation_advice: SkillActivationAdvice
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "TurnSkillActivationAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("TurnSkillActivationAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("TurnSkillActivationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StepToolGroupReleaseAdvice:
    """Step 级工具组释放建议接线。"""

    advice_ref: TypedRef
    step_ref: TypedRef
    release_advice: ToolGroupReleaseAdvice
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "StepToolGroupReleaseAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("StepToolGroupReleaseAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("StepToolGroupReleaseAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillToolResumeAdvice:
    """Skill / ToolGroup 编排续接建议。"""

    advice_ref: TypedRef
    route_ranking: SkillToolRouteRanking
    advice_kind: ResumeAdviceKind = ResumeAdviceKind.RESUME_CURRENT
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.RESUMABLE
    suggested_route_ref: TypedRef | None = None
    math_result_ref: TypedRef | None = None
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.advice_kind, ResumeAdviceKind):
            raise ValueError("SkillToolResumeAdvice.advice_kind must use ResumeAdviceKind")
        _ensure_short_text(self.reason_summary, "SkillToolResumeAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolResumeAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolResumeAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillToolInterruptionAdvice:
    """Skill / ToolGroup 编排中断建议。"""

    advice_ref: TypedRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.ACTIVE
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.WAITING
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.reason_summary, "SkillToolInterruptionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolInterruptionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolInterruptionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillToolContinuityAdvice:
    """Skill / ToolGroup 编排连续性建议。"""

    advice_ref: TypedRef
    continuity_evaluation: ContinuityEvaluationSet
    route_ranking: SkillToolRouteRanking
    math_result: SkillToolMathResult | None = None
    recommended_route_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "SkillToolContinuityAdvice.confidence")
        _ensure_short_text(self.reason_summary, "SkillToolContinuityAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillToolContinuityAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillToolContinuityAdvice.schema_version cannot be empty")


def build_skill_tool_route_ranking(
    ranking_ref: TypedRef,
    route_candidates: tuple[SkillToolRouteCandidate, ...],
    confidence: float = 0.8,
    reason_summary: str = "skill tool route ranking advice",
) -> SkillToolRouteRanking:
    """生成稳定 Skill / ToolGroup 路径排序建议。"""

    ordered = tuple(
        sorted(
            route_candidates,
            key=lambda item: (-item.weighted_score_hint, _ref_sort_value(item.skill_ref), _ref_sort_value(item.route_ref)),
        )
    )
    target_scores = tuple((item.route_ref, item.weighted_score_hint) for item in ordered)
    top_ref = ordered[0].route_ref if ordered else None
    return SkillToolRouteRanking(
        ranking_ref=ranking_ref,
        route_candidates=ordered,
        order=RankingOrder.HIGHER_SCORE_FIRST,
        target_scores=target_scores,
        top_route_ref=top_ref,
        confidence=confidence,
        reason_summary=reason_summary,
    )
