"""Declarative permission requirements for L5 phase 2 manifests."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_schema_version, ensure_text_items


@dataclass(frozen=True, slots=True)
class PluginPermissionDeclaration:
    required_permissions: tuple[str, ...] = field(default_factory=tuple)
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    human_confirmation_required: bool = False
    lease_required: bool = True
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    permit_issued: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.required_permissions, "PluginPermissionDeclaration.required_permissions", limit=128)
        ensure_text_items(self.risk_tags, "PluginPermissionDeclaration.risk_tags", limit=128)
        ensure_bool(self.human_confirmation_required, "PluginPermissionDeclaration.human_confirmation_required")
        ensure_bool(self.lease_required, "PluginPermissionDeclaration.lease_required")
        ensure_ref_items(self.policy_refs, "PluginPermissionDeclaration.policy_refs")
        ensure_bool(self.permit_issued, "PluginPermissionDeclaration.permit_issued")
        if self.permit_issued:
            raise ValueError("PluginPermissionDeclaration must not issue permits")
        ensure_schema_version(self.schema_version, "PluginPermissionDeclaration.schema_version")
