"""Disabled real model/tool adapter stub for L4 phase 4."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor
from .model_action_failure import ModelActionFailure, ModelActionFailureKind
from .model_action_request import ModelActionRequest
from .tool_action_failure import ToolActionFailure, ToolActionFailureKind
from .tool_action_request import ToolActionRequest
from .tool_failure_envelope import ToolFailureEnvelope


def _disabled_model_tool_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("model_action", "tool_action"),
        envelope_types=("model_action_request", "tool_action_request"),
        supported_modes=(AdapterMode.REAL_STUB,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="future_real_model_tool_side_effect_not_enabled",
        resource_usage_declared="future_real_model_tool_usage_not_enabled",
        audit_requirement_declared="future_audit_requirement_not_enabled",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="disabled.real_model_tool_adapter_stub",
            adapter_kind="disabled_model_tool_stub",
        ),
        adapter_name="Disabled Real Model Tool Adapter Stub",
        mode=AdapterMode.REAL_STUB,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        requires_l5_permit=True,
        enabled_by_default=False,
        production_enabled=False,
        test_only=False,
        side_effect_declared="future_real_model_tool_side_effect_not_enabled",
        resource_usage_declared="future_real_model_tool_usage_not_enabled",
        audit_requirement_declared="future_audit_requirement_not_enabled",
    )


@dataclass(frozen=True, slots=True)
class DisabledRealModelToolAdapterStub:
    """Disabled shell for future real model/tool adapters."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_disabled_model_tool_descriptor)

    def describe(self) -> AdapterDescriptor:
        return self.adapter_descriptor

    def prepare_model_action(self, request: ModelActionRequest) -> ModelActionFailure:
        return self.invoke_model_action(request)

    def invoke_model_action(self, request: ModelActionRequest) -> ModelActionFailure:
        return ModelActionFailure(
            failure_ref=new_adapter_typed_ref("model_action_failure"),
            request_ref=request.request_ref,
            failure_kind=ModelActionFailureKind.DISABLED_BY_DEFAULT,
            message="real model action is disabled in L4 phase 4",
            real_model_called=False,
        )

    def prepare_tool_action(self, request: ToolActionRequest) -> ToolActionFailure:
        return self.disabled_tool_action(request)

    def disabled_tool_action(self, request: ToolActionRequest) -> ToolActionFailure:
        failure_envelope = ToolFailureEnvelope(
            failure_ref=new_adapter_typed_ref("tool_failure_envelope"),
            failure_code="adapter_disabled",
            message="real tool action is disabled in L4 phase 4",
            real_tool_called=False,
        )
        return ToolActionFailure(
            failure_ref=new_adapter_typed_ref("tool_action_failure"),
            request_ref=request.request_ref,
            failure_kind=ToolActionFailureKind.ADAPTER_DISABLED,
            failure_envelope=failure_envelope,
            message=failure_envelope.message,
            real_tool_called=False,
        )
