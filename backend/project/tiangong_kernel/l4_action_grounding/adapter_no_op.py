"""No-op adapter for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_envelope import AdapterFailureEnvelope, AdapterInputEnvelope, AdapterOutputEnvelope
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_normalization import AdapterFailureNormalizer, AdapterResultNormalizer
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor


def _no_op_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("generic_action", "no_op_action"),
        envelope_types=("adapter_input",),
        supported_modes=(AdapterMode.NO_OP,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="none",
        resource_usage_declared="none",
        audit_requirement_declared="none",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="no_op.action_adapter",
            adapter_kind="no_op",
        ),
        adapter_name="No-Op Action Adapter",
        mode=AdapterMode.NO_OP,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        supports_no_op=True,
        enabled_by_default=True,
        production_enabled=False,
        test_only=False,
        side_effect_declared="none",
        resource_usage_declared="none",
        audit_requirement_declared="none",
    )


@dataclass(frozen=True, slots=True)
class NoOpActionAdapter:
    """Adapter that always returns a standard no-op result."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_no_op_descriptor)

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
        return (AdapterMode.NO_OP,)

    def supports(self, envelope: AdapterInputEnvelope) -> bool:
        return self.adapter_descriptor.structurally_supports(envelope.action_kind, envelope.envelope_type, AdapterMode.NO_OP)

    def prepare(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return self.invoke(envelope)

    def invoke(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.NO_OP,
            success=True,
            result_payload=(("adapter_result", "no_op"), ("real_action_performed", "false")),
            side_effect_summary="none",
            reversibility_summary="not_applicable",
        )

    def normalize_result(self, raw: object) -> AdapterOutputEnvelope:
        return AdapterResultNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            raw,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.NO_OP,
        )

    def normalize_failure(self, error: object) -> AdapterFailureEnvelope:
        return AdapterFailureNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            error,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.NO_OP,
        )


NoOpAdapter = NoOpActionAdapter
