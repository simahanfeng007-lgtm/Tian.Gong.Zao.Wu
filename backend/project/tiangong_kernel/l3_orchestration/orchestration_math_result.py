"""L3 数学编排结果对象，只表达评估、建议、排序和状态转移建议。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state.math_state import MathAssessmentStatus, MathEvaluationState, MathRecommendationState
from tiangong_kernel.l2_state.state_status import L2StateStatusKind

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathScoreVector
from .orchestration_math_input import MathOrchestrationInput


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


class RecommendationMode(str, Enum):
    """数学建议模式。"""

    UNKNOWN = "unknown"
    SUGGEST = "suggest"
    DEFER = "defer"
    ESCALATE_TO_BOUNDARY = "escalate_to_boundary"
    REQUEST_UPPER_LAYER = "request_upper_layer"


class RankingOrder(str, Enum):
    """排序表达方式。"""

    UNKNOWN = "unknown"
    HIGHER_SCORE_FIRST = "higher_score_first"
    LOWER_COST_FIRST = "lower_cost_first"


@dataclass(frozen=True, slots=True)
class MathEvaluation:
    """L3 数学评估结果事实。

    作用：引用数学输入、评分向量和 L2 数学评估状态。
    边界：不运行评估器，不创建排序，不触发动作。
    """

    evaluation_ref: TypedRef | None = None
    input_value: MathOrchestrationInput | None = None
    score_vector: MathScoreVector | None = None
    source_evaluation_state: MathEvaluationState | None = None
    confidence: float = 0.0
    evaluation_status: MathAssessmentStatus = MathAssessmentStatus.UNKNOWN
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "MathEvaluation.confidence")
        if len(self.summary) > 512:
            raise ValueError("MathEvaluation.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathEvaluation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RouteRanking:
    """路径排序结果事实。

    作用：保存目标引用与分值、排序方式、首位目标引用、备选目标引用和理由。
    边界：只表达排序建议，不代表最终路径已经确定。
    """

    ranking_ref: TypedRef | None = None
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    order: RankingOrder = RankingOrder.UNKNOWN
    top_ranked_target_ref: TypedRef | None = None
    alternative_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for _target_ref, score in self.target_scores:
            _ensure_unit_interval(score, "RouteRanking.target_scores score")
        _ensure_unit_interval(self.confidence, "RouteRanking.confidence")
        if self.advisory_only is not True:
            raise ValueError("RouteRanking.advisory_only must remain true in L3 phase 1")
        if len(self.reason_summary) > 512:
            raise ValueError("RouteRanking.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RouteRanking.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StateTransitionAdvice:
    """状态转移建议。

    作用：保存主体状态引用、建议状态码、来源排序引用、边界审查引用和理由。
    边界：不写入 L2 状态，不替代边界层，不触发执行层。
    """

    advice_ref: TypedRef | None = None
    subject_state_ref: TypedRef | None = None
    suggested_status: L2StateStatusKind = L2StateStatusKind.UNKNOWN
    source_ranking_ref: TypedRef | None = None
    boundary_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "StateTransitionAdvice.confidence")
        if self.advisory_only is not True:
            raise ValueError("StateTransitionAdvice.advisory_only must remain true in L3 phase 1")
        if len(self.reason_summary) > 512:
            raise ValueError("StateTransitionAdvice.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathRecommendation:
    """数学建议结果。

    作用：保存评估结果、路径排序、建议模式、推荐目标引用、边界审查引用、L4 请求提示引用和状态建议引用。
    边界：数学建议永远是建议，不是许可、裁决或真实动作。
    """

    recommendation_ref: TypedRef | None = None
    evaluation: MathEvaluation | None = None
    route_ranking: RouteRanking | None = None
    source_recommendation_state: MathRecommendationState | None = None
    recommendation_mode: RecommendationMode = RecommendationMode.UNKNOWN
    recommended_target_ref: TypedRef | None = None
    alternative_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_review_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l4_request_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    state_transition_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    advisory_only: bool = True
    reason_summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.confidence, "MathRecommendation.confidence")
        if self.advisory_only is not True:
            raise ValueError("MathRecommendation.advisory_only must remain true in L3 phase 1")
        if len(self.reason_summary) > 512:
            raise ValueError("MathRecommendation.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathRecommendation.schema_version cannot be empty")
