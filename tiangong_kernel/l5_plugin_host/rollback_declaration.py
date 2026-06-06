"""Declarative rollback requirements for L5 phase 2."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class PluginRollbackDeclaration:
    rollback_anchor_ref: str = ""
    rollback_policy_ref: str = ""
    tombstone_required: bool = True
    hot_switch_permission_required: bool = True
    manual_confirmation_required: bool = True
    rollback_executed: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rollback_anchor_ref, "PluginRollbackDeclaration.rollback_anchor_ref", required=False)
        ensure_ref_text(self.rollback_policy_ref, "PluginRollbackDeclaration.rollback_policy_ref", required=False)
        for name in ("tombstone_required", "hot_switch_permission_required", "manual_confirmation_required", "rollback_executed"):
            ensure_bool(getattr(self, name), f"PluginRollbackDeclaration.{name}")
        if self.rollback_executed:
            raise ValueError("PluginRollbackDeclaration must not execute rollback")
        ensure_schema_version(self.schema_version, "PluginRollbackDeclaration.schema_version")
