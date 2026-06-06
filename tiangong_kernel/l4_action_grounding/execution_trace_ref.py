"""Trace references for L4 phase 6 returns."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionTraceRef:
    """Trace reference aligned to existing trace refs; no old chain is created."""

    trace_ref: TypedRef
    action_ref: TypedRef | None = None
    parent_trace_ref: TypedRef | None = None
    trace_hint: str = "l0_trace_ref"
    ref_only: bool = True
    creates_legacy_trace: bool = False
    writes_trace_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.trace_hint, "ExecutionTraceRef.trace_hint", 128)
        ensure_true(self.ref_only, "ExecutionTraceRef.ref_only")
        ensure_false(self.creates_legacy_trace, "ExecutionTraceRef.creates_legacy_trace")
        ensure_false(self.writes_trace_store, "ExecutionTraceRef.writes_trace_store")
        ensure_schema_version(self.schema_version, "ExecutionTraceRef.schema_version")
