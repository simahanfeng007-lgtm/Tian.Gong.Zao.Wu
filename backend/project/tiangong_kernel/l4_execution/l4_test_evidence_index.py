"""Machine-readable test evidence index for L4 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, ensure_false, ensure_pair_items, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L4TestEvidenceIndex:
    index_ref: TypedRef
    test_log_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    compile_log_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    static_scan_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    zip_integrity_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    full_test_summary: str = ""
    targeted_test_summary: str = ""
    regression_test_summary: str = ""
    evidence_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    index_only: bool = True
    machine_readable: bool = field(default=True)
    executes_test: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for value in (self.full_test_summary, self.targeted_test_summary, self.regression_test_summary):
            ensure_short_text(value, "L4TestEvidenceIndex summary")
        ensure_pair_items(self.evidence_items, "L4TestEvidenceIndex.evidence_items")
        ensure_true(self.index_only, "L4TestEvidenceIndex.index_only")
        ensure_true(self.machine_readable, "L4TestEvidenceIndex.machine_readable")
        ensure_false(self.executes_test, "L4TestEvidenceIndex.executes_test")
        ensure_schema_version(self.schema_version, "L4TestEvidenceIndex.schema_version")
