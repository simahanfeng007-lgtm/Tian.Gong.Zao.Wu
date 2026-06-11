"""L2 记忆状态对象，只记录记忆引用、层级、召回、注入和健康事实，不实现记忆系统。

作用：为上层记忆系统留下可序列化、可比较、可快照的状态事实。
边界：不读取记忆库，不执行召回，不做遗忘、晋升、embedding、检索或 Skill 生产。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class MemoryLayer(str, Enum):
    """记忆层级状态枚举。

    作用：表达记忆引用所属的层级标签。
    边界：不实现旧记忆系统，不决定召回、晋升或遗忘。
    """

    UNKNOWN = "unknown"
    TRANSIENT = "transient"
    SHORT_CONTEXT = "short_context"
    EPISODIC = "episodic"
    STABLE = "stable"
    RULE_LIKE = "rule_like"
    EXTERNAL_REF = "external_ref"


class MemoryCognitiveKind(str, Enum):
    """记忆认知类型枚举。

    作用：区分工作、情景、语义、程序性、自我和系统运行记忆。
    边界：不决定召回、注入、晋升或遗忘，只补充记忆引用维度。
    """

    UNKNOWN = "unknown"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    SELF = "self"
    SYSTEM = "system"


class MemoryVisibilityStatus(str, Enum):
    """记忆可见性状态枚举。

    作用：表达记忆引用当前是否隐藏、被引用、可见、已注入、过期或撤销。
    边界：不执行可见性过滤，不读取记忆正文，不构造上下文。
    """

    UNKNOWN = "unknown"
    HIDDEN = "hidden"
    REFERENCED = "referenced"
    VISIBLE = "visible"
    INJECTED = "injected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MemoryRecallStatus(str, Enum):
    """记忆召回状态枚举。

    作用：记录一次召回请求在状态层被声明、匹配、部分、空结果、阻断或过期。
    边界：不执行真实召回，不查询索引，不调用 embedding 或模型。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    MATCHED = "matched"
    PARTIAL = "partial"
    EMPTY = "empty"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class MemoryInjectionStatus(str, Enum):
    """记忆注入状态枚举。

    作用：表达记忆引用与上下文窗口之间的注入事实状态。
    边界：不执行真实注入，不拼接 prompt，不写入对话历史。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    READY = "ready"
    INJECTED = "injected"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class MemoryHealthStatus(str, Enum):
    """记忆健康状态枚举。

    作用：表达记忆引用集合的新鲜、冲突、缺失或超预算等健康事实。
    边界：不执行清理，不改写记忆，不触发遗忘或晋升。
    """

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    STALE = "stale"
    CONFLICTED = "conflicted"
    MISSING_REFS = "missing_refs"
    OVER_BUDGET = "over_budget"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class MemoryLayerState:
    """记忆层级状态对象。

    作用：记录某一记忆层级在当前范围内的引用集合、可见性和预算事实。
    边界：不读取记忆层，不执行召回，不执行晋升、降级或遗忘。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    layer: MemoryLayer = MemoryLayer.UNKNOWN
    scope_ref: TypedRef | None = None
    memory_ref_count: int = 0
    visible_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    hidden_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    revoked_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    budget_limit: int = 0
    budget_used: int = 0
    boundary: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.memory_ref_count < 0:
            raise ValueError("MemoryLayerState.memory_ref_count cannot be negative")
        if self.budget_limit < 0:
            raise ValueError("MemoryLayerState.budget_limit cannot be negative")
        if self.budget_used < 0:
            raise ValueError("MemoryLayerState.budget_used cannot be negative")
        if not self.schema_version:
            raise ValueError("MemoryLayerState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryRefState:
    """记忆引用状态对象。

    作用：记录一个记忆引用的层级、来源、摘要、hash、新鲜度、置信度、可见性和边界事实。
    边界：不保存完整记忆正文，不读取记忆库，不执行召回、遗忘或 Skill 生产。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    memory_ref_id: TypedRef | None = None
    layer: MemoryLayer = MemoryLayer.UNKNOWN
    memory_kind: str = MemoryCognitiveKind.UNKNOWN.value
    scope_ref: TypedRef | None = None
    source_ref: TypedRef | None = None
    content_hash: str = ""
    summary: str = ""
    visibility: MemoryVisibilityStatus = MemoryVisibilityStatus.UNKNOWN
    confidence: float = 0.0
    freshness: str = "unknown"
    boundary_status: L2StateBoundary | None = None
    privacy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    created_at_ref: TypedRef | None = None
    updated_at_ref: TypedRef | None = None
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    related_skill_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.memory_kind not in {item.value for item in MemoryCognitiveKind}:
            raise ValueError("MemoryRefState.memory_kind must be a known cognitive memory kind")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("MemoryRefState.confidence must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("MemoryRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MemoryRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryRecallState:
    """记忆召回状态对象。

    作用：记录召回请求引用、查询引用、请求层级、匹配引用和覆盖/噪声指标。
    边界：不执行真实召回，不查询索引，不计算 embedding，不做模型重排。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recall_id: TypedRef | None = None
    query_ref: TypedRef | None = None
    requested_layers: tuple[MemoryLayer, ...] = field(default_factory=tuple)
    matched_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recall_status: MemoryRecallStatus = MemoryRecallStatus.UNKNOWN
    coverage_score: float = 0.0
    noise_score: float = 0.0
    reason_summary: str = ""
    boundary_status: L2StateBoundary | None = None
    created_at_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("coverage_score", self.coverage_score), ("noise_score", self.noise_score)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"MemoryRecallState.{name} must be between 0 and 1")
        if len(self.reason_summary) > 512:
            raise ValueError("MemoryRecallState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MemoryRecallState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryInjectionState:
    """记忆注入状态对象。

    作用：记录已被声明用于上下文注入的记忆引用、目标上下文引用、预算和可见性事实。
    边界：不执行真实注入，不拼接上下文，不生成模型消息。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    injection_id: TypedRef | None = None
    injected_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    target_context_ref: TypedRef | None = None
    visibility_status: MemoryVisibilityStatus = MemoryVisibilityStatus.UNKNOWN
    budget_used: int = 0
    injection_status: MemoryInjectionStatus = MemoryInjectionStatus.UNKNOWN
    boundary_status: L2StateBoundary | None = None
    privacy_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consent_ref: TypedRef | None = None
    purpose_ref: TypedRef | None = None
    retention_policy_ref: TypedRef | None = None
    trust_boundary_ref: TypedRef | None = None
    created_at_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.budget_used < 0:
            raise ValueError("MemoryInjectionState.budget_used cannot be negative")
        if not self.schema_version:
            raise ValueError("MemoryInjectionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryHealthState:
    """记忆健康状态对象。

    作用：记录记忆集合的过期、冲突、缺失引用、超预算计数和健康标签。
    边界：不执行真实清理，不合并冲突，不触发遗忘或晋升。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    health_ref: TypedRef | None = None
    related_memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    stale_count: int = 0
    conflict_count: int = 0
    missing_ref_count: int = 0
    over_budget_count: int = 0
    health_status: MemoryHealthStatus = MemoryHealthStatus.UNKNOWN
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("stale_count", self.stale_count),
            ("conflict_count", self.conflict_count),
            ("missing_ref_count", self.missing_ref_count),
            ("over_budget_count", self.over_budget_count),
        ):
            if value < 0:
                raise ValueError(f"MemoryHealthState.{name} cannot be negative")
        if len(self.reason_summary) > 512:
            raise ValueError("MemoryHealthState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("MemoryHealthState.schema_version cannot be empty")
