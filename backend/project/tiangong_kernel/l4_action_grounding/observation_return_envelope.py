"""Observation return envelope for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ObservationReturnEnvelope:
    """Observation return by ref only; it samples no observation source."""

    observation_return_ref: TypedRef
    action_ref: TypedRef
    observation_ref: TypedRef
    summary_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    l3_continue_hint: str = "llm_or_l3_decides"
    envelope_only: bool = True
    samples_real_observation: bool = False
    implements_observation_system: bool = False
    decides_next_step: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.l3_continue_hint, "ObservationReturnEnvelope.l3_continue_hint", 128)
        ensure_true(self.envelope_only, "ObservationReturnEnvelope.envelope_only")
        ensure_false(self.samples_real_observation, "ObservationReturnEnvelope.samples_real_observation")
        ensure_false(self.implements_observation_system, "ObservationReturnEnvelope.implements_observation_system")
        ensure_false(self.decides_next_step, "ObservationReturnEnvelope.decides_next_step")
        ensure_false(self.writes_l2_state, "ObservationReturnEnvelope.writes_l2_state")
        ensure_schema_version(self.schema_version, "ObservationReturnEnvelope.schema_version")
