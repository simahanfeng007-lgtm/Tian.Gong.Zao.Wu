"""L0 记忆事实语言原语。

本模块在 L0 中的职责：定义可被长期引用、巩固、保留或遗忘治理的记忆事实引用。
本模块只表达：记忆引用、记忆轨迹引用、来源引用、置信度、保留引用、记忆类别与状态。
本模块明确不做：记忆正文保存、召回、索引、图结构、巩固计算、遗忘计算、上层系统编排。
禁止事项：不得接触真实数据源，不得做向量检索，不得调用模型、工具、网络或任何外部资源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class MemoryKind(str, Enum):
    """记忆类别枚举：只标记记忆事实的语义类型；UNKNOWN 表示类别未知或暂不归类。

    WORKING：工作记忆；EPISODIC：情节记忆；SEMANTIC：语义记忆；PROCEDURAL：程序性记忆；
    RESOURCE：资源相关记忆；SELF：自我相关记忆；USER：用户相关记忆；SYSTEM：系统相关记忆；UNKNOWN：未知兜底。
    """

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    RESOURCE = "resource"
    SELF = "self"
    USER = "user"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class MemoryState(str, Enum):
    """记忆状态枚举：只表达记忆事实的生命周期位置；UNKNOWN 表示状态未知或暂不可判定。

    CANDIDATE：候选；ACTIVE：活动；REINFORCED：被强化；CONSOLIDATING：巩固中；STABLE：稳定；
    DECAYING：衰减中；SUPPRESSED：被抑制；DEPRECATED：弃用；ARCHIVED：归档；FORGOTTEN：已遗忘；UNKNOWN：未知兜底。
    """

    CANDIDATE = "candidate"
    ACTIVE = "active"
    REINFORCED = "reinforced"
    CONSOLIDATING = "consolidating"
    STABLE = "stable"
    DECAYING = "decaying"
    SUPPRESSED = "suppressed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    FORGOTTEN = "forgotten"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MemoryTraceRef:
    """记忆轨迹引用。

    作用：引用某条记忆形成、强化、衰减或治理的轨迹事实。
    所属 L0 边界：只保存 trace_id 与 memory_ref 等引用事实。
    不能承担的上层职责：不能保存完整轨迹、不能折叠事件、不能执行召回或治理流程。
    字段：value 为轨迹引用 ID；memory_ref 为关联记忆引用；evidence_refs 为证据引用集合。
    """

    value: RefId
    memory_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MemoryTraceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryOriginRef:
    """记忆来源引用。

    作用：表达记忆来自观察、事件、反馈、人工输入或其他事实对象的来源引用。
    所属 L0 边界：只记录 origin_ref 等来源事实。
    不能承担的上层职责：不能读取来源内容、不能验证来源真实性、不能做来源评分。
    字段：value 为来源引用 ID；origin_ref 为外部事实引用；trace_ref 为来源轨迹引用。
    """

    value: RefId
    origin_ref: TypedRef | None = None
    trace_ref: MemoryTraceRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MemoryOriginRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryConfidence:
    """记忆置信度。

    作用：表达某条记忆事实当前可信程度的数值事实。
    所属 L0 边界：只保存 confidence 数值和证据引用。
    不能承担的上层职责：不能计算置信度、不能合并证据、不能触发强化或遗忘。
    字段：confidence 为 0 到 1 的置信度；evidence_refs 为证据引用集合。
    """

    confidence: float
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MemoryConfidence.confidence must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("MemoryConfidence.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryRetentionRef:
    """记忆保留引用。

    作用：引用某条记忆的保留状态、保留依据或保留治理事实。
    所属 L0 边界：只保存 retention_id 与 memory_ref 等引用事实。
    不能承担的上层职责：不能制定保留策略、不能执行保留或清理动作。
    字段：value 为保留引用 ID；memory_ref 为关联记忆引用；policy_ref 为外部治理引用。
    """

    value: RefId
    memory_ref: TypedRef | None = None
    policy_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MemoryRetentionRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryRef:
    """记忆引用。

    作用：表达可被长期引用、召回、巩固或遗忘治理的记忆事实引用。
    所属 L0 边界：只保存 memory_id、kind、state、origin_ref、confidence、retention_ref 等引用和值对象。
    不能承担的上层职责：不能保存完整记忆内容，不能执行召回、索引、巩固、遗忘或图结构维护。
    字段：value 为记忆引用 ID；kind 为记忆类别；state 为记忆状态；evidence_refs 为证据引用集合。
    """

    value: RefId
    kind: MemoryKind = MemoryKind.UNKNOWN
    state: MemoryState = MemoryState.UNKNOWN
    trace_ref: MemoryTraceRef | None = None
    origin_ref: MemoryOriginRef | None = None
    confidence: MemoryConfidence | None = None
    retention_ref: MemoryRetentionRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("MemoryRef.schema_version cannot be empty")
