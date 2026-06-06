"""L4 to L5 quality gate summary."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5QualityGateSummary:
    handoff_ref: TypedRef
    quality_gate_ref: TypedRef
    quality_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    required_before_permit_activation: bool = field(default=True)
    requires_test_evidence: bool = field(default=True)
    requires_regression_evidence: bool = field(default=True)
    l5_must_recheck: bool = field(default=True)
    l4_approves_permit: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.quality_items, "L4ToL5QualityGateSummary.quality_items")
        ensure_true(self.required_before_permit_activation, "L4ToL5QualityGateSummary.required_before_permit_activation")
        ensure_true(self.requires_test_evidence, "L4ToL5QualityGateSummary.requires_test_evidence")
        ensure_true(self.requires_regression_evidence, "L4ToL5QualityGateSummary.requires_regression_evidence")
        ensure_true(self.l5_must_recheck, "L4ToL5QualityGateSummary.l5_must_recheck")
        ensure_false(self.l4_approves_permit, "L4ToL5QualityGateSummary.l4_approves_permit")
        ensure_schema_version(self.schema_version, "L4ToL5QualityGateSummary.schema_version")
