"""L2 状态快照对象，只表达快照引用、状态引用集合和摘要，不落盘或恢复状态。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.state import StateSnapshotRef

from .base_state import L2StateMetadata


@dataclass(frozen=True, slots=True)
class L2SnapshotSummary:
    """L2 快照摘要。

    作用：记录快照中状态数量、活跃数量、阻断数量、失败数量和备注。
    边界：不读取真实状态库，不压缩上下文，不执行恢复。
    """

    total_states: int = 0
    active_states: int = 0
    blocked_states: int = 0
    failed_states: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if self.total_states < 0:
            raise ValueError("L2SnapshotSummary.total_states cannot be negative")
        if self.active_states < 0:
            raise ValueError("L2SnapshotSummary.active_states cannot be negative")
        if self.blocked_states < 0:
            raise ValueError("L2SnapshotSummary.blocked_states cannot be negative")
        if self.failed_states < 0:
            raise ValueError("L2SnapshotSummary.failed_states cannot be negative")
        if not self.schema_version:
            raise ValueError("L2SnapshotSummary.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L2StateSnapshot:
    """L2 状态快照。

    作用：记录一个快照引用、纳入快照的状态引用、摘要和元信息。
    边界：不落盘，不扫描真实状态，不执行检查点恢复。
    """

    snapshot_ref: StateSnapshotRef
    state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: L2SnapshotSummary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("L2StateSnapshot.schema_version cannot be empty")
