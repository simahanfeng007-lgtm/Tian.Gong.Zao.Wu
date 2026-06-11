"""L2 Action / Effect 状态对象，只记录动作意图和效果观察引用，不执行动作或采集观察。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ActionIntentSource(str, Enum):
    """动作意图来源枚举。

    作用：表达动作意图来自模型工具意图、用户请求、任务计划、恢复提示或验证提示。
    边界：不生成动作，不执行动作，不调用工具。
    """

    UNKNOWN = "unknown"
    MODEL_TOOL_INTENT = "model_tool_intent"
    USER_REQUEST = "user_request"
    TASK_PLAN = "task_plan"
    RECOVERY_HINT = "recovery_hint"
    VALIDATION_HINT = "validation_hint"


class ActionIntentStatus(str, Enum):
    """动作意图状态枚举。

    作用：表达动作意图的提出、等待边界、上层就绪、阻断、拒绝、取消或替代状态。
    边界：不执行动作，不调度任务，不调用工具。
    """

    UNKNOWN = "unknown"
    PROPOSED = "proposed"
    BOUNDARY_WAITING = "boundary_waiting"
    READY_FOR_UPPER_LAYER = "ready_for_upper_layer"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class EffectObservationStatus(str, Enum):
    """效果观察状态枚举。

    作用：表达动作效果未观察、等待观察、已观察、部分观察、观察失败或冲突状态。
    边界：不采集观察，不读取屏幕、文件、网络或真实环境。
    """

    UNKNOWN = "unknown"
    NOT_OBSERVED = "not_observed"
    OBSERVATION_PENDING = "observation_pending"
    OBSERVED = "observed"
    PARTIALLY_OBSERVED = "partially_observed"
    OBSERVATION_FAILED = "observation_failed"
    CONFLICTED = "conflicted"


@dataclass(frozen=True, slots=True)
class ActionIntentState:
    """动作意图状态。

    作用：记录动作意图来源、运行任务、Skill、工具意图、工具、目标、边界和效果观察引用。
    边界：不是动作执行器，不执行动作，不调用工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    action_status: ActionIntentStatus = ActionIntentStatus.UNKNOWN
    action_source: ActionIntentSource = ActionIntentSource.UNKNOWN
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_intent_ref: TypedRef | None = None
    tool_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    boundary_state_ref: TypedRef | None = None
    effect_observation_ref: TypedRef | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ActionIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectObservationState:
    """效果观察状态。

    作用：记录动作意图对应的观察、效果、指标、证据、失败和反馈引用。
    边界：不采集观察，不读取屏幕、文件、网络或真实环境。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    observation_status: EffectObservationStatus = EffectObservationStatus.UNKNOWN
    action_intent_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    feedback_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("EffectObservationState.schema_version cannot be empty")
