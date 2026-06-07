"""L2 数学模型状态对象，记录特征、目标、约束、评分、评估、建议与模型引用事实。

本模块位于 L2 状态层，只为后续数学驱动提供不可变状态入口，服务工程生命体把行为倾向表达为特征、目标、约束、评分和建议引用。
本模块不实现加权公式，不执行排序算法，不训练模型，不调用大模型或工具，不推进状态转移，也不做最终边界裁决。
本模块为后续 L3 编排计算、L5 边界审查、L4 真实动作和 L6 子系统实现提供可引用状态，但数学建议永远只是建议状态，不是执行命令。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class MathFeatureKind(str, Enum):
    """数学特征类型枚举。

    作用：记录目标匹配、置信、风险提示、成本、可逆性、稳定性、连续性、学习价值等状态特征类别。
    边界：只做特征分类，不计算特征值，不读取源状态，不触发排序或动作。
    """

    GOAL_FIT = "goal_fit"
    CONFIDENCE = "confidence"
    RISK_HINT = "risk_hint"
    COST = "cost"
    REVERSIBILITY = "reversibility"
    STABILITY = "stability"
    CONTINUITY = "continuity"
    LEARNING_VALUE = "learning_value"
    INFORMATION_GAIN = "information_gain"
    RESOURCE_PRESSURE = "resource_pressure"
    CONTEXT_PRESSURE = "context_pressure"
    TOOL_EXPOSURE = "tool_exposure"
    BOUNDARY_PRESSURE = "boundary_pressure"
    USER_PREFERENCE = "user_preference"
    AFFECTIVE_BIAS = "affective_bias"
    UNKNOWN = "unknown"


class MathObjectiveKind(str, Enum):
    """数学目标类型枚举。

    作用：记录任务成功、安全、稳定、速度、质量、可逆、学习、探索、用户对齐、资源效率等目标类别。
    边界：只表达目标事实，不计算目标函数，不决定最终行为。
    """

    TASK_SUCCESS = "task_success"
    SAFETY = "safety"
    STABILITY = "stability"
    SPEED = "speed"
    QUALITY = "quality"
    REVERSIBILITY = "reversibility"
    LEARNING = "learning"
    EXPLORATION = "exploration"
    USER_ALIGNMENT = "user_alignment"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    MINIMAL_TOOL_EXPOSURE = "minimal_tool_exposure"
    CONTINUITY = "continuity"
    UNKNOWN = "unknown"


class MathConstraintKind(str, Enum):
    """数学约束类型枚举。

    作用：记录硬边界、软边界、资源限制、时间限制、安全限制、工具暴露限制、上下文预算、确认需求等约束类别。
    边界：只表达约束事实，不执行权限裁决，不改变边界结果。
    """

    HARD_BOUNDARY = "hard_boundary"
    SOFT_BOUNDARY = "soft_boundary"
    RESOURCE_LIMIT = "resource_limit"
    TIME_LIMIT = "time_limit"
    SAFETY_LIMIT = "safety_limit"
    TOOL_EXPOSURE_LIMIT = "tool_exposure_limit"
    CONTEXT_BUDGET = "context_budget"
    USER_CONFIRMATION_REQUIRED = "user_confirmation_required"
    REVERSIBILITY_REQUIRED = "reversibility_required"
    L5_REVIEW_REQUIRED = "l5_review_required"
    UNKNOWN = "unknown"


class MathAssessmentStatus(str, Enum):
    """数学评估相关状态枚举。

    作用：记录评分、评估或建议处于声明、可用、部分、过期、阻断或未知状态。
    边界：不刷新评分，不生成建议，不推进状态迁移。
    """

    DECLARED = "declared"
    AVAILABLE = "available"
    PARTIAL = "partial"
    STALE = "stale"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MathFeatureState:
    """数学特征状态。

    作用：记录单个数学特征的来源引用、原始值、归一化值、置信度、新鲜度、权重提示、边界状态和摘要。
    边界：不计算特征，不读取来源状态，不触发排序或动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    feature_id: TypedRef | None = None
    feature_kind: MathFeatureKind = MathFeatureKind.UNKNOWN
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    numeric_value: float = 0.0
    normalized_value: float = 0.0
    confidence: float = 0.0
    freshness: str = "unknown"
    weight_hint: float = 0.0
    boundary_status: L2StateBoundary | None = None
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.normalized_value <= 1.0:
            raise ValueError("MathFeatureState.normalized_value must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MathFeatureState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("MathFeatureState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathFeatureState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathObjectiveState:
    """数学目标状态。

    作用：记录目标类别、目标值、优先权重、容忍度、来源引用、激活状态和摘要。
    边界：不求解目标函数，不比较目标，不选择动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    objective_id: TypedRef | None = None
    objective_kind: MathObjectiveKind = MathObjectiveKind.UNKNOWN
    target_value: float = 0.0
    priority_weight: float = 0.0
    tolerance: float = 0.0
    source_ref: TypedRef | None = None
    active: bool = True
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.priority_weight <= 1.0:
            raise ValueError("MathObjectiveState.priority_weight must be between 0.0 and 1.0")
        if self.tolerance < 0.0:
            raise ValueError("MathObjectiveState.tolerance cannot be negative")
        if len(self.summary) > 512:
            raise ValueError("MathObjectiveState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathObjectiveState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathConstraintState:
    """数学约束状态。

    作用：记录约束类别、硬约束标记、限制值、当前值、违规提示、边界引用、来源引用和摘要。
    边界：不做真实裁决，不阻断动作，不修改边界状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    constraint_id: TypedRef | None = None
    constraint_kind: MathConstraintKind = MathConstraintKind.UNKNOWN
    hard: bool = False
    limit_value: float = 0.0
    current_value: float = 0.0
    violation_hint: str = ""
    boundary_ref: TypedRef | None = None
    source_ref: TypedRef | None = None
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.violation_hint) > 256:
            raise ValueError("MathConstraintState.violation_hint must be short")
        if len(self.summary) > 512:
            raise ValueError("MathConstraintState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathConstraintState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathScoreState:
    """数学评分状态。

    作用：记录目标引用、特征引用、目标集合、约束集合、原始分、归一化分、置信度、惩罚、奖励、评分状态和摘要。
    边界：不计算分数，不排名，不触发状态迁移。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    score_id: TypedRef | None = None
    target_ref: TypedRef | None = None
    feature_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    objective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    raw_score: float = 0.0
    normalized_score: float = 0.0
    confidence: float = 0.0
    penalty_total: float = 0.0
    bonus_total: float = 0.0
    score_status: MathAssessmentStatus = MathAssessmentStatus.UNKNOWN
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.normalized_score <= 1.0:
            raise ValueError("MathScoreState.normalized_score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MathScoreState.confidence must be between 0.0 and 1.0")
        if self.penalty_total < 0.0:
            raise ValueError("MathScoreState.penalty_total cannot be negative")
        if self.bonus_total < 0.0:
            raise ValueError("MathScoreState.bonus_total cannot be negative")
        if len(self.summary) > 512:
            raise ValueError("MathScoreState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathScoreState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathEvaluationState:
    """数学评估状态。

    作用：记录评估引用、评估者引用、输入状态、特征、目标、约束、评分、排序引用、置信度、评估状态和摘要。
    边界：不运行评估器，不生成排序，不读取输入状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evaluation_id: TypedRef | None = None
    evaluator_ref: TypedRef | None = None
    input_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    feature_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    objective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ranking_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    evaluation_status: MathAssessmentStatus = MathAssessmentStatus.UNKNOWN
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MathEvaluationState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("MathEvaluationState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathEvaluationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathRecommendationState:
    """数学建议状态。

    作用：记录评估引用、建议目标、备选目标、拒绝目标、原因摘要、置信度、所需边界引用、所需动作引用和状态更新建议引用。
    边界：建议不是执行命令，不绕过边界，不调用工具，不改变状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recommendation_id: TypedRef | None = None
    evaluation_ref: TypedRef | None = None
    recommended_target_ref: TypedRef | None = None
    alternative_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rejected_target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    confidence: float = 0.0
    required_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_execution_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    state_update_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recommendation_status: MathAssessmentStatus = MathAssessmentStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MathRecommendationState.confidence must be between 0.0 and 1.0")
        if len(self.reason_summary) > 512:
            raise ValueError("MathRecommendationState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathRecommendationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelRefState:
    """数学模型引用状态。

    作用：记录模型引用、模型名称、模型类型、版本、适用范围、所属层、是否确定性和摘要。
    边界：不持有模型对象，不训练模型，不调用模型，不执行推理。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    model_ref_id: TypedRef | None = None
    model_name: str = ""
    model_kind: str = "unknown"
    version: str = L2_STATE_SCHEMA_VERSION
    scope: str = ""
    owner_layer: str = "L3"
    deterministic: bool = False
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.model_name) > 128:
            raise ValueError("MathModelRefState.model_name must be short")
        if len(self.model_kind) > 64:
            raise ValueError("MathModelRefState.model_kind must be short")
        if not self.version:
            raise ValueError("MathModelRefState.version cannot be empty")
        if len(self.summary) > 512:
            raise ValueError("MathModelRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathModelRefState.schema_version cannot be empty")
