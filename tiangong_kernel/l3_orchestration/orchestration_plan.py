"""L3 编排计划对象，组合通用步骤、排序引用和转移建议引用。"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus
from .orchestration_step import OrchestrationStep


@dataclass(frozen=True, slots=True)
class OrchestrationPlan:
    """L3 编排计划。

    作用：保存请求、上下文、步骤、排序引用、不变量引用和转移建议引用。
    边界：不启动运行循环，不派发任务，不改变任何状态。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    plan_ref: TypedRef | None = None
    request_ref: TypedRef | None = None
    context_ref: TypedRef | None = None
    steps: tuple[OrchestrationStep, ...] = field(default_factory=tuple)
    invariant_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    route_ranking_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    transition_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("OrchestrationPlan.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationPlan.schema_version cannot be empty")
