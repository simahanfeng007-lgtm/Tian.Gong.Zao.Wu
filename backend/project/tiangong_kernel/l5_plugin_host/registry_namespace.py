"""L5 phase 3 registry namespace declaration.

Namespace objects describe registry visibility grouping only. They do not make
access decisions, grant permissions, isolate processes, or hide plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text

NAMESPACE_POLICY_SINGLE_PLUGIN_ID = "single_plugin_id"
NAMESPACE_POLICY_MULTI_VERSION_ALLOWED = "multi_version_allowed"
NAMESPACE_POLICY_EXPLICIT_ALIAS_REQUIRED = "explicit_alias_required"
NAMESPACE_POLICY_FROZEN_ARCHIVE = "frozen_archive"
_ALLOWED_POLICIES = (
    NAMESPACE_POLICY_SINGLE_PLUGIN_ID,
    NAMESPACE_POLICY_MULTI_VERSION_ALLOWED,
    NAMESPACE_POLICY_EXPLICIT_ALIAS_REQUIRED,
    NAMESPACE_POLICY_FROZEN_ARCHIVE,
)


@dataclass(frozen=True, slots=True)
class PluginRegistryNamespace:
    namespace_id: str
    namespace_kind: str
    owner_ref: str = ""
    boundary_ref: str = ""
    uniqueness_policy: str = NAMESPACE_POLICY_MULTI_VERSION_ALLOWED
    version_policy_ref: str = ""
    description: str = ""
    alias_refs: tuple[str, ...] = field(default_factory=tuple)
    channel_refs: tuple[str, ...] = field(default_factory=tuple)
    revision_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.namespace_id, "PluginRegistryNamespace.namespace_id")
        ensure_ref_text(self.namespace_kind, "PluginRegistryNamespace.namespace_kind")
        ensure_ref_text(self.owner_ref, "PluginRegistryNamespace.owner_ref", required=False)
        ensure_ref_text(self.boundary_ref, "PluginRegistryNamespace.boundary_ref", required=False)
        if self.uniqueness_policy not in _ALLOWED_POLICIES:
            raise ValueError("PluginRegistryNamespace.uniqueness_policy has unsupported value")
        ensure_ref_text(self.version_policy_ref, "PluginRegistryNamespace.version_policy_ref", required=False)
        ensure_short_text(self.description, "PluginRegistryNamespace.description")
        ensure_ref_items(self.alias_refs, "PluginRegistryNamespace.alias_refs")
        ensure_ref_items(self.channel_refs, "PluginRegistryNamespace.channel_refs")
        ensure_ref_text(self.revision_ref, "PluginRegistryNamespace.revision_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginRegistryNamespace.schema_version")
