"""L4 to L5 boundary feedback for phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5BoundaryFeedback:
    """Boundary feedback only; it makes no boundary decision."""

    feedback_ref: TypedRef
    boundary_feedback_ref: TypedRef | None = None
    permit_ref: TypedRef | None = None
    failure_ref: TypedRef | None = None
    feedback_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    feedback_only: bool = True
    makes_boundary_decision: bool = False
    makes_risk_decision: bool = False
    generates_confirmation_ticket: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.feedback_items, "L4ToL5BoundaryFeedback.feedback_items")
        ensure_true(self.feedback_only, "L4ToL5BoundaryFeedback.feedback_only")
        ensure_false(self.makes_boundary_decision, "L4ToL5BoundaryFeedback.makes_boundary_decision")
        ensure_false(self.makes_risk_decision, "L4ToL5BoundaryFeedback.makes_risk_decision")
        ensure_false(self.generates_confirmation_ticket, "L4ToL5BoundaryFeedback.generates_confirmation_ticket")
        ensure_schema_version(self.schema_version, "L4ToL5BoundaryFeedback.schema_version")
