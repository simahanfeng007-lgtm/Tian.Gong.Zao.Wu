"""L5 phase 2 manifest validation report data shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .phase2_common import SEVERITY_P0, SEVERITY_P1, SEVERITY_P2, SEVERITY_P3

_VALID_SEVERITIES = (SEVERITY_P0, SEVERITY_P1, SEVERITY_P2, SEVERITY_P3)


@dataclass(frozen=True, slots=True)
class PluginManifestValidationIssue:
    issue_code: str
    severity: str
    field_path: str
    message: str
    blocking: bool
    evidence_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.issue_code, "PluginManifestValidationIssue.issue_code")
        if self.severity not in _VALID_SEVERITIES:
            raise ValueError("PluginManifestValidationIssue.severity has unsupported value")
        ensure_short_text(self.field_path, "PluginManifestValidationIssue.field_path", 256)
        ensure_short_text(self.message, "PluginManifestValidationIssue.message")
        ensure_bool(self.blocking, "PluginManifestValidationIssue.blocking")
        if self.severity in (SEVERITY_P0, SEVERITY_P1) and not self.blocking:
            raise ValueError("P0/P1 validation issues must be blocking")
        ensure_ref_text(self.evidence_ref, "PluginManifestValidationIssue.evidence_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginManifestValidationIssue.schema_version")


@dataclass(frozen=True, slots=True)
class PluginManifestValidationReport:
    report_ref: str
    manifest_ref: str
    issues: tuple[PluginManifestValidationIssue, ...] = field(default_factory=tuple)
    observed_summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.report_ref, "PluginManifestValidationReport.report_ref")
        ensure_ref_text(self.manifest_ref, "PluginManifestValidationReport.manifest_ref")
        for issue in self.issues:
            if not isinstance(issue, PluginManifestValidationIssue):
                raise ValueError("PluginManifestValidationReport.issues must contain PluginManifestValidationIssue")
        ensure_short_text(self.observed_summary, "PluginManifestValidationReport.observed_summary")
        ensure_schema_version(self.schema_version, "PluginManifestValidationReport.schema_version")

    @property
    def passed(self) -> bool:
        return not any(issue.blocking for issue in self.issues)

    @property
    def p0_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == SEVERITY_P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == SEVERITY_P1)
