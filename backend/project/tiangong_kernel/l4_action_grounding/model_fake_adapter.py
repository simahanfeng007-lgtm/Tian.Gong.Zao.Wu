"""Fake model adapter for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor
from .model_action_failure import ModelActionFailure
from .model_action_request import ModelActionRequest
from .model_action_result import ModelActionResult


def _fake_model_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("model_action",),
        envelope_types=("model_action_request",),
        supported_modes=(AdapterMode.FAKE,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="none",
        resource_usage_declared="fake_usage_only",
        audit_requirement_declared="test_trace_only",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="fake.model_action_adapter",
            adapter_kind="fake_model",
        ),
        adapter_name="Fake Model Action Adapter",
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
        resource_usage_declared="fake_usage_only",
        audit_requirement_declared="test_trace_only",
    )


@dataclass(frozen=True, slots=True)
class FakeModelAdapter:
    """Deterministic test adapter; it never contacts a model service."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_model_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare(self, request: ModelActionRequest) -> ModelActionResult | ModelActionFailure:
        return self.invoke(request)

    def dry_run_model_action(self, request: ModelActionRequest) -> ModelActionResult | ModelActionFailure:
        return self.invoke(request)

    def invoke(self, request: ModelActionRequest) -> ModelActionResult:
        return ModelActionResult(
            result_ref=new_adapter_typed_ref("model_action_result"),
            request_ref=request.request_ref,
            output_ref=new_adapter_typed_ref("model_output"),
            usage_summary="fake_usage_only",
            payload_items=(("model_result", "fake"), ("real_model_called", "false")),
            dry_run_only=False,
            fake_result=True,
            real_model_called=False,
        )
