"""L5 phase 1 error view objects."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_non_empty_text, ensure_schema_version, ensure_short_text


@dataclass(frozen=True, slots=True)
class L5PluginHostError:
    code: str
    message: str
    severity: str = "recoverable"
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_non_empty_text(self.code, "L5PluginHostError.code", 128)
        ensure_short_text(self.message, "L5PluginHostError.message")
        ensure_non_empty_text(self.severity, "L5PluginHostError.severity", 64)
        ensure_schema_version(self.schema_version, "L5PluginHostError.schema_version")
