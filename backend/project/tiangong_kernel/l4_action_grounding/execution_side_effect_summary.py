"""Side-effect summaries for L4 phase 7."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionSideEffectSummary:
    """Side-effect summary only; it does not decide risk or permission."""

    side_effect_summary_ref: TypedRef
    action_ref: TypedRef | None = None
    side_effect_descriptor_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    summary_only: bool = True
    makes_risk_decision: bool = False
    grants_permission: bool = False
    performs_side_effect: bool = False
    writes_audit_store: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.summary_items:
            ensure_short_text(key, "ExecutionSideEffectSummary.summary_items key", 128)
            ensure_short_text(value, "ExecutionSideEffectSummary.summary_items value")
        ensure_true(self.summary_only, "ExecutionSideEffectSummary.summary_only")
        ensure_false(self.makes_risk_decision, "ExecutionSideEffectSummary.makes_risk_decision")
        ensure_false(self.grants_permission, "ExecutionSideEffectSummary.grants_permission")
        ensure_false(self.performs_side_effect, "ExecutionSideEffectSummary.performs_side_effect")
        ensure_false(self.writes_audit_store, "ExecutionSideEffectSummary.writes_audit_store")
        ensure_schema_version(self.schema_version, "ExecutionSideEffectSummary.schema_version")
