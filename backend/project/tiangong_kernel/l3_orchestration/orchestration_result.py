"""L3 编排结果对象，只表达计划产物、建议引用和结果事实。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.result import CoreResult
from tiangong_kernel.l1_ports.port_result import PortResult

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus


class OrchestrationResultKind(str, Enum):
    """编排结果类别。"""

    UNKNOWN = "unknown"
    PLAN_PREPARED = "plan_prepared"
    MATH_RECOMMENDATION_READY = "math_recommendation_ready"
    ADVICE_READY = "advice_ready"
    BLOCKED_BY_INPUT = "blocked_by_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    """L3 编排结果。

    作用：保存编排后的引用、L0/L1 结果包装和摘要。
    边界：结果仅表达事实和建议，不代表下游层已经采取动作。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    result_kind: OrchestrationResultKind = OrchestrationResultKind.UNKNOWN
    plan_ref: TypedRef | None = None
    core_result: CoreResult[Any] | None = None
    port_result: PortResult[Any] | None = None
    output_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recommendation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    transition_advice_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("OrchestrationResult.advisory_only must remain true in L3 phase 1")
        if len(self.summary) > 512:
            raise ValueError("OrchestrationResult.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationResult.schema_version cannot be empty")
