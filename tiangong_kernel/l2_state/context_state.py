"""L2 上下文状态对象，只记录窗口、片段、预算、压缩、注入和连续性事实，不管理真实上下文。

作用：为模型可见上下文、记忆注入、检索引用和连续性状态提供稳定记录。
边界：不拼接 prompt，不执行压缩，不计算真实 token，不写入对话历史，不调用模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ContextSegmentKind(str, Enum):
    """上下文片段类型枚举。

    作用：表达上下文片段来自用户输入、助手输出、工具观察引用、Skill 引用、记忆引用或检索引用等来源。
    边界：不生成消息，不读取真实内容，不执行提示词注入。
    """

    UNKNOWN = "unknown"
    USER_INPUT = "user_input"
    ASSISTANT_OUTPUT = "assistant_output"
    TOOL_OBSERVATION_REF = "tool_observation_ref"
    SKILL_REF = "skill_ref"
    MEMORY_REF = "memory_ref"
    RETRIEVAL_REF = "retrieval_ref"
    SYSTEM_BOUNDARY = "system_boundary"
    AUDIT_REF = "audit_ref"
    OTHER = "other"


class ContextVisibilityStatus(str, Enum):
    """上下文可见性状态枚举。

    作用：表达上下文片段或窗口是否隐藏、可见、已注入、已脱敏、过期或被边界阻断。
    边界：不执行可见性过滤，不构造模型请求。
    """

    UNKNOWN = "unknown"
    HIDDEN = "hidden"
    VISIBLE = "visible"
    INJECTED = "injected"
    REDACTED = "redacted"
    EXPIRED = "expired"
    BOUNDARY_BLOCKED = "boundary_blocked"


class ContextOverflowStatus(str, Enum):
    """上下文溢出状态枚举。

    作用：表达上下文窗口预算是否正常、接近上限、溢出、截断或被保留预算限制。
    边界：不执行截断，不重新排序上下文，不计算真实 token。
    """

    UNKNOWN = "unknown"
    WITHIN_BUDGET = "within_budget"
    NEAR_LIMIT = "near_limit"
    OVERFLOWED = "overflowed"
    TRUNCATED = "truncated"
    RESERVED_LIMITED = "reserved_limited"


class ContextCompressionStatus(str, Enum):
    """上下文压缩状态枚举。

    作用：记录压缩事实处于声明、外部完成、部分、有损、阻断或过期状态。
    边界：不执行真实压缩，不调用模型摘要，不改写上下文内容。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    COMPRESSED = "compressed"
    PARTIAL = "partial"
    LOSSY = "lossy"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class ContextInjectionStatus(str, Enum):
    """上下文注入状态枚举。

    作用：表达来源引用进入目标窗口的注入事实状态。
    边界：不执行真实注入，不写入 prompt，不调用模型。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    READY = "ready"
    INJECTED = "injected"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    REVOKED = "revoked"


class ContextContinuityStatus(str, Enum):
    """上下文连续性状态枚举。

    作用：表达相邻上下文窗口之间的延续、部分延续、断裂或冲突事实。
    边界：不执行恢复，不重放历史，不重新生成消息。
    """

    UNKNOWN = "unknown"
    CONTINUOUS = "continuous"
    PARTIAL = "partial"
    BROKEN = "broken"
    CONFLICTED = "conflicted"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class ContextSegmentState:
    """上下文片段状态对象。

    作用：记录上下文片段的类型、来源引用、内容 hash、预算估算、可见性、重要性、新鲜度和边界事实。
    边界：不保存无限正文，不读取外部内容，不生成消息，不执行上下文拼接。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    segment_id: TypedRef | None = None
    kind: ContextSegmentKind = ContextSegmentKind.UNKNOWN
    source_ref: TypedRef | None = None
    content_hash: str = ""
    token_estimate: int = 0
    visibility: ContextVisibilityStatus = ContextVisibilityStatus.UNKNOWN
    importance_score: float = 0.0
    freshness: str = "unknown"
    boundary_status: L2StateBoundary | None = None
    privacy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    summary: str = ""
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    related_skill_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.token_estimate < 0:
            raise ValueError("ContextSegmentState.token_estimate cannot be negative")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("ContextSegmentState.importance_score must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("ContextSegmentState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ContextSegmentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextBudgetState:
    """上下文预算状态对象。

    作用：记录上下文窗口预算上限、已用、保留、检索预留、记忆预留和工具观察预留等事实。
    边界：不计算真实 token，不扣减预算，不触发压缩或截断。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    budget_ref: TypedRef | None = None
    max_budget: int = 0
    used_budget: int = 0
    reserved_budget: int = 0
    memory_reserved_budget: int = 0
    retrieval_reserved_budget: int = 0
    observation_reserved_budget: int = 0
    overflow_status: ContextOverflowStatus = ContextOverflowStatus.UNKNOWN
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("max_budget", self.max_budget),
            ("used_budget", self.used_budget),
            ("reserved_budget", self.reserved_budget),
            ("memory_reserved_budget", self.memory_reserved_budget),
            ("retrieval_reserved_budget", self.retrieval_reserved_budget),
            ("observation_reserved_budget", self.observation_reserved_budget),
        ):
            if value < 0:
                raise ValueError(f"ContextBudgetState.{name} cannot be negative")
        if not self.schema_version:
            raise ValueError("ContextBudgetState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextWindowState:
    """上下文窗口状态对象。

    作用：记录活动片段、预算、溢出状态、连续性引用和模型请求引用。
    边界：不构造真实窗口，不拼接消息，不调用模型，不压缩上下文。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    window_id: TypedRef | None = None
    active_segments: tuple[TypedRef, ...] = field(default_factory=tuple)
    max_budget: int = 0
    used_budget: int = 0
    reserved_budget: int = 0
    overflow_status: ContextOverflowStatus = ContextOverflowStatus.UNKNOWN
    continuity_ref: TypedRef | None = None
    budget_state_ref: TypedRef | None = None
    model_request_ref: TypedRef | None = None
    visibility: ContextVisibilityStatus = ContextVisibilityStatus.UNKNOWN
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("max_budget", self.max_budget), ("used_budget", self.used_budget), ("reserved_budget", self.reserved_budget)):
            if value < 0:
                raise ValueError(f"ContextWindowState.{name} cannot be negative")
        if not self.schema_version:
            raise ValueError("ContextWindowState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextCompressionState:
    """上下文压缩状态对象。

    作用：记录来源片段、压缩后引用、压缩状态、损失风险和覆盖分数。
    边界：不执行真实压缩，不调用模型摘要，不读取片段正文。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    compression_id: TypedRef | None = None
    source_segments: tuple[TypedRef, ...] = field(default_factory=tuple)
    compressed_ref: TypedRef | None = None
    compression_status: ContextCompressionStatus = ContextCompressionStatus.UNKNOWN
    loss_risk: float = 0.0
    coverage_score: float = 0.0
    reason_summary: str = ""
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("loss_risk", self.loss_risk), ("coverage_score", self.coverage_score)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"ContextCompressionState.{name} must be between 0 and 1")
        if len(self.reason_summary) > 512:
            raise ValueError("ContextCompressionState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ContextCompressionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextInjectionState:
    """上下文注入状态对象。

    作用：记录来源引用、目标窗口、注入状态、预算变化和可见性事实。
    边界：不执行真实注入，不写入提示词，不生成模型请求。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    injection_id: TypedRef | None = None
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    target_window_ref: TypedRef | None = None
    injection_status: ContextInjectionStatus = ContextInjectionStatus.UNKNOWN
    budget_delta: int = 0
    visibility_status: ContextVisibilityStatus = ContextVisibilityStatus.UNKNOWN
    boundary_status: L2StateBoundary | None = None
    privacy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(str(self.budget_delta)) > 32:
            raise ValueError("ContextInjectionState.budget_delta representation is too long")
        if not self.schema_version:
            raise ValueError("ContextInjectionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ContextContinuityState:
    """上下文连续性状态对象。

    作用：记录前后窗口引用、承接引用、断裂引用、连续性状态和原因摘要。
    边界：不执行恢复，不重放历史，不重新拼接上下文。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    continuity_id: TypedRef | None = None
    previous_window_ref: TypedRef | None = None
    current_window_ref: TypedRef | None = None
    carryover_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    broken_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    continuity_status: ContextContinuityStatus = ContextContinuityStatus.UNKNOWN
    reason_summary: str = ""
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("ContextContinuityState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ContextContinuityState.schema_version cannot be empty")
