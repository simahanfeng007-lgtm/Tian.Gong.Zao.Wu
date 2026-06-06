"""L2 实验状态对象，只记录实验意图、设计、观察、结果、对比和回退提示事实，不启动实验。

作用：为候选学习、迭代和进化提供可引用的实验状态骨架，使实验仍停留在状态事实层。
边界：不运行实验，不调用模型或工具，不计算结果，不执行回退或迁移。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ExperimentKind(str, Enum):
    """实验类型枚举。

    作用：表达实验面向学习材料、Skill 流程、工具组绑定、边界说明、上下文策略、检索质量或进化连续性。
    边界：只分类实验事实，不启动实验。
    """

    UNKNOWN = "unknown"
    LEARNING_MATERIAL = "learning_material"
    SKILL_FLOW = "skill_flow"
    TOOL_GROUP_BINDING = "tool_group_binding"
    BOUNDARY_DESCRIPTION = "boundary_description"
    CONTEXT_STRATEGY = "context_strategy"
    RETRIEVAL_QUALITY = "retrieval_quality"
    EVOLUTION_CONTINUITY = "evolution_continuity"


class ExperimentStatus(str, Enum):
    """实验状态枚举。

    作用：表达实验处于未知、已提出、已设计、等待证据、等待边界、观察已引用、结果已引用、阻断或移交。
    边界：不推进实验，不运行实验，不计算实验结果。
    """

    UNKNOWN = "unknown"
    PROPOSED = "proposed"
    DESIGNED = "designed"
    WAITING_EVIDENCE = "waiting_evidence"
    WAITING_BOUNDARY = "waiting_boundary"
    OBSERVATION_REFERENCED = "observation_referenced"
    RESULT_REFERENCED = "result_referenced"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"


class ExperimentComparisonStatus(str, Enum):
    """实验对比状态枚举。

    作用：表达实验对比未知、基线缺失、候选缺失、证据不足、差异已引用、需复核或阻断。
    边界：不计算差异，不跑基线，不排序候选。
    """

    UNKNOWN = "unknown"
    BASELINE_MISSING = "baseline_missing"
    CANDIDATE_MISSING = "candidate_missing"
    EVIDENCE_MISSING = "evidence_missing"
    DIFFERENCE_REFERENCED = "difference_referenced"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ExperimentIntentState:
    """实验意图状态对象。

    作用：记录实验意图引用、候选引用、实验类型、目标引用、摘要和边界事实。
    边界：不启动实验，不创建任务，不调用模型或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    experiment_intent_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    experiment_kind: ExperimentKind = ExperimentKind.UNKNOWN
    target_ref: TypedRef | None = None
    hypothesis_summary: str = ""
    expected_signal_summary: str = ""
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("hypothesis_summary", self.hypothesis_summary), ("expected_signal_summary", self.expected_signal_summary)):
            if len(value) > 512:
                raise ValueError(f"ExperimentIntentState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("ExperimentIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentDesignState:
    """实验设计状态对象。

    作用：记录实验设计引用、实验意图、基线引用、候选引用、观察指标引用和状态。
    边界：不生成实验方案，不调度实验，不读取材料。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    design_ref: TypedRef | None = None
    experiment_intent_ref: TypedRef | None = None
    baseline_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    design_summary: str = ""
    experiment_status: ExperimentStatus = ExperimentStatus.UNKNOWN
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.design_summary) > 512:
            raise ValueError("ExperimentDesignState.design_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExperimentDesignState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentObservationState:
    """实验观察状态对象。

    作用：记录实验观察引用、设计引用、观察帧、指标和证据引用。
    边界：不观察真实系统，不采样数据，不写入审计。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    experiment_observation_ref: TypedRef | None = None
    design_ref: TypedRef | None = None
    observation_frame_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.observation_summary) > 512:
            raise ValueError("ExperimentObservationState.observation_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExperimentObservationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentResultState:
    """实验结果状态对象。

    作用：记录实验结果引用、设计引用、观察引用、结果摘要、置信度和验证引用。
    边界：不计算结果，不判定成败，不触发候选晋升。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    result_ref: TypedRef | None = None
    design_ref: TypedRef | None = None
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    result_summary: str = ""
    confidence: float = 0.0
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("ExperimentResultState.confidence must be between 0 and 1")
        if len(self.result_summary) > 512:
            raise ValueError("ExperimentResultState.result_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExperimentResultState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentComparisonState:
    """实验对比状态对象。

    作用：记录基线结果、候选结果、差异摘要、证据引用和对比状态。
    边界：不计算差异，不排序候选，不决定是否采纳。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    comparison_ref: TypedRef | None = None
    baseline_result_ref: TypedRef | None = None
    candidate_result_ref: TypedRef | None = None
    comparison_status: ExperimentComparisonStatus = ExperimentComparisonStatus.UNKNOWN
    difference_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.difference_summary) > 512:
            raise ValueError("ExperimentComparisonState.difference_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExperimentComparisonState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentRollbackHintState:
    """实验回退提示状态对象。

    作用：记录实验候选的回退提示、恢复点、原因和关联证据。
    边界：不执行回退，不恢复状态，不取消实验或候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    rollback_hint_ref: TypedRef | None = None
    experiment_ref: TypedRef | None = None
    recovery_point_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("ExperimentRollbackHintState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ExperimentRollbackHintState.schema_version cannot be empty")
