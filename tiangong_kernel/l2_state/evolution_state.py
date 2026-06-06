"""L2 进化状态对象，只记录进化意图、候选、边界、证据、决策提示、回退提示和连续性事实。

作用：为工程生命体的长期结构演进保留状态引用，使进化必须先候选化、证据化、边界化。
边界：不修改架构，不生成插件，不生产工具，不改代码，不合入进化，不执行回退。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class EvolutionIntentKind(str, Enum):
    """进化意图类型枚举。

    作用：表达进化意图来自重复失败、长期 Skill 不足、工具组长期缺失、模型反思、学习结果、用户要求或验证反馈。
    边界：只分类意图，不启动进化。
    """

    UNKNOWN = "unknown"
    REPEATED_FAILURE = "repeated_failure"
    LONG_TERM_SKILL_GAP = "long_term_skill_gap"
    LONG_TERM_TOOL_GROUP_GAP = "long_term_tool_group_gap"
    MODEL_REFLECTION = "model_reflection"
    LEARNING_RESULT = "learning_result"
    USER_REQUEST = "user_request"
    VERIFICATION_FEEDBACK = "verification_feedback"


class EvolutionCandidateStatus(str, Enum):
    """进化候选状态枚举。

    作用：表达进化候选处于未知、已提出、已记录、需证据、需边界、需连续性、需人工复核、阻断或移交。
    边界：不执行进化，不改变架构，不合入候选。
    """

    UNKNOWN = "unknown"
    PROPOSED = "proposed"
    RECORDED = "recorded"
    NEEDS_EVIDENCE = "needs_evidence"
    NEEDS_BOUNDARY = "needs_boundary"
    NEEDS_CONTINUITY = "needs_continuity"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"


class EvolutionBoundaryLabel(str, Enum):
    """进化边界标签枚举。

    作用：表达进化候选仅可建议、必须验证、必须人工确认、绝对禁止或需要兼容迁移说明。
    边界：不执行真实裁决，不生成确认，不改变候选权限。
    """

    UNKNOWN = "unknown"
    SUGGESTION_ONLY = "suggestion_only"
    MUST_VERIFY = "must_verify"
    MUST_HUMAN_CONFIRM = "must_human_confirm"
    FORBIDDEN = "forbidden"
    NEEDS_COMPATIBILITY_NOTE = "needs_compatibility_note"


class EvolutionContinuityStatus(str, Enum):
    """进化连续性状态枚举。

    作用：表达进化前后连续性未知、已声明、缺少 Skill 可理解性、缺少工具组释放性、边界断裂或主链断裂。
    边界：不执行迁移，不修复断裂，不改变主链。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    SKILL_UNDERSTANDING_GAP = "skill_understanding_gap"
    TOOL_GROUP_RELEASE_GAP = "tool_group_release_gap"
    BOUNDARY_BREAK = "boundary_break"
    MAIN_CHAIN_BREAK = "main_chain_break"
    CONTINUOUS = "continuous"


@dataclass(frozen=True, slots=True)
class EvolutionIntentState:
    """进化意图状态对象。

    作用：记录进化意图引用、意图类型、来源引用、目标引用、摘要和强度。
    边界：不启动进化，不生成候选变更，不修改系统结构。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evolution_intent_ref: TypedRef | None = None
    intent_kind: EvolutionIntentKind = EvolutionIntentKind.UNKNOWN
    source_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    summary: str = ""
    strength: float = 0.0
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("EvolutionIntentState.strength must be between 0 and 1")
        if len(self.summary) > 512:
            raise ValueError("EvolutionIntentState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("EvolutionIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionCandidateState:
    """进化候选状态对象。

    作用：记录进化候选引用、候选引用、意图引用、目标引用、候选状态和摘要。
    边界：不修改架构，不生成插件或工具，不合入候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evolution_candidate_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    intent_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    candidate_status: EvolutionCandidateStatus = EvolutionCandidateStatus.UNKNOWN
    summary: str = ""
    expected_benefit_summary: str = ""
    continuity_ref: TypedRef | None = None
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("summary", self.summary), ("expected_benefit_summary", self.expected_benefit_summary)):
            if len(value) > 512:
                raise ValueError(f"EvolutionCandidateState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("EvolutionCandidateState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionBoundaryState:
    """进化边界状态对象。

    作用：记录进化候选的边界标签、相关边界引用、原因和证据引用。
    边界：不执行裁决，不提升权限，不生成确认，不绕过边界层。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    boundary_state_ref: TypedRef | None = None
    evolution_candidate_ref: TypedRef | None = None
    boundary_label: EvolutionBoundaryLabel = EvolutionBoundaryLabel.UNKNOWN
    related_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("EvolutionBoundaryState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("EvolutionBoundaryState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionEvidenceState:
    """进化证据状态对象。

    作用：记录进化候选的证据、观察、验证、学习和实验结果引用。
    边界：不采集证据，不生成实验结果，不执行验证，不更新候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    evidence_state_ref: TypedRef | None = None
    evolution_candidate_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    observation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    experiment_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    completeness_score: float = 0.0
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not 0.0 <= self.completeness_score <= 1.0:
            raise ValueError("EvolutionEvidenceState.completeness_score must be between 0 and 1")
        if not self.schema_version:
            raise ValueError("EvolutionEvidenceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionDecisionHintState:
    """进化决策提示状态对象。

    作用：记录进化候选的决策提示引用、建议动作标签、原因和关联验证引用。
    边界：不做真实决策，不批准进化，不合入候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    decision_hint_ref: TypedRef | None = None
    evolution_candidate_ref: TypedRef | None = None
    suggested_action: str = "unknown"
    reason_summary: str = ""
    verification_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.suggested_action:
            raise ValueError("EvolutionDecisionHintState.suggested_action cannot be empty")
        if len(self.reason_summary) > 512:
            raise ValueError("EvolutionDecisionHintState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("EvolutionDecisionHintState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionRollbackHintState:
    """进化回退提示状态对象。

    作用：记录进化候选的回退提示引用、恢复点、原因、证据和连续性影响。
    边界：不执行回退，不恢复架构，不修改文件，不撤销进化。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    rollback_hint_ref: TypedRef | None = None
    evolution_candidate_ref: TypedRef | None = None
    recovery_point_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    continuity_risk_summary: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("reason_summary", self.reason_summary), ("continuity_risk_summary", self.continuity_risk_summary)):
            if len(value) > 512:
                raise ValueError(f"EvolutionRollbackHintState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("EvolutionRollbackHintState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EvolutionContinuityState:
    """进化连续性状态对象。

    作用：记录进化前后需要保持的 Skill 可理解性、工具组释放性、边界、主链和层级隔离连续性。
    边界：不迁移结构，不修复连续性，不执行进化。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    continuity_ref: TypedRef | None = None
    evolution_candidate_ref: TypedRef | None = None
    continuity_status: EvolutionContinuityStatus = EvolutionContinuityStatus.UNKNOWN
    required_continuity_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    broken_continuity_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.reason_summary) > 512:
            raise ValueError("EvolutionContinuityState.reason_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("EvolutionContinuityState.schema_version cannot be empty")
