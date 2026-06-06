"""Replay summaries for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionReplaySummary:
    """Structural replay summary; it cannot execute replay or hold credentials."""

    replay_summary_ref: TypedRef
    action_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    input_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    failure_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    permit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    replay_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    executes_replay: bool = False
    guarantees_real_replay: bool = False
    contains_plain_credential: bool = False
    stores_sensitive_plaintext: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.replay_items:
            ensure_short_text(key, "ExecutionReplaySummary.replay_items key", 128)
            ensure_short_text(value, "ExecutionReplaySummary.replay_items value")
        ensure_true(self.summary_only, "ExecutionReplaySummary.summary_only")
        ensure_false(self.executes_replay, "ExecutionReplaySummary.executes_replay")
        ensure_false(self.guarantees_real_replay, "ExecutionReplaySummary.guarantees_real_replay")
        ensure_false(self.contains_plain_credential, "ExecutionReplaySummary.contains_plain_credential")
        ensure_false(self.stores_sensitive_plaintext, "ExecutionReplaySummary.stores_sensitive_plaintext")
        ensure_false(self.writes_l2_state, "ExecutionReplaySummary.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionReplaySummary.schema_version")
