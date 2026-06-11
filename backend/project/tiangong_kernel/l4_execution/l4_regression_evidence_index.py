"""Regression evidence index for L4 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4RegressionEvidenceIndex:
    baseline_ref: TypedRef
    current_ref: TypedRef
    regression_log_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    hash_compare_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    changed_surface_summary: str = ""
    regression_passed_ref: TypedRef | None = None
    regression_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    index_only: bool = True
    detects_regression: bool = False
    modifies_baseline: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.changed_surface_summary, "L4RegressionEvidenceIndex.changed_surface_summary")
        ensure_pair_items(self.regression_items, "L4RegressionEvidenceIndex.regression_items")
        ensure_true(self.index_only, "L4RegressionEvidenceIndex.index_only")
        ensure_false(self.detects_regression, "L4RegressionEvidenceIndex.detects_regression")
        ensure_false(self.modifies_baseline, "L4RegressionEvidenceIndex.modifies_baseline")
        ensure_schema_version(self.schema_version, "L4RegressionEvidenceIndex.schema_version")
