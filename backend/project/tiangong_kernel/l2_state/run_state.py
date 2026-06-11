"""L2 运行状态对象，只记录一次运行的阶段、进度和连续性引用，不实现运行循环。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.state import CheckpointRef, RecoveryPointRef, StateSnapshotRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class RunPhase(str, Enum):
    """运行阶段枚举。

    作用：表达一次运行当前所处阶段。
    边界：不执行运行循环，不调度任务，不调用模型或工具。
    """

    UNKNOWN = "unknown"
    CREATED = "created"
    PREPARING = "preparing"
    ACTIVE = "active"
    WAITING_MODEL = "waiting_model"
    WAITING_OBSERVATION = "waiting_observation"
    WAITING_BOUNDARY = "waiting_boundary"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    PAUSED = "paused"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class RunProgressState:
    """运行进度状态。

    作用：记录一次运行的阶段、完成/失败/阻断/待处理数量和当前单元引用。
    边界：不推进运行，不保存真实上下文，不执行调度。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    phase: RunPhase = RunPhase.UNKNOWN
    completed_units: int = 0
    failed_units: int = 0
    blocked_units: int = 0
    pending_units: int = 0
    current_unit_ref: TypedRef | None = None
    last_success_ref: TypedRef | None = None
    last_failure_ref: TypedRef | None = None
    progress_note: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.completed_units < 0:
            raise ValueError("RunProgressState.completed_units cannot be negative")
        if self.failed_units < 0:
            raise ValueError("RunProgressState.failed_units cannot be negative")
        if self.blocked_units < 0:
            raise ValueError("RunProgressState.blocked_units cannot be negative")
        if self.pending_units < 0:
            raise ValueError("RunProgressState.pending_units cannot be negative")
        if not self.schema_version:
            raise ValueError("RunProgressState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RunState:
    """运行状态。

    作用：记录一次运行的主体引用、目标计划引用、活跃任务引用、进度和连续性锚点。
    边界：不实现运行循环，不推进任务，不调用模型或工具，不创建检查点，不执行恢复。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    phase: RunPhase = RunPhase.UNKNOWN
    agent_ref: TypedRef | None = None
    scope_ref: ScopeRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    active_task_ref: TypedRef | None = None
    progress: RunProgressState | None = None
    snapshot_ref: StateSnapshotRef | None = None
    checkpoint_ref: CheckpointRef | None = None
    recovery_point_ref: RecoveryPointRef | None = None
    trace_context: TraceContext | None = None
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    budget_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    quota_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rate_limit_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_pressure_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RunState.schema_version cannot be empty")
