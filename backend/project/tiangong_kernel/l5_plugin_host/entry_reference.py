"""L5 phase 2 plugin entry reference declaration.

The entry reference is logical and non-executable. It must not be an import
path, file path, URL, command template, loader, handler, class, function, or
runtime object.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version, ensure_short_text
from .phase2_common import ensure_no_executable_reference, ensure_no_runtime_object


@dataclass(frozen=True, slots=True)
class PluginEntryReference:
    entry_ref: str
    entry_kind: str = "logical_declaration"
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_no_runtime_object(self.entry_ref, "PluginEntryReference.entry_ref")
        ensure_no_executable_reference(self.entry_ref, "PluginEntryReference.entry_ref")
        ensure_ref_text(self.entry_kind, "PluginEntryReference.entry_kind")
        ensure_short_text(self.summary, "PluginEntryReference.summary")
        ensure_schema_version(self.schema_version, "PluginEntryReference.schema_version")
