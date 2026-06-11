"""L5 phase 1 plugin host identity shells."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_PHASE, L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items


@dataclass(frozen=True, slots=True)
class PluginHostIdentity:
    host_ref: str
    host_name: str = "tiangong_l5_plugin_host"
    phase: str = L5_PLUGIN_HOST_PHASE
    supported_surfaces: tuple[str, ...] = field(default_factory=lambda: (
        "plugin_manifest_view",
        "plugin_registry_snapshot",
        "handoff_evidence_index",
        "boundary_baseline",
        "quality_gate_summary",
    ))
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.host_ref, "PluginHostIdentity.host_ref")
        ensure_short_text(self.host_name, "PluginHostIdentity.host_name", 128)
        ensure_short_text(self.phase, "PluginHostIdentity.phase", 64)
        ensure_text_items(self.supported_surfaces, "PluginHostIdentity.supported_surfaces", limit=128)
        ensure_schema_version(self.schema_version, "PluginHostIdentity.schema_version")
