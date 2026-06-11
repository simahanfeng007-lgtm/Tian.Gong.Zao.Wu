"""L4 自愈交接引用对象。

L4 只承载失败、证据、审计、checkpoint、transaction、rollback、recovery、
validation 和 regression 引用，不执行恢复或回滚。
"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4SelfHealingHandoffRef:
    """L4 自愈交接引用。"""

    handoff_ref: TypedRef
    failure_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    checkpoint_ref: TypedRef | None = None
    transaction_ref: TypedRef | None = None
    rollback_intent_ref: TypedRef | None = None
    recovery_requirement_ref: TypedRef | None = None
    validation_requirement_ref: TypedRef | None = None
    regression_requirement_ref: TypedRef | None = None
    handoff_only: bool = True
    ref_only: bool = True
    executes_recovery: bool = False
    executes_rollback: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.handoff_only, "L4SelfHealingHandoffRef.handoff_only")
        ensure_true(self.ref_only, "L4SelfHealingHandoffRef.ref_only")
        ensure_false(self.executes_recovery, "L4SelfHealingHandoffRef.executes_recovery")
        ensure_false(self.executes_rollback, "L4SelfHealingHandoffRef.executes_rollback")
        ensure_false(self.writes_l2_state, "L4SelfHealingHandoffRef.writes_l2_state")
        ensure_false(self.writes_audit_store, "L4SelfHealingHandoffRef.writes_audit_store")
        ensure_schema_version(self.schema_version, "L4SelfHealingHandoffRef.schema_version")


@dataclass(frozen=True, slots=True)
class L4FailureRecoveryRequirementBundle:
    """L4 失败恢复需求引用包。"""

    bundle_ref: TypedRef
    handoff_ref: L4SelfHealingHandoffRef
    handoff_ready: bool = False
    bundle_only: bool = True
    executes_recovery: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.bundle_only, "L4FailureRecoveryRequirementBundle.bundle_only")
        ensure_false(self.executes_recovery, "L4FailureRecoveryRequirementBundle.executes_recovery")
        if self.handoff_ready:
            if (
                self.handoff_ref.checkpoint_ref is None
                or self.handoff_ref.validation_requirement_ref is None
                or self.handoff_ref.regression_requirement_ref is None
            ):
                raise ValueError("L4FailureRecoveryRequirementBundle ready state requires checkpoint, validation and regression refs")
        ensure_schema_version(self.schema_version, "L4FailureRecoveryRequirementBundle.schema_version")


@dataclass(frozen=True, slots=True)
class L4PostRecoveryValidationRequirement:
    """L4 恢复后验证需求。"""

    requirement_ref: TypedRef
    recovery_result_ref: TypedRef | None = None
    validation_requirement_ref: TypedRef | None = None
    regression_requirement_ref: TypedRef | None = None
    requirement_only: bool = True
    runs_validation: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requirement_only, "L4PostRecoveryValidationRequirement.requirement_only")
        ensure_false(self.runs_validation, "L4PostRecoveryValidationRequirement.runs_validation")
        ensure_false(self.writes_l2_state, "L4PostRecoveryValidationRequirement.writes_l2_state")
        ensure_schema_version(self.schema_version, "L4PostRecoveryValidationRequirement.schema_version")
