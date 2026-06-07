"""L3 数学驱动基础向量对象，只表达特征、目标、约束与分数事实。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state.math_state import MathConstraintKind, MathFeatureKind, MathObjectiveKind

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class MathVectorKind(str, Enum):
    """数学向量类别。"""

    UNKNOWN = "unknown"
    FEATURE = "feature"
    OBJECTIVE = "objective"
    CONSTRAINT = "constraint"
    SCORE = "score"


class ScoreDirection(str, Enum):
    """分数项方向。"""

    BENEFIT = "benefit"
    COST = "cost"
    NEUTRAL = "neutral"


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_non_negative(value: float, field_name: str) -> None:
    if value < 0.0:
        raise ValueError(f"{field_name} cannot be negative")


@dataclass(frozen=True, slots=True)
class MathFeatureVector:
    """数学特征向量。

    作用：保存特征类别和值、来源特征引用、来源状态引用和置信度。
    边界：不计算特征，不合成策略，不选择路径。
    """

    vector_ref: TypedRef | None = None
    vector_kind: MathVectorKind = MathVectorKind.FEATURE
    feature_entries: tuple[tuple[MathFeatureKind, float], ...] = field(default_factory=tuple)
    source_feature_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for kind, value in self.feature_entries:
            if not isinstance(kind, MathFeatureKind):
                raise ValueError("MathFeatureVector.feature_entries kind must use MathFeatureKind")
            _ensure_unit_interval(value, "MathFeatureVector.feature_entries value")
        _ensure_unit_interval(self.confidence, "MathFeatureVector.confidence")
        if len(self.summary) > 512:
            raise ValueError("MathFeatureVector.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathFeatureVector.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathObjectiveVector:
    """数学目标向量。

    作用：保存目标类别及权重、目标引用、来源状态引用和置信度。
    边界：不求解目标函数，不比较候选动作，不决定最终行为。
    """

    vector_ref: TypedRef | None = None
    vector_kind: MathVectorKind = MathVectorKind.OBJECTIVE
    objective_entries: tuple[tuple[MathObjectiveKind, float], ...] = field(default_factory=tuple)
    objective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for kind, value in self.objective_entries:
            if not isinstance(kind, MathObjectiveKind):
                raise ValueError("MathObjectiveVector.objective_entries kind must use MathObjectiveKind")
            _ensure_unit_interval(value, "MathObjectiveVector.objective_entries value")
        _ensure_unit_interval(self.confidence, "MathObjectiveVector.confidence")
        if len(self.summary) > 512:
            raise ValueError("MathObjectiveVector.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathObjectiveVector.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathConstraintSet:
    """数学约束集合。

    作用：保存约束类别、归一化限制、硬约束标记和相关引用。
    边界：不做边界裁决，不阻断下游流程，只表达约束输入事实。
    """

    constraint_set_ref: TypedRef | None = None
    vector_kind: MathVectorKind = MathVectorKind.CONSTRAINT
    constraint_entries: tuple[tuple[MathConstraintKind, float, bool], ...] = field(default_factory=tuple)
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for kind, value, hard in self.constraint_entries:
            if not isinstance(kind, MathConstraintKind):
                raise ValueError("MathConstraintSet.constraint_entries kind must use MathConstraintKind")
            _ensure_unit_interval(value, "MathConstraintSet.constraint_entries value")
            if not isinstance(hard, bool):
                raise ValueError("MathConstraintSet.constraint_entries hard flag must be bool")
        _ensure_unit_interval(self.confidence, "MathConstraintSet.confidence")
        if len(self.summary) > 512:
            raise ValueError("MathConstraintSet.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathConstraintSet.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathScoreVector:
    """数学评分向量。

    作用：保存分数项、方向、归一化总分、惩罚、收益和来源评分引用。
    边界：不生成分数，不执行排序算法，不产生执行令。
    """

    score_ref: TypedRef | None = None
    vector_kind: MathVectorKind = MathVectorKind.SCORE
    score_entries: tuple[tuple[str, float, ScoreDirection], ...] = field(default_factory=tuple)
    source_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    normalized_score: float = 0.0
    confidence: float = 0.0
    penalty_total: float = 0.0
    bonus_total: float = 0.0
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value, direction in self.score_entries:
            if not name:
                raise ValueError("MathScoreVector.score_entries name cannot be empty")
            if len(name) > 64:
                raise ValueError("MathScoreVector.score_entries name must be short")
            _ensure_unit_interval(value, "MathScoreVector.score_entries value")
            if not isinstance(direction, ScoreDirection):
                raise ValueError("MathScoreVector.score_entries direction must use ScoreDirection")
        _ensure_unit_interval(self.normalized_score, "MathScoreVector.normalized_score")
        _ensure_unit_interval(self.confidence, "MathScoreVector.confidence")
        _ensure_non_negative(self.penalty_total, "MathScoreVector.penalty_total")
        _ensure_non_negative(self.bonus_total, "MathScoreVector.bonus_total")
        if len(self.summary) > 512:
            raise ValueError("MathScoreVector.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathScoreVector.schema_version cannot be empty")


from .math_formula_profile_ref import DefaultHeuristicScoringProfile, LegacyHeuristicCompatibility


LEGACY_HEURISTIC_COMPATIBILITY = LegacyHeuristicCompatibility(
    source_module="tiangong_kernel.l3_orchestration.orchestration_math",
    source_object_names=("MathFeatureVector", "MathObjectiveVector", "MathConstraintSet", "MathScoreVector"),
)
DEFAULT_HEURISTIC_SCORING_PROFILE = DefaultHeuristicScoringProfile()
