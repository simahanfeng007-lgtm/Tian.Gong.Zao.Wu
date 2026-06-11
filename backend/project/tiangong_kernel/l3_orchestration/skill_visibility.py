"""L3 第三阶段 Skill 直显、选择与激活编排建议对象。

本模块只表达 Skill 直显流程中的请求引用、候选、排序与建议。
它不实现真实 Skill 系统，不选择真实能力，不调用模型，不调用工具，不产生权限或执行结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_lifecycle import LifecycleTransitionIntent, OrchestrationLifecycleKind
from .orchestration_math_result import RankingOrder


class SkillVisibilityAdviceKind(str, Enum):
    """Skill 直显相关建议类别。"""

    UNKNOWN = "unknown"
    DISPLAY = "display"
    SELECT = "select"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    MISMATCH = "mismatch"
    NEED_CLARIFICATION = "need_clarification"
    STATE_TRANSITION = "state_transition"


class SkillDisplayReasonCode(str, Enum):
    """Skill 直显候选解释码。"""

    GOAL_MATCH = "goal_match"
    CONTINUITY_MATCH = "continuity_match"
    READY_FOR_NEXT_STAGE = "ready_for_next_stage"
    NEED_MORE_CONTEXT = "need_more_context"
    HIGH_EXPOSURE_CAUTION = "high_exposure_caution"
    UNKNOWN = "unknown"


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _candidate_score(candidate: "SkillDisplayCandidate") -> float:
    return round(
        (candidate.match_score * 0.42)
        + (candidate.readiness_score * 0.22)
        + (candidate.continuity_score * 0.22)
        + ((1.0 - candidate.risk_awareness_hint) * 0.14),
        6,
    )


def _ref_sort_value(ref_value: TypedRef | None) -> str:
    if ref_value is None:
        return ""
    return ref_value.ref_id.value + ":" + ref_value.ref_type


@dataclass(frozen=True, slots=True)
class SkillVisibilityRequestRef:
    """Skill 直显请求引用。"""

    request_ref: TypedRef
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    source_context_ref: TypedRef | None = None
    objective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("SkillVisibilityRequestRef.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillVisibilityRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillDisplayCandidate:
    """可直显 Skill 候选引用与轻量评分事实。"""

    candidate_ref: TypedRef
    skill_ref: TypedRef
    request_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    turn_ref: TypedRef | None = None
    step_ref: TypedRef | None = None
    skill_label: str = ""
    skill_summary: str = ""
    match_score: float = 0.0
    readiness_score: float = 0.0
    continuity_score: float = 0.0
    risk_awareness_hint: float = 0.0
    reason_codes: tuple[SkillDisplayReasonCode, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.skill_label, "SkillDisplayCandidate.skill_label", 128)
        _ensure_short_text(self.skill_summary, "SkillDisplayCandidate.skill_summary")
        _ensure_unit_interval(self.match_score, "SkillDisplayCandidate.match_score")
        _ensure_unit_interval(self.readiness_score, "SkillDisplayCandidate.readiness_score")
        _ensure_unit_interval(self.continuity_score, "SkillDisplayCandidate.continuity_score")
        _ensure_unit_interval(self.risk_awareness_hint, "SkillDisplayCandidate.risk_awareness_hint")
        if any(not isinstance(code, SkillDisplayReasonCode) for code in self.reason_codes):
            raise ValueError("SkillDisplayCandidate.reason_codes must use SkillDisplayReasonCode")
        if self.advisory_only is not True:
            raise ValueError("SkillDisplayCandidate.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillDisplayCandidate.schema_version cannot be empty")

    @property
    def weighted_score_hint(self) -> float:
        """返回确定性排序提示值；只供编排排序参考。"""

        return _candidate_score(self)


@dataclass(frozen=True, slots=True)
class SkillDisplayRanking:
    """Skill 直显候选排序结果。"""

    ranking_ref: TypedRef
    candidates: tuple[SkillDisplayCandidate, ...] = field(default_factory=tuple)
    order: RankingOrder = RankingOrder.HIGHER_SCORE_FIRST
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_ranked_skill_ref: TypedRef | None = None
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "SkillDisplayRanking.confidence")
        _ensure_short_text(self.reason_summary, "SkillDisplayRanking.reason_summary")
        for _, value in self.target_scores:
            _ensure_unit_interval(value, "SkillDisplayRanking.target_scores value")
        if self.advisory_only is not True:
            raise ValueError("SkillDisplayRanking.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillDisplayRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillDisplayAdvice:
    """Skill 直显建议。"""

    advice_ref: TypedRef
    request_ref: SkillVisibilityRequestRef
    ranking: SkillDisplayRanking
    advice_kind: SkillVisibilityAdviceKind = SkillVisibilityAdviceKind.DISPLAY
    display_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    need_clarification_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advice_kind is not SkillVisibilityAdviceKind.DISPLAY:
            raise ValueError("SkillDisplayAdvice.advice_kind must be DISPLAY")
        _ensure_short_text(self.reason_summary, "SkillDisplayAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillDisplayAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillDisplayAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillSelectionAdvice:
    """Skill 选择建议；只表达候选选择，不真实激活 Skill。"""

    advice_ref: TypedRef
    selected_skill_ref: TypedRef | None = None
    ranking_ref: TypedRef | None = None
    request_ref: TypedRef | None = None
    required_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    alternative_skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    selection_score: float = 0.0
    confidence: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.selection_score, "SkillSelectionAdvice.selection_score")
        _ensure_unit_interval(self.confidence, "SkillSelectionAdvice.confidence")
        _ensure_short_text(self.reason_summary, "SkillSelectionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillSelectionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillSelectionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillActivationAdvice:
    """Skill 激活建议；不执行激活。"""

    advice_ref: TypedRef
    skill_ref: TypedRef
    selection_advice_ref: TypedRef | None = None
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    activation_score: float = 0.0
    required_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_review_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.activation_score, "SkillActivationAdvice.activation_score")
        _ensure_short_text(self.reason_summary, "SkillActivationAdvice.reason_summary")
        if not isinstance(self.suggested_lifecycle, OrchestrationLifecycleKind):
            raise ValueError("SkillActivationAdvice.suggested_lifecycle must use OrchestrationLifecycleKind")
        if not isinstance(self.transition_intent, LifecycleTransitionIntent):
            raise ValueError("SkillActivationAdvice.transition_intent must use LifecycleTransitionIntent")
        if self.advisory_only is not True:
            raise ValueError("SkillActivationAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillActivationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillDeactivationAdvice:
    """Skill 停用建议；不修改真实 Skill 状态。"""

    advice_ref: TypedRef
    skill_ref: TypedRef
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PAUSED
    reason_codes: tuple[SkillDisplayReasonCode, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if any(not isinstance(code, SkillDisplayReasonCode) for code in self.reason_codes):
            raise ValueError("SkillDeactivationAdvice.reason_codes must use SkillDisplayReasonCode")
        _ensure_short_text(self.reason_summary, "SkillDeactivationAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillDeactivationAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillDeactivationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillMismatchAdvice:
    """Skill 不匹配建议。"""

    advice_ref: TypedRef
    skill_ref: TypedRef | None = None
    mismatch_score: float = 0.0
    missing_goal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[SkillDisplayReasonCode, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.mismatch_score, "SkillMismatchAdvice.mismatch_score")
        if any(not isinstance(code, SkillDisplayReasonCode) for code in self.reason_codes):
            raise ValueError("SkillMismatchAdvice.reason_codes must use SkillDisplayReasonCode")
        _ensure_short_text(self.reason_summary, "SkillMismatchAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillMismatchAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillMismatchAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillNeedClarificationAdvice:
    """Skill 选择前的澄清建议。"""

    advice_ref: TypedRef
    request_ref: TypedRef | None = None
    ambiguous_skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_context_fields: tuple[str, ...] = field(default_factory=tuple)
    clarification_priority: float = 0.0
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.clarification_priority, "SkillNeedClarificationAdvice.clarification_priority")
        if any(len(item) > 128 for item in self.missing_context_fields):
            raise ValueError("SkillNeedClarificationAdvice.missing_context_fields entries must be short")
        _ensure_short_text(self.reason_summary, "SkillNeedClarificationAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillNeedClarificationAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillNeedClarificationAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillStateTransitionAdvice:
    """Skill 编排状态转移建议；不写入真实状态。"""

    advice_ref: TypedRef
    skill_ref: TypedRef
    current_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.CREATED
    suggested_lifecycle: OrchestrationLifecycleKind = OrchestrationLifecycleKind.PREPARED
    transition_intent: LifecycleTransitionIntent = LifecycleTransitionIntent.CONTINUE_CURRENT_STEP
    transition_score: float = 0.0
    blocker_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.transition_score, "SkillStateTransitionAdvice.transition_score")
        if not isinstance(self.current_lifecycle, OrchestrationLifecycleKind):
            raise ValueError("SkillStateTransitionAdvice.current_lifecycle must use OrchestrationLifecycleKind")
        if not isinstance(self.suggested_lifecycle, OrchestrationLifecycleKind):
            raise ValueError("SkillStateTransitionAdvice.suggested_lifecycle must use OrchestrationLifecycleKind")
        if not isinstance(self.transition_intent, LifecycleTransitionIntent):
            raise ValueError("SkillStateTransitionAdvice.transition_intent must use LifecycleTransitionIntent")
        _ensure_short_text(self.reason_summary, "SkillStateTransitionAdvice.reason_summary")
        if self.advisory_only is not True:
            raise ValueError("SkillStateTransitionAdvice.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("SkillStateTransitionAdvice.schema_version cannot be empty")


def build_skill_display_ranking(
    ranking_ref: TypedRef,
    candidates: tuple[SkillDisplayCandidate, ...],
    confidence: float = 0.8,
    reason_summary: str = "skill display ranking advice",
) -> SkillDisplayRanking:
    """生成稳定 Skill 直显排序建议。"""

    ordered = tuple(
        sorted(
            candidates,
            key=lambda item: (-_candidate_score(item), _ref_sort_value(item.skill_ref), _ref_sort_value(item.candidate_ref)),
        )
    )
    target_scores = tuple((item.skill_ref, _candidate_score(item)) for item in ordered)
    top_ref = ordered[0].skill_ref if ordered else None
    return SkillDisplayRanking(
        ranking_ref=ranking_ref,
        candidates=ordered,
        order=RankingOrder.HIGHER_SCORE_FIRST,
        target_scores=target_scores,
        top_ranked_skill_ref=top_ref,
        confidence=confidence,
        reason_summary=reason_summary,
    )
