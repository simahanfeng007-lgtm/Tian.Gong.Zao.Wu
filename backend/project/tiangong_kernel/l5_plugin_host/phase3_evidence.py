"""L5 phase 3 test and regression evidence data shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class L5Phase3TestEvidenceRecord:
    command: str
    purpose: str
    runtime_summary: str
    status: str
    evidence_ref: str
    output_summary: str = ""
    related_tests: tuple[str, ...] = field(default_factory=tuple)
    related_requirements: tuple[str, ...] = field(default_factory=tuple)
    real_execution_result: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.command, "L5Phase3TestEvidenceRecord.command")
        ensure_short_text(self.purpose, "L5Phase3TestEvidenceRecord.purpose")
        ensure_short_text(self.runtime_summary, "L5Phase3TestEvidenceRecord.runtime_summary")
        if self.status not in ("not_run", "passed", "failed", "skipped_with_reason"):
            raise ValueError("L5Phase3TestEvidenceRecord.status has unsupported value")
        ensure_ref_text(self.evidence_ref, "L5Phase3TestEvidenceRecord.evidence_ref")
        ensure_short_text(self.output_summary, "L5Phase3TestEvidenceRecord.output_summary")
        for item in self.related_tests:
            ensure_short_text(item, "L5Phase3TestEvidenceRecord.related_tests", 256)
        for item in self.related_requirements:
            ensure_short_text(item, "L5Phase3TestEvidenceRecord.related_requirements", 256)
        ensure_schema_version(self.schema_version, "L5Phase3TestEvidenceRecord.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase3TestEvidenceIndex:
    index_ref: str
    records: tuple[L5Phase3TestEvidenceRecord, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "L5Phase3TestEvidenceIndex.index_ref")
        for record in self.records:
            if not isinstance(record, L5Phase3TestEvidenceRecord):
                raise ValueError("L5Phase3TestEvidenceIndex.records must contain L5Phase3TestEvidenceRecord")
        ensure_ref_items(self.evidence_refs, "L5Phase3TestEvidenceIndex.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase3TestEvidenceIndex.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase3RegressionEvidenceIndex:
    index_ref: str
    l0_l4_regression_summary: str
    l5_phase1_modified_refs: tuple[str, ...] = field(default_factory=tuple)
    l5_phase2_modified_refs: tuple[str, ...] = field(default_factory=tuple)
    no_live_action_preserved: bool = True
    no_l6_implementation_preserved: bool = True
    no_legacy_runtime_preserved: bool = True
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "L5Phase3RegressionEvidenceIndex.index_ref")
        ensure_short_text(self.l0_l4_regression_summary, "L5Phase3RegressionEvidenceIndex.l0_l4_regression_summary")
        ensure_ref_items(self.l5_phase1_modified_refs, "L5Phase3RegressionEvidenceIndex.l5_phase1_modified_refs")
        ensure_ref_items(self.l5_phase2_modified_refs, "L5Phase3RegressionEvidenceIndex.l5_phase2_modified_refs")
        ensure_ref_items(self.evidence_refs, "L5Phase3RegressionEvidenceIndex.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase3RegressionEvidenceIndex.schema_version")
