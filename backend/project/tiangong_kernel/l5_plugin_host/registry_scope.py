"""L5 phase 3 registry scope declaration.

Scope objects are visibility declarations only. They are not authorization
results and must not be used as permit, lease, or policy decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class PluginRegistryScope:
    scope_id: str
    scope_kind: str
    visible_to_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    boundary_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.scope_id, "PluginRegistryScope.scope_id")
        ensure_ref_text(self.scope_kind, "PluginRegistryScope.scope_kind")
        ensure_ref_items(self.visible_to_refs, "PluginRegistryScope.visible_to_refs")
        ensure_ref_items(self.policy_refs, "PluginRegistryScope.policy_refs")
        ensure_ref_items(self.handoff_refs, "PluginRegistryScope.handoff_refs")
        ensure_ref_text(self.boundary_ref, "PluginRegistryScope.boundary_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginRegistryScope.schema_version")
