"""L4 to L5 plugin host handoff envelope."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, L5_PLUGIN_HOST_SURFACES, ensure_false, ensure_pair_items, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4ToL5PluginHostHandoffEnvelope:
    handoff_ref: TypedRef
    package_ref: TypedRef | None = None
    manifest_material_ref: TypedRef | None = None
    sandbox_requirement_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    health_observation_requirement_ref: TypedRef | None = None
    external_adapter_requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    required_l5_plugin_host_surfaces: tuple[str, ...] = field(default_factory=lambda: L5_PLUGIN_HOST_SURFACES)
    handoff_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    handoff_only: bool = field(default=True)
    implements_plugin_host: bool = False
    dynamically_loads_plugins: bool = False
    writes_plugin_registry: bool = False
    creates_sandbox: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_l5_plugin_host_surfaces, "L4ToL5PluginHostHandoffEnvelope.required_l5_plugin_host_surfaces", 128)
        ensure_pair_items(self.handoff_items, "L4ToL5PluginHostHandoffEnvelope.handoff_items")
        ensure_true(self.handoff_only, "L4ToL5PluginHostHandoffEnvelope.handoff_only")
        ensure_false(self.implements_plugin_host, "L4ToL5PluginHostHandoffEnvelope.implements_plugin_host")
        ensure_false(self.dynamically_loads_plugins, "L4ToL5PluginHostHandoffEnvelope.dynamically_loads_plugins")
        ensure_false(self.writes_plugin_registry, "L4ToL5PluginHostHandoffEnvelope.writes_plugin_registry")
        ensure_false(self.creates_sandbox, "L4ToL5PluginHostHandoffEnvelope.creates_sandbox")
        ensure_schema_version(self.schema_version, "L4ToL5PluginHostHandoffEnvelope.schema_version")
