"""In-memory simulation adapter for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_envelope import AdapterFailureEnvelope, AdapterInputEnvelope, AdapterOutputEnvelope
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_normalization import AdapterFailureNormalizer, AdapterResultNormalizer
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor


def _in_memory_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("generic_action", "memory_action"),
        envelope_types=("adapter_input",),
        supported_modes=(AdapterMode.IN_MEMORY,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="in_memory_only",
        resource_usage_declared="memory_preview_only",
        audit_requirement_declared="preview_only",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="in_memory.action_adapter",
            adapter_kind="in_memory",
        ),
        adapter_name="In-Memory Action Adapter",
        mode=AdapterMode.IN_MEMORY,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        enabled_by_default=True,
        production_enabled=False,
        test_only=False,
        side_effect_declared="in_memory_only",
        resource_usage_declared="memory_preview_only",
        audit_requirement_declared="preview_only",
    )


@dataclass(frozen=True, slots=True)
class InMemoryActionAdapter:
    """Adapter that only echoes deterministic in-memory simulation data."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_in_memory_descriptor)
    memory_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)

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
        return (AdapterMode.IN_MEMORY,)

    def supports(self, envelope: AdapterInputEnvelope) -> bool:
        return self.adapter_descriptor.structurally_supports(envelope.action_kind, envelope.envelope_type, AdapterMode.IN_MEMORY)

    def prepare(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.IN_MEMORY,
            success=True,
            result_payload=(("prepared", "in_memory"),),
            resource_usage_preview="memory_preview_only",
            side_effect_summary="in_memory_only",
        )

    def invoke(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        payload = self.memory_items + (("adapter_result", "in_memory_simulation"), ("real_action_performed", "false"))
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.IN_MEMORY,
            success=True,
            result_payload=payload,
            resource_usage_preview="memory_preview_only",
            side_effect_summary="in_memory_only",
        )

    def normalize_result(self, raw: object) -> AdapterOutputEnvelope:
        return AdapterResultNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            raw,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.IN_MEMORY,
        )

    def normalize_failure(self, error: object) -> AdapterFailureEnvelope:
        return AdapterFailureNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            error,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.IN_MEMORY,
        )


InMemoryAdapter = InMemoryActionAdapter
