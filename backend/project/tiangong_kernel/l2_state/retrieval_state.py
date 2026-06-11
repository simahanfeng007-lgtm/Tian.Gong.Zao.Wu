"""L2 检索状态对象，只记录检索请求、通道、查询、结果引用、覆盖和质量事实，不执行检索。

作用：为记忆、文件索引、代码索引、网页引用、审计日志和观察流等检索来源提供状态记录。
边界：不执行文件搜索、网页搜索、数据库查询、向量检索、embedding、重排或 RAG。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class RetrievalChannelKind(str, Enum):
    """检索通道类型枚举。

    作用：表达检索状态涉及的记忆、文件索引、代码索引、网页引用、审计日志、观察流或外部连接器等通道。
    边界：不连接真实通道，不执行查询或读取。
    """

    UNKNOWN = "unknown"
    MEMORY = "memory"
    FILE_INDEX = "file_index"
    CODE_INDEX = "code_index"
    WEB_REF = "web_ref"
    AUDIT_LOG = "audit_log"
    OBSERVATION_STREAM = "observation_stream"
    EXTERNAL_CONNECTOR = "external_connector"


class RetrievalChannelStatus(str, Enum):
    """检索通道状态枚举。

    作用：表达通道在状态层是未知、声明、可用、受限、阻断、过期或撤销。
    边界：不打开连接，不探测通道，不执行外部请求。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    AVAILABLE = "available"
    LIMITED = "limited"
    BLOCKED = "blocked"
    STALE = "stale"
    REVOKED = "revoked"


