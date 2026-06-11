"""L2 状态增量对象，只表达状态变化事实，不计算差异或写入事件流。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.state import StateDeltaRef

from .base_state import L2StateMetadata


class L2DeltaKind(str, Enum):
    """L2 增量类型枚举；只描述变化类别，不修改状态。"""

    UNKNOWN = "unknown"
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    BOUNDARY_CHANGED = "boundary_changed"
    SNAPSHOT_LINKED = "snapshot_linked"
    INVARIANT_LINKED = "invariant_linked"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class L2DeltaEntry:
    """L2 增量条目。

    作用：记录某个状态主体的变化类型、前后引用、原因和证据引用。
    边界：不计算真实差异，不修改状态，不写入事件流。
    """

    subject_ref: TypedRef
    kind: L2DeltaKind = L2DeltaKind.UNKNOWN
    before_ref: TypedRef | None = None
    after_ref: TypedRef | None = None
    reason: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2DeltaEntry.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2StateDelta:
    """L2 状态增量。

    作用：记录一个状态增量引用、增量条目集合和元信息。
    边界：不生成增量，不改变状态，不触发事件发布。
    """

    delta_ref: StateDeltaRef
    entries: tuple[L2DeltaEntry, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateDelta.schema_version cannot be empty")
