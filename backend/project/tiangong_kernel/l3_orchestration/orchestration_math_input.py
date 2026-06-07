"""L3 数学编排输入对象，接入 L2 数学、情感与动态驱动状态。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state.affective_state import AffectiveColorState, ActionBiasState, ExpressionBiasState
from tiangong_kernel.l2_state.dynamic_drive_state import (
    DynamicDriveEvaluationRefState,
    DynamicWeightState,
    ExecutionReadinessState,
    SystemDriveState,
)
from tiangong_kernel.l2_state.math_state import (
    MathConstraintState,
    MathFeatureState,
    MathObjectiveState,
    MathScoreState,
)
from tiangong_kernel.l2_state.projection_state import RuntimeSliceProjectionState

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .orchestration_math import MathConstraintSet, MathFeatureVector, MathObjectiveVector


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class AffectiveWeightInput:
    """情感权重输入。

    作用：把 L2 情感总色彩、表达倾向和行动倾向状态作为 L3 数学编排的权重输入。
    边界：只影响倾向和排序建议，不产生执行令，不提升边界级别。
    """

    input_ref: TypedRef | None = None
    affective_color: AffectiveColorState | None = None
    expression_bias: ExpressionBiasState | None = None
    action_bias: ActionBiasState | None = None
    affective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    exploration_weight: float = 0.0
    caution_weight: float = 0.0
    persistence_weight: float = 0.0
    learning_weight: float = 0.0
    stability_weight: float = 0.0
    confidence: float = 0.0
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("AffectiveWeightInput.exploration_weight", self.exploration_weight),
            ("AffectiveWeightInput.caution_weight", self.caution_weight),
            ("AffectiveWeightInput.persistence_weight", self.persistence_weight),
            ("AffectiveWeightInput.learning_weight", self.learning_weight),
            ("AffectiveWeightInput.stability_weight", self.stability_weight),
            ("AffectiveWeightInput.confidence", self.confidence),
        ):
            _ensure_unit_interval(value, name)
        if self.advisory_only is not True:
            raise ValueError("AffectiveWeightInput.advisory_only must remain true in L3 phase 1")
        if len(self.summary) > 512:
            raise ValueError("AffectiveWeightInput.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("AffectiveWeightInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DynamicDriveInput:
    """动态驱动输入。

    作用：把 L2 动态权重、系统驱动力、准备度引用和动态评估引用纳入 L3 数学编排。
    边界：只影响优先级和路径排序建议，不选择 Skill，不释放工具组。
    """

    input_ref: TypedRef | None = None
    dynamic_weights: tuple[DynamicWeightState, ...] = field(default_factory=tuple)
    system_drive: SystemDriveState | None = None
    readiness: ExecutionReadinessState | None = None
    evaluation_ref_state: DynamicDriveEvaluationRefState | None = None
    dynamic_drive_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    priority_weight: float = 0.0
    stability_pressure_weight: float = 0.0
    risk_pressure_weight: float = 0.0
    exploration_pressure_weight: float = 0.0
    confidence: float = 0.0
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("DynamicDriveInput.priority_weight", self.priority_weight),
            ("DynamicDriveInput.stability_pressure_weight", self.stability_pressure_weight),
            ("DynamicDriveInput.risk_pressure_weight", self.risk_pressure_weight),
            ("DynamicDriveInput.exploration_pressure_weight", self.exploration_pressure_weight),
            ("DynamicDriveInput.confidence", self.confidence),
        ):
            _ensure_unit_interval(value, name)
        if self.advisory_only is not True:
            raise ValueError("DynamicDriveInput.advisory_only must remain true in L3 phase 1")
        if len(self.summary) > 512:
            raise ValueError("DynamicDriveInput.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("DynamicDriveInput.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathOrchestrationInput:
    """数学编排输入聚合。

    作用：把 L3 数学向量、L2 数学状态、L2 情感权重输入、L2 动态驱动输入和运行切片引用聚合为一个输入事实。
    边界：不运行评分器，不改变状态，不调用上层或下层能力。
    """

    input_ref: TypedRef | None = None
    feature_vector: MathFeatureVector | None = None
    objective_vector: MathObjectiveVector | None = None
    constraint_set: MathConstraintSet | None = None
    math_features: tuple[MathFeatureState, ...] = field(default_factory=tuple)
    math_objectives: tuple[MathObjectiveState, ...] = field(default_factory=tuple)
    math_constraints: tuple[MathConstraintState, ...] = field(default_factory=tuple)
    math_scores: tuple[MathScoreState, ...] = field(default_factory=tuple)
    math_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affective_input: AffectiveWeightInput | None = None
    dynamic_drive_input: DynamicDriveInput | None = None
    runtime_slice_projection: RuntimeSliceProjectionState | None = None
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("MathOrchestrationInput.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MathOrchestrationInput.schema_version cannot be empty")
