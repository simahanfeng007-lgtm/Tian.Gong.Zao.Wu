"""L3 resource budget preflight and pressure advice."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ActionBudgetPreflightAdvice:
    advice_ref: TypedRef
    action_ref: TypedRef | None = None
    budget_ref: TypedRef | None = None
    quota_ref: TypedRef | None = None
    rate_limit_ref: TypedRef | None = None
    resource_pressure_ref: TypedRef | None = None
    recommended_next_step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    reserves_budget: bool = False
    consumes_resource: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION


ResourcePressureDegradeAdvice = ActionBudgetPreflightAdvice
BudgetExhaustionReplanAdvice = ActionBudgetPreflightAdvice
