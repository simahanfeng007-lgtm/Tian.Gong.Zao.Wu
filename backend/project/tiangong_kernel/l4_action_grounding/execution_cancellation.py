"""Cancellation structures for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class ExecutionCancellationStatus(str, Enum):
    CANCELLED = "cancelled"
    NOT_STARTED = "not_started"
    ALREADY_FINISHED = "already_finished"
    NOT_SUPPORTED = "not_supported"
    REQUIRES_L5 = "requires_l5"
    ADAPTER_DISABLED = "adapter_disabled"


@dataclass(frozen=True, slots=True)
class ExecutionCancellationRequest:
    """Cancellation intent only; it kills no process and stops no live action."""

    cancellation_ref: TypedRef
    action_ref: TypedRef
    reason_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    permit_ref: TypedRef | None = None
    request_only: bool = True
    kills_process: bool = False
    terminates_live_action: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.request_only, "ExecutionCancellationRequest.request_only")
        ensure_false(self.kills_process, "ExecutionCancellationRequest.kills_process")
        ensure_false(self.terminates_live_action, "ExecutionCancellationRequest.terminates_live_action")
        ensure_false(self.writes_l2_state, "ExecutionCancellationRequest.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionCancellationRequest.schema_version")


@dataclass(frozen=True, slots=True)
class ExecutionCancellationResult:
    """Cancellation result only; it does not progress recovery."""

    cancellation_result_ref: TypedRef
    cancellation_ref: TypedRef
    action_ref: TypedRef
    status: ExecutionCancellationStatus = ExecutionCancellationStatus.REQUIRES_L5
    summary: str = "cancellation is structural only"
    recovery_requirement_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    result_only: bool = True
    progresses_recovery: bool = False
    kills_process: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.summary, "ExecutionCancellationResult.summary")
        ensure_true(self.result_only, "ExecutionCancellationResult.result_only")
        ensure_false(self.progresses_recovery, "ExecutionCancellationResult.progresses_recovery")
        ensure_false(self.kills_process, "ExecutionCancellationResult.kills_process")
        ensure_false(self.writes_l2_state, "ExecutionCancellationResult.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionCancellationResult.schema_version")
