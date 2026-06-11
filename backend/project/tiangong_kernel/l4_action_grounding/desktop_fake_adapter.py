"""Fake desktop adapter for L4 phase 5."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_descriptor import AdapterDescriptor
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .desktop_action_failure import DesktopActionFailure
from .desktop_action_request import DesktopActionRequest
from .desktop_action_result import DesktopActionResult
from .external_adapter_common import external_adapter_descriptor


def _fake_desktop_descriptor() -> AdapterDescriptor:
    return external_adapter_descriptor(
        adapter_id="fake.desktop_action_adapter",
        adapter_kind="fake_desktop",
        adapter_name="Fake Desktop Action Adapter",
        action_kind="desktop_action",
        envelope_type="desktop_action_request",
        mode=AdapterMode.FAKE,
        side_effect_declared="none",
        resource_usage_declared="fake_usage_only",
        audit_requirement_declared="test_trace_only",
        supports_fake=True,
        test_only=True,
    )


@dataclass(frozen=True, slots=True)
class FakeDesktopAdapter:
    """Deterministic test adapter; it does not control the desktop."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_desktop_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_desktop_action(self, request: DesktopActionRequest) -> DesktopActionResult | DesktopActionFailure:
        return self.fake_desktop_action(request)

    def fake_desktop_action(self, request: DesktopActionRequest) -> DesktopActionResult:
        return DesktopActionResult(
            result_ref=new_adapter_typed_ref("desktop_action_result"),
            request_ref=request.request_ref,
            ui_observation_ref=new_adapter_typed_ref("desktop_observation"),
            gesture_result_ref=new_adapter_typed_ref("desktop_gesture_result"),
            resource_usage_summary="fake_usage_only",
            payload_items=(("desktop_result", "fake"), ("real_desktop_control", "false")),
            fake_result=True,
            real_desktop_control=False,
            real_screen_access=False,
            real_input_sent=False,
        )
