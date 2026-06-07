"""L2 生命周期状态对象，只记录生命周期阶段和迁移引用，不执行迁移或删除。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.lifecycle import LifecycleRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class L2LifecyclePhase(str, Enum):
    """L2 生命周期阶段枚举。

    作用：表达 L2 状态对象生命周期阶段。
    边界：不触发生命周期迁移，不执行恢复或调度。
    """

    UNKNOWN = "unknown"
    BIRTH = "birth"
    ACTIVATION = "activation"
    OPERATION = "operation"
    WAITING = "waiting"
    DEGRADATION = "degradation"
    RECOVERY_HINTED = "recovery_hinted"
    TERMINATION = "termination"
    ARCHIVAL = "archival"


class L2LifecycleStatus(str, Enum):
    """L2 生命周期状态枚举。

    作用：表达生命周期当前状态事实。
    边界：不启动、不暂停、不恢复、不删除生命周期对象。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    FAILED = "failed"
    COMPLETED = "completed"
    CLOSED = "closed"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class LifecycleState:
    """L2 生命周期状态。

    作用：记录生命周期引用、目标状态引用、前后状态引用、迁移引用、原因和证据。
    边界：不执行迁移，不启动生命周期，不恢复生命周期，不删除对象。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    phase: L2LifecyclePhase = L2LifecyclePhase.UNKNOWN
    lifecycle_status: L2LifecycleStatus = L2LifecycleStatus.UNKNOWN
    lifecycle_ref: LifecycleRef | None = None
    target_state_ref: TypedRef | None = None
    previous_state_ref: TypedRef | None = None
    next_expected_state_ref: TypedRef | None = None
    transition_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("LifecycleState.schema_version cannot be empty")