class RetrievalStatus(str, Enum):
    """检索请求状态枚举。

    作用：表达检索请求已声明、等待、已有结果引用、部分、空结果、阻断或失败。
    边界：不执行真实检索，不调用文件、网络、向量库或模型。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    WAITING = "waiting"
    RESULT_REFERENCED = "result_referenced"
    PARTIAL = "partial"
    EMPTY = "empty"
    BLOCKED = "blocked"
    FAILED = "failed"


class RetrievalQueryKind(str, Enum):
    """检索查询类型枚举。

    作用：表达查询是关键词、语义摘要、引用追踪、范围过滤、时间过滤或混合查询。
    边界：不执行查询改写，不调用 embedding，不构造外部请求。
    """

    UNKNOWN = "unknown"
    KEYWORD = "keyword"
    SEMANTIC_SUMMARY = "semantic_summary"
    REF_TRACE = "ref_trace"
    SCOPE_FILTER = "scope_filter"
    TIME_FILTER = "time_filter"
    HYBRID = "hybrid"


class RetrievalPrivacyLevel(str, Enum):
    """检索隐私等级状态枚举。

    作用：表达查询或结果引用的隐私暴露标签。
    边界：不执行脱敏，不裁决权限，不读取真实内容。
    """

    UNKNOWN = "unknown"
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    SENSITIVE_REF_ONLY = "sensitive_ref_only"
    REDACTED = "redacted"


class RetrievalQualityStatus(str, Enum):
    """检索质量状态枚举。

    作用：表达检索质量是未知、可用、部分、噪声高、过期、冲突或需复核。
    边界：不计算真实评分，不重排，不解决冲突。
    """

    UNKNOWN = "unknown"
    USABLE = "usable"
    PARTIAL = "partial"
    NOISY = "noisy"
    STALE = "stale"
    CONFLICTED = "conflicted"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class RetrievalChannelState:
    """检索通道状态对象。

    作用：记录检索通道引用、类型、状态、可见范围、资源、边界、安全和观察来源引用。
    边界：不打开真实连接，不读取文件、网页、数据库、向量库或观察流。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    channel_ref: TypedRef | None = None
    channel_kind: RetrievalChannelKind = RetrievalChannelKind.UNKNOWN
    channel_status: RetrievalChannelStatus = RetrievalChannelStatus.UNKNOWN
    scope_ref: TypedRef | None = None
    resource_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trust_label: str = "unknown"
    freshness: str = "unknown"
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.trust_label) > 128:
            raise ValueError("RetrievalChannelState.trust_label must be short")
        if not self.schema_version:
            raise ValueError("RetrievalChannelState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalRequestState:
    """检索请求状态对象。

    作用：记录请求引用、发起者引用、通道类型、查询 hash、查询摘要、检索状态和边界事实。
    边界：不执行真实检索，不访问文件、网页、数据库、向量库或模型。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    request_id: TypedRef | None = None
    requester_ref: TypedRef | None = None
    channel_kinds: tuple[RetrievalChannelKind, ...] = field(default_factory=tuple)
    query_hash: str = ""
    query_summary: str = ""
    retrieval_status: RetrievalStatus = RetrievalStatus.UNKNOWN
    boundary_status: L2StateBoundary | None = None
    created_at_ref: TypedRef | None = None
    related_run_ref: TypedRef | None = None
    related_task_ref: TypedRef | None = None
    related_skill_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.query_summary) > 512:
            raise ValueError("RetrievalRequestState.query_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RetrievalRequestState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalQueryState:
    """检索查询状态对象。

    作用：记录查询引用、类型、归一化 hash、语言、预期范围和隐私等级。
    边界：不执行查询改写，不生成 embedding，不调用重排器。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    query_id: TypedRef | None = None
    query_kind: RetrievalQueryKind = RetrievalQueryKind.UNKNOWN
    normalized_hash: str = ""
    language: str = "unknown"
    expected_scope: str = "unknown"
    privacy_level: RetrievalPrivacyLevel = RetrievalPrivacyLevel.UNKNOWN
    source_request_ref: TypedRef | None = None
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.language) > 64:
            raise ValueError("RetrievalQueryState.language must be short")
        if len(self.expected_scope) > 256:
            raise ValueError("RetrievalQueryState.expected_scope must be short")
        if not self.schema_version:
            raise ValueError("RetrievalQueryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalResultRefState:
    """检索结果引用状态对象。

    作用：记录结果引用、来源、通道、排序、分数、片段 hash、摘要、新鲜度、可信度和边界事实。
    边界：不读取结果正文，不抓取网页，不访问文件，不执行重排。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    result_ref_id: TypedRef | None = None
    source_ref: TypedRef | None = None
    channel_kind: RetrievalChannelKind = RetrievalChannelKind.UNKNOWN
    rank: int = 0
    score: float = 0.0
    snippet_hash: str = ""
    summary: str = ""
    freshness: str = "unknown"
    trust_level: str = "unknown"
    boundary_status: L2StateBoundary | None = None
    request_state_ref: TypedRef | None = None
    query_state_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.rank < 0:
            raise ValueError("RetrievalResultRefState.rank cannot be negative")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("RetrievalResultRefState.score must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("RetrievalResultRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("RetrievalResultRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalCoverageState:
    """检索覆盖状态对象。

    作用：记录请求范围、已覆盖范围、缺失范围、覆盖分数、冲突计数和过期计数。
    边界：不执行补充检索，不解决冲突，不读取真实结果。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    coverage_id: TypedRef | None = None
    requested_scope: str = ""
    covered_scope: str = ""
    missing_scope: str = ""
    coverage_score: float = 0.0
    conflict_count: int = 0
    stale_count: int = 0
    result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.coverage_score <= 1.0:
            raise ValueError("RetrievalCoverageState.coverage_score must be between 0 and 1")
        for name, value in (("conflict_count", self.conflict_count), ("stale_count", self.stale_count)):
            if value < 0:
                raise ValueError(f"RetrievalCoverageState.{name} cannot be negative")
        for name, value in (("requested_scope", self.requested_scope), ("covered_scope", self.covered_scope), ("missing_scope", self.missing_scope)):
            if len(value) > 512:
                raise ValueError(f"RetrievalCoverageState.{name} must be short")
        if not self.schema_version:
            raise ValueError("RetrievalCoverageState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetrievalQualityState:
    """检索质量状态对象。

    作用：记录精度提示、召回提示、新鲜度、可信度、噪声分数和质量状态。
    边界：不计算真实质量评分，不重排，不触发追加检索或模型判断。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    quality_id: TypedRef | None = None
    precision_hint: float = 0.0
    recall_hint: float = 0.0
    freshness_score: float = 0.0
    trust_score: float = 0.0
    noise_score: float = 0.0
    quality_status: RetrievalQualityStatus = RetrievalQualityStatus.UNKNOWN
    evidence_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("precision_hint", self.precision_hint),
            ("recall_hint", self.recall_hint),
            ("freshness_score", self.freshness_score),
            ("trust_score", self.trust_score),
            ("noise_score", self.noise_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"RetrievalQualityState.{name} must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("RetrievalQualityState.schema_version cannot be empty")
