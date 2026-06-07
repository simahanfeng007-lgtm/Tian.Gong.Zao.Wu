"""Declarative plugin version requirements for L5 phase 2."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version, ensure_short_text
from .phase2_common import ensure_semver_text


@dataclass(frozen=True, slots=True)
class PluginVersionDeclaration:
    plugin_version: str
    api_version: str
    schema_version_text: str
    compatibility_range: str = ""
    migration_ref: str = ""
    version_slot_ref: str = ""
    hot_switch_executed: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_semver_text(self.plugin_version, "PluginVersionDeclaration.plugin_version")
        ensure_semver_text(self.api_version, "PluginVersionDeclaration.api_version")
        ensure_semver_text(self.schema_version_text, "PluginVersionDeclaration.schema_version_text")
        ensure_short_text(self.compatibility_range, "PluginVersionDeclaration.compatibility_range", 128)
        ensure_ref_text(self.migration_ref, "PluginVersionDeclaration.migration_ref", required=False)
        ensure_ref_text(self.version_slot_ref, "PluginVersionDeclaration.version_slot_ref", required=False)
        if self.hot_switch_executed:
            raise ValueError("PluginVersionDeclaration must not execute hot switch")
        ensure_schema_version(self.schema_version, "PluginVersionDeclaration.schema_version")
