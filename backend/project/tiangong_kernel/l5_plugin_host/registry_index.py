"""L5 phase 3 registry index declaration.

The index is derived from explicit in-memory RegistryRecord inputs. It has no
persistence, no plugin discovery, no registry writer, and no authorization
meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version
from .registry_record import PluginRegistryRecord
from .registry_serialization import registry_canonical_digest


@dataclass(frozen=True, slots=True)
class PluginRegistryIndex:
    index_ref: str
    records: tuple[PluginRegistryRecord, ...] = field(default_factory=tuple)
    index_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.index_ref, "PluginRegistryIndex.index_ref")
        for record in self.records:
            if not isinstance(record, PluginRegistryRecord):
                raise ValueError("PluginRegistryIndex.records must contain PluginRegistryRecord")
        ensure_schema_version(self.schema_version, "PluginRegistryIndex.schema_version")
        if self.index_digest:
            ensure_ref_text(self.index_digest, "PluginRegistryIndex.index_digest")
        else:
            object.__setattr__(self, "index_digest", registry_canonical_digest(self))

    def by_plugin_id(self, plugin_id: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.plugin_id == plugin_id)

    def by_namespace(self, namespace: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.namespace == namespace)

    def by_plugin_kind(self, plugin_kind: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.plugin_kind == plugin_kind)

    def by_version(self, version: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.version_identity == version)

    def by_mount_surface(self, surface_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if surface_ref in record.mount_surface_refs)

    def by_permission_tag(self, permission_tag: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if permission_tag in record.permission_tags)

    def by_resource_tag(self, resource_tag: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if resource_tag in record.resource_tags)

    def by_source_trust_ref(self, source_trust_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.source_trust_ref == source_trust_ref)

    def by_compatibility_ref(self, compatibility_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.compatibility_decl_ref == compatibility_ref)

    def by_version_slot_ref(self, version_slot_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.version_slot_ref == version_slot_ref)

    def by_migration_ref(self, migration_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.migration_ref == migration_ref)

    def by_rollback_anchor_ref(self, rollback_anchor_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.rollback_anchor_ref == rollback_anchor_ref)

    def by_hot_switch_decl_ref(self, hot_switch_decl_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.hot_switch_decl_ref == hot_switch_decl_ref)

    def by_replay_compatibility_ref(self, replay_compatibility_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.replay_compatibility_ref == replay_compatibility_ref)

    def by_breaking_change_policy_ref(self, breaking_change_policy_ref: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.breaking_change_policy_ref == breaking_change_policy_ref)

    def by_schema_version(self, schema_version_text: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.schema_version_text == schema_version_text)

    def by_api_version(self, api_version: str) -> tuple[PluginRegistryRecord, ...]:
        return tuple(record for record in self.records if record.api_version == api_version)
