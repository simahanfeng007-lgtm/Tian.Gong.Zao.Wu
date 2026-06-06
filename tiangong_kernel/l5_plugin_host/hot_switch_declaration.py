"""Declarative hot-switch requirements for L5 phase 2."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_text, ensure_schema_version


@dataclass(frozen=True, slots=True)
class PluginHotSwitchDeclaration:
    version_slot_ref: str = ""
    switch_readiness_ref: str = ""
    hot_switch_boundary_ref: str = ""
    pre_switch_checkpoint_ref: str = ""
    post_switch_observation_ref: str = ""
    switch_rollback_route_ref: str = ""
    old_event_replay_compatibility_ref: str = ""
    breaking_change_detection_ref: str = ""
    manual_confirmation_required: bool = True
    hot_switch_executed: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "version_slot_ref",
            "switch_readiness_ref",
            "hot_switch_boundary_ref",
            "pre_switch_checkpoint_ref",
            "post_switch_observation_ref",
            "switch_rollback_route_ref",
            "old_event_replay_compatibility_ref",
            "breaking_change_detection_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginHotSwitchDeclaration.{name}", required=False)
        ensure_bool(self.manual_confirmation_required, "PluginHotSwitchDeclaration.manual_confirmation_required")
        ensure_bool(self.hot_switch_executed, "PluginHotSwitchDeclaration.hot_switch_executed")
        if self.hot_switch_executed:
            raise ValueError("PluginHotSwitchDeclaration must not execute switching")
        ensure_schema_version(self.schema_version, "PluginHotSwitchDeclaration.schema_version")
