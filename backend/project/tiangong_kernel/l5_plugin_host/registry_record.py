"""L5 phase 3 immutable registry record declaration."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items
from .registry_key import PluginRegistryKey
from .registry_serialization import registry_canonical_digest


@dataclass(frozen=True, slots=True)
class PluginRegistryRecord:
    registry_record_ref: str
    registry_key: PluginRegistryKey | None = None
    manifest_ref: str = ""
    manifest_hash: str = ""
    manifest_digest_value: str = ""
    package_ref: str = ""
    entry_ref: str = ""
    source_trust_ref: str = ""
    signature_ref: str = ""
    permission_decl_ref: str = ""
    resource_decl_ref: str = ""
    credential_decl_ref: str = ""
    data_governance_decl_ref: str = ""
    audit_decl_ref: str = ""
    version_decl_ref: str = ""
    rollback_decl_ref: str = ""
    compatibility_decl_ref: str = ""
    capability_token_decl_ref: str = ""
    trust_boundary_decl_ref: str = ""
    hot_switch_decl_ref: str = ""
    migration_ref: str = ""
    upcast_policy_ref: str = ""
    replay_compatibility_ref: str = ""
    breaking_change_policy_ref: str = ""
    version_slot_ref: str = ""
    rollback_anchor_ref: str = ""
    schema_version_text: str = ""
    api_version: str = ""
    manifest_version: str = ""
    plugin_version_ref: str = ""
    plugin_version_text: str = ""
    alias_ref: str = ""
    channel_ref: str = ""
    status_ref: str = "status:declared_only"
    created_at_ref: str = ""
    updated_at_ref: str = ""
    mount_surface_refs: tuple[str, ...] = field(default_factory=tuple)
    exclusive_mount_surface_refs: tuple[str, ...] = field(default_factory=tuple)
    permission_tags: tuple[str, ...] = field(default_factory=tuple)
    resource_tags: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    forbidden_scan_report_ref: str = ""
    forbidden_scan_summary: str = ""
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
    canonical_record_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.registry_record_ref, "PluginRegistryRecord.registry_record_ref")
        if self.registry_key is not None and not isinstance(self.registry_key, PluginRegistryKey):
            raise ValueError("PluginRegistryRecord.registry_key must be PluginRegistryKey or None")
        for name in (
            "manifest_ref", "manifest_hash", "manifest_digest_value", "package_ref", "entry_ref",
            "source_trust_ref", "signature_ref", "permission_decl_ref", "resource_decl_ref",
            "credential_decl_ref", "data_governance_decl_ref", "audit_decl_ref", "version_decl_ref",
            "rollback_decl_ref", "compatibility_decl_ref", "capability_token_decl_ref", "trust_boundary_decl_ref",
            "hot_switch_decl_ref", "migration_ref", "upcast_policy_ref", "replay_compatibility_ref",
            "breaking_change_policy_ref", "version_slot_ref", "rollback_anchor_ref", "schema_version_text",
            "api_version", "manifest_version", "plugin_version_ref", "plugin_version_text", "alias_ref",
            "channel_ref", "status_ref", "created_at_ref", "updated_at_ref", "forbidden_scan_report_ref",
            "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref",
            "accountability_ref", "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginRegistryRecord.{name}", required=False)
        ensure_text_items(self.mount_surface_refs, "PluginRegistryRecord.mount_surface_refs", limit=128)
        ensure_text_items(self.exclusive_mount_surface_refs, "PluginRegistryRecord.exclusive_mount_surface_refs", limit=128)
        ensure_text_items(self.permission_tags, "PluginRegistryRecord.permission_tags", limit=128)
        ensure_text_items(self.resource_tags, "PluginRegistryRecord.resource_tags", limit=128)
        ensure_short_text(self.summary, "PluginRegistryRecord.summary")
        ensure_short_text(self.forbidden_scan_summary, "PluginRegistryRecord.forbidden_scan_summary")
        ensure_ref_items(self.provenance_refs, "PluginRegistryRecord.provenance_refs")
        ensure_ref_items(self.evidence_refs, "PluginRegistryRecord.evidence_refs")
        ensure_schema_version(self.schema_version, "PluginRegistryRecord.schema_version")
        if self.canonical_record_digest:
            ensure_ref_text(self.canonical_record_digest, "PluginRegistryRecord.canonical_record_digest")
        else:
            object.__setattr__(self, "canonical_record_digest", registry_canonical_digest(self))

    @property
    def registry_key_text(self) -> str:
        if self.registry_key is None:
            return ""
        return self.registry_key.key_text

    @property
    def plugin_id(self) -> str:
        return "" if self.registry_key is None else self.registry_key.plugin_id

    @property
    def namespace(self) -> str:
        return "" if self.registry_key is None else self.registry_key.namespace

    @property
    def plugin_kind(self) -> str:
        return "" if self.registry_key is None else self.registry_key.plugin_kind

    @property
    def version_identity(self) -> str:
        if self.registry_key is None:
            return self.plugin_version_ref or self.plugin_version_text
        return self.registry_key.version_ref or self.registry_key.version_text
