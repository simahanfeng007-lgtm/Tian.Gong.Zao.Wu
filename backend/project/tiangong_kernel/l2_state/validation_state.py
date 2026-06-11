"""L2 验证状态对象，只记录验证意图、验证引用、测试计划引用、候选验证和恢复验证事实。

作用：为第七阶段候选、变更、实验和恢复对象提供验证状态引用，不执行任何测试或验证。
边界：不运行测试，不计算验证结果，不晋升候选，不执行回退或恢复。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_boundary import L2StateBoundary
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ValidationIntentKind(str, Enum):
    """验证意图类型枚举。

    作用：表达验证意图面向候选、变更、实验、学习结果、迭代、进化、恢复或兼容性。
    边界：只分类验证意图，不启动验证。
    """

    UNKNOWN = "unknown"
    CANDIDATE = "candidate"
    CHANGE = "change"
    EXPERIMENT = "experiment"
    LEARNING_RESULT = "learning_result"
    ITERATION = "iteration"
    EVOLUTION = "evolution"
    RECOVERY = "recovery"
    COMPATIBILITY = "compatibility"


class ValidationReadinessStatus(str, Enum):
    """验证准备状态枚举。

    作用：表达验证准备未知、已声明、测试缺失、证据缺失、边界缺失、准备就绪、阻断或移交。
    边界：不运行验证，不生成测试，不收集证据。
    """

    UNKNOWN = "unknown"
    DECLARED = "declared"
    TEST_MISSING = "test_missing"
    EVIDENCE_MISSING = "evidence_missing"
    BOUNDARY_MISSING = "boundary_missing"
    READY = "ready"
    BLOCKED = "blocked"
    HANDED_OFF = "handed_off"


class ValidationOutcomeRefStatus(str, Enum):
    """验证结果引用状态枚举。

    作用：表达验证结果处于未知、未引用、已引用、部分引用、冲突引用、过期或阻断。
    边界：不计算结果，不判定通过或失败，不改变候选。
    """

    UNKNOWN = "unknown"
    NOT_REFERENCED = "not_referenced"
    REFERENCED = "referenced"
    PARTIAL = "partial"
    CONFLICTED = "conflicted"
    EXPIRED = "expired"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ValidationIntentState:
    """验证意图状态对象。

    作用：记录验证意图引用、验证类型、目标引用、候选引用和摘要。
    边界：不运行验证，不生成测试，不推进候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    validation_intent_ref: TypedRef | None = None
    intent_kind: ValidationIntentKind = ValidationIntentKind.UNKNOWN
    target_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    summary: str = ""
    boundary_status: L2StateBoundary | None = None
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("ValidationIntentState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ValidationIntentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ValidationRefState:
    """验证引用状态对象。

    作用：记录验证引用、测试引用、验证结果引用、证据引用和结果引用状态。
    边界：不执行验证，不创建结果，不判断通过或失败。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    validation_ref: TypedRef | None = None
    validation_intent_ref: TypedRef | None = None
    test_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    outcome_status: ValidationOutcomeRefStatus = ValidationOutcomeRefStatus.UNKNOWN
    summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError("ValidationRefState.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ValidationRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class VerificationRefState:
    """验证规格引用状态对象。

    作用：记录规格验证引用、目标引用、不变量引用、契约引用和证据引用。
    边界：不执行规格验证，不检查不变量，不做形式化证明。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    verification_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    invariant_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    contract_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    outcome_status: ValidationOutcomeRefStatus = ValidationOutcomeRefStatus.UNKNOWN
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("VerificationRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class TestPlanRefState:
    """测试计划引用状态对象。

    作用：记录测试计划引用、目标引用、测试引用、覆盖引用和准备状态。
    边界：不生成测试，不运行测试，不计算覆盖。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    test_plan_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    test_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    coverage_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_status: ValidationReadinessStatus = ValidationReadinessStatus.UNKNOWN
    plan_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.plan_summary) > 512:
            raise ValueError("TestPlanRefState.plan_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("TestPlanRefState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class CandidateValidationState:
    """候选验证状态对象。

    作用：记录候选引用、验证意图、验证引用、准备状态和缺失摘要。
    边界：不执行候选验证，不晋升候选，不拒绝候选。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    candidate_validation_ref: TypedRef | None = None
    candidate_ref: TypedRef | None = None
    validation_intent_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_status: ValidationReadinessStatus = ValidationReadinessStatus.UNKNOWN
    missing_summary: str = ""
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.missing_summary) > 512:
            raise ValueError("CandidateValidationState.missing_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("CandidateValidationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryValidationState:
    """恢复验证状态对象。

    作用：记录恢复点、回退提示、验证引用、恢复验证状态和证据引用。
    边界：不执行恢复验证，不回退文件，不修改状态。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    recovery_validation_ref: TypedRef | None = None
    recovery_point_ref: TypedRef | None = None
    rollback_hint_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    readiness_status: ValidationReadinessStatus = ValidationReadinessStatus.UNKNOWN
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RecoveryValidationState.schema_version cannot be empty")

# 防止 pytest 将 L2 状态对象误识别为测试类。
TestPlanRefState.__test__ = False
