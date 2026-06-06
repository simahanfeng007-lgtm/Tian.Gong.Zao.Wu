"""Shared descriptor helpers for phase 5 external adapters."""

from __future__ import annotations

from .adapter_capability import AdapterCapabilityDescriptor
from .adapter_descriptor import AdapterDescriptor, AdapterIdentity
from .adapter_failure import new_adapter_typed_ref
from .adapter_mode import AdapterMode
from .adapter_risk_surface import AdapterRiskSurfaceDescriptor


def external_adapter_descriptor(
    *,
    adapter_id: str,
    adapter_kind: str,
    adapter_name: str,
    action_kind: str,
    envelope_type: str,
    mode: AdapterMode,
    side_effect_declared: str,
    resource_usage_declared: str,
    audit_requirement_declared: str,
    supports_fake: bool = False,
    supports_dry_run: bool = False,
    supports_no_op: bool = False,
    requires_l5_permit: bool = False,
    enabled_by_default: bool = True,
    production_enabled: bool = False,
    test_only: bool = False,
) -> AdapterDescriptor:
    capability = AdapterCapabilityDescriptor(
        capability_ref=new_adapter_typed_ref("adapter_capability"),
        action_kinds=(action_kind,),
        envelope_types=(envelope_type,),
        supported_modes=(mode,),
    )
    risk = AdapterRiskSurfaceDescriptor(
        risk_surface_ref=new_adapter_typed_ref("adapter_risk_surface"),
        side_effect_declared=side_effect_declared,
        resource_usage_declared=resource_usage_declared,
        audit_requirement_declared=audit_requirement_declared,
    )
    return AdapterDescriptor(
        identity=AdapterIdentity(
            adapter_ref=new_adapter_typed_ref("adapter"),
            adapter_id=adapter_id,
            adapter_kind=adapter_kind,
        ),
        adapter_name=adapter_name,
        mode=mode,
        capability_descriptor=capability,
        risk_surface_descriptor=risk,
        supported_action_kinds=capability.action_kinds,
        supported_envelope_types=capability.envelope_types,
        requires_l5_permit=requires_l5_permit,
        supports_fake=supports_fake,
        supports_dry_run=supports_dry_run,
        supports_no_op=supports_no_op,
        enabled_by_default=enabled_by_default,
        production_enabled=production_enabled,
        test_only=test_only,
        side_effect_declared=side_effect_declared,
        resource_usage_declared=resource_usage_declared,
        audit_requirement_declared=audit_requirement_declared,
    )
