"""L2 Model 状态对象，只记录模型请求、响应、反馈和反思事实，不调用模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ModelRequestStatus(str, Enum):
    """模型请求状态。

    作用：表达模型请求准备、可见上下文构建、上层提交、取消或失败状态。
    边界：不调用模型，不发送请求，不导入模型客户端。
    """

    UNKNOWN = "unknown"
    PREPARED = "prepared"
    VISIBLE_CONTEXT_BUILT = "visible_context_built"
    SUBMITTED_BY_UPPER_LAYER = "submitted_by_upper_layer"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ModelResponseStatus(str, Enum):
    """模型响应状态。

    作用：表达模型响应接收、解析、发现工具意图、拒绝、无效或失败状态。
    边界：不消费真实流式响应，不解析真实模型流，不调用模型。
    """

    UNKNOWN = "unknown"
    RECEIVED = "received"
    PARSED = "parsed"
    TOOL_INTENT_FOUND = "tool_intent_found"
    TEXT_ONLY = "text_only"
    REFUSED = "refused"
    INVALID = "invalid"
    FAILED = "failed"


class ModelFeedbackKind(str, Enum):
    """模型反馈类别。

    作用：表达模型反馈涉及进度、Skill 缺口、工具缺口、边界、观察、恢复、验证或澄清需求。
    边界：不生产候选，不修改 Skill，不改工具。
    """

    UNKNOWN = "unknown"
    TASK_PROGRESS = "task_progress"
    SKILL_GAP = "skill_gap"
    TOOL_GAP = "tool_gap"
    BOUNDARY_PROBLEM = "boundary_problem"
    OBSERVATION_NEED = "observation_need"
    RECOVERY_NEED = "recovery_need"
    VALIDATION_NEED = "validation_need"
    USER_CLARIFICATION_NEED = "user_clarification_need"


class ModelReflectionStatus(str, Enum):
    """模型反思状态。

    作用：表达模型反思记录、引用、忽略、阻断或替代状态。
    边界：不触发自我学习、自我迭代或自我进化。
    """

    UNKNOWN = "unknown"
    RECORDED = "recorded"
    REFERENCED = "referenced"
    IGNORED = "ignored"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class ModelRequestState:
    """模型请求状态。

    作用：记录模型请求与运行、任务、可见 Skill、可见工具组、上下文快照和输入消息引用。
    边界：不调用模型，不发送请求，不导入模型客户端。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    request_status: ModelRequestStatus = ModelRequestStatus.UNKNOWN
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    actor_ref: TypedRef | None = None
    visible_skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    visible_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    context_snapshot_ref: TypedRef | None = None
    input_message_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ModelRequestState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelResponseState:
    """模型响应状态。

    作用：记录模型响应、输出消息、工具意图、反馈、反思和解析错误引用。
    边界：不消费真实响应流，不解析真实流式输出，不调用模型。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    response_status: ModelResponseStatus = ModelResponseStatus.UNKNOWN
    request_state_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    output_message_ref: TypedRef | None = None
    tool_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    feedback_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reflection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    parse_error_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ModelResponseState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelFeedbackState:
    """模型反馈状态。

    作用：记录模型反馈类别及响应、Skill、工具组、工具意图、观察、证据和候选提示引用。
    边界：不生产候选，不修改 Skill，不改工具，不调用模型。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    feedback_kind: ModelFeedbackKind = ModelFeedbackKind.UNKNOWN
    response_state_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    tool_intent_ref: TypedRef | None = None
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    candidate_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ModelFeedbackState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelReflectionState:
    """模型反思状态。

    作用：记录模型反思及响应、反馈、来源消息、相关 Skill、工具和失败引用。
    边界：不触发自我学习、自我迭代或自我进化，不调用模型。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    reflection_status: ModelReflectionStatus = ModelReflectionStatus.UNKNOWN
    response_state_ref: TypedRef | None = None
    feedback_state_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    source_message_ref: TypedRef | None = None
    related_skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_tool_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("ModelReflectionState.schema_version cannot be empty")
