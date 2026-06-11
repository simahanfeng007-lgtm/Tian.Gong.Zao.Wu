"""L6 quality gate declarations.

Quality gates are deterministic decisions over already-provided counts and refs.
They do not freeze plugins by themselves and do not grant external action.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class L6QualityGateDecision:
    gate_ref: str = "quality:l6_quality_gate"
    plugin_ref: str = "l6:plugin_ref"
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    blocking_reason_refs: tuple[str, ...] = field(default_factory=tuple)
    warning_reason_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    full_pytest_required: bool = True
    targeted_tests_required: bool = True
    forbidden_scan_required: bool = True
    hash_compare_required: bool = True
    is_execution_authorization: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.gate_ref, "L6QualityGateDecision.gate_ref")
        ensure_ref_text(self.plugin_ref, "L6QualityGateDecision.plugin_ref")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"L6QualityGateDecision.{name} must be a non-negative integer")
        ensure_ref_items(self.blocking_reason_refs, "L6QualityGateDecision.blocking_reason_refs")
        ensure_ref_items(self.warning_reason_refs, "L6QualityGateDecision.warning_reason_refs")
        ensure_ref_items(self.evidence_refs, "L6QualityGateDecision.evidence_refs")
        if self.is_execution_authorization:
            raise ValueError("L6 quality gate decision is not execution authorization")
        ensure_schema_version(self.schema_version)

    @property
    def allow_freeze_plugin(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0 and not self.blocking_reason_refs

    @property
    def allow_register_with_l5_host(self) -> bool:
        return self.allow_freeze_plugin

    @property
    def requires_repair_before_freeze(self) -> bool:
        return not self.allow_freeze_plugin

    @property
    def severity_summary(self) -> str:
        return f"p0={self.p0_count};p1={self.p1_count};p2={self.p2_count};p3={self.p3_count}"
