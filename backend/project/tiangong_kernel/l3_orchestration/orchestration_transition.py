"""L3 编排转移建议对象，只表达从一个编排状态到另一个状态的建议。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus, OrchestrationStatusKind


class OrchestrationTransitionKind(str, Enum):
    """转移建议类别。"""

    UNKNOWN = "unknown"
    STATUS_ADVICE = "status_advice"
    STEP_ADVICE = "step_advice"
    PLAN_ADVICE = "plan_advice"
    STATE_ADVICE = "state_advice"


@dataclass(frozen=True, slots=True)
class OrchestrationTransition:
    """编排转移建议。

    作用：记录来源状态、目标状态、关联引用、原因和证据。
    边界：不更新状态，不签发许可，不决定最终路径。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    transition_ref: TypedRef | None = None
    transition_kind: OrchestrationTransitionKind = OrchestrationTransitionKind.UNKNOWN
    from_status: OrchestrationStatusKind = OrchestrationStatusKind.UNKNOWN
    to_status: OrchestrationStatusKind = OrchestrationStatusKind.UNKNOWN
    source_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    reason: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("OrchestrationTransition.advisory_only must remain true in L3 phase 1")
        if len(self.reason) > 512:
            raise ValueError("OrchestrationTransition.reason must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationTransition.schema_version cannot be empty")
