"""Disabled real adapter stub for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_envelope import AdapterFailureEnvelope, AdapterInputEnvelope, AdapterOutputEnvelope
from .adapter_failure import AdapterProductionDisabledFailure, new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_normalization import AdapterFailureNormalizer, AdapterResultNormalizer
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor


def _real_stub_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("generic_action", "future_real_action"),
        envelope_types=("adapter_input",),
        supported_modes=(AdapterMode.REAL_STUB,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="future_real_side_effect_not_enabled",
        resource_usage_declared="future_resource_usage_not_enabled",
        audit_requirement_declared="future_audit_requirement_not_enabled",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="real_stub.action_adapter",
            adapter_kind="real_stub",
        ),
        adapter_name="Disabled Real Action Adapter Stub",
        mode=AdapterMode.REAL_STUB,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        requires_l5_permit=True,
        enabled_by_default=False,
        production_enabled=False,
        test_only=False,
        side_effect_declared="future_real_side_effect_not_enabled",
        resource_usage_declared="future_resource_usage_not_enabled",
        audit_requirement_declared="future_audit_requirement_not_enabled",
    )


@dataclass(frozen=True, slots=True)
class RealActionAdapterStub:
    """Disabled shell for future real adapters; invoke always fails."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_real_stub_descriptor)

    @property
    def is_real_adapter(self) -> bool:
        return True

    @property
    def is_enabled_by_default(self) -> bool:
        return False

    @property
    def requires_l5_permit(self) -> bool:
        return True

    @property
    def allowed_modes(self) -> tuple[AdapterMode, ...]:
        return (AdapterMode.REAL_STUB,)

    def supports(self, envelope: AdapterInputEnvelope) -> bool:
        return self.adapter_descriptor.structurally_supports(envelope.action_kind, envelope.envelope_type, AdapterMode.REAL_STUB)

    def prepare(self, envelope: AdapterInputEnvelope) -> AdapterFailureEnvelope:
        return self.invoke(envelope)

    def invoke(self, envelope: AdapterInputEnvelope) -> AdapterFailureEnvelope:
        failure = AdapterProductionDisabledFailure(
            failure_ref=new_adapter_typed_ref("adapter_failure"),
            message="real adapter stub is disabled in L4 phase 3",
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.REAL_STUB,
        )
        return failure.to_envelope()

    def normalize_result(self, raw: object) -> AdapterOutputEnvelope:
        return AdapterResultNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            raw,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.REAL_STUB,
            success=False,
        )

    def normalize_failure(self, error: object) -> AdapterFailureEnvelope:
        return AdapterFailureNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            error,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.REAL_STUB,
        )


RealAdapterStub = RealActionAdapterStub
