"""Dry-run desktop adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .desktop_action_failure import DesktopActionFailure
from .desktop_action_request import DesktopActionRequest
from .desktop_action_result import DesktopActionResult
from .external_adapter_common import external_adapter_descriptor


def _dry_run_desktop_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="dry_run.desktop_action_adapter",
        adapter_kind="dry_run_desktop",
        adapter_name="Dry Run Desktop Action Adapter",
        action_kind="desktop_action",
        envelope_type="desktop_action_request",
        mode=AdapterMode.DRY_RUN,
        side_effect_declared="preview_only",
        resource_usage_declared="dry_run_preview_only",
        audit_requirement_declared="future_audit_requirement_ref",
        supports_dry_run=True,
    )


@dataclass(frozen=True, slots=True)
class DryRunDesktopAdapter:
    """Preview adapter; it performs no desktop control."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_dry_run_desktop_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_desktop_action(self, request: DesktopActionRequest) -> DesktopActionResult | DesktopActionFailure:
        return self.dry_run_desktop_action(request)

    def dry_run_desktop_action(self, request: DesktopActionRequest) -> DesktopActionResult:
        return DesktopActionResult(
            result_ref=new_adapter_typed_ref("desktop_action_result"),
            request_ref=request.request_ref,
            ui_observation_ref=new_adapter_typed_ref("desktop_dry_run_observation"),
            resource_usage_summary=request.resource_usage.summary,
            payload_items=(("mode", "dry_run"), ("real_desktop_control", "false")),
            dry_run_only=True,
            real_desktop_control=False,
            real_screen_access=False,
            real_input_sent=False,
        )
