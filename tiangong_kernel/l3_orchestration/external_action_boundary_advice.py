"""L3 advice for external action surfaces and sandbox boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ExternalActionBoundaryAdvice:
    advice_ref: TypedRef
    surface: str
    source_request_ref: TypedRef | None = None
    source_step_ref: TypedRef | None = None
    effect_intent_ref: TypedRef | None = None
    rollback_hint_ref: TypedRef | None = None
    audit_expectation_ref: TypedRef | None = None
    resource_budget_ref: TypedRef | None = None
    credential_scope_ref: TypedRef | None = None
    sandbox_policy_ref: TypedRef | None = None
    advisory_only: bool = True
    dispatches_action: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ExternalSurfaceCompletenessAdvice:
    advice_ref: TypedRef
    required_surface_names: tuple[str, ...] = field(default_factory=tuple)
    missing_surface_names: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION
