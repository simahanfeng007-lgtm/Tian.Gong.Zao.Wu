"""L2 Skill 状态对象，只记录可见、选择、激活和失败事实，不读取或执行 Skill。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class SkillVisibilityStatus(str, Enum):
    """Skill 可见性状态。

    作用：表达 Skill 对模型或任务是否可见。
    边界：不执行可见性过滤，不读取 Skill 内容。
    """

    UNKNOWN = "unknown"
    HIDDEN = "hidden"
    VISIBLE = "visible"
    FILTERED = "filtered"
    BOUNDARY_BLOCKED = "boundary_blocked"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class SkillSelectionStatus(str, Enum):
    """Skill 选择状态。

    作用：表达 Skill 是否被模型、任务或外部编排层标记为候选或已选。
    边界：不选择 Skill，不执行路由，不调用模型或工具。
    """

    UNKNOWN = "unknown"
    CANDIDATE = "candidate"
    SELECTED = "selected"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    CONFLICTED = "conflicted"


class SkillActivationStatus(str, Enum):
    """Skill 激活状态。

    作用：表达已选 Skill 在当前运行或任务中的激活事实。
    边界：不激活 Skill，不生成工具组，不执行动作。
    """

    UNKNOWN = "unknown"
    WAITING_TOOL_GROUP = "waiting_tool_group"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SkillFailureKind(str, Enum):
    """Skill 失败类别。

    作用：表达 Skill 层失败原因类别。
    边界：不执行修复，不产生学习候选，不修改 Skill。
    """

    UNKNOWN = "unknown"
    NOT_FOUND = "not_found"
    VERSION_MISMATCH = "version_mismatch"
    BOUNDARY_BLOCKED = "boundary_blocked"
    TOOL_GROUP_MISSING = "tool_group_missing"
    TOOL_INTENT_REJECTED = "tool_intent_rejected"
    MODEL_REFUSED = "model_refused"
    OBSERVATION_MISSING = "observation_missing"
    INVARIANT_FAILED = "invariant_failed"


@dataclass(frozen=True, slots=True)
class SkillVisibilityState:
    """Skill 可见状态。

    作用：记录 Skill 对当前运行、任务或模型请求的可见性事实和可见工具组引用。
    边界：不读取 Skill 内容，不执行过滤，不调用模型或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    visibility_status: SkillVisibilityStatus = SkillVisibilityStatus.UNKNOWN
    skill_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    model_request_ref: TypedRef | None = None
    visible_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SkillVisibilityState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillSelectionState:
    """Skill 选择事实状态。

    作用：记录 Skill 被标记为候选、已选、拒绝或冲突的事实和来源引用。
    边界：不选择 Skill，不生成计划，不调用模型或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    selection_status: SkillSelectionStatus = SkillSelectionStatus.UNKNOWN
    skill_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    selected_by_ref: TypedRef | None = None
    source_message_ref: TypedRef | None = None
    reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    alternative_skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SkillSelectionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillActivationState:
    """Skill 激活状态。

    作用：记录已选 Skill 在运行或任务中的激活状态、工具组、工具意图、动作、观察和反馈引用。
    边界：不激活 Skill，不生成工具组，不执行动作，不调用模型或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    activation_status: SkillActivationStatus = SkillActivationStatus.UNKNOWN
    skill_ref: TypedRef | None = None
    selection_state_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    tool_group_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tool_intent_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    action_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    feedback_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    continuity_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SkillActivationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SkillFailureState:
    """Skill 失败状态。

    作用：记录 Skill 失败类别、阻断的工具组或工具意图、边界、证据、审计和恢复提示引用。
    边界：不执行修复，不生成候选，不修改 Skill，不调用模型或工具。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    failure_kind: SkillFailureKind = SkillFailureKind.UNKNOWN
    skill_ref: TypedRef | None = None
    activation_state_ref: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    blocked_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    blocked_tool_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_ref: L2StateBoundary | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recovery_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("SkillFailureState.schema_version cannot be empty")
