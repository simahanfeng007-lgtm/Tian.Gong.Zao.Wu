"""Projection helpers for L4 phase 6 return envelopes."""

from __future__ import annotations

from dataclasses import dataclass

from .action_failure_return_envelope import ActionFailureReturnEnvelope
from .action_outcome_envelope import ActionOutcomeEnvelope
from .action_result_return_envelope import ActionResultReturnEnvelope
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionReturnProjection:
    """Projection only; it does not decide the next step or write state."""

    projection_only: bool = True
    decides_next_step: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.projection_only, "ExecutionReturnProjection.projection_only")
        ensure_false(self.decides_next_step, "ExecutionReturnProjection.decides_next_step")
        ensure_false(self.writes_l2_state, "ExecutionReturnProjection.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionReturnProjection.schema_version")

    def from_result(self, value: ActionResultReturnEnvelope) -> ActionOutcomeEnvelope:
        return ActionOutcomeEnvelope(
            outcome_ref=value.outcome_ref,
            action_ref=value.action_ref,
            result_ref=value.result_ref,
            observation_ref=value.observation_ref,
            evidence_ref=value.evidence_ref,
            audit_requirement_ref=value.audit_requirement_ref,
            trace_ref=value.trace_ref,
        )

    def from_failure(self, value: ActionFailureReturnEnvelope) -> ActionOutcomeEnvelope:
        return ActionOutcomeEnvelope(
            outcome_ref=value.failure_return_ref,
            action_ref=value.action_ref,
            failure_ref=value.failure_ref,
            audit_requirement_ref=value.audit_requirement_ref,
            trace_ref=value.trace_ref,
        )
