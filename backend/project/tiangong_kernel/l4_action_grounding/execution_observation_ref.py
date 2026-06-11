"""Observation references for L4 phase 6 returns."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionObservationRef:
    """Reference to a future observation; it samples nothing."""

    observation_ref: TypedRef
    action_ref: TypedRef | None = None
    summary_ref: TypedRef | None = None
    source_hint: str = "future_l6_observation"
    ref_only: bool = True
    samples_real_observation: bool = False
    reads_real_screen: bool = False
    reads_real_file: bool = False
    accesses_real_network: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.source_hint, "ExecutionObservationRef.source_hint", 128)
        ensure_true(self.ref_only, "ExecutionObservationRef.ref_only")
        ensure_false(self.samples_real_observation, "ExecutionObservationRef.samples_real_observation")
        ensure_false(self.reads_real_screen, "ExecutionObservationRef.reads_real_screen")
        ensure_false(self.reads_real_file, "ExecutionObservationRef.reads_real_file")
        ensure_false(self.accesses_real_network, "ExecutionObservationRef.accesses_real_network")
        ensure_schema_version(self.schema_version, "ExecutionObservationRef.schema_version")
