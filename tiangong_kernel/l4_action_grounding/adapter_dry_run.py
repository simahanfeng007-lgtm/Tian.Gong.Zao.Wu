"""Dry-run adapter for L4 phase 3."""

from __future__ import annotations

from dataclasses import dataclass, field

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_envelope import AdapterFailureEnvelope, AdapterInputEnvelope, AdapterOutputEnvelope
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_normalization import AdapterFailureNormalizer, AdapterResultNormalizer
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor


def _dry_run_descriptor() -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=("generic_action", "dry_run_action"),
        envelope_types=("adapter_input",),
        supported_modes=(AdapterMode.DRY_RUN,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared="preview_only",
        resource_usage_declared="resource_usage_preview_only",
        audit_requirement_declared="audit_requirement_preview_only",
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id="dry_run.action_adapter",
            adapter_kind="dry_run",
        ),
        adapter_name="Dry-Run Action Adapter",
        mode=AdapterMode.DRY_RUN,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        supports_dry_run=True,
        enabled_by_default=True,
        production_enabled=False,
        test_only=False,
        side_effect_declared="preview_only",
        resource_usage_declared="resource_usage_preview_only",
        audit_requirement_declared="audit_requirement_preview_only",
    )


@dataclass(frozen=True, slots=True)
class DryRunActionAdapter:
    """Dry-run adapter; it returns a preview, not real success."""

    adapter_descriptor: AdapterDescriptor = field(default_factory=_dry_run_descriptor)

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
        return (AdapterMode.DRY_RUN,)

    def supports(self, envelope: AdapterInputEnvelope) -> bool:
        return self.adapter_descriptor.structurally_supports(envelope.action_kind, envelope.envelope_type, AdapterMode.DRY_RUN)

    def prepare(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return self.invoke(envelope)

    def invoke(self, envelope: AdapterInputEnvelope) -> AdapterOutputEnvelope:
        return AdapterOutputEnvelope(
            output_ref=new_adapter_typed_ref("adapter_output"),
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind=envelope.action_kind,
            mode=AdapterMode.DRY_RUN,
            success=True,
            result_payload=(
                ("dry_run_only", "true"),
                ("side_effect_preview", "preview_only"),
                ("resource_usage_preview", "resource_usage_preview_only"),
                ("audit_requirement_preview", "audit_requirement_preview_only"),
            ),
            resource_usage_preview="resource_usage_preview_only",
            side_effect_summary="preview_only",
            reversibility_summary="not_applicable",
        )

    def normalize_result(self, raw: object) -> AdapterOutputEnvelope:
        return AdapterResultNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            raw,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.DRY_RUN,
        )

    def normalize_failure(self, error: object) -> AdapterFailureEnvelope:
        return AdapterFailureNormalizer(new_adapter_typed_ref("adapter_normalizer")).normalize(
            error,
            adapter_id=self.adapter_descriptor.adapter_id,
            adapter_kind=self.adapter_descriptor.adapter_kind,
            action_kind="generic_action",
            mode=AdapterMode.DRY_RUN,
        )


DryRunAdapter = DryRunActionAdapter
