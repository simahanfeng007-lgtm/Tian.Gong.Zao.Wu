"""L5 phase 1 test and regression evidence data shells.

This module restores the public API exported by ``l5_plugin_host.__init__``.
It is deliberately data-only: no plugin loading, no tool execution, no lower
layer mutation, and no external I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import (
    L5_PLUGIN_HOST_SCHEMA_VERSION,
    ensure_digest,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    ensure_short_text,
)


@dataclass(frozen=True, slots=True)
class L5Phase1TestEvidenceRecord:
    """Single deterministic test evidence record for L5 phase 1 planning."""

    command: str
    purpose: str
    status: str
    evidence_ref: str
    output_summary: str = ""
    related_tests: tuple[str, ...] = field(default_factory=tuple)
    related_requirements: tuple[str, ...] = field(default_factory=tuple)
    real_execution_result: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.command, "L5Phase1TestEvidenceRecord.command")
        ensure_short_text(self.purpose, "L5Phase1TestEvidenceRecord.purpose")
        if self.status not in ("not_run", "passed", "failed", "skipped_with_reason"):
            raise ValueError("L5Phase1TestEvidenceRecord.status has unsupported value")
        ensure_ref_text(self.evidence_ref, "L5Phase1TestEvidenceRecord.evidence_ref")
        ensure_short_text(self.output_summary, "L5Phase1TestEvidenceRecord.output_summary")
        for item in self.related_tests:
            ensure_short_text(item, "L5Phase1TestEvidenceRecord.related_tests", 256)
        for item in self.related_requirements:
            ensure_short_text(item, "L5Phase1TestEvidenceRecord.related_requirements", 256)
        ensure_schema_version(self.schema_version, "L5Phase1TestEvidenceRecord.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1TestEvidenceIndex:
    """Stable index of phase 1 test evidence records."""

    index_ref: str
    records: tuple[L5Phase1TestEvidenceRecord, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "L5Phase1TestEvidenceIndex.index_ref")
        for record in self.records:
            if not isinstance(record, L5Phase1TestEvidenceRecord):
                raise ValueError("L5Phase1TestEvidenceIndex.records must contain L5Phase1TestEvidenceRecord")
        ensure_ref_items(self.evidence_refs, "L5Phase1TestEvidenceIndex.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase1TestEvidenceIndex.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1RegressionBaselineRecord:
    """Compact immutable baseline pointer for later L5 regression checks."""

    baseline_ref: str
    target_ref: str
    baseline_digest: str = ""
    status: str = "captured"
    summary: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.baseline_ref, "L5Phase1RegressionBaselineRecord.baseline_ref")
        ensure_ref_text(self.target_ref, "L5Phase1RegressionBaselineRecord.target_ref")
        ensure_digest(self.baseline_digest, "L5Phase1RegressionBaselineRecord.baseline_digest", required=False)
        if self.status not in ("captured", "not_captured", "superseded", "skipped_with_reason"):
            raise ValueError("L5Phase1RegressionBaselineRecord.status has unsupported value")
        ensure_short_text(self.summary, "L5Phase1RegressionBaselineRecord.summary")
        ensure_ref_items(self.evidence_refs, "L5Phase1RegressionBaselineRecord.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase1RegressionBaselineRecord.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1RegressionEvidenceIndex:
    """Phase 1 regression evidence index; declarative and side-effect free."""

    index_ref: str
    baselines: tuple[L5Phase1RegressionBaselineRecord, ...] = field(default_factory=tuple)
    l0_l4_regression_summary: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    no_live_action_preserved: bool = True
    no_l6_implementation_preserved: bool = True
    no_legacy_runtime_preserved: bool = True
    no_lower_layer_mutation_preserved: bool = True
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "L5Phase1RegressionEvidenceIndex.index_ref")
        for baseline in self.baselines:
            if not isinstance(baseline, L5Phase1RegressionBaselineRecord):
                raise ValueError("L5Phase1RegressionEvidenceIndex.baselines must contain L5Phase1RegressionBaselineRecord")
        ensure_short_text(self.l0_l4_regression_summary, "L5Phase1RegressionEvidenceIndex.l0_l4_regression_summary")
        ensure_ref_items(self.evidence_refs, "L5Phase1RegressionEvidenceIndex.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase1RegressionEvidenceIndex.schema_version")
