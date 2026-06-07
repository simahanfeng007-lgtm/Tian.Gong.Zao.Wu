"""L3 记忆遗忘治理服务请求与建议。

本模块只产生 request/advice/score/ranking 引用，不读取记忆库，不执行遗忘、
不删除数据，不写死遗忘公式。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION
from .subsystem_service_request import SubsystemServiceKind, SubsystemServiceRouteCandidate, SubsystemServiceRouteRanking


class ForgettingGovernanceScoreKind(str, Enum):
    """遗忘治理压力分数类型。"""

    RETENTION_PRESSURE = "retention_pressure"
    DECAY_PRESSURE = "decay_pressure"
    INTERFERENCE_PRESSURE = "interference_pressure"
    SUPPRESSION_PRESSURE = "suppression_pressure"
    PRUNING_SUITABILITY = "pruning_suitability"
    REVISION_NEED = "revision_need"
    FORGETTING_GOVERNANCE_NEED = "forgetting_governance_need"


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _short(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class ForgettingServiceRequestRef:
    """遗忘服务请求引用。"""

    request_ref: TypedRef
    source_memory_scope_ref: TypedRef | None = None
    request_scope_hint: str = "future_forgetting_governance_service"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _short(self.request_scope_hint, "ForgettingServiceRequestRef.request_scope_hint", 128)
        if not self.schema_version:
            raise ValueError("ForgettingServiceRequestRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ForgettingAdviceBase:
    """遗忘治理建议基础对象。"""

    advice_ref: TypedRef
    memory_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    no_memory_read: bool = True
    no_context_write: bool = True
    executes_forgetting: bool = False
    deletes_memory: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _short(item, f"{self.__class__.__name__}.reason_codes", 128)
        _short(self.summary, f"{self.__class__.__name__}.summary")
        _true(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        _true(self.no_memory_read, f"{self.__class__.__name__}.no_memory_read")
        _true(self.no_context_write, f"{self.__class__.__name__}.no_context_write")
        _false(self.executes_forgetting, f"{self.__class__.__name__}.executes_forgetting")
        _false(self.deletes_memory, f"{self.__class__.__name__}.deletes_memory")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MemoryGovernanceAdvice(ForgettingAdviceBase):
    """记忆治理总建议。"""

    governance_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class RetentionReviewAdvice(ForgettingAdviceBase):
    """保留复核建议。"""

    retention_boundary_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DecayReviewAdvice(ForgettingAdviceBase):
    """衰减复核建议。"""

    decay_trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class InterferenceReviewAdvice(ForgettingAdviceBase):
    """干扰复核建议。"""

    interference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SuppressionAdvice(ForgettingAdviceBase):
    """抑制建议。"""

    suppression_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PruningAdvice(ForgettingAdviceBase):
    """剪枝建议。"""

    pruning_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RevisionAdvice(ForgettingAdviceBase):
    """修订建议。"""

    revision_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DeletionTombstoneAdvice(ForgettingAdviceBase):
    """删除与墓碑链路建议。"""

    forgetting_ref: TypedRef | None = None
    deletion_ref: TypedRef | None = None
    tombstone_ref: TypedRef | None = None
    audit_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class MemoryPrivacyReviewAdvice(ForgettingAdviceBase):
    """记忆隐私复核建议。"""

    privacy_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    retention_policy_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    requires_l5_boundary: bool = True

    def __post_init__(self) -> None:
        ForgettingAdviceBase.__post_init__(self)
        _true(self.requires_l5_boundary, "MemoryPrivacyReviewAdvice.requires_l5_boundary")


@dataclass(frozen=True, slots=True)
class ForgettingGovernanceScore:
    """遗忘治理压力分数，只接收外部模型或配置结果引用。"""

    score_ref: TypedRef
    score_kind: ForgettingGovernanceScoreKind
    value: float = 0.0
    confidence: float = 0.0
    model_result_ref: TypedRef | None = None
    formula_profile_ref: TypedRef | None = None
    parameter_snapshot_ref: TypedRef | None = None
    externalized: bool = True
    advisory_only: bool = True
    no_hardcoded_formula: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.value, f"{self.__class__.__name__}.value")
        _unit(self.confidence, f"{self.__class__.__name__}.confidence")
        _true(self.externalized, f"{self.__class__.__name__}.externalized")
        _true(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        _true(self.no_hardcoded_formula, f"{self.__class__.__name__}.no_hardcoded_formula")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RetentionPressureScore(ForgettingGovernanceScore):
    """保留压力分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.RETENTION_PRESSURE


