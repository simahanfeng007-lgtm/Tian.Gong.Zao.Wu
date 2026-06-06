"""L5 phase 1 handoff evidence index shells.

The index accepts caller-provided compact metadata only. It does not open,
read, parse, or scan handoff files by path hints.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, digest_without, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class PluginHandoffEvidenceRecord:
    ref: str
    title: str = ""
    summary: str = ""
    digest: str = ""
    path_hint: str = ""
    source_layer: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.ref, "PluginHandoffEvidenceRecord.ref")
        ensure_short_text(self.title, "PluginHandoffEvidenceRecord.title", 128)
        ensure_short_text(self.summary, "PluginHandoffEvidenceRecord.summary")
        ensure_ref_text(self.digest, "PluginHandoffEvidenceRecord.digest", required=False)
        ensure_short_text(self.path_hint, "PluginHandoffEvidenceRecord.path_hint")
        ensure_ref_text(self.source_layer, "PluginHandoffEvidenceRecord.source_layer", required=False)
        ensure_schema_version(self.schema_version, "PluginHandoffEvidenceRecord.schema_version")


@dataclass(frozen=True, slots=True)
class PluginHandoffEvidenceIndex:
    index_ref: str
    records: tuple[PluginHandoffEvidenceRecord, ...] = field(default_factory=tuple)
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    handoff_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    handoff_index_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "PluginHandoffEvidenceIndex.index_ref")
        for item in self.records:
            if not isinstance(item, PluginHandoffEvidenceRecord):
                raise ValueError("PluginHandoffEvidenceIndex.records must contain PluginHandoffEvidenceRecord")
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "handoff_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHandoffEvidenceIndex.{name}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginHandoffEvidenceIndex.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginHandoffEvidenceIndex.provenance_refs")
        ensure_schema_version(self.schema_version, "PluginHandoffEvidenceIndex.schema_version")
        if self.handoff_index_digest:
            ensure_ref_text(self.handoff_index_digest, "PluginHandoffEvidenceIndex.handoff_index_digest")
        else:
            object.__setattr__(self, "handoff_index_digest", digest_without(self, ("handoff_index_digest",)))
