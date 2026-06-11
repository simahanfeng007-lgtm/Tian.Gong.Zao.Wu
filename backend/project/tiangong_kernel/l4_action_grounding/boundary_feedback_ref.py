"""Boundary feedback references for future L5 checks."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class BoundaryFeedbackRef:
    """Feedback reference only; it decides no boundary permission."""

    boundary_feedback_ref: TypedRef
    action_ref: TypedRef
    permit_consumption_summary_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    confirmation_advice_ref: TypedRef | None = None
    feedback_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    ref_only: bool = True
    makes_boundary_decision: bool = False
    issues_permit: bool = False
    requires_confirmation_ticket: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.feedback_items:
            ensure_short_text(key, "BoundaryFeedbackRef.feedback_items key", 128)
            ensure_short_text(value, "BoundaryFeedbackRef.feedback_items value")
        ensure_true(self.ref_only, "BoundaryFeedbackRef.ref_only")
        ensure_false(self.makes_boundary_decision, "BoundaryFeedbackRef.makes_boundary_decision")
        ensure_false(self.issues_permit, "BoundaryFeedbackRef.issues_permit")
        ensure_false(self.requires_confirmation_ticket, "BoundaryFeedbackRef.requires_confirmation_ticket")
        ensure_schema_version(self.schema_version, "BoundaryFeedbackRef.schema_version")
