"""L0 遗忘治理事实语言原语。

本模块在 L0 中的职责：定义遗忘、保留、衰减、干扰、抑制、剪枝和修订的事实引用。
本模块只表达：遗忘引用、保留轨迹、衰减轨迹、干扰轨迹、抑制引用、剪枝引用、修订引用、数值事实。
本模块明确不做：遗忘调度、真实删除、记忆库清理、衰减曲线计算、睡眠清理、向量库处理。
禁止事项：不得接触真实数据，不得销毁内容，不得实现具体心理学或认知科学算法。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef
from .time import TimeRange


class ForgettingKind(str, Enum):
    """遗忘类型枚举：只标记治理事实类别；UNKNOWN 表示未知或未分类。

    PASSIVE_DECAY：被动衰减；ACTIVE_DELETION：主动删除意图；SAFETY_TRIGGERED：安全触发；ADAPTIVE_REINFORCED：适应性强化保留；
    INTERFERENCE_BASED：干扰导致；REVISION_BASED：修订导致；SUPPRESSION：抑制；PRUNING：剪枝；UNKNOWN：未知兜底。
    """

    PASSIVE_DECAY = "passive_decay"
    ACTIVE_DELETION = "active_deletion"
    SAFETY_TRIGGERED = "safety_triggered"
    ADAPTIVE_REINFORCED = "adaptive_reinforced"
    INTERFERENCE_BASED = "interference_based"
    REVISION_BASED = "revision_based"
    SUPPRESSION = "suppression"
    PRUNING = "pruning"
    UNKNOWN = "unknown"


class ForgettingState(str, Enum):
    """遗忘状态枚举：只表达治理事实所处阶段；UNKNOWN 表示状态未知。

    PROPOSED：已提出；SCHEDULED：已排期引用；DECAYING：衰减中；SUPPRESSED：已抑制；PRUNED：已剪枝；
    REVISED：已修订；DELETED：已删除事实；BLOCKED：被阻塞；ARCHIVED：已归档；UNKNOWN：未知兜底。
    """

    PROPOSED = "proposed"
    SCHEDULED = "scheduled"
    DECAYING = "decaying"
    SUPPRESSED = "suppressed"
    PRUNED = "pruned"
    REVISED = "revised"
    DELETED = "deleted"
    BLOCKED = "blocked"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RetentionScore:
    """保留分值。

    作用：表达记忆保留强度的数值事实。
    所属 L0 边界：只保存 score 与依据引用。
    不能承担的上层职责：不能计算分值，不能决定保留、删除或强化。
    字段：score 为 0 到 1 的保留强度；basis_refs 为依据引用集合。
    """

    score: float
    basis_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("RetentionScore.score must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("RetentionScore.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DecayRate:
    """衰减率。

    作用：表达某条记忆或轨迹的衰减速率数值事实。
    所属 L0 边界：只保存 rate 与单位文本。
    不能承担的上层职责：不能套用具体遗忘曲线，不能执行衰减更新。
    字段：rate 为非负速率；unit 为单位说明。
    """

    rate: float
    unit: str = "per_window"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.rate < 0:
            raise ValueError("DecayRate.rate cannot be negative")
        if not self.unit:
            raise ValueError("DecayRate.unit cannot be empty")
        if not self.schema_version:
            raise ValueError("DecayRate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetentionTrace:
    """保留轨迹。

    作用：表达某条记忆被保留的强度、依据和轨迹引用。
    所属 L0 边界：只保存 trace_ref、memory_ref、score 和证据引用。
    不能承担的上层职责：不能执行保留策略，不能改变记忆状态。
    字段：trace_ref 为轨迹引用；memory_ref 为记忆引用；score 为保留分值。
    """

    trace_ref: TypedRef
    memory_ref: TypedRef | None = None
    score: RetentionScore | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RetentionTrace.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DecayTrace:
    """衰减轨迹。

    作用：表达随时间、冲突、低使用率或策略压力产生的衰减事实引用。
    所属 L0 边界：只保存 trace_ref、memory_ref、decay_rate、window 和证据引用。
    不能承担的上层职责：不能推进衰减，不能清理数据。
    字段：window 为时间窗口；decay_rate 为衰减率事实。
    """

    trace_ref: TypedRef
    memory_ref: TypedRef | None = None
    decay_rate: DecayRate | None = None
    window: TimeRange | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("DecayTrace.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class InterferenceTrace:
    """干扰轨迹。

    作用：表达记忆之间相互干扰的轨迹引用。
    所属 L0 边界：只保存 source_memory_ref、target_memory_ref、strength 等事实。
    不能承担的上层职责：不能判定冲突优先级，不能改写记忆。
    字段：strength 为 0 到 1 的干扰强度。
    """

    trace_ref: TypedRef
    source_memory_ref: TypedRef | None = None
    target_memory_ref: TypedRef | None = None
    strength: float = 0.0
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("InterferenceTrace.strength must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("InterferenceTrace.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SuppressionRef:
    """抑制引用。

    作用：表达某条记忆被暂时压低可见性或使用性的事实引用。
    所属 L0 边界：只保存引用事实。
    不能承担的上层职责：不能执行抑制策略，不能修改上下文可见性。
    字段：value 为抑制引用 ID；memory_ref 为关联记忆引用。
    """

    value: RefId
    memory_ref: TypedRef | None = None
    reason_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SuppressionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PruningRef:
    """剪枝引用。

    作用：表达某条记忆或轨迹被剪枝治理的事实引用。
    所属 L0 边界：只保存引用事实。
    不能承担的上层职责：不能执行真实剪枝，不能删除数据。
    字段：value 为剪枝引用 ID；memory_ref 为关联记忆引用。
    """

    value: RefId
    memory_ref: TypedRef | None = None
    basis_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("PruningRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RevisionRef:
    """修订引用。

    作用：表达某条记忆被修订、替换或纠偏的事实引用。
    所属 L0 边界：只保存旧引用、新引用和修订依据引用。
    不能承担的上层职责：不能改写原始记忆，不能合并版本。
    字段：previous_ref 为旧事实引用；revised_ref 为新事实引用。
    """

    value: RefId
    previous_ref: TypedRef | None = None
    revised_ref: TypedRef | None = None
    basis_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RevisionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ForgettingRef:
    """遗忘治理引用。

    作用：表达遗忘、抑制、剪枝、删除、修订等治理动作的事实引用。
    所属 L0 边界：只保存 forgetting_id、kind、state、memory_ref 和相关轨迹引用。
    不能承担的上层职责：不能执行遗忘流程，不能清理真实数据，不能启动调度。
    字段：value 为遗忘引用 ID；kind 为治理类型；state 为治理状态。
    """

    value: RefId
    kind: ForgettingKind = ForgettingKind.UNKNOWN
    state: ForgettingState = ForgettingState.UNKNOWN
    memory_ref: TypedRef | None = None
    retention_trace: RetentionTrace | None = None
    decay_trace: DecayTrace | None = None
    interference_trace: InterferenceTrace | None = None
    suppression_ref: SuppressionRef | None = None
    pruning_ref: PruningRef | None = None
    revision_ref: RevisionRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ForgettingRef.schema_version cannot be empty")
