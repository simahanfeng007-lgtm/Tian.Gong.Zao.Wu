"""Quality gate handoff objects for L4 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class L4QualityGateHandoffEnvelope:
    quality_gate_ref: TypedRef
    test_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    verification_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    assertion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evaluation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    regression_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    gate_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    report_only: bool = True
    approves_l5_l6_start: bool = False
    executes_test: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_pair_items(self.gate_items, "L4QualityGateHandoffEnvelope.gate_items")
        ensure_true(self.report_only, "L4QualityGateHandoffEnvelope.report_only")
        ensure_false(self.approves_l5_l6_start, "L4QualityGateHandoffEnvelope.approves_l5_l6_start")
        ensure_false(self.executes_test, "L4QualityGateHandoffEnvelope.executes_test")
        ensure_schema_version(self.schema_version, "L4QualityGateHandoffEnvelope.schema_version")
