"""L3 replan suggestion references for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L3ReplanSuggestionRef:
    """Suggestion reference only; L4 never rewrites an L3 plan."""

    replan_suggestion_ref: TypedRef
    action_ref: TypedRef
    failure_ref: TypedRef | None = None
    reason_ref: TypedRef | None = None
    suggestion_summary: str = "l3_replan_suggestion_ref_only"
    ref_only: bool = True
    modifies_l3_plan: bool = False
    creates_plan: bool = False
    decides_next_step: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.suggestion_summary, "L3ReplanSuggestionRef.suggestion_summary")
        ensure_true(self.ref_only, "L3ReplanSuggestionRef.ref_only")
        ensure_false(self.modifies_l3_plan, "L3ReplanSuggestionRef.modifies_l3_plan")
        ensure_false(self.creates_plan, "L3ReplanSuggestionRef.creates_plan")
        ensure_false(self.decides_next_step, "L3ReplanSuggestionRef.decides_next_step")
        ensure_schema_version(self.schema_version, "L3ReplanSuggestionRef.schema_version")
