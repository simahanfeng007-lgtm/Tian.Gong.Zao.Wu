"""L5 phase 2 mount surface declarations.

This module only declares expected surfaces. It never mounts, binds, attaches,
enables, exposes, publishes, or activates any plugin capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .phase2_common import ALLOWED_MOUNT_SURFACE_KINDS, ensure_allowed_value, ensure_no_runtime_object

_BLOCKED_SURFACE_WORDS = ("callback", "hook", "callable", "handler", "loader", "runner", "executor")


@dataclass(frozen=True, slots=True)
class PluginMountSurfaceDeclaration:
    surface_ref: str
    surface_kind: str
    surface_name: str = ""
    exposed_ref: str = ""
    boundary_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    callback_ref_absent: bool = True
    hook_ref_absent: bool = True
    raw_surface_payload: Any = None
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.surface_ref, "PluginMountSurfaceDeclaration.surface_ref")
        ensure_allowed_value(self.surface_kind, ALLOWED_MOUNT_SURFACE_KINDS, "PluginMountSurfaceDeclaration.surface_kind")
        ensure_short_text(self.surface_name, "PluginMountSurfaceDeclaration.surface_name", 128)
        ensure_ref_text(self.exposed_ref, "PluginMountSurfaceDeclaration.exposed_ref", required=False)
        ensure_ref_text(self.boundary_ref, "PluginMountSurfaceDeclaration.boundary_ref", required=False)
        ensure_ref_items(self.evidence_refs, "PluginMountSurfaceDeclaration.evidence_refs")
        ensure_bool(self.callback_ref_absent, "PluginMountSurfaceDeclaration.callback_ref_absent")
        ensure_bool(self.hook_ref_absent, "PluginMountSurfaceDeclaration.hook_ref_absent")
        if not self.callback_ref_absent or not self.hook_ref_absent:
            raise ValueError("PluginMountSurfaceDeclaration cannot carry callback or hook refs in phase 2")
        ensure_no_runtime_object(self.raw_surface_payload, "PluginMountSurfaceDeclaration.raw_surface_payload")
        for value in (self.surface_ref, self.surface_kind, self.surface_name, self.exposed_ref, self.boundary_ref):
            lowered = value.lower()
            if any(word in lowered for word in _BLOCKED_SURFACE_WORDS):
                raise ValueError("PluginMountSurfaceDeclaration must not contain runtime surface hooks")
        ensure_schema_version(self.schema_version, "PluginMountSurfaceDeclaration.schema_version")
