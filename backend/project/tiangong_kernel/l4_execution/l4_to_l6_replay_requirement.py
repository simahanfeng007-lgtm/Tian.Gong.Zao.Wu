"""L4 to L6 replay requirement for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL6ReplayRequirement:
    """Replay requirement only; it executes no replay."""

    replay_requirement_ref: TypedRef
    replay_summary_ref: TypedRef | None = None
    determinism_hint_ref: TypedRef | None = None
    idempotency_hint_ref: TypedRef | None = None
    replay_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    requirement_only: bool = True
    executes_replay: bool = False
    creates_snapshot: bool = False
    stores_sensitive_plaintext: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.replay_items, "L4ToL6ReplayRequirement.replay_items")
        ensure_true(self.requirement_only, "L4ToL6ReplayRequirement.requirement_only")
        ensure_false(self.executes_replay, "L4ToL6ReplayRequirement.executes_replay")
        ensure_false(self.creates_snapshot, "L4ToL6ReplayRequirement.creates_snapshot")
        ensure_false(self.stores_sensitive_plaintext, "L4ToL6ReplayRequirement.stores_sensitive_plaintext")
        ensure_schema_version(self.schema_version, "L4ToL6ReplayRequirement.schema_version")
