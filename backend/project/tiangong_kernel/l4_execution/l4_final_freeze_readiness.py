"""Final freeze readiness report for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, L4_PHASES, ensure_false, ensure_pair_items, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4FinalFreezeReadinessReport:
    """Freeze readiness report; it does not start quality or L5/L6 work."""

    readiness_report_ref: TypedRef
    completed_phases: tuple[str, ...] = field(default_factory=lambda: L4_PHASES)
    test_result_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    risk_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    report_only: bool = True
    recommends_l4_quality_audit: bool = True
    recommends_direct_l5_or_l6_development: bool = False
    skips_l4_quality_audit: bool = False
    enables_live_action: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.completed_phases, "L4FinalFreezeReadinessReport.completed_phases", 128)
        ensure_pair_items(self.test_result_items, "L4FinalFreezeReadinessReport.test_result_items")
        ensure_pair_items(self.risk_items, "L4FinalFreezeReadinessReport.risk_items")
        ensure_true(self.report_only, "L4FinalFreezeReadinessReport.report_only")
        ensure_true(self.recommends_l4_quality_audit, "L4FinalFreezeReadinessReport.recommends_l4_quality_audit")
        ensure_false(self.recommends_direct_l5_or_l6_development, "L4FinalFreezeReadinessReport.recommends_direct_l5_or_l6_development")
        ensure_false(self.skips_l4_quality_audit, "L4FinalFreezeReadinessReport.skips_l4_quality_audit")
        ensure_false(self.enables_live_action, "L4FinalFreezeReadinessReport.enables_live_action")
        ensure_schema_version(self.schema_version, "L4FinalFreezeReadinessReport.schema_version")
