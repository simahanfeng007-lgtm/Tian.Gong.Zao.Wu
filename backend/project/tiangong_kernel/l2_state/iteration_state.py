"""L2 迭代状态对象，只记录自我迭代候选、补丁意图、复核、回退提示和证据事实。

作用：把模型反馈、学习信号、Skill 缺口和工具组缺口转成可审计的迭代状态引用。
边界：不生成补丁，不修改代码、Skill 或工具组，不批准合入，不执行回退。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class IterationTargetKind(str, Enum):
    """迭代目标类型枚举。

    作用：表达迭代面向 Skill 流程、工具组绑定、边界说明、测试、文档、状态结构或模型反馈处理。
    边界：只描述目标，不调整目标对象。
    """

    UNKNOWN = "unknown"
    SKILL_FLOW = "skill_flow"
    TOOL_GROUP_BINDING = "tool_group_binding"
    BOUNDARY_DESCRIPTION = "boundary_description"
    TEST = "test"
    DOCUMENTATION = "documentation"
    STATE_SCHEMA = "state_schema"
    MODEL_FEEDBACK_HANDLING = "model_feedback_handling"


class IterationCandidateStatus(str, Enum):
    """迭代候选状态枚举。

    作用：表达迭代候选处于未知、已提出、已记录、证据不足、需边界、需复核、阻断或移交后续阶段。
    边界：不执行迭代，不推进候选，不触发变更。
    """

    UNKNOWN = "unknown"
    PROPOSED = "proposed"
    RECORDED = "recorded"
    EVIDENCE_MISSING = "evidence_missing"
    BOUNDARY_MISSING = "boundary_missing"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"


class IterationReviewStatus(str, Enum):
    """迭代复核状态枚举。

    作用：表达复核未知、待复核、需更多证据、需测试引用、需人工复核、阻断或移交。
    边界：不执行真实复核，不批准或拒绝候选。
    """

    UNKNOWN = "unknown"
    PENDING = "pending"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    NEEDS_TEST_REF = "needs_test_ref"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"


@dataclass(frozen=True, slots=True)
class IterationCandidateState:
    """迭代候选状态对象。

    作用：记录迭代候选引用、目标类型、目标引用、来源候选、学习信号、模型反馈和摘要。
    边界：不修改目标，不生成补丁，不合入迭代，不执行验证。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    iteration_candidate_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    target_kind: IterationTargetKind = IterationTargetKind.UNKNOWN
    target_ref: TypedRef | None = None
    source_feedback_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_learning_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_gap_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    candidate_status: IterationCandidateStatus = IterationCandidateStatus.UNKNOWN
    priority: float = 0.0
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError("IterationCandidateState.priority must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("IterationCandidateState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("IterationCandidateState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationPatchIntentState:
    """迭代补丁意图状态对象。

    作用：记录迭代候选可能需要补丁的意图引用、目标引用、摘要和关联变更引用。
    边界：不生成 patch，不写源码，不修改 Skill，不应用任何变更。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    patch_intent_ref: TypedRef | None = None
    iteration_candidate_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    change_ref: TypedRef | None = None
    patch_intent_summary: str = ""
    patch_generated: bool = False
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.patch_intent_summary) > 512:
            raise ValueError("IterationPatchIntentState.patch_intent_summary must be a short summary")
        if self.patch_generated:
            raise ValueError("IterationPatchIntentState.patch_generated must remain False in L2 state layer")
        if not self.schema_version:
            raise ValueError("IterationPatchIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationEvidenceState:
    """迭代证据状态对象。

    作用：记录迭代候选的证据引用、观察引用、测试引用、验证引用和完整度事实。
    边界：不采集证据，不执行测试，不执行验证，不更新候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evidence_state_ref: TypedRef | None = None
    iteration_candidate_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    test_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    completeness_score: float = 0.0
    evidence_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.completeness_score <= 1.0:
            raise ValueError("IterationEvidenceState.completeness_score must be between 0 and 1")
        if len(self.evidence_summary) > 512:
            raise ValueError("IterationEvidenceState.evidence_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("IterationEvidenceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationReviewState:
    """迭代复核状态对象。

    作用：记录迭代候选复核引用、复核状态、复核者引用、证据引用和复核摘要。
    边界：不批准候选，不拒绝候选，不合入变更，不执行测试。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    review_ref: TypedRef | None = None
    iteration_candidate_ref: TypedRef | None = None
    review_status: IterationReviewStatus = IterationReviewStatus.UNKNOWN
    reviewer_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    review_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.review_summary) > 512:
            raise ValueError("IterationReviewState.review_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("IterationReviewState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class IterationRollbackHintState:
    """迭代回退提示状态对象。

    作用：记录迭代候选的回退提示引用、恢复点引用、原因和可逆性说明。
    边界：不执行回退，不恢复文件，不撤销候选，不修改状态库。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    rollback_hint_ref: TypedRef | None = None
    iteration_candidate_ref: TypedRef | None = None
    recovery_point_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    reversibility_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("reason_summary", self.reason_summary), ("reversibility_summary", self.reversibility_summary)):
            if len(value) > 512:
                raise ValueError(f"IterationRollbackHintState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("IterationRollbackHintState.schema_version cannot be empty")
