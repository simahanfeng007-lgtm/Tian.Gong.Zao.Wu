"""Successful action return envelope for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .execution_resource_usage import ExecutionResourceUsage
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionResultReturnEnvelope:
    """Standard result return; state update is only a suggestion ref."""

    outcome_ref: TypedRef
    action_ref: TypedRef
    result_ref: TypedRef
    observation_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    resource_usage: ExecutionResourceUsage | None = None
    trace_ref: TypedRef | None = None
    state_update_suggestion_ref: TypedRef | None = None
    source_handoff_ref: TypedRef | None = None
    conversation_ref: TypedRef | None = None
    parent_actor_ref: TypedRef | None = None
    parent_task_ref: TypedRef | None = None
    parent_run_ref: TypedRef | None = None
    result_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    envelope_only: bool = True
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    decides_next_step: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.result_items:
            ensure_short_text(key, "ActionResultReturnEnvelope.result_items key", 128)
            ensure_short_text(value, "ActionResultReturnEnvelope.result_items value")
        ensure_true(self.envelope_only, "ActionResultReturnEnvelope.envelope_only")
        ensure_false(self.writes_l2_state, "ActionResultReturnEnvelope.writes_l2_state")
        ensure_false(self.writes_audit_store, "ActionResultReturnEnvelope.writes_audit_store")
        ensure_false(self.decides_next_step, "ActionResultReturnEnvelope.decides_next_step")
        ensure_schema_version(self.schema_version, "ActionResultReturnEnvelope.schema_version")
