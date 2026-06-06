"""Declarative adapter capability descriptors."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .adapter_mode import AdapterMode
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class AdapterCapabilityDescriptor:
    """Adapter capability facts; these facts do not grant permission."""

    capability_ref: TypedRef
    action_kinds: tuple[str, ...] = field(default_factory=tuple)
    envelope_types: tuple[str, ...] = ("adapter_input",)
    supported_modes: tuple[AdapterMode, ...] = (AdapterMode.NO_OP,)
    supports_prepare: bool = True
    supports_result_normalization: bool = True
    supports_failure_normalization: bool = True
    capability_only: bool = True
    l4_grants_permission: bool = False
    l4_scores_risk: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.action_kinds + self.envelope_types:
            ensure_short_text(item, "AdapterCapabilityDescriptor text", 128)
        ensure_true(self.capability_only, "AdapterCapabilityDescriptor.capability_only")
        ensure_false(self.l4_grants_permission, "AdapterCapabilityDescriptor.l4_grants_permission")
        ensure_false(self.l4_scores_risk, "AdapterCapabilityDescriptor.l4_scores_risk")
        ensure_schema_version(self.schema_version, "AdapterCapabilityDescriptor.schema_version")

    def structurally_supports(self, action_kind: str, envelope_type: str, mode: AdapterMode) -> bool:
        """Return structural support only; no permission or risk decision."""

        return (
            action_kind in self.action_kinds
            and envelope_type in self.envelope_types
            and mode in self.supported_modes
        )
