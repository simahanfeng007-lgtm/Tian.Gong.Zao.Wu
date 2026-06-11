"""L5 phase 2 Plugin Manifest schema shell."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version, ensure_text_items
from .phase2_common import ALLOWED_PLUGIN_KINDS, L5_PLUGIN_MANIFEST_SCHEMA_VERSION

PHASE2_REQUIRED_MANIFEST_FIELDS = (
    "plugin_id",
    "plugin_name",
    "plugin_kind",
    "schema_version",
    "manifest_version",
    "entry_ref",
    "package_ref",
    "mount_surfaces",
    "permission_decl",
    "resource_decl",
    "credential_decl",
    "data_governance_decl",
    "audit_decl",
    "version_decl",
    "rollback_decl",
    "compatibility_decl",
    "capability_token_decl",
    "trust_boundary_decl",
    "source_trust_ref",
    "signature_ref",
    "manifest_hash",
    "created_at_ref",
    "producer_ref",
    "boundary_baseline_ref",
    "handoff_evidence_refs",
    "no_live_external_action_guarantee_ref",
    "no_l6_implementation_guarantee_ref",
    "no_lower_layer_mutation_guarantee_ref",
    "no_legacy_runtime_guarantee_ref",
    "actor_ref",
    "scope_ref",
    "trace_ref",
    "policy_ref",
    "approval_ref",
    "accountability_ref",
    "provenance_refs",
    "tamper_evidence_ref",
    "lifecycle_event_refs",
    "consent_refs",
    "purpose_refs",
    "data_lifecycle_refs",
)


@dataclass(frozen=True, slots=True)
class PluginManifestSchema:
    schema_ref: str
    schema_version: str = L5_PLUGIN_MANIFEST_SCHEMA_VERSION
    required_fields: tuple[str, ...] = PHASE2_REQUIRED_MANIFEST_FIELDS
    allowed_plugin_kinds: tuple[str, ...] = ALLOWED_PLUGIN_KINDS
    summary: str = "phase2_manifest_schema_data_only"
    host_schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.schema_ref, "PluginManifestSchema.schema_ref")
        ensure_schema_version(self.schema_version, "PluginManifestSchema.schema_version")
        ensure_text_items(self.required_fields, "PluginManifestSchema.required_fields", limit=128)
        ensure_text_items(self.allowed_plugin_kinds, "PluginManifestSchema.allowed_plugin_kinds", limit=128)
        ensure_text_items((self.summary,), "PluginManifestSchema.summary", limit=256)
        ensure_schema_version(self.host_schema_version, "PluginManifestSchema.host_schema_version")
