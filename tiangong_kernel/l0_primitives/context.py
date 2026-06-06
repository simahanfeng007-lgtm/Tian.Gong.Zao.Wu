"""L0 上下文事实语言原语。

本模块在 L0 中的职责：定义上下文集合引用、边界引用、摘要引用、来源引用、信念状态引用和世界状态引用。
本模块只表达：某个主体在某个作用域、轨迹、跨度和时间窗口内可见、可引用、可使用的信息集合引用。
本模块明确不做：上下文装配、压缩、选择、污染检测、模型消息拼接、记忆注入或提示词生成。
禁止事项：不得保存完整上下文，不得保存消息列表、记忆片段、工具结果或模型输入文本。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef
from .time import TimeRange


class ContextKind(str, Enum):
    """上下文类别枚举：只标记上下文引用的语义范围；UNKNOWN 表示未知或暂不归类。

    CONVERSATION：对话上下文；RUN_CONTEXT：运行上下文；TASK_CONTEXT：任务上下文；TOOL_CONTEXT：工具相关上下文引用；
    MEMORY_CONTEXT：记忆上下文引用；OBSERVATION_CONTEXT：观察上下文；SYSTEM_CONTEXT：系统上下文；RECOVERY_CONTEXT：恢复上下文；UNKNOWN：未知兜底。
    """

    CONVERSATION = "conversation"
    RUN_CONTEXT = "run_context"
    TASK_CONTEXT = "task_context"
    TOOL_CONTEXT = "tool_context"
    MEMORY_CONTEXT = "memory_context"
    OBSERVATION_CONTEXT = "observation_context"
    SYSTEM_CONTEXT = "system_context"
    RECOVERY_CONTEXT = "recovery_context"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ContextWindow:
    """上下文窗口。

    作用：表达上下文引用所属的时间、轨迹或跨度窗口。
    所属 L0 边界：只保存 window_id、time_range、trace_ref、span_ref 等引用事实。
    不能承担的上层职责：不能选择上下文，不能裁剪内容，不能计算窗口预算。
    字段：value 为窗口引用 ID；time_range 为时间范围；trace_ref 为追踪引用。
    """

    value: RefId
    time_range: TimeRange | None = None
    trace_ref: TypedRef | None = None
    span_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContextWindow.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextBoundary:
    """上下文边界。

    作用：表达上下文的可见边界、可引用边界和可使用边界。
    所属 L0 边界：只保存边界引用事实，不做边界判断。
    不能承担的上层职责：不能执行权限判断，不能释放数据，不能过滤上下文。
    字段：visible_boundary_ref 为可见边界；reference_boundary_ref 为可引用边界；usable_boundary_ref 为可使用边界。
    """

    visible_boundary_ref: TypedRef | None = None
    reference_boundary_ref: TypedRef | None = None
    usable_boundary_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContextBoundary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextDigest:
    """上下文摘要引用。

    作用：表达上下文摘要、哈希或摘要产物的引用事实。
    所属 L0 边界：只保存 digest 文本、algorithm 和 source_ref。
    不能承担的上层职责：不能生成摘要，不能压缩上下文，不能校验完整内容。
    字段：digest 为摘要值；algorithm 为摘要算法名称；source_ref 为来源引用。
    """

    digest: str
    algorithm: str = "sha256"
    source_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.digest:
            raise ValueError("ContextDigest.digest cannot be empty")
        if not self.algorithm:
            raise ValueError("ContextDigest.algorithm cannot be empty")
        if not self.schema_version:
            raise ValueError("ContextDigest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextOriginRef:
    """上下文来源引用。

    作用：表达上下文来自事件、观察、记忆、任务或恢复过程的来源事实。
    所属 L0 边界：只保存来源引用，不读取来源内容。
    不能承担的上层职责：不能装配来源，不能决定来源优先级。
    字段：value 为来源引用 ID；origin_ref 为被引用的来源事实。
    """

    value: RefId
    origin_ref: TypedRef | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContextOriginRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BeliefStateRef:
    """信念状态引用。

    作用：表达主体基于观察、上下文、事件、信号或指标形成的当前信念状态引用。
    所属 L0 边界：只保存 belief_state_id 与依据引用集合。
    不能承担的上层职责：不能建模信念，不能推理世界状态，不能更新上下文。
    字段：value 为信念状态引用 ID；evidence_refs 为依据引用集合。
    """

    value: RefId
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("BeliefStateRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class WorldStateRef:
    """世界状态引用。

    作用：表达系统对内部或外部世界结构化状态表征的引用。
    所属 L0 边界：只保存 world_state_id、scope_ref 和 evidence_refs。
    不能承担的上层职责：不能构建世界模型，不能同步外部环境，不能做状态折叠。
    字段：value 为世界状态引用 ID；scope_ref 为作用域引用。
    """

    value: RefId
    scope_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("WorldStateRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextRef:
    """上下文引用。

    作用：表达某个主体在某个作用域、轨迹、跨度、时间窗口内可见、可引用、可使用的信息集合引用。
    所属 L0 边界：只保存 context_id、kind、window、boundary、digest、origin_ref、actor_ref、scope_ref 等引用事实。
    不能承担的上层职责：不能保存完整上下文内容，不能保存消息列表，不能组装模型输入。
    字段：value 为上下文引用 ID；kind 为上下文类别；boundary 为上下文边界。
    """

    value: RefId
    kind: ContextKind = ContextKind.UNKNOWN
    window: ContextWindow | None = None
    boundary: ContextBoundary | None = None
    digest: ContextDigest | None = None
    origin_ref: ContextOriginRef | None = None
    actor_ref: TypedRef | None = None
    scope_ref: TypedRef | None = None
    belief_state_ref: BeliefStateRef | None = None
    world_state_ref: WorldStateRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ContextRef.schema_version cannot be empty")
