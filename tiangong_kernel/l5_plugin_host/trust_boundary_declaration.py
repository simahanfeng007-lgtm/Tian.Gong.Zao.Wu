"""Declarative trust-boundary requirements for L5 phase 2."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class PluginTrustBoundaryDeclaration:
    host_boundary_ref: str = ""
    plugin_boundary_ref: str = ""
    data_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    network_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    external_disclosure_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    recovery_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    boundary_decision_executed: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.host_boundary_ref, "PluginTrustBoundaryDeclaration.host_boundary_ref", required=False)
        ensure_ref_text(self.plugin_boundary_ref, "PluginTrustBoundaryDeclaration.plugin_boundary_ref", required=False)
        for name in (
            "data_boundary_refs",
            "tool_boundary_refs",
            "network_boundary_refs",
            "credential_boundary_refs",
            "external_disclosure_boundary_refs",
            "audit_boundary_refs",
            "recovery_boundary_refs",
        ):
            ensure_ref_items(getattr(self, name), f"PluginTrustBoundaryDeclaration.{name}")
        if self.boundary_decision_executed:
            raise ValueError("PluginTrustBoundaryDeclaration must not execute trust-boundary decisions")
        ensure_schema_version(self.schema_version, "PluginTrustBoundaryDeclaration.schema_version")
