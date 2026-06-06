"""Test-only fake adapter for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_envelope import AdapterFailureEnvelope, AdapterInputEnvelope, AdapterOutputEnvelope
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_normalization import AdapterFailureNormalizer, AdapterResultNormalizer
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor


def _fake_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("generic_action", "test_action"),
        envelope_types=("adapter_input",),
        supported_modes=(AdapterMode.FAKE,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="none",
        resource_usage_declared="none",
        audit_requirement_declared="test_trace_only",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="fake.action_adapter",
            adapter_kind="fake",
        ),
        adapter_name="Fake Action Adapter",
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
        resource_usage_declared="none",
        audit_requirement_declared="test_trace_only",
    )


@dataclass(frozen=True, slots=True)
class FakeActionAdapter:
    """Deterministic fake adapter; it must never enter production path."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_fake_descriptor)

    @property
    def is_real_adapter(self) -> bool:
        return False

    @property
    def is_enabled_by_default(self) -> bool:
        return self.adapter_descriptor.enabled_by_default

    @property
    def requires_l5_permit(self) -> bool:
        return self.adapter_descriptor.requires_l5_permit

    @property
    def allowed_modes(self) -> tuple[AdapterMode, ...]:
        return (AdapterMode.FAKE,)

    def supports(self, envelope: AdapterInputEnvelope) -> bool:
        return self.adapter_descriptor.structurally_supports(envelope.action_kind, envelope.envelope_type, AdapterMode.FAKE)

    def prepare(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.FAKE,
            success=True,
            result_payload=(("prepared", "fake"),),
            side_effect_summary="none",
        )

    def invoke(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.FAKE,
            success=True,
            result_payload=(("adapter_result", "fake"), ("real_action_performed", "false")),
            side_effect_summary="none",
            reversibility_summary="not_applicable",
        )

    def normalize_result(self, raw: object) -> AdapterOutputEnvelope:
        return AdapterResultNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            raw,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.FAKE,
        )

    def normalize_failure(self, error: object) -> AdapterFailureEnvelope:
        return AdapterFailureNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            error,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.FAKE,
        )


FakeAdapter = FakeActionAdapter
