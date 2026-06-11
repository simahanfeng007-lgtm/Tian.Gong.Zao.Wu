"""Unified action outcome envelope for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionOutcomeEnvelope:
    """Unified action outcome; it carries either a result ref or a failure ref."""

    outcome_ref: TypedRef
    action_ref: TypedRef
    result_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    outcome_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    envelope_only: bool = True
    triggers_next_step: bool = False
    writes_l2_state: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (self.result_ref is None) == (self.failure_ref is None):
            raise ValueError("ActionOutcomeEnvelope must carry exactly one result_ref or failure_ref")
        for key, value in self.outcome_items:
            ensure_short_text(key, "ActionOutcomeEnvelope.outcome_items key", 128)
            ensure_short_text(value, "ActionOutcomeEnvelope.outcome_items value")
        ensure_true(self.envelope_only, "ActionOutcomeEnvelope.envelope_only")
        ensure_false(self.triggers_next_step, "ActionOutcomeEnvelope.triggers_next_step")
        ensure_false(self.writes_l2_state, "ActionOutcomeEnvelope.writes_l2_state")
        ensure_false(self.writes_audit_store, "ActionOutcomeEnvelope.writes_audit_store")
        ensure_schema_version(self.schema_version, "ActionOutcomeEnvelope.schema_version")
