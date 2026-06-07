"""L2 变更状态对象，只记录变更意图、影响、可逆性、补丁引用和复核事实，不应用变更。

作用：为后续层提供可追踪的变更候选状态，连接候选、测试引用、证据引用和恢复引用。
边界：不生成补丁，不修改文件，不合入代码，不执行迁移，不执行回退。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ChangeKind(str, Enum):
    """变更类型枚举。

    作用：表达变更候选涉及文档、测试、Skill、工具组绑定、边界说明、状态结构、兼容迁移或架构建议。
    边界：只分类变更事实，不生成或应用任何变更。
    """

    UNKNOWN = "unknown"
    DOCUMENTATION = "documentation"
    TEST = "test"
    SKILL_FLOW = "skill_flow"
    TOOL_GROUP_BINDING = "tool_group_binding"
    BOUNDARY_DESCRIPTION = "boundary_description"
    STATE_SCHEMA = "state_schema"
    COMPATIBILITY_NOTE = "compatibility_note"
    ARCHITECTURE_HINT = "architecture_hint"


class ChangeImpactStatus(str, Enum):
    """变更影响状态枚举。

    作用：表达影响未知、无影响、局部影响、跨阶段影响、破坏性影响、需复核或阻断。
    边界：不计算影响，不扫描依赖，不执行风险评分。
    """

    UNKNOWN = "unknown"
    NONE = "none"
    LOCAL = "local"
    CROSS_PHASE = "cross_phase"
    BREAKING = "breaking"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class ChangeReversibilityStatus(str, Enum):
    """变更可逆性状态枚举。

    作用：表达变更是否未知、可逆、部分可逆、不可逆、需要恢复点或需要人工复核。
    边界：不创建恢复点，不执行回退，不恢复文件。
    """

    UNKNOWN = "unknown"
    REVERSIBLE = "reversible"
    PARTIAL = "partial"
    IRREVERSIBLE = "irreversible"
    NEEDS_RECOVERY_POINT = "needs_recovery_point"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class ChangeReviewStatus(str, Enum):
    """变更复核状态枚举。

    作用：表达变更复核处于未知、待复核、证据不足、边界不足、通过引用、拒绝引用或阻断。
    边界：不执行真实审核，不批准或拒绝变更。
    """

    UNKNOWN = "unknown"
    PENDING = "pending"
    EVIDENCE_MISSING = "evidence_missing"
    BOUNDARY_MISSING = "boundary_missing"
    PASSED_REF = "passed_ref"
    REJECTED_REF = "rejected_ref"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ChangeIntentState:
    """变更意图状态对象。

    作用：记录变更意图引用、候选引用、目标引用、变更类型、摘要和关联证据。
    边界：不生成补丁，不修改目标，不执行迁移，不进入合入链。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    change_intent_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    change_kind: ChangeKind = ChangeKind.UNKNOWN
    summary: str = ""
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("summary", self.summary), ("reason_summary", self.reason_summary)):
            if len(value) > 512:
                raise ValueError(f"ChangeIntentState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("ChangeIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ChangeImpactState:
    """变更影响状态对象。

    作用：记录变更影响范围、受影响状态引用、风险提示和影响状态。
    边界：不分析真实依赖，不评分风险，不修改受影响对象。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    impact_ref: TypedRef | None = None
    change_ref: TypedRef | None = None
    impacted_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    impacted_phase_labels: tuple[str, ...] = field(default_factory=tuple)
    impact_status: ChangeImpactStatus = ChangeImpactStatus.UNKNOWN
    risk_hint: str = "unknown"
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("ChangeImpactState.summary must be a short summary")
        if not self.risk_hint:
            raise ValueError("ChangeImpactState.risk_hint cannot be empty")
        if not self.schema_version:
            raise ValueError("ChangeImpactState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ChangeReversibilityState:
    """变更可逆性状态对象。

    作用：记录变更是否有恢复点引用、回退提示引用、可逆性状态和原因摘要。
    边界：不创建恢复点，不执行回退，不恢复文件或状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    reversibility_ref: TypedRef | None = None
    change_ref: TypedRef | None = None
    recovery_point_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    rollback_hint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reversibility_status: ChangeReversibilityStatus = ChangeReversibilityStatus.UNKNOWN
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("ChangeReversibilityState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ChangeReversibilityState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ChangePatchRefState:
    """变更补丁引用状态对象。

    作用：记录变更关联的补丁意图引用、摘要 hash、目标引用和可见性事实。
    边界：不生成 patch，不读取或写入源码，不应用补丁。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    patch_ref: TypedRef | None = None
    change_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    patch_hash: str = ""
    patch_summary: str = ""
    is_generated: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.patch_summary) > 512:
            raise ValueError("ChangePatchRefState.patch_summary must be a short summary")
        if self.is_generated:
            raise ValueError("ChangePatchRefState.is_generated must remain False in L2 state layer")
        if not self.schema_version:
            raise ValueError("ChangePatchRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ChangeReviewState:
    """变更复核状态对象。

    作用：记录变更复核引用、复核状态、证据引用、验证引用和复核摘要。
    边界：不执行真实复核，不批准变更，不拒绝变更，不触发合入。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    review_ref: TypedRef | None = None
    change_ref: TypedRef | None = None
    review_status: ChangeReviewStatus = ChangeReviewStatus.UNKNOWN
    reviewer_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    review_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.review_summary) > 512:
            raise ValueError("ChangeReviewState.review_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ChangeReviewState.schema_version cannot be empty")
