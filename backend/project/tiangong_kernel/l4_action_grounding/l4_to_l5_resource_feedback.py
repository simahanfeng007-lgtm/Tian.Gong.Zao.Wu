"""L4 to L5 resource feedback references for phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5ResourceFeedback:
    """Feedback only; it does not allocate, expand, or authorize resources."""

    feedback_ref: TypedRef
    resource_budget_ref: TypedRef | None = None
    consumption_summary_ref: TypedRef | None = None
    future_l5_resource_recheck_required: bool = True
    future_l5_concurrency_recheck_required: bool = True
    feedback_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    ref_only: bool = True
    allocates_resource: bool = False
    authorizes_concurrency: bool = False
    issues_permit: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.feedback_items:
            ensure_short_text(key, "L4ToL5ResourceFeedback.feedback_items key", 128)
            ensure_short_text(value, "L4ToL5ResourceFeedback.feedback_items value")
        ensure_true(self.future_l5_resource_recheck_required, "L4ToL5ResourceFeedback.future_l5_resource_recheck_required")
        ensure_true(self.future_l5_concurrency_recheck_required, "L4ToL5ResourceFeedback.future_l5_concurrency_recheck_required")
        ensure_true(self.ref_only, "L4ToL5ResourceFeedback.ref_only")
        ensure_false(self.allocates_resource, "L4ToL5ResourceFeedback.allocates_resource")
        ensure_false(self.authorizes_concurrency, "L4ToL5ResourceFeedback.authorizes_concurrency")
        ensure_false(self.issues_permit, "L4ToL5ResourceFeedback.issues_permit")
        ensure_schema_version(self.schema_version, "L4ToL5ResourceFeedback.schema_version")
