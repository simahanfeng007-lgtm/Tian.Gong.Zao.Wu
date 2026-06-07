"""L5 phase 1 readiness summary data shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items

_REQUIRED_RESPONSIBILITY_FIELDS = (
    "actor_ref",
    "scope_ref",
    "trace_ref",
    "policy_ref",
    "evidence_refs",
)


@dataclass(frozen=True, slots=True)
class PluginHostReadinessSummary:
    readiness_ref: str
    actor_ref: str
    scope_ref: str
    trace_ref: str
    policy_ref: str
    approval_ref: str = ""
    handoff_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    completed_checks: tuple[str, ...] = field(default_factory=tuple)
    missing_checks: tuple[str, ...] = field(default_factory=tuple)
    ready_for_next_phase: bool = False
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.readiness_ref, "PluginHostReadinessSummary.readiness_ref")
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHostReadinessSummary.{name}")
        for name in ("approval_ref", "handoff_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHostReadinessSummary.{name}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginHostReadinessSummary.evidence_refs", required=True)
        ensure_ref_items(self.provenance_refs, "PluginHostReadinessSummary.provenance_refs")
        ensure_text_items(self.completed_checks, "PluginHostReadinessSummary.completed_checks", limit=128)
        ensure_text_items(self.missing_checks, "PluginHostReadinessSummary.missing_checks", limit=128)
        if self.ready_for_next_phase and self.missing_checks:
            raise ValueError("PluginHostReadinessSummary cannot be ready with missing checks")
        ensure_short_text(self.summary, "PluginHostReadinessSummary.summary")
        ensure_schema_version(self.schema_version, "PluginHostReadinessSummary.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1Readiness:
    readiness_ref: str
    required_fields: tuple[str, ...] = field(default_factory=lambda: _REQUIRED_RESPONSIBILITY_FIELDS)
    observed_fields: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    complete: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.readiness_ref, "L5Phase1Readiness.readiness_ref")
        ensure_text_items(self.required_fields, "L5Phase1Readiness.required_fields", limit=128)
        ensure_text_items(self.observed_fields, "L5Phase1Readiness.observed_fields", limit=128)
        ensure_text_items(self.missing_fields, "L5Phase1Readiness.missing_fields", limit=128)
        ensure_ref_items(self.evidence_refs, "L5Phase1Readiness.evidence_refs")
        if self.complete and self.missing_fields:
            raise ValueError("L5Phase1Readiness cannot be complete with missing responsibility fields")
        ensure_schema_version(self.schema_version, "L5Phase1Readiness.schema_version")


def evaluate_phase1_responsibility_fields(readiness_ref: str, observed_fields: tuple[str, ...], evidence_refs: tuple[str, ...]) -> L5Phase1Readiness:
    missing = tuple(field for field in _REQUIRED_RESPONSIBILITY_FIELDS if field not in observed_fields)
    return L5Phase1Readiness(
        readiness_ref=readiness_ref,
        observed_fields=observed_fields,
        missing_fields=missing,
        evidence_refs=evidence_refs,
        complete=not missing and bool(evidence_refs),
    )
