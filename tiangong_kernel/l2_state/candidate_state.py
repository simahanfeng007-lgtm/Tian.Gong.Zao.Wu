"""L2 候选状态对象，只记录学习、迭代、进化等候选的来源、证据、边界和生命周期事实。

作用：为工程生命体保留候选化状态，使后续层能追踪候选从哪里来、依赖哪些证据、当前处于什么治理阶段。
边界：不创建真实候选池，不执行晋升，不批准合入，不修改 Skill、工具、代码或架构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class CandidateKind(str, Enum):
    """候选类型枚举。

    作用：表达候选来自学习、记忆、上下文、检索、Skill、工具组、迭代、进化、变更、实验或恢复建议。
    边界：只分类候选事实，不决定候选是否通过、合入或回退。
    """

    UNKNOWN = "unknown"
    LEARNING = "learning"
    MEMORY = "memory"
    CONTEXT = "context"
    RETRIEVAL = "retrieval"
    SKILL = "skill"
    TOOL_GROUP = "tool_group"
    ITERATION = "iteration"
    EVOLUTION = "evolution"
    CHANGE = "change"
    EXPERIMENT = "experiment"
    RECOVERY = "recovery"


class CandidateSourceKind(str, Enum):
    """候选来源类型枚举。

    作用：表达候选来源于用户要求、模型反馈、模型反思、观察异常、检索缺口、学习信号、测试引用或人工复核提示。
    边界：不采集来源，不判断来源可信度，不生成新候选。
    """

    UNKNOWN = "unknown"
    USER_REQUEST = "user_request"
    MODEL_FEEDBACK = "model_feedback"
    MODEL_REFLECTION = "model_reflection"
    OBSERVATION_GAP = "observation_gap"
    RETRIEVAL_GAP = "retrieval_gap"
    LEARNING_SIGNAL = "learning_signal"
    TEST_REF = "test_ref"
    HUMAN_REVIEW_HINT = "human_review_hint"


class CandidateLifecycleStatus(str, Enum):
    """候选生命周期状态枚举。

    作用：表达候选处于未知、已提出、已记录、需证据、需边界、需复核、阻断、已关闭或移交后续阶段。
    边界：不执行晋升，不触发验证，不做真实关闭动作。
    """

    UNKNOWN = "unknown"
    PROPOSED = "proposed"
    RECORDED = "recorded"
    NEEDS_EVIDENCE = "needs_evidence"
    NEEDS_BOUNDARY = "needs_boundary"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    CLOSED = "closed"
    HANDED_OFF = "handed_off"


class CandidateBoundaryStatus(str, Enum):
    """候选边界状态枚举。

    作用：表达候选边界处于未知、仅可记录、仅可引用、受限、阻断、需人工复核或已撤销。
    边界：不执行权限裁决，不生成确认票据，不提升候选权限。
    """

    UNKNOWN = "unknown"
    RECORD_ONLY = "record_only"
    REF_ONLY = "ref_only"
    LIMITED = "limited"
    BLOCKED = "blocked"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class CandidateRefState:
    """候选引用状态对象。

    作用：记录统一候选引用、候选类型、主体引用、来源引用、摘要、优先级和生命周期事实。
    边界：不创建候选池，不晋升候选，不调用验证，不修改任何目标对象。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    candidate_ref: TypedRef | None = None
    candidate_kind: CandidateKind = CandidateKind.UNKNOWN
    subject_ref: TypedRef | None = None
    source_ref: TypedRef | None = None
    source_kind: CandidateSourceKind = CandidateSourceKind.UNKNOWN
    summary: str = ""
    priority: float = 0.0
    lifecycle_status: CandidateLifecycleStatus = CandidateLifecycleStatus.UNKNOWN
    boundary_status: L2StateBoundary | None = None
    created_at_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError("CandidateRefState.priority must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("CandidateRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("CandidateRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateSourceState:
    """候选来源状态对象。

    作用：记录候选来源引用、来源类型、关联的模型反馈、观察、学习或人工提示引用。
    边界：不读取来源内容，不判断来源真伪，不重新生成候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    source_state_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    source_kind: CandidateSourceKind = CandidateSourceKind.UNKNOWN
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("CandidateSourceState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("CandidateSourceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateEvidenceState:
    """候选证据状态对象。

    作用：记录候选关联证据、验证引用、观察引用和证据完整度事实。
    边界：不采集证据，不验证证据，不复制证据，不写审计库。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evidence_state_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    completeness_score: float = 0.0
    missing_evidence_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.completeness_score <= 1.0:
            raise ValueError("CandidateEvidenceState.completeness_score must be between 0 and 1")
        if len(self.missing_evidence_summary) > 512:
            raise ValueError("CandidateEvidenceState.missing_evidence_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("CandidateEvidenceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateBoundaryState:
    """候选边界状态对象。

    作用：记录候选边界标签、原因、关联边界状态引用和证据引用。
    边界：不执行真实边界裁决，不提升风险等级，不生成审批或确认。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    boundary_state_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    boundary_label: CandidateBoundaryStatus = CandidateBoundaryStatus.UNKNOWN
    related_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("CandidateBoundaryState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("CandidateBoundaryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateLifecycleState:
    """候选生命周期状态对象。

    作用：记录候选从提出到记录、等待证据、等待边界、等待复核、阻断、关闭或移交的状态事实。
    边界：不推进候选，不执行复核，不进行真实晋升或拒绝。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    lifecycle_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    previous_status: CandidateLifecycleStatus = CandidateLifecycleStatus.UNKNOWN
    current_status: CandidateLifecycleStatus = CandidateLifecycleStatus.UNKNOWN
    transition_reason: str = ""
    checkpoint_ref: TypedRef | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.transition_reason) > 512:
            raise ValueError("CandidateLifecycleState.transition_reason must be a short summary")
        if not self.schema_version:
            raise ValueError("CandidateLifecycleState.schema_version cannot be empty")
