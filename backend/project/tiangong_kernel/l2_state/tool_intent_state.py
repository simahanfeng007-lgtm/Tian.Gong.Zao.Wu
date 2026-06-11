"""L2 ToolIntent 状态对象，只记录模型工具意图和边界事实，不调用工具或裁决权限。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ToolIntentSource(str, Enum):
    """工具意图来源枚举。

    作用：表达工具意图来自模型、用户、任务或提示引用。
    边界：不生成意图，不调用模型或工具。
    """

    UNKNOWN = "unknown"
    MODEL = "model"
    USER = "user"
    TASK = "task"
    RECOVERY_HINT = "recovery_hint"
    VALIDATION_HINT = "validation_hint"


class ToolIntentStatus(str, Enum):
    """工具意图状态枚举。

    作用：表达工具意图的提出、解析、等待边界、就绪、拒绝或取消状态。
    边界：不调用工具，不执行参数校验器，不提交执行。
    """

    UNKNOWN = "unknown"
    PROPOSED = "proposed"
    PARSED = "parsed"
    BOUNDARY_WAITING = "boundary_waiting"
    BOUNDARY_BLOCKED = "boundary_blocked"
    READY_FOR_L3 = "ready_for_l3"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class ToolIntentBoundaryStatus(str, Enum):
    """工具意图边界状态枚举。

    作用：表达工具意图是否已检查、允许、拒绝、需要确认、降级允许或阻断。
    边界：不做风险评分，不做权限裁决，不生成确认票据。
    """

    UNKNOWN = "unknown"
    NOT_CHECKED = "not_checked"
    WAITING_CHECK = "waiting_check"
    CHECKED_ALLOWED = "checked_allowed"
    CHECKED_REJECTED = "checked_rejected"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DEGRADED_ALLOWED = "degraded_allowed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ToolIntentState:
    """工具意图状态。

    作用：记录模型想调用的工具、工具组、Skill、运行任务、参数摘要和动作意图引用。
    边界：不是工具调用执行器，不执行参数校验，不调用工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    intent_status: ToolIntentStatus = ToolIntentStatus.UNKNOWN
    intent_source: ToolIntentSource = ToolIntentSource.UNKNOWN
    tool_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    tool_group_release_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    model_response_ref: TypedRef | None = None
    source_message_ref: TypedRef | None = None
    argument_schema_ref: TypedRef | None = None
    argument_digest: str | None = None
    argument_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_state_ref: TypedRef | None = None
    action_intent_ref: TypedRef | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.argument_digest == "":
            raise ValueError("ToolIntentState.argument_digest cannot be empty when provided")
        if not self.schema_version:
            raise ValueError("ToolIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ToolIntentBoundaryState:
    """工具意图边界状态。

    作用：记录工具意图关联工具、工具组、Skill、运行任务、边界对象和决策引用。
    边界：不做风险评分，不做权限裁决，不调用工具，不生成确认票据。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    boundary_status: ToolIntentBoundaryStatus = ToolIntentBoundaryStatus.UNKNOWN
    tool_intent_ref: TypedRef | None = None
    tool_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    boundary_ref: L2StateBoundary | None = None
    risk_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    policy_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confirmation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    decision_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ToolIntentBoundaryState.schema_version cannot be empty")
