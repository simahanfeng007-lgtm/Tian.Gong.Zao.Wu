"""No L6 implementation guarantee for L4 phase 8 closure."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from ._common import L4_EXECUTION_CLOSURE_SCHEMA_VERSION, L4_L6_SURFACES, ensure_false, ensure_schema_version, ensure_text_items, ensure_true


@dataclass(frozen=True, slots=True)
class L4NoL6ImplementationGuarantee:
    """Guarantee that L4 exposes requirements only and implements no L6 service."""

    guarantee_ref: TypedRef
    covered_l6_surfaces: tuple[str, ...] = field(default_factory=lambda: L4_L6_SURFACES + ("plugin_host",))
    guarantee_only: bool = True
    implements_l6_service: bool = False
    implements_adapter: bool = False
    implements_observation_system: bool = False
    implements_recovery_system: bool = False
    implements_replay_system: bool = False
    hosts_plugins: bool = False
    hosts_connectors: bool = False
    schema_version: str = L4_EXECUTION_CLOSURE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_text_items(self.covered_l6_surfaces, "L4NoL6ImplementationGuarantee.covered_l6_surfaces", 128)
        ensure_true(self.guarantee_only, "L4NoL6ImplementationGuarantee.guarantee_only")
        ensure_false(self.implements_l6_service, "L4NoL6ImplementationGuarantee.implements_l6_service")
        ensure_false(self.implements_adapter, "L4NoL6ImplementationGuarantee.implements_adapter")
        ensure_false(self.implements_observation_system, "L4NoL6ImplementationGuarantee.implements_observation_system")
        ensure_false(self.implements_recovery_system, "L4NoL6ImplementationGuarantee.implements_recovery_system")
        ensure_false(self.implements_replay_system, "L4NoL6ImplementationGuarantee.implements_replay_system")
        ensure_false(self.hosts_plugins, "L4NoL6ImplementationGuarantee.hosts_plugins")
        ensure_false(self.hosts_connectors, "L4NoL6ImplementationGuarantee.hosts_connectors")
        ensure_schema_version(self.schema_version, "L4NoL6ImplementationGuarantee.schema_version")
