"""Declarative compatibility requirements for L5 phase 2."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_schema_version, ensure_text_items


@dataclass(frozen=True, slots=True)
class PluginCompatibilityDeclaration:
    required_l0_l1_l2_l3_l4_l5_ranges: tuple[str, ...] = field(default_factory=tuple)
    required_port_refs: tuple[str, ...] = field(default_factory=tuple)
    required_state_refs: tuple[str, ...] = field(default_factory=tuple)
    required_handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    incompatible_plugin_refs: tuple[str, ...] = field(default_factory=tuple)
    auto_migration_executed: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_l0_l1_l2_l3_l4_l5_ranges, "PluginCompatibilityDeclaration.required_l0_l1_l2_l3_l4_l5_ranges", limit=128)
        ensure_ref_items(self.required_port_refs, "PluginCompatibilityDeclaration.required_port_refs")
        ensure_ref_items(self.required_state_refs, "PluginCompatibilityDeclaration.required_state_refs")
        ensure_ref_items(self.required_handoff_refs, "PluginCompatibilityDeclaration.required_handoff_refs")
        ensure_ref_items(self.incompatible_plugin_refs, "PluginCompatibilityDeclaration.incompatible_plugin_refs")
        if self.auto_migration_executed:
            raise ValueError("PluginCompatibilityDeclaration must not execute migration")
        ensure_schema_version(self.schema_version, "PluginCompatibilityDeclaration.schema_version")
