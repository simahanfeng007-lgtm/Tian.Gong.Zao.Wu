"""L2 学习状态对象，只记录学习信号、学习需要、材料引用、准备度、边界和可见性事实。

作用：表达学习需求是否出现、材料是否具备、边界是否清晰、是否可被人或模型看见。
边界：不实现自我学习算法，不生成 Skill、Tool、补丁、实验、验证、回滚或进化策略。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class LearningSignalKind(str, Enum):
    """学习信号类型枚举。

    作用：表达学习信号来自用户请求、模型反思、重复失败、工具缺口、Skill 缺口、观察缺口、检索缺口、质量缺口或外部材料引用。
    边界：不生成学习计划，不触发知识生产，不进入变更链。
    """

    UNKNOWN = "unknown"
    USER_REQUEST = "user_request"
    MODEL_REFLECTION = "model_reflection"
    REPEATED_FAILURE = "repeated_failure"
    MISSING_TOOL_HINT = "missing_tool_hint"
    MISSING_SKILL_HINT = "missing_skill_hint"
    OBSERVATION_GAP = "observation_gap"
    RETRIEVAL_GAP = "retrieval_gap"
    QUALITY_GAP = "quality_gap"
    EXTERNAL_MATERIAL_REF = "external_material_ref"


class LearningMaterialKind(str, Enum):
    """学习材料类型枚举。

    作用：表达学习材料引用来自文档、代码、观察、审计、对话、网页引用、文件引用或人工说明。
    边界：不读取材料正文，不抽取知识，不生成 Skill。
    """

    UNKNOWN = "unknown"
    DOCUMENT_REF = "document_ref"
    CODE_REF = "code_ref"
    OBSERVATION_REF = "observation_ref"
    AUDIT_REF = "audit_ref"
    CONVERSATION_REF = "conversation_ref"
    WEB_REF = "web_ref"
    FILE_REF = "file_ref"
    HUMAN_NOTE_REF = "human_note_ref"


class LearningReadinessStatus(str, Enum):
    """学习准备状态枚举。

    作用：表达学习需要处于未知、已声明、材料不足、证据不足、准备就绪、阻断或需人工复核。
    边界：不启动学习，不生成候选，不执行验证或回滚。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    MATERIAL_MISSING = "material_missing"
    EVIDENCE_MISSING = "evidence_missing"
    READY = "ready"
    BLOCKED = "blocked"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class LearningBoundaryStatus(str, Enum):
    """学习边界状态枚举。

    作用：表达学习信号或学习需要是否在边界上未知、允许记录、受限、阻断或仅可引用。
    边界：不执行边界裁决，不发起确认，不产生替代执行路径。
    """

    UNKNOWN = "unknown"
    RECORDABLE = "recordable"
    REF_ONLY = "ref_only"
    LIMITED = "limited"
    BLOCKED = "blocked"
    REVOKED = "revoked"


class LearningVisibilityStatus(str, Enum):
    """学习可见性状态枚举。

    作用：表达学习相关引用是否对模型、人类、审计或后续阶段可见。
    边界：不执行可见性过滤，不暴露材料正文，不触发学习。
    """

    UNKNOWN = "unknown"
    HIDDEN = "hidden"
    MODEL_VISIBLE = "model_visible"
    HUMAN_VISIBLE = "human_visible"
    AUDIT_VISIBLE = "audit_visible"
    LIMITED = "limited"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class LearningSignalState:
    """学习信号状态对象。

    作用：记录学习信号引用、类型、来源、摘要、强度、紧急度、边界和创建时间引用。
    边界：不启动学习，不生成 Skill、Tool、补丁、实验、验证或回滚。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    signal_id: TypedRef | None = None
    kind: LearningSignalKind = LearningSignalKind.UNKNOWN
    source_ref: TypedRef | None = None
    summary: str = ""
    strength: float = 0.0
    urgency: float = 0.0
    boundary_status: L2StateBoundary | None = None
    created_at_ref: TypedRef | None = None
    related_observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_retrieval_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("strength", self.strength), ("urgency", self.urgency)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"LearningSignalState.{name} must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("LearningSignalState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("LearningSignalState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningNeedState:
    """学习需要状态对象。

    作用：记录学习需要引用、信号引用、目标领域、预期用途、缺失知识摘要、缺失工具摘要、准备状态和风险提示。
    边界：不产生变更候选，不生成 Skill 或 Tool，不启动实验或验证。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    need_id: TypedRef | None = None
    signal_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    target_domain: str = ""
    expected_use: str = ""
    missing_knowledge_summary: str = ""
    missing_tool_summary: str = ""
    readiness_status: LearningReadinessStatus = LearningReadinessStatus.UNKNOWN
    risk_hint: str = "unknown"
    boundary_status: L2StateBoundary | None = None
    related_skill_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    related_tool_group_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("target_domain", self.target_domain),
            ("expected_use", self.expected_use),
            ("missing_knowledge_summary", self.missing_knowledge_summary),
            ("missing_tool_summary", self.missing_tool_summary),
        ):
            if len(value) > 512:
                raise ValueError(f"LearningNeedState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("LearningNeedState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningMaterialRefState:
    """学习材料引用状态对象。

    作用：记录学习材料引用、来源、材料类型、内容 hash、摘要、新鲜度、可信等级和边界事实。
    边界：不读取材料正文，不抽取知识，不调用检索器或模型。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    material_ref_id: TypedRef | None = None
    source_ref: TypedRef | None = None
    material_kind: LearningMaterialKind = LearningMaterialKind.UNKNOWN
    content_hash: str = ""
    summary: str = ""
    freshness: str = "unknown"
    trust_level: str = "unknown"
    boundary_status: L2StateBoundary | None = None
    related_need_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("LearningMaterialRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("LearningMaterialRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningReadinessState:
    """学习准备状态对象。

    作用：记录学习需要引用、可用材料、缺失材料摘要、证据引用、准备分数和准备状态。
    边界：不启动学习，不创建实验，不执行验证，不生成 Skill 或 Tool。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    readiness_id: TypedRef | None = None
    need_ref: TypedRef | None = None
    available_material_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_material_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_score: float = 0.0
    readiness_status: LearningReadinessStatus = LearningReadinessStatus.UNKNOWN
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.readiness_score <= 1.0:
            raise ValueError("LearningReadinessState.readiness_score must be between 0 and 1")
        if len(self.missing_material_summary) > 512:
            raise ValueError("LearningReadinessState.missing_material_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("LearningReadinessState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningBoundaryState:
    """学习边界状态对象。

    作用：记录学习相关引用的边界标签、原因、证据和边界状态引用。
    边界：不执行权限裁决，不发起确认，不推进学习动作。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    boundary_ref: TypedRef | None = None
    learning_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_label: LearningBoundaryStatus = LearningBoundaryStatus.UNKNOWN
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("LearningBoundaryState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("LearningBoundaryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LearningVisibilityState:
    """学习可见性状态对象。

    作用：记录学习引用是否对模型、人类可见，以及边界状态和原因摘要。
    边界：不暴露材料正文，不执行可见性过滤，不触发学习或变更。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    visibility_id: TypedRef | None = None
    learning_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    visible_to_model: bool = False
    visible_to_human: bool = False
    visibility_status: LearningVisibilityStatus = LearningVisibilityStatus.UNKNOWN
    boundary_status: L2StateBoundary | None = None
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("LearningVisibilityState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("LearningVisibilityState.schema_version cannot be empty")
