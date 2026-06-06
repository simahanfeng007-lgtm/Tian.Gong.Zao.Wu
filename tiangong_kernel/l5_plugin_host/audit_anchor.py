"""Audit and responsibility-chain reference shells for L5 phase 1."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_digest, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class PluginHostEvidenceRef:
    ref: str
    summary: str = ""
    digest: str = ""
    source_layer: str = ""
    created_by_ref: str = ""
    trace_ref: str = ""
    scope_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.ref, "PluginHostEvidenceRef.ref")
        ensure_short_text(self.summary, "PluginHostEvidenceRef.summary")
        ensure_digest(self.digest, "PluginHostEvidenceRef.digest")
        ensure_ref_text(self.source_layer, "PluginHostEvidenceRef.source_layer", required=False)
        ensure_ref_text(self.created_by_ref, "PluginHostEvidenceRef.created_by_ref", required=False)
        ensure_ref_text(self.trace_ref, "PluginHostEvidenceRef.trace_ref", required=False)
        ensure_ref_text(self.scope_ref, "PluginHostEvidenceRef.scope_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginHostEvidenceRef.schema_version")


@dataclass(frozen=True, slots=True)
class PluginHostProvenanceRef:
    ref: str
    summary: str = ""
    digest: str = ""
    source_layer: str = ""
    created_by_ref: str = ""
    trace_ref: str = ""
    scope_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.ref, "PluginHostProvenanceRef.ref")
        ensure_short_text(self.summary, "PluginHostProvenanceRef.summary")
        ensure_digest(self.digest, "PluginHostProvenanceRef.digest")
        ensure_ref_text(self.source_layer, "PluginHostProvenanceRef.source_layer", required=False)
        ensure_ref_text(self.created_by_ref, "PluginHostProvenanceRef.created_by_ref", required=False)
        ensure_ref_text(self.trace_ref, "PluginHostProvenanceRef.trace_ref", required=False)
        ensure_ref_text(self.scope_ref, "PluginHostProvenanceRef.scope_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginHostProvenanceRef.schema_version")


@dataclass(frozen=True, slots=True)
class PluginHostAccountabilityRef:
    ref: str
    summary: str = ""
    digest: str = ""
    source_layer: str = ""
    created_by_ref: str = ""
    trace_ref: str = ""
    scope_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.ref, "PluginHostAccountabilityRef.ref")
        ensure_short_text(self.summary, "PluginHostAccountabilityRef.summary")
        ensure_digest(self.digest, "PluginHostAccountabilityRef.digest")
        ensure_ref_text(self.source_layer, "PluginHostAccountabilityRef.source_layer", required=False)
        ensure_ref_text(self.created_by_ref, "PluginHostAccountabilityRef.created_by_ref", required=False)
        ensure_ref_text(self.trace_ref, "PluginHostAccountabilityRef.trace_ref", required=False)
        ensure_ref_text(self.scope_ref, "PluginHostAccountabilityRef.scope_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginHostAccountabilityRef.schema_version")


@dataclass(frozen=True, slots=True)
class PluginHostTamperEvidenceRef:
    ref: str
    summary: str = ""
    digest: str = ""
    source_layer: str = ""
    created_by_ref: str = ""
    trace_ref: str = ""
    scope_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.ref, "PluginHostTamperEvidenceRef.ref")
        ensure_short_text(self.summary, "PluginHostTamperEvidenceRef.summary")
        ensure_digest(self.digest, "PluginHostTamperEvidenceRef.digest")
        ensure_ref_text(self.source_layer, "PluginHostTamperEvidenceRef.source_layer", required=False)
        ensure_ref_text(self.created_by_ref, "PluginHostTamperEvidenceRef.created_by_ref", required=False)
        ensure_ref_text(self.trace_ref, "PluginHostTamperEvidenceRef.trace_ref", required=False)
        ensure_ref_text(self.scope_ref, "PluginHostTamperEvidenceRef.scope_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginHostTamperEvidenceRef.schema_version")


@dataclass(frozen=True, slots=True)
class PluginHostAuditAnchor:
    anchor_ref: str
    summary: str = ""
    digest: str = ""
    source_layer: str = "L5.phase1"
    created_by_ref: str = ""
    trace_ref: str = ""
    scope_ref: str = ""
    evidence_ref: str = ""
    provenance_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.anchor_ref, "PluginHostAuditAnchor.anchor_ref")
        ensure_short_text(self.summary, "PluginHostAuditAnchor.summary")
        ensure_digest(self.digest, "PluginHostAuditAnchor.digest")
        ensure_ref_text(self.source_layer, "PluginHostAuditAnchor.source_layer")
        ensure_ref_text(self.created_by_ref, "PluginHostAuditAnchor.created_by_ref", required=False)
        ensure_ref_text(self.trace_ref, "PluginHostAuditAnchor.trace_ref", required=False)
        ensure_ref_text(self.scope_ref, "PluginHostAuditAnchor.scope_ref", required=False)
        ensure_ref_text(self.evidence_ref, "PluginHostAuditAnchor.evidence_ref", required=False)
        ensure_ref_text(self.provenance_ref, "PluginHostAuditAnchor.provenance_ref", required=False)
        ensure_ref_text(self.accountability_ref, "PluginHostAuditAnchor.accountability_ref", required=False)
        ensure_ref_text(self.tamper_evidence_ref, "PluginHostAuditAnchor.tamper_evidence_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginHostAuditAnchor.schema_version")
