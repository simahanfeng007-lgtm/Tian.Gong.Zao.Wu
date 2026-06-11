"""Fake tool adapter for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor
from .tool_action_failure import ToolActionFailure
from .tool_action_request import ToolActionRequest
from .tool_action_result import ToolActionResult
from .tool_result_envelope import ToolResultEnvelope


def _fake_tool_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("tool_action",),
        envelope_types=("tool_action_request",),
        supported_modes=(AdapterMode.FAKE,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="none",
        resource_usage_declared="fake_tool_usage_only",
        audit_requirement_declared="test_trace_only",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="fake.tool_action_adapter",
            adapter_kind="fake_tool",
        ),
        adapter_name="Fake Tool Action Adapter",
        mode=AdapterMode.FAKE,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        supports_fake=True,
        enabled_by_default=True,
        production_enabled=False,
        test_only=True,
        side_effect_declared="none",
        resource_usage_declared="fake_tool_usage_only",
        audit_requirement_declared="test_trace_only",
    )


@dataclass(frozen=True, slots=True)
class FakeToolAdapter:
    """Deterministic test adapter; it never invokes a real tool."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_tool_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare(self, request: ToolActionRequest) -> ToolActionResult | ToolActionFailure:
        return self.invoke(request)

    def dry_run_tool_action(self, request: ToolActionRequest) -> ToolActionResult | ToolActionFailure:
        return self.invoke(request)

    def invoke(self, request: ToolActionRequest) -> ToolActionResult:
        envelope = ToolResultEnvelope(
            result_ref=new_adapter_typed_ref("tool_result_envelope"),
            output_ref=new_adapter_typed_ref("tool_output"),
            normalized_output=(("tool_result", "fake"), ("real_tool_called", "false")),
            resource_usage_summary="fake_tool_usage_only",
            side_effect_summary="none",
            dry_run_only=False,
            fake_result=True,
            real_tool_called=False,
        )
        return ToolActionResult(
            result_ref=new_adapter_typed_ref("tool_action_result"),
            request_ref=request.request_ref,
            tool_result_ref=envelope.result_ref,
            result_envelope=envelope,
            resource_usage_summary=envelope.resource_usage_summary,
            side_effect_summary=envelope.side_effect_summary,
            dry_run_only=False,
            fake_result=True,
            real_tool_called=False,
        )
