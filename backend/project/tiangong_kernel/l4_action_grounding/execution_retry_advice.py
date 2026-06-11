"""Retry advice references for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionRetryAdviceRef:
    """Retry advice reference only; it does not call an adapter again."""

    retry_advice_ref: TypedRef
    action_ref: TypedRef
    failure_ref: TypedRef | None = None
    retry_cost_score_ref: TypedRef | None = None
    advice_hint: str = "retry_advice_ref_only"
    ref_only: bool = True
    automatic_retry: bool = False
    invokes_adapter: bool = False
    elevates_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.advice_hint, "ExecutionRetryAdviceRef.advice_hint")
        ensure_true(self.ref_only, "ExecutionRetryAdviceRef.ref_only")
        ensure_false(self.automatic_retry, "ExecutionRetryAdviceRef.automatic_retry")
        ensure_false(self.invokes_adapter, "ExecutionRetryAdviceRef.invokes_adapter")
        ensure_false(self.elevates_permission, "ExecutionRetryAdviceRef.elevates_permission")
        ensure_schema_version(self.schema_version, "ExecutionRetryAdviceRef.schema_version")
