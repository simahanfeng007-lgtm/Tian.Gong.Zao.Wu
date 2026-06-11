"""Final quality checklist for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


DEFAULT_QUALITY_ITEMS = (
    ("P0", "no real external action or boundary bypass"),
    ("P1", "no L5/L6 implementation or legacy main chain"),
    ("P2", "public exports and object families are coherent"),
    ("P3", "reports and handoff documents are complete"),
)


@dataclass(frozen=True, slots=True)
class L4FinalQualityChecklist:
    """Quality checklist only; it does not run or repair quality gates."""

    quality_checklist_ref: TypedRef
    checklist_items: tuple[tuple[str, str], ...] = field(default_factory=lambda: DEFAULT_QUALITY_ITEMS)
    checklist_only: bool = True
    executes_quality_audit: bool = False
    executes_repair_flow: bool = False
    approves_l5_or_l6_start: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.checklist_items, "L4FinalQualityChecklist.checklist_items")
        ensure_true(self.checklist_only, "L4FinalQualityChecklist.checklist_only")
        ensure_false(self.executes_quality_audit, "L4FinalQualityChecklist.executes_quality_audit")
        ensure_false(self.executes_repair_flow, "L4FinalQualityChecklist.executes_repair_flow")
        ensure_false(self.approves_l5_or_l6_start, "L4FinalQualityChecklist.approves_l5_or_l6_start")
        ensure_schema_version(self.schema_version, "L4FinalQualityChecklist.schema_version")
