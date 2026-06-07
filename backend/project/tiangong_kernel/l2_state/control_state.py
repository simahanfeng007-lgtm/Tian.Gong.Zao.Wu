"""L2 控制面状态对象。

作用：记录控制面、控制信号和控制约束的状态事实。
边界：不启动控制面，不应用控制模式，不路由任务，不做权限裁决。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ControlPlaneStatus(str, Enum):
    """控制面整体状态。

    作用：表达控制面在当前运行或任务中的状态标签。
    边界：不启动、暂停、关闭或改变任何控制面行为。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    LIMITED = "limited"
    FAILED = "failed"
    CLOSED = "closed"


class ControlPlaneMode(str, Enum):
    """控制面模式标签。

    作用：表达外部控制面记录的普通、安全、严格、只读或确认模式。
    边界：不应用模式，不改变工具、模型、任务或运行行为。
    """

    UNKNOWN = "unknown"
    NORMAL = "normal"
    SAFE = "safe"
    STRICT = "strict"
    READ_ONLY = "read_only"
    CONFIRMATION_REQUIRED = "confirmation_required"
    RECOVERY = "recovery"
    DIAGNOSTIC = "diagnostic"


class ControlSignalStatus(str, Enum):
    """控制信号状态。

    作用：表达暂停、恢复、确认需求、降级等控制信号的记录状态。
    边界：不发送信号，不处理信号，不改变运行或任务。
    """

    UNKNOWN = "unknown"
    OBSERVED = "observed"
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class ControlPlaneState:
    """控制面状态。

    作用：记录 run、task、Skill、ToolIntent 或 ActionIntent 所关联的控制面状态摘要。
    边界：不执行控制，不应用模式，不裁决、不路由、不调度。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    control_status: ControlPlaneStatus = ControlPlaneStatus.UNKNOWN
    mode: ControlPlaneMode = ControlPlaneMode.UNKNOWN
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    skill_state_ref: TypedRef | None = None
    tool_intent_state_ref: TypedRef | None = None
    action_intent_state_ref: TypedRef | None = None
    model_feedback_state_ref: TypedRef | None = None
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    risk_decision_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    policy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("ControlPlaneState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ControlPlaneState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ControlSignalState:
    """控制信号状态。

    作用：记录外部控制面观察到的暂停、恢复、确认需求或降级信号。
    边界：不发送信号，不确认信号，不恢复任务，不改变运行。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    signal_status: ControlSignalStatus = ControlSignalStatus.UNKNOWN
    signal_ref: TypedRef | None = None
    control_plane_state_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    source_ref: TypedRef | None = None
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("ControlSignalState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ControlSignalState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ControlConstraintState:
    """控制约束状态。

    作用：记录只读、确认需求、禁止外传、只允许摘要或只允许引用等约束引用。
    边界：不实现约束拦截器，不过滤内容，不改变任务或工具状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    control_plane_state_ref: TypedRef | None = None
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    applies_to_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.summary == "":
            raise ValueError("ControlConstraintState.summary cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ControlConstraintState.schema_version cannot be empty")
