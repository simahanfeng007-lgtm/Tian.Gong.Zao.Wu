"""Determinism hints for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class DeterminismKind(str, Enum):
    DETERMINISTIC = "deterministic"
    MOSTLY_DETERMINISTIC = "mostly_deterministic"
    NONDETERMINISTIC = "nondeterministic"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExecutionDeterminismHint:
    """Determinism hint only; it does not enforce runtime determinism."""

    determinism_hint_ref: TypedRef
    action_ref: TypedRef | None = None
    determinism_kind: DeterminismKind = DeterminismKind.UNKNOWN
    determinism_score_ref: TypedRef | None = None
    hint_summary: str = "determinism_hint_only"
    hint_only: bool = True
    enforces_determinism: bool = False
    grants_replay_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.hint_summary, "ExecutionDeterminismHint.hint_summary")
        ensure_true(self.hint_only, "ExecutionDeterminismHint.hint_only")
        ensure_false(self.enforces_determinism, "ExecutionDeterminismHint.enforces_determinism")
        ensure_false(self.grants_replay_permission, "ExecutionDeterminismHint.grants_replay_permission")
        ensure_schema_version(self.schema_version, "ExecutionDeterminismHint.schema_version")
