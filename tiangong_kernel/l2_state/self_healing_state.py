"""L2 自愈主链状态对象。

状态只记录诊断、恢复计划、恢复尝试、恢复后验证、回归与复盘引用，不执行恢复。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class SelfHealingStateBase:
    """自愈状态基础对象。"""

    identity: L2StateIdentity
    status: L2StateStatus
    failure_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_ref: TypedRef | None = None
    summary: str = ""
    state_only: bool = True
    ref_only: bool = True
    executes_recovery: bool = False
    executes_rollback: bool = False
    writes_audit_store: bool = False
    writes_l2_state: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.summary) > 512:
            raise ValueError(f"{self.__class__.__name__}.summary must be short")
        _true(self.state_only, f"{self.__class__.__name__}.state_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _false(self.executes_recovery, f"{self.__class__.__name__}.executes_recovery")
        _false(self.executes_rollback, f"{self.__class__.__name__}.executes_rollback")
        _false(self.writes_audit_store, f"{self.__class__.__name__}.writes_audit_store")
        _false(self.writes_l2_state, f"{self.__class__.__name__}.writes_l2_state")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class FailureDiagnosisState(SelfHealingStateBase):
    """失败诊断状态。"""

    diagnosis_ref: TypedRef | None = None
    diagnosis_confidence: float = 0.0

    def __post_init__(self) -> None:
        SelfHealingStateBase.__post_init__(self)
        _unit(self.diagnosis_confidence, "FailureDiagnosisState.diagnosis_confidence")


@dataclass(frozen=True, slots=True)
class CriticalFailureStepState(SelfHealingStateBase):
    """关键失败步状态。"""

    critical_step_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class RootCauseAnalysisState(SelfHealingStateBase):
    """根因分析状态。"""

    root_cause_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        SelfHealingStateBase.__post_init__(self)
        _unit(self.confidence, "RootCauseAnalysisState.confidence")


@dataclass(frozen=True, slots=True)
class RecoveryPlanState(SelfHealingStateBase):
    """恢复计划状态。"""

    recovery_plan_ref: TypedRef | None = None
    checkpoint_ref: TypedRef | None = None
    recovery_point_ref: TypedRef | None = None
    transaction_ref: TypedRef | None = None
    validation_requirement_ref: TypedRef | None = None
    regression_requirement_ref: TypedRef | None = None
    readiness_score: float = 0.0

    def __post_init__(self) -> None:
        SelfHealingStateBase.__post_init__(self)
        _unit(self.readiness_score, "RecoveryPlanState.readiness_score")


@dataclass(frozen=True, slots=True)
class SelfHealingAttemptState(SelfHealingStateBase):
    """自愈尝试状态。"""

    attempt_ref: TypedRef | None = None
    recovery_plan_ref: TypedRef | None = None
    boundary_review_ref: TypedRef | None = None
    l4_handoff_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class PostRecoveryValidationState(SelfHealingStateBase):
    """恢复后验证状态。"""

    recovery_result_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    regression_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_required: bool = True
    regression_required: bool = True
    marks_recovery_complete: bool = False

    def __post_init__(self) -> None:
        SelfHealingStateBase.__post_init__(self)
        _true(self.validation_required, "PostRecoveryValidationState.validation_required")
        _true(self.regression_required, "PostRecoveryValidationState.regression_required")
        _false(self.marks_recovery_complete, "PostRecoveryValidationState.marks_recovery_complete")


@dataclass(frozen=True, slots=True)
class RegressionOutcomeState(SelfHealingStateBase):
    """回归结果状态。"""

    regression_ref: TypedRef | None = None
    outcome_ref: TypedRef | None = None
    result_only: bool = True

    def __post_init__(self) -> None:
        SelfHealingStateBase.__post_init__(self)
        _true(self.result_only, "RegressionOutcomeState.result_only")


@dataclass(frozen=True, slots=True)
class PostmortemState(SelfHealingStateBase):
    """复盘状态。"""

    postmortem_ref: TypedRef | None = None
    repair_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    record_only: bool = True

    def __post_init__(self) -> None:
        SelfHealingStateBase.__post_init__(self)
        _true(self.record_only, "PostmortemState.record_only")
