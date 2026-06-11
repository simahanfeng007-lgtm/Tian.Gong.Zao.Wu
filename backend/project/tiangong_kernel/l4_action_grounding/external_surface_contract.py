"""Extended external action surface contracts for L4.

L4 only names the action surface and carries refs. Real database, browser, git,
build, test, sandbox, or storage behavior belongs to later hosted adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


REQUIRED_EXTERNAL_ACTION_SURFACES = (
    "model",
    "tool",
    "file",
    "network",
    "terminal",
    "desktop",
    "database",
    "browser",
    "git",
    "build",
    "test",
    "sandbox",
    "storage",
)


HIGH_RISK_EXTERNAL_ACTION_SURFACES = (
    "database",
    "browser",
    "git",
    "build",
    "test",
    "sandbox",
    "storage",
)


@dataclass(frozen=True, slots=True)
class ExternalSurfaceActionRequest:
    request_ref: TypedRef
    surface: str
    source_l3_request_ref: TypedRef | None = None
    source_l3_step_ref: TypedRef | None = None
    effect_intent_ref: TypedRef | None = None
    boundary_decision_ref: TypedRef | None = None
    lease_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    evidence_requirement_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    credential_scope_ref: TypedRef | None = None
    sandbox_policy_ref: TypedRef | None = None
    data_governance_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    executes_external_action: bool = False
    collapses_to_generic_terminal_or_network: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.surface, "ExternalSurfaceActionRequest.surface", 128)
        ensure_true(self.request_only, "ExternalSurfaceActionRequest.request_only")
        ensure_false(self.executes_external_action, "ExternalSurfaceActionRequest.executes_external_action")
        ensure_false(
            self.collapses_to_generic_terminal_or_network,
            "ExternalSurfaceActionRequest.collapses_to_generic_terminal_or_network",
        )
        ensure_schema_version(self.schema_version, "ExternalSurfaceActionRequest.schema_version")

    @property
    def has_production_chain_refs(self) -> bool:
        return all(
            ref is not None
            for ref in (
                self.source_l3_request_ref,
                self.source_l3_step_ref,
                self.effect_intent_ref,
                self.boundary_decision_ref,
                self.lease_ref,
                self.audit_requirement_ref,
                self.resource_budget_ref,
                self.credential_scope_ref,
            )
        )


@dataclass(frozen=True, slots=True)
class ExternalSurfaceActionResult:
    result_ref: TypedRef
    request_ref: TypedRef
    surface: str
    observation_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    resource_usage_report_ref: TypedRef | None = None
    cost_actual_ref: TypedRef | None = None
    result_only: bool = True
    real_action_performed: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.surface, "ExternalSurfaceActionResult.surface", 128)
        ensure_true(self.result_only, "ExternalSurfaceActionResult.result_only")
        ensure_false(self.real_action_performed, "ExternalSurfaceActionResult.real_action_performed")
        ensure_false(self.writes_l2_state, "ExternalSurfaceActionResult.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExternalSurfaceActionResult.schema_version")


@dataclass(frozen=True, slots=True)
class ExternalSurfaceActionFailure:
    failure_ref: TypedRef
    request_ref: TypedRef
    surface: str
    audit_requirement_ref: TypedRef | None = None
    evidence_ref: TypedRef | None = None
    recovery_requirement_ref: TypedRef | None = None
    failure_only: bool = True
    executes_recovery: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.surface, "ExternalSurfaceActionFailure.surface", 128)
        ensure_true(self.failure_only, "ExternalSurfaceActionFailure.failure_only")
        ensure_false(self.executes_recovery, "ExternalSurfaceActionFailure.executes_recovery")
        ensure_false(self.writes_l2_state, "ExternalSurfaceActionFailure.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExternalSurfaceActionFailure.schema_version")


@dataclass(frozen=True, slots=True)
class DisabledExternalSurfaceAdapterStub:
    stub_ref: TypedRef
    surface: str
    supports_fake: bool = True
    supports_dry_run: bool = True
    supports_no_op: bool = True
    disabled_real_stub: bool = True
    production_enabled: bool = False
    loads_real_adapter: bool = False
    executes_external_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.surface, "DisabledExternalSurfaceAdapterStub.surface", 128)
        ensure_true(self.supports_fake, "DisabledExternalSurfaceAdapterStub.supports_fake")
        ensure_true(self.supports_dry_run, "DisabledExternalSurfaceAdapterStub.supports_dry_run")
        ensure_true(self.supports_no_op, "DisabledExternalSurfaceAdapterStub.supports_no_op")
        ensure_true(self.disabled_real_stub, "DisabledExternalSurfaceAdapterStub.disabled_real_stub")
        ensure_false(self.production_enabled, "DisabledExternalSurfaceAdapterStub.production_enabled")
        ensure_false(self.loads_real_adapter, "DisabledExternalSurfaceAdapterStub.loads_real_adapter")
        ensure_false(self.executes_external_action, "DisabledExternalSurfaceAdapterStub.executes_external_action")
        ensure_schema_version(self.schema_version, "DisabledExternalSurfaceAdapterStub.schema_version")


EXTERNAL_SURFACE_CONTRACT_REGISTRY = {
    surface: ("request", "result", "failure", "port_protocol", "fake", "dry_run", "no_op", "disabled_real_stub")
    for surface in REQUIRED_EXTERNAL_ACTION_SURFACES
}
