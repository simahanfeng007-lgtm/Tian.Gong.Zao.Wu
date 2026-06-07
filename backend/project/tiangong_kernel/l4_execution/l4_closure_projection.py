"""Closure projection for L4 phase 8."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ClosureProjection:
    """Closure projection for L3/L5/L6; it writes no state and starts no stage."""

    closure_projection_ref: TypedRef
    l3_handoff_ref: TypedRef | None = None
    l5_handoff_ref: TypedRef | None = None
    l6_handoff_ref: TypedRef | None = None
    projection_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    projection_only: bool = True
    writes_l2_state: bool = False
    mutates_l3_plan: bool = False
    starts_l5_or_l6: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.projection_items, "L4ClosureProjection.projection_items")
        ensure_true(self.projection_only, "L4ClosureProjection.projection_only")
        ensure_false(self.writes_l2_state, "L4ClosureProjection.writes_l2_state")
        ensure_false(self.mutates_l3_plan, "L4ClosureProjection.mutates_l3_plan")
        ensure_false(self.starts_l5_or_l6, "L4ClosureProjection.starts_l5_or_l6")
        ensure_schema_version(self.schema_version, "L4ClosureProjection.schema_version")
