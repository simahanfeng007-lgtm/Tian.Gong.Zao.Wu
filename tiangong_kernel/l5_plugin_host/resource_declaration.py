"""Declarative resource, cost, quota, and rate-limit requirements."""

from __future__ import annotations

from dataclasses import dataclass

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_text, ensure_schema_version
from .phase2_common import ensure_no_unbounded_resource_text


@dataclass(frozen=True, slots=True)
class PluginResourceDeclaration:
    cpu_budget_ref: str = ""
    memory_budget_ref: str = ""
    io_budget_ref: str = ""
    network_budget_ref: str = ""
    concurrency_budget_ref: str = ""
    rate_limit_ref: str = ""
    cost_budget_ref: str = ""
    run_budget_scope_ref: str = ""
    goal_budget_scope_ref: str = ""
    actor_budget_scope_ref: str = ""
    budget_owner_ref: str = ""
    quota_ref: str = ""
    resource_pressure_policy_ref: str = ""
    degradation_policy_ref: str = ""
    exhaustion_behavior_ref: str = ""
    metering_policy_ref: str = ""
    high_permission_does_not_bypass_budget: bool = True
    budget_consumed: bool = False
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "cpu_budget_ref",
            "memory_budget_ref",
            "io_budget_ref",
            "network_budget_ref",
            "concurrency_budget_ref",
            "rate_limit_ref",
            "cost_budget_ref",
            "run_budget_scope_ref",
            "goal_budget_scope_ref",
            "actor_budget_scope_ref",
            "budget_owner_ref",
            "quota_ref",
            "resource_pressure_policy_ref",
            "degradation_policy_ref",
            "exhaustion_behavior_ref",
            "metering_policy_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginResourceDeclaration.{name}", required=False)
        ensure_bool(self.high_permission_does_not_bypass_budget, "PluginResourceDeclaration.high_permission_does_not_bypass_budget")
        ensure_bool(self.budget_consumed, "PluginResourceDeclaration.budget_consumed")
        if self.budget_consumed:
            raise ValueError("PluginResourceDeclaration must not consume budgets")
        if not self.high_permission_does_not_bypass_budget:
            raise ValueError("high permission declarations must not bypass budget controls")
        ensure_no_unbounded_resource_text(self, "PluginResourceDeclaration")
        ensure_schema_version(self.schema_version, "PluginResourceDeclaration.schema_version")
