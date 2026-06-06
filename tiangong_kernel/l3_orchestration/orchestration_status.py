"""L3 编排状态对象，只表达编排阶段的当前事实。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class OrchestrationStatusKind(str, Enum):
    """L3 编排状态枚举。"""

    UNKNOWN = "unknown"
    DECLARED = "declared"
    PREPARED = "prepared"
    RANKED = "ranked"
    ADVISED = "advised"
    WAITING_UPPER_LAYER = "waiting_upper_layer"
    BLOCKED_BY_BOUNDARY = "blocked_by_boundary"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OrchestrationStatus:
    """编排状态事实。

    作用：记录当前编排状态、原因、置信度和证据引用。
    边界：不推进状态，不改变 L2 记录，不触发上层或下层动作。
    """

    kind: OrchestrationStatusKind = OrchestrationStatusKind.UNKNOWN
    reason: str = ""
    confidence: float = 0.0
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("OrchestrationStatus.confidence must be between 0.0 and 1.0")
        if len(self.reason) > 512:
            raise ValueError("OrchestrationStatus.reason must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationStatus.schema_version cannot be empty")
