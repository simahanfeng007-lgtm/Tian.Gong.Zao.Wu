"""L2 工程生命体整体状态对象，只记录可用性与健康事实，不执行动作或调度任务。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.state import RuntimeStateRef, StateDeltaRef, StateSnapshotRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class AgentAvailability(str, Enum):
    """工程生命体可用性枚举。

    作用：表达整体可用性。
    边界：不启动服务，不停止服务，不执行调度。
    """

    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class AgentHealthLevel(str, Enum):
    """工程生命体健康等级枚举。

    作用：表达当前健康等级事实。
    边界：不执行自愈，不调用模型或工具，不调整运行状态。
    """

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARN = "warn"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    QUARANTINED = "quarantined"


@dataclass(frozen=True, slots=True)
class AgentHealthState:
    """工程生命体健康状态。

    作用：记录整体健康等级、可用性、主体引用、范围引用、观测引用和失败引用。
    边界：不执行自愈，不采集真实指标，不调用模型或工具，只表达健康事实。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    health_level: AgentHealthLevel = AgentHealthLevel.UNKNOWN
    availability: AgentAvailability = AgentAvailability.UNKNOWN
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    runtime_state_ref: RuntimeStateRef | None = None
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    budget_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    quota_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rate_limit_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_pressure_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AgentHealthState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AgentState:
    """工程生命体整体状态。

    作用：记录工程生命体当前主体、范围、运行引用、健康状态和当前活跃运行/任务引用。
    边界：不是 AgentCore，不处理聊天，不执行路由，不调用模型或工具，不保存状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    actor_ref: ActorRef | None = None
    scope_ref: ScopeRef | None = None
    runtime_state_ref: RuntimeStateRef | None = None
    health: AgentHealthState | None = None
    active_run_ref: TypedRef | None = None
    active_task_ref: TypedRef | None = None
    current_snapshot_ref: StateSnapshotRef | None = None
    last_delta_ref: StateDeltaRef | None = None
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AgentState.schema_version cannot be empty")
