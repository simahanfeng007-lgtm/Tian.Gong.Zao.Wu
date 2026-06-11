"""L2 动态驱动状态对象，记录全系统驱动力、动态权重、偏好权重、压力状态、执行准备度和评估引用事实。

本模块位于 L2 状态层，只为后续动态驱动体系预留不可变状态入口，服务工程生命体把探索、稳定、谨慎、学习、修复、恢复等压力转为可引用状态。
本模块不实现动态决策算法，不选择 Skill，不释放工具，不做权限裁决，不写入状态存储，不引入运行循环。
本模块为后续 L3 排序和状态转移建议、L5 边界审查、L4 动作层和 L6 子系统提供输入引用；动态权重永远不是执行命令。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class DynamicDriveKind(str, Enum):
    """动态驱动类型枚举。

    作用：记录探索、利用、谨慎、稳定、速度、质量、学习、修复、恢复、验证、资源节省、上下文节省、最小暴露、用户对齐等驱动类别。
    边界：只做驱动分类，不计算权重，不选择动作。
    """

    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    CAUTION = "caution"
    STABILITY = "stability"
    SPEED = "speed"
    QUALITY = "quality"
    LEARNING = "learning"
    REPAIR = "repair"
    RECOVERY = "recovery"
    VERIFICATION = "verification"
    RESOURCE_SAVING = "resource_saving"
    CONTEXT_SAVING = "context_saving"
    MINIMAL_EXPOSURE = "minimal_exposure"
    USER_ALIGNMENT = "user_alignment"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DynamicWeightState:
    """动态权重状态。

    作用：记录驱动类别、权重值、来源引用、置信度、新鲜度、激活状态、边界状态和摘要。
    边界：不计算权重，不根据权重执行动作，不做裁决。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    weight_id: TypedRef | None = None
    drive_kind: DynamicDriveKind = DynamicDriveKind.UNKNOWN
    value: float = 0.0
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    freshness: str = "unknown"
    active: bool = True
    boundary_status: L2StateBoundary | None = None
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("DynamicWeightState.value must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("DynamicWeightState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("DynamicWeightState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("DynamicWeightState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SystemDriveState:
    """系统驱动力状态。

    作用：记录目标系统、权重引用、主导驱动、平衡提示、置信度和摘要。
    边界：不调度系统，不改变子系统，不生成动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    drive_id: TypedRef | None = None
    target_system: str = ""
    weight_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dominant_drive_kind: DynamicDriveKind = DynamicDriveKind.UNKNOWN
    drive_balance_hint: str = ""
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.target_system) > 128:
            raise ValueError("SystemDriveState.target_system must be short")
        if len(self.drive_balance_hint) > 512:
            raise ValueError("SystemDriveState.drive_balance_hint must be short")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("SystemDriveState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("SystemDriveState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("SystemDriveState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PreferenceWeightState:
    """目标偏好权重状态。

    作用：记录偏好类型、权重值、来源引用、稳定提示、置信度和摘要。
    边界：不学习偏好，不覆盖用户要求，不选择动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    preference_id: TypedRef | None = None
    preference_kind: str = "unknown"
    weight_value: float = 0.0
    source_ref: TypedRef | None = None
    stability_hint: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.preference_kind) > 128:
            raise ValueError("PreferenceWeightState.preference_kind must be short")
        if not 0.0 <= self.weight_value <= 1.0:
            raise ValueError("PreferenceWeightState.weight_value must be between 0.0 and 1.0")
        if not 0.0 <= self.stability_hint <= 1.0:
            raise ValueError("PreferenceWeightState.stability_hint must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("PreferenceWeightState.confidence must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("PreferenceWeightState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("PreferenceWeightState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class StabilityPressureState:
    """稳定压力状态。

    作用：记录目标引用、稳定压力值、不稳定来源、建议偏置提示、置信度和摘要。
    边界：不修复稳定性问题，不触发恢复，不改变候选排序。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    pressure_id: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    pressure_value: float = 0.0
    instability_sources: tuple[TypedRef, ...] = field(default_factory=tuple)
    recommended_bias_hint: str = ""
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.pressure_value <= 1.0:
            raise ValueError("StabilityPressureState.pressure_value must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("StabilityPressureState.confidence must be between 0.0 and 1.0")
        if len(self.recommended_bias_hint) > 512:
            raise ValueError("StabilityPressureState.recommended_bias_hint must be short")
        if len(self.summary) > 512:
            raise ValueError("StabilityPressureState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("StabilityPressureState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RiskPressureState:
    """风险压力状态。

    作用：记录目标引用、风险压力值、风险来源引用、边界审查需求提示、置信度和摘要。
    边界：不做真实风险评分，不做权限裁决，不放行动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    pressure_id: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    risk_value: float = 0.0
    risk_source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l5_review_need_hint: str = ""
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.risk_value <= 1.0:
            raise ValueError("RiskPressureState.risk_value must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("RiskPressureState.confidence must be between 0.0 and 1.0")
        if len(self.l5_review_need_hint) > 512:
            raise ValueError("RiskPressureState.l5_review_need_hint must be short")
        if len(self.summary) > 512:
            raise ValueError("RiskPressureState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RiskPressureState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExplorationPressureState:
    """探索压力状态。

    作用：记录目标引用、新颖性值、信息增益提示、学习价值提示、置信度和摘要。
    边界：不启动探索，不抓取资料，不生成学习候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    pressure_id: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    novelty_value: float = 0.0
    information_gain_hint: float = 0.0
    learning_value_hint: float = 0.0
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        values = (self.novelty_value, self.information_gain_hint, self.learning_value_hint, self.confidence)
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("ExplorationPressureState numeric hints must be between 0.0 and 1.0")
        if len(self.summary) > 512:
            raise ValueError("ExplorationPressureState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExplorationPressureState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExecutionReadinessState:
    """执行准备度状态。

    作用：记录目标引用、所需边界引用、所需动作层引用、所需上下文引用、准备度分、缺失需求、置信度和摘要。
    边界：不执行动作，不创建请求，不放行权限。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    readiness_id: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_execution_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_score: float = 0.0
    missing_requirements: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.readiness_score <= 1.0:
            raise ValueError("ExecutionReadinessState.readiness_score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("ExecutionReadinessState.confidence must be between 0.0 and 1.0")
        if any(len(item) > 128 for item in self.missing_requirements):
            raise ValueError("ExecutionReadinessState.missing_requirements entries must be short")
        if len(self.summary) > 512:
            raise ValueError("ExecutionReadinessState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExecutionReadinessState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DynamicDriveEvaluationRefState:
    """动态驱动评估引用状态。

    作用：记录数学评估引用、系统驱动力引用、情感总色彩引用、目标引用和摘要。
    边界：不合成评估结果，不计算权重，不推进动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evaluation_ref_id: TypedRef | None = None
    math_evaluation_ref: TypedRef | None = None
    system_drive_ref: TypedRef | None = None
    affective_color_ref: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("DynamicDriveEvaluationRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("DynamicDriveEvaluationRefState.schema_version cannot be empty")
