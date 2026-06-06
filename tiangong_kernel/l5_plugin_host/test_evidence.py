"""L5 phase 1 test and regression evidence shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items

_TEST_STATUSES = ("not_run", "passed", "failed", "skipped_with_reason")
_REGRESSION_STATUSES = ("not_run", "clean", "changed_with_explanation", "regressed")


@dataclass(frozen=True, slots=True)
class L5Phase1TestEvidenceRecord:
    record_ref: str
    command: str
    scope: str
    expected_purpose: str
    observed_summary: str
    return_code: int
    status: str
    report_ref: str
    evidence_ref: str
    notes: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.record_ref, "L5Phase1TestEvidenceRecord.record_ref")
        ensure_short_text(self.command, "L5Phase1TestEvidenceRecord.command")
        ensure_short_text(self.scope, "L5Phase1TestEvidenceRecord.scope", 128)
        ensure_short_text(self.expected_purpose, "L5Phase1TestEvidenceRecord.expected_purpose")
        ensure_short_text(self.observed_summary, "L5Phase1TestEvidenceRecord.observed_summary")
        if not isinstance(self.return_code, int):
            raise ValueError("L5Phase1TestEvidenceRecord.return_code must be int")
        if self.status not in _TEST_STATUSES:
            raise ValueError("L5Phase1TestEvidenceRecord.status is unsupported")
        if self.status == "passed" and (not self.command or self.return_code != 0 or not self.observed_summary):
            raise ValueError("passed evidence requires command, zero return_code, and observed_summary")
        ensure_ref_text(self.report_ref, "L5Phase1TestEvidenceRecord.report_ref")
        ensure_ref_text(self.evidence_ref, "L5Phase1TestEvidenceRecord.evidence_ref")
        ensure_short_text(self.notes, "L5Phase1TestEvidenceRecord.notes")
        ensure_schema_version(self.schema_version, "L5Phase1TestEvidenceRecord.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1TestEvidenceIndex:
    index_ref: str
    records: tuple[L5Phase1TestEvidenceRecord, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "L5Phase1TestEvidenceIndex.index_ref")
        for item in self.records:
            if not isinstance(item, L5Phase1TestEvidenceRecord):
                raise ValueError("records must contain L5Phase1TestEvidenceRecord")
        ensure_schema_version(self.schema_version, "L5Phase1TestEvidenceIndex.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1RegressionBaselineRecord:
    baseline_ref: str
    pre_l5_baseline_summary: str
    post_l5_full_test_summary: str
    delta_explanation: str
    changed_test_files: tuple[str, ...] = field(default_factory=tuple)
    deleted_test_files: tuple[str, ...] = field(default_factory=tuple)
    skipped_or_xfailed_tests: tuple[str, ...] = field(default_factory=tuple)
    warning_summary: str = ""
    regression_status: str = "not_run"
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.baseline_ref, "L5Phase1RegressionBaselineRecord.baseline_ref")
        ensure_short_text(self.pre_l5_baseline_summary, "L5Phase1RegressionBaselineRecord.pre_l5_baseline_summary")
        ensure_short_text(self.post_l5_full_test_summary, "L5Phase1RegressionBaselineRecord.post_l5_full_test_summary")
        ensure_short_text(self.delta_explanation, "L5Phase1RegressionBaselineRecord.delta_explanation")
        ensure_text_items(self.changed_test_files, "L5Phase1RegressionBaselineRecord.changed_test_files", limit=256)
        ensure_text_items(self.deleted_test_files, "L5Phase1RegressionBaselineRecord.deleted_test_files", limit=256)
        ensure_text_items(self.skipped_or_xfailed_tests, "L5Phase1RegressionBaselineRecord.skipped_or_xfailed_tests", limit=256)
        ensure_short_text(self.warning_summary, "L5Phase1RegressionBaselineRecord.warning_summary")
        if self.regression_status not in _REGRESSION_STATUSES:
            raise ValueError("L5Phase1RegressionBaselineRecord.regression_status is unsupported")
        ensure_schema_version(self.schema_version, "L5Phase1RegressionBaselineRecord.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1RegressionEvidenceIndex:
    index_ref: str
    records: tuple[L5Phase1RegressionBaselineRecord, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "L5Phase1RegressionEvidenceIndex.index_ref")
        for item in self.records:
            if not isinstance(item, L5Phase1RegressionBaselineRecord):
                raise ValueError("records must contain L5Phase1RegressionBaselineRecord")
        ensure_ref_items(self.evidence_refs, "L5Phase1RegressionEvidenceIndex.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase1RegressionEvidenceIndex.schema_version")
