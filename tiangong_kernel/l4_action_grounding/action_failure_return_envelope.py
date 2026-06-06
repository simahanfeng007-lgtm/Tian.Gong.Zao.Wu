"""Failed action return envelope for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .failure_category import FailureCategory
from .failure_recoverability_hint import FailureRecoverabilityHint
from .failure_severity import FailureSeverity
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionFailureReturnEnvelope:
    """Standard failure return; retry, resume, rollback, and replan remain refs."""

    failure_return_ref: TypedRef
    action_ref: TypedRef
    failure_ref: TypedRef
    failure_category: FailureCategory = FailureCategory.UNKNOWN
    failure_severity: FailureSeverity = FailureSeverity.WARNING
    recoverability_hint: FailureRecoverabilityHint = FailureRecoverabilityHint.UNKNOWN
    retry_advice_ref: TypedRef | None = None
    resume_ref: TypedRef | None = None
    rollback_hint_ref: TypedRef | None = None
    replan_suggestion_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    source_handoff_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    parent_actor_ref: TypedRef | None = None
    parent_task_ref: TypedRef | None = None
    parent_run_ref: TypedRef | None = None
    failure_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    envelope_only: bool = True
    automatic_retry: bool = False
    executes_recovery: bool = False
    executes_rollback: bool = False
    modifies_l3_plan: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    replaces_l5_risk_decision: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.failure_items:
            ensure_short_text(key, "ActionFailureReturnEnvelope.failure_items key", 128)
            ensure_short_text(value, "ActionFailureReturnEnvelope.failure_items value")
        ensure_true(self.envelope_only, "ActionFailureReturnEnvelope.envelope_only")
        ensure_false(self.automatic_retry, "ActionFailureReturnEnvelope.automatic_retry")
        ensure_false(self.executes_recovery, "ActionFailureReturnEnvelope.executes_recovery")
        ensure_false(self.executes_rollback, "ActionFailureReturnEnvelope.executes_rollback")
        ensure_false(self.modifies_l3_plan, "ActionFailureReturnEnvelope.modifies_l3_plan")
        ensure_false(self.writes_l2_state, "ActionFailureReturnEnvelope.writes_l2_state")
        ensure_false(self.writes_audit_store, "ActionFailureReturnEnvelope.writes_audit_store")
        ensure_false(self.replaces_l5_risk_decision, "ActionFailureReturnEnvelope.replaces_l5_risk_decision")
        ensure_schema_version(self.schema_version, "ActionFailureReturnEnvelope.schema_version")
