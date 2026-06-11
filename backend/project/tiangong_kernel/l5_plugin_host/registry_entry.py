"""L5 phase 1 immutable plugin registry entry shell."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, digest_without, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items


@dataclass(frozen=True, slots=True)
class PluginRegistryEntry:
    entry_ref: str
    plugin_id: str
    manifest_ref: str
    package_ref: str = ""
    registry_view_ref: str = ""
    registry_record_ref: str = ""
    manifest_hash: str = ""
    version_ref: str = ""
    compatibility_decl_ref: str = ""
    declared_mount_surfaces: tuple[str, ...] = field(default_factory=tuple)
    declared_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    declared_audit_refs: tuple[str, ...] = field(default_factory=tuple)
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
    registry_entry_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.entry_ref, "PluginRegistryEntry.entry_ref")
        ensure_ref_text(self.plugin_id, "PluginRegistryEntry.plugin_id")
        ensure_ref_text(self.manifest_ref, "PluginRegistryEntry.manifest_ref")
        ensure_ref_text(self.package_ref, "PluginRegistryEntry.package_ref", required=False)
        ensure_ref_text(self.registry_view_ref, "PluginRegistryEntry.registry_view_ref", required=False)
        ensure_ref_text(self.registry_record_ref, "PluginRegistryEntry.registry_record_ref", required=False)
        ensure_ref_text(self.manifest_hash, "PluginRegistryEntry.manifest_hash", required=False)
        ensure_ref_text(self.version_ref, "PluginRegistryEntry.version_ref", required=False)
        ensure_ref_text(self.compatibility_decl_ref, "PluginRegistryEntry.compatibility_decl_ref", required=False)
        ensure_text_items(self.declared_mount_surfaces, "PluginRegistryEntry.declared_mount_surfaces", limit=128)
        ensure_ref_items(self.declared_boundary_refs, "PluginRegistryEntry.declared_boundary_refs")
        ensure_ref_items(self.declared_audit_refs, "PluginRegistryEntry.declared_audit_refs")
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "handoff_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryEntry.{name}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginRegistryEntry.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginRegistryEntry.provenance_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryEntry.schema_version")
        if self.registry_entry_digest:
            ensure_ref_text(self.registry_entry_digest, "PluginRegistryEntry.registry_entry_digest")
        else:
            object.__setattr__(self, "registry_entry_digest", digest_without(self, ("registry_entry_digest",)))


@dataclass(frozen=True, slots=True)
class PluginRegistryDataOnlyResult:
    result_ref: str
    entry_ref: str
    accepted_as_view: bool
    reason: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.result_ref, "PluginRegistryDataOnlyResult.result_ref")
        ensure_ref_text(self.entry_ref, "PluginRegistryDataOnlyResult.entry_ref")
        if not isinstance(self.accepted_as_view, bool):
            raise ValueError("PluginRegistryDataOnlyResult.accepted_as_view must be boolean")
        ensure_short_text(self.reason, "PluginRegistryDataOnlyResult.reason")
        ensure_ref_items(self.evidence_refs, "PluginRegistryDataOnlyResult.evidence_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryDataOnlyResult.schema_version")
