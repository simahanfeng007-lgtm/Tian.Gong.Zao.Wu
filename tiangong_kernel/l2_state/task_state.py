"""L2 任务状态对象，只记录任务阶段、进度和引用链，不拆分任务或执行工具。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.scope import ScopeRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class TaskPhase(str, Enum):
    """任务阶段枚举。

    作用：表达任务当前阶段。
    边界：不推进步骤，不执行工具，不调用模型或工具。
    """

    UNKNOWN = "unknown"
    DRAFT = "draft"
    READY = "ready"
    ACTIVE = "active"
    WAITING_INPUT = "waiting_input"
    WAITING_MODEL = "waiting_model"
    WAITING_TOOL_RESULT = "waiting_tool_result"
    WAITING_OBSERVATION = "waiting_observation"
    BLOCKED = "blocked"
    DEGRADED = "degraded"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class TaskProgressState:
    """任务进度状态。

    作用：记录任务步骤数量、当前步骤引用、最近观察引用和失败引用。
    边界：不保存完整任务上下文，不推进步骤，不执行调度。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    phase: TaskPhase = TaskPhase.UNKNOWN
    completed_steps: int = 0
    failed_steps: int = 0
    blocked_steps: int = 0
    pending_steps: int = 0
    current_step_ref: TypedRef | None = None
    last_observation_ref: TypedRef | None = None
    last_failure_ref: TypedRef | None = None
    progress_note: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.completed_steps < 0:
            raise ValueError("TaskProgressState.completed_steps cannot be negative")
        if self.failed_steps < 0:
            raise ValueError("TaskProgressState.failed_steps cannot be negative")
        if self.blocked_steps < 0:
            raise ValueError("TaskProgressState.blocked_steps cannot be negative")
        if self.pending_steps < 0:
            raise ValueError("TaskProgressState.pending_steps cannot be negative")
        if not self.schema_version:
            raise ValueError("TaskProgressState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TaskState:
    """任务状态。

    作用：记录任务所属运行、范围、目标计划、进度、父子任务引用、阻断和证据引用。
    边界：不拆任务，不创建计划，不判断下一步，不执行工具，只记录任务事实。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    phase: TaskPhase = TaskPhase.UNKNOWN
    run_ref: TypedRef | None = None
    scope_ref: ScopeRef | None = None
    goal_ref: GoalRef | None = None
    plan_ref: PlanRef | None = None
    progress: TaskProgressState | None = None
    parent_task_ref: TypedRef | None = None
    child_task_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    blocking_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    boundary: L2StateBoundary | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("TaskState.schema_version cannot be empty")
