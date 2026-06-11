"""L5 phase 3 plugin registry key declaration.

The key is an immutable logical locator. It is not a plugin entrypoint, path,
module name, URL, command, loader, or executable handle.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version
from .phase2_common import ensure_no_executable_reference


@dataclass(frozen=True, slots=True)
class PluginRegistryKey:
    plugin_id: str
    namespace: str
    plugin_kind: str
    version_ref: str = ""
    version_text: str = ""
    entry_ref: str = ""
    key_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_id, "PluginRegistryKey.plugin_id")
        ensure_ref_text(self.namespace, "PluginRegistryKey.namespace")
        ensure_ref_text(self.plugin_kind, "PluginRegistryKey.plugin_kind")
        ensure_ref_text(self.version_ref, "PluginRegistryKey.version_ref", required=False)
        ensure_ref_text(self.version_text, "PluginRegistryKey.version_text", required=False)
        ensure_ref_text(self.entry_ref, "PluginRegistryKey.entry_ref", required=False)
        if self.entry_ref:
            ensure_no_executable_reference(self.entry_ref, "PluginRegistryKey.entry_ref")
        ensure_schema_version(self.schema_version, "PluginRegistryKey.schema_version")

    @property
    def stable_parts(self) -> tuple[str, str, str, str]:
        return (self.namespace, self.plugin_id, self.plugin_kind, self.version_ref or self.version_text)

    @property
    def key_text(self) -> str:
        namespace, plugin_id, plugin_kind, version = self.stable_parts
        return f"{namespace}|{plugin_id}|{plugin_kind}|{version}"
