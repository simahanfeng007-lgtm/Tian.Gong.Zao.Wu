"""L5 phase 3 registry revision declaration."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .registry_serialization import registry_canonical_digest


@dataclass(frozen=True, slots=True)
class PluginRegistryRevision:
    revision_id: str
    parent_revision_id: str = ""
    created_at_ref: str = ""
    reason_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    revision_digest: str = ""
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.revision_id, "PluginRegistryRevision.revision_id")
        for name in ("parent_revision_id", "created_at_ref", "reason_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryRevision.{name}", required=False)
        ensure_ref_items(self.provenance_refs, "PluginRegistryRevision.provenance_refs")
        ensure_ref_items(self.evidence_refs, "PluginRegistryRevision.evidence_refs")
        ensure_short_text(self.summary, "PluginRegistryRevision.summary")
        ensure_schema_version(self.schema_version, "PluginRegistryRevision.schema_version")
        if self.revision_digest:
            ensure_ref_text(self.revision_digest, "PluginRegistryRevision.revision_digest")
        else:
            object.__setattr__(self, "revision_digest", registry_canonical_digest(self))
