"""L2 基础状态对象，提供状态元信息和通用记录骨架，不采集证据或写入外部日志。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


L2_STATE_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class L2StateMetadata:
    """L2 状态元信息。

    作用：保存追踪上下文、来源引用、证据引用和审计引用等状态元事实。
    边界：不采集审计，不读取证据，不生成外部日志，不触发模型或工具动作。
    """

    schema_version: str = L2_STATE_SCHEMA_VERSION
    trace_context: TraceContext | None = None
    source_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateMetadata.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2StateRecord:
    """L2 状态通用记录。

    作用：组合状态身份、状态码、元信息和边界事实，作为后续状态对象的共同骨架。
    边界：不推进状态，不保存状态，不做运行编排，只表达当前状态事实。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateRecord.schema_version cannot be empty")