@dataclass(frozen=True, slots=True)
class DecayPressureScore(ForgettingGovernanceScore):
    """衰减压力分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.DECAY_PRESSURE


@dataclass(frozen=True, slots=True)
class InterferencePressureScore(ForgettingGovernanceScore):
    """干扰压力分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.INTERFERENCE_PRESSURE


@dataclass(frozen=True, slots=True)
class SuppressionPressureScore(ForgettingGovernanceScore):
    """抑制压力分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.SUPPRESSION_PRESSURE


@dataclass(frozen=True, slots=True)
class PruningSuitabilityScore(ForgettingGovernanceScore):
    """剪枝适配分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.PRUNING_SUITABILITY


@dataclass(frozen=True, slots=True)
class RevisionNeedScore(ForgettingGovernanceScore):
    """修订需求分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.REVISION_NEED


@dataclass(frozen=True, slots=True)
class ForgettingGovernanceNeedScore(ForgettingGovernanceScore):
    """遗忘治理需求分数。"""

    score_kind: ForgettingGovernanceScoreKind = ForgettingGovernanceScoreKind.FORGETTING_GOVERNANCE_NEED


@dataclass(frozen=True, slots=True)
class ForgettingServiceRequest:
    """遗忘治理服务请求。"""

    request_ref: ForgettingServiceRequestRef
    retention_reviews: tuple[RetentionReviewAdvice, ...] = field(default_factory=tuple)
    decay_reviews: tuple[DecayReviewAdvice, ...] = field(default_factory=tuple)
    interference_reviews: tuple[InterferenceReviewAdvice, ...] = field(default_factory=tuple)
    suppression_advices: tuple[SuppressionAdvice, ...] = field(default_factory=tuple)
    pruning_advices: tuple[PruningAdvice, ...] = field(default_factory=tuple)
    revision_advices: tuple[RevisionAdvice, ...] = field(default_factory=tuple)
    deletion_tombstone_advices: tuple[DeletionTombstoneAdvice, ...] = field(default_factory=tuple)
    privacy_reviews: tuple[MemoryPrivacyReviewAdvice, ...] = field(default_factory=tuple)
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.request_only, "ForgettingServiceRequest.request_only")
        if not self.schema_version:
            raise ValueError("ForgettingServiceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ForgettingStateTransitionAdvice:
    """遗忘治理状态转移建议。"""

    advice_ref: TypedRef
    request_ref: TypedRef
    suggested_status: str = "needs_l5_l6_forgetting_governance_review"
    confidence: float = 0.0
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _short(self.suggested_status, "ForgettingStateTransitionAdvice.suggested_status", 128)
        _unit(self.confidence, "ForgettingStateTransitionAdvice.confidence")
        _true(self.advisory_only, "ForgettingStateTransitionAdvice.advisory_only")
        if not self.schema_version:
            raise ValueError("ForgettingStateTransitionAdvice.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ForgettingServiceRouteRanking:
    """遗忘服务路由排序。"""

    ranking: SubsystemServiceRouteRanking
    forgetting_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.advisory_only, "ForgettingServiceRouteRanking.advisory_only")
        if not self.schema_version:
            raise ValueError("ForgettingServiceRouteRanking.schema_version cannot be empty")


def forgetting_route_candidate(candidate_ref: TypedRef, request_ref: TypedRef, priority_score: float) -> SubsystemServiceRouteCandidate:
    """构造遗忘治理服务候选路由。"""

    return SubsystemServiceRouteCandidate(
        candidate_ref=candidate_ref,
        service_kind=SubsystemServiceKind.MEMORY,
        target_request_ref=request_ref,
        priority_score=priority_score,
        reason_codes=("forgetting_governance_request_advice_only",),
    )
