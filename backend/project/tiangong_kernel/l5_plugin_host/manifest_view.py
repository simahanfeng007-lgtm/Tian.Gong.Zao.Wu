"""L5 phase 1 PluginManifestView.

The view is a whitelist-based declaration shell. It stores compact refs and
summaries only; it never resolves entry refs, checks dependency targets, reads
plugin directories, or accepts callable/module/class objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields

from ._common import (
    L5_PLUGIN_HOST_SCHEMA_VERSION,
    digest_without,
    ensure_allowed_manifest_field_names,
    ensure_entry_ref,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    ensure_short_text,
    ensure_text_items,
)


@dataclass(frozen=True, slots=True)
class PluginManifestView:
    plugin_id: str
    name: str
    version: str
    kind: str
    declared_entry_ref: str
    declared_permissions: tuple[str, ...] = field(default_factory=tuple)
    declared_dependencies: tuple[str, ...] = field(default_factory=tuple)
    declared_lifecycle: tuple[str, ...] = field(default_factory=tuple)
    declared_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    declared_audit_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
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
    validation_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    verification_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    evaluation_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    rollback_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    health_requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    manifest_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_allowed_manifest_field_names(tuple(field.name for field in fields(self)))
        ensure_ref_text(self.plugin_id, "PluginManifestView.plugin_id")
        ensure_short_text(self.name, "PluginManifestView.name", 128)
        ensure_short_text(self.version, "PluginManifestView.version", 64)
        ensure_short_text(self.kind, "PluginManifestView.kind", 64)
        ensure_entry_ref(self.declared_entry_ref, "PluginManifestView.declared_entry_ref")
        ensure_text_items(self.declared_permissions, "PluginManifestView.declared_permissions", limit=128)
        ensure_text_items(self.declared_dependencies, "PluginManifestView.declared_dependencies", limit=128)
        ensure_text_items(self.declared_lifecycle, "PluginManifestView.declared_lifecycle", limit=128)
        ensure_ref_items(self.declared_boundary_refs, "PluginManifestView.declared_boundary_refs")
        ensure_ref_items(self.declared_audit_refs, "PluginManifestView.declared_audit_refs")
        ensure_short_text(self.summary, "PluginManifestView.summary")
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "handoff_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginManifestView.{name}", required=False)
        ensure_ref_items(self.evidence_refs, "PluginManifestView.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginManifestView.provenance_refs")
        for name in (
            "validation_requirement_refs",
            "verification_requirement_refs",
            "evaluation_requirement_refs",
            "regression_requirement_refs",
            "rollback_requirement_refs",
            "health_requirement_refs",
        ):
            ensure_ref_items(getattr(self, name), f"PluginManifestView.{name}")
        ensure_schema_version(self.schema_version, "PluginManifestView.schema_version")
        if self.manifest_digest:
            ensure_ref_text(self.manifest_digest, "PluginManifestView.manifest_digest")
        else:
            object.__setattr__(self, "manifest_digest", digest_without(self, ("manifest_digest",)))
