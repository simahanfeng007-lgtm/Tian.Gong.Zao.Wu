"""Idempotency hints for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class IdempotencyKind(str, Enum):
    IDEMPOTENT = "idempotent"
    CONDITIONALLY_IDEMPOTENT = "conditionally_idempotent"
    NON_IDEMPOTENT = "non_idempotent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExecutionIdempotencyHint:
    """Idempotency hint only; it does not authorize duplicate execution."""

    idempotency_hint_ref: TypedRef
    action_ref: TypedRef | None = None
    idempotency_kind: IdempotencyKind = IdempotencyKind.UNKNOWN
    idempotency_score_ref: TypedRef | None = None
    hint_summary: str = "idempotency_hint_only"
    hint_only: bool = True
    authorizes_repeat_execution: bool = False
    grants_replay_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.hint_summary, "ExecutionIdempotencyHint.hint_summary")
        ensure_true(self.hint_only, "ExecutionIdempotencyHint.hint_only")
        ensure_false(self.authorizes_repeat_execution, "ExecutionIdempotencyHint.authorizes_repeat_execution")
        ensure_false(self.grants_replay_permission, "ExecutionIdempotencyHint.grants_replay_permission")
        ensure_schema_version(self.schema_version, "ExecutionIdempotencyHint.schema_version")
