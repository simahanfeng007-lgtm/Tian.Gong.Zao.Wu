"""L3 编排上下文对象，只引用 L2 投影与状态切片。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l2_state.projection_state import (
    L3HandoffProjection,
    ModelVisibleStateProjection,
    RuntimeSliceProjectionState,
)

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus


@dataclass(frozen=True, slots=True)
class OrchestrationContext:
    """L3 编排上下文。

    作用：组合 L2 大模型可见投影、L3 交接投影、运行切片投影与相关状态引用。
    边界：不构造提示词，不过滤内容，不刷新状态，只保存可引用事实。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    request_ref: TypedRef | None = None
    model_visible_projection: ModelVisibleStateProjection | None = None
    handoff_projection: L3HandoffProjection | None = None
    runtime_slice_projection: RuntimeSliceProjectionState | None = None
    active_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    math_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affective_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dynamic_drive_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if any(len(item) > 256 for item in self.notes):
            raise ValueError("OrchestrationContext.notes entries must be short")
        if not self.schema_version:
            raise ValueError("OrchestrationContext.schema_version cannot be empty")
