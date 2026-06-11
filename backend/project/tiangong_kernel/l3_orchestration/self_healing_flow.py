"""L3 自愈主生命周期 Flow。

本模块只表达失败到诊断、恢复计划、边界复核、恢复交接、恢复后验证和复盘
的建议链，不调用工具、不执行回滚、不写状态、不签发许可。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class SelfHealingReadiness(str, Enum):
    """自愈交接就绪度。"""

    NEEDS_PRECONDITION = "needs_precondition"
    READY_FOR_BOUNDARY_REVIEW = "ready_for_boundary_review"


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class SelfHealingAdviceBase:
    """自愈建议基础对象。"""

    advice_ref: TypedRef
    failure_ref: TypedRef | None = None
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_requirement_ref: TypedRef | None = None
    advisory_only: bool = True
    ref_only: bool = True
    executes_recovery: bool = False
    executes_rollback: bool = False
    writes_state: bool = False
    signs_permission: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        _true(self.ref_only, f"{self.__class__.__name__}.ref_only")
        _false(self.executes_recovery, f"{self.__class__.__name__}.executes_recovery")
        _false(self.executes_rollback, f"{self.__class__.__name__}.executes_rollback")
        _false(self.writes_state, f"{self.__class__.__name__}.writes_state")
        _false(self.signs_permission, f"{self.__class__.__name__}.signs_permission")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class FailureToDiagnosisAdvice(SelfHealingAdviceBase):
    """失败到诊断建议。"""

    diagnosis_request_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class DiagnosisToRecoveryPlanAdvice(SelfHealingAdviceBase):
    """诊断到恢复计划建议。"""

    diagnosis_ref: TypedRef | None = None
    recovery_plan_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class RecoveryPlanToBoundaryReviewAdvice(SelfHealingAdviceBase):
    """恢复计划到 L5 边界复核建议。"""

    recovery_plan_ref: TypedRef | None = None
    boundary_review_ref: TypedRef | None = None
    lease_requirement_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class RecoveryExecutionHandoffAdvice(SelfHealingAdviceBase):
    """恢复执行交接建议。"""

    l4_handoff_ref: TypedRef | None = None
    l6_recovery_requirement_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class PostRecoveryValidationAdvice(SelfHealingAdviceBase):
    """恢复后验证与回归建议。"""

    validation_requirement_ref: TypedRef | None = None
    regression_requirement_ref: TypedRef | None = None
    validation_required: bool = True
    regression_required: bool = True

    def __post_init__(self) -> None:
        SelfHealingAdviceBase.__post_init__(self)
        _true(self.validation_required, "PostRecoveryValidationAdvice.validation_required")
        _true(self.regression_required, "PostRecoveryValidationAdvice.regression_required")


@dataclass(frozen=True, slots=True)
class SelfHealingClosureAdvice(SelfHealingAdviceBase):
    """自愈复盘收口建议。"""

    postmortem_ref: TypedRef | None = None
    repair_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SelfHealingFlowEnvelope:
    """自愈主生命周期信封。"""

    envelope_ref: TypedRef
    failure_ref: TypedRef | None = None
    checkpoint_ref: TypedRef | None = None
    transaction_ref: TypedRef | None = None
    recovery_plan_ref: TypedRef | None = None
    boundary_review_ref: TypedRef | None = None
    validation_requirement_ref: TypedRef | None = None
    regression_requirement_ref: TypedRef | None = None
    advices: tuple[SelfHealingAdviceBase, ...] = field(default_factory=tuple)
    readiness: SelfHealingReadiness = SelfHealingReadiness.NEEDS_PRECONDITION
    request_only: bool = True
    advisory_only: bool = True
    executes_recovery: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.request_only, "SelfHealingFlowEnvelope.request_only")
        _true(self.advisory_only, "SelfHealingFlowEnvelope.advisory_only")
        _false(self.executes_recovery, "SelfHealingFlowEnvelope.executes_recovery")
        if self.readiness is SelfHealingReadiness.READY_FOR_BOUNDARY_REVIEW:
            if self.checkpoint_ref is None or self.validation_requirement_ref is None or self.regression_requirement_ref is None:
                raise ValueError("SelfHealingFlowEnvelope ready state requires checkpoint, validation and regression refs")
        if not self.schema_version:
            raise ValueError("SelfHealingFlowEnvelope.schema_version cannot be empty")
