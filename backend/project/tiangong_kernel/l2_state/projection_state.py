"""L2 状态投影对象，记录面向人类、大模型、调试、审计和 L3 交接的结构化投影事实。

本模块位于 L2 状态层，只定义状态投影的数据结构，服务工程生命体把运行切片、候选、观察、记忆上下文、验证和恢复引用组织为可交接的状态摘要。
本模块不实现 UI，不生成真实 prompt，不调用模型，不释放工具，不读取状态仓库，不写审计日志，也不执行权限或边界裁决。
本模块为后续 L3-L6 提供投影引用输入，但不授予执行权限，不启动编排，不改变任何状态对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ProjectionAudience(str, Enum):
    """投影受众枚举。

    作用：表达投影面向人类、大模型、调试、审计、L3 交接、测试或未知受众。
    边界：不决定真实可见性，不生成内容，不触发渲染。
    """

    HUMAN = "human"
    MODEL = "model"
    DEBUG = "debug"
    AUDIT = "audit"
    L3_HANDOFF = "l3_handoff"
    TEST = "test"
    UNKNOWN = "unknown"


class ProjectionStatus(str, Enum):
    """投影状态枚举。

    作用：记录投影处于声明、就绪、部分、过期、阻断或归档等状态事实。
    边界：不刷新投影，不生成投影，不读取状态源。
    """

    DECLARED = "declared"
    READY = "ready"
    PARTIAL = "partial"
    STALE = "stale"
    BLOCKED = "blocked"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class ProjectionVisibility(str, Enum):
    """投影可见性枚举。

    作用：记录片段隐藏、仅摘要、仅引用、详细或受限可见等状态事实。
    边界：不做真实可见性裁决，不过滤内容，不构造模型上下文。
    """

    HIDDEN = "hidden"
    SUMMARY_ONLY = "summary_only"
    REF_ONLY = "ref_only"
    DETAILED = "detailed"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class ProjectionFreshness(str, Enum):
    """投影新鲜度枚举。

    作用：记录投影片段的新鲜、可接受、陈旧、未知或阻断状态。
    边界：不计算真实时间差，不刷新片段，不读取源状态。
    """

    FRESH = "fresh"
    ACCEPTABLE = "acceptable"
    STALE = "stale"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProjectionFragmentState:
    """投影片段状态。

    作用：记录片段引用、源状态引用、受众、可见性、标题、摘要、内容哈希、边界状态和新鲜度。
    边界：不生成片段内容，不读取源状态，不执行渲染或模型总结。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    fragment_id: TypedRef | None = None
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audience: ProjectionAudience = ProjectionAudience.UNKNOWN
    visibility: ProjectionVisibility = ProjectionVisibility.UNKNOWN
    title: str = ""
    summary: str = ""
    content_hash: str = ""
    boundary_status: L2StateBoundary | None = None
    freshness: ProjectionFreshness = ProjectionFreshness.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.title) > 128:
            raise ValueError("ProjectionFragmentState.title must be short")
        if len(self.summary) > 512:
            raise ValueError("ProjectionFragmentState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ProjectionFragmentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelVisibleStateProjection:
    """大模型可见状态投影。

    作用：记录运行、Skill、工具组、模型意图、观察、记忆上下文、候选、验证和恢复等可见引用集合。
    边界：不给模型执行权限，不释放工具，不构造真实 prompt，不调用模型。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    projection_id: TypedRef | None = None
    run_ref: TypedRef | None = None
    skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    model_intent_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    memory_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recovery_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    math_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affective_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dynamic_drive_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    visible_fragments: tuple[TypedRef, ...] = field(default_factory=tuple)
    hidden_reason_summary: str = ""
    projection_status: ProjectionStatus = ProjectionStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.hidden_reason_summary) > 512:
            raise ValueError("ModelVisibleStateProjection.hidden_reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ModelVisibleStateProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class HumanReadableStateProjection:
    """人类可读状态投影。

    作用：记录标题、生命周期摘要、当前运行摘要、Skill、工具组、观察、候选、验证、恢复和风险摘要。
    边界：不生成自然语言长文，不读取真实运行状态，不渲染 UI。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    projection_id: TypedRef | None = None
    title: str = ""
    lifecycle_summary: str = ""
    current_run_summary: str = ""
    active_skill_summary: str = ""
    tool_group_summary: str = ""
    observation_summary: str = ""
    candidate_summary: str = ""
    validation_summary: str = ""
    recovery_summary: str = ""
    risk_summary: str = ""
    projection_status: ProjectionStatus = ProjectionStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        summaries = (
            self.lifecycle_summary,
            self.current_run_summary,
            self.active_skill_summary,
            self.tool_group_summary,
            self.observation_summary,
            self.candidate_summary,
            self.validation_summary,
            self.recovery_summary,
            self.risk_summary,
        )
        if len(self.title) > 128:
            raise ValueError("HumanReadableStateProjection.title must be short")
        if any(len(item) > 512 for item in summaries):
            raise ValueError("HumanReadableStateProjection summaries must be short")
        if not self.schema_version:
            raise ValueError("HumanReadableStateProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DebugStateProjection:
    """调试状态投影。

    作用：记录组件、依赖、失败不变量、序列化问题、导入问题和测试结果引用。
    边界：不执行调试，不运行测试，不导入模块，不修复问题。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    projection_id: TypedRef | None = None
    component_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dependency_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failed_invariant_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    serialization_issue_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    import_issue_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    test_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    projection_status: ProjectionStatus = ProjectionStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("DebugStateProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AuditStateProjection:
    """审计状态投影。

    作用：记录审计、边界、决策、恢复、验证引用和不可变摘要哈希。
    边界：不写审计日志，不生成审计事件，不执行边界裁决。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    projection_id: TypedRef | None = None
    audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    decision_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recovery_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    immutable_summary_hash: str = ""
    projection_status: ProjectionStatus = ProjectionStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("AuditStateProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3HandoffProjection:
    """L3 交接投影。

    作用：记录 L2 版本、稳定状态域、公共状态引用、边界引用、不支持事项和 L3 使用边界摘要。
    边界：不启动 L3，不生成编排计划，不改变 L2 冻结状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    projection_id: TypedRef | None = None
    l2_version: str = L2_STATE_SCHEMA_VERSION
    stable_state_domains: tuple[str, ...] = field(default_factory=tuple)
    public_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    unsupported_items: tuple[str, ...] = field(default_factory=tuple)
    math_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affective_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    dynamic_drive_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    l3_allowed_usage_summary: str = ""
    l3_forbidden_usage_summary: str = ""
    projection_status: ProjectionStatus = ProjectionStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.l2_version:
            raise ValueError("L3HandoffProjection.l2_version cannot be empty")
        if len(self.l3_allowed_usage_summary) > 512:
            raise ValueError("L3HandoffProjection.l3_allowed_usage_summary must be a short summary")
        if len(self.l3_forbidden_usage_summary) > 512:
            raise ValueError("L3HandoffProjection.l3_forbidden_usage_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("L3HandoffProjection.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RuntimeSliceProjectionState:
    """运行切片投影状态。

    作用：记录一次运行切片中的运行、任务、目标、Skill、工具组、模型意图、观察、上下文、候选、验证、恢复和投影引用。
    边界：不创建运行切片，不推进任务，不调用工具，不执行恢复。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    slice_id: TypedRef | None = None
    run_ref: TypedRef | None = None
    task_ref: TypedRef | None = None
    goal_ref: TypedRef | None = None
    skill_ref: TypedRef | None = None
    tool_group_ref: TypedRef | None = None
    model_intent_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    context_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    validation_ref: TypedRef | None = None
    recovery_ref: TypedRef | None = None
    math_state_ref: TypedRef | None = None
    affective_state_ref: TypedRef | None = None
    dynamic_drive_ref: TypedRef | None = None
    projection_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    projection_status: ProjectionStatus = ProjectionStatus.UNKNOWN
    created_at: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RuntimeSliceProjectionState.schema_version cannot be empty")
