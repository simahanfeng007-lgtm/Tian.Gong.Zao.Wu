"""L6 invariant declarations and inert check result containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


class L6InvariantSeverity(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


@dataclass(frozen=True, slots=True)
class L6InvariantRule:
    invariant_ref: str
    assertion_ref: str
    severity: L6InvariantSeverity | str = L6InvariantSeverity.P0
    evidence_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_invariant_evidence_required",))
    blocking_when_failed: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.invariant_ref, "L6InvariantRule.invariant_ref")
        ensure_ref_text(self.assertion_ref, "L6InvariantRule.assertion_ref")
        object.__setattr__(self, "severity", L6InvariantSeverity(self.severity))
        ensure_ref_items(self.evidence_requirement_refs, "L6InvariantRule.evidence_requirement_refs", required=True)
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6InvariantCheckResult:
    result_ref: str
    invariant_ref: str
    passed: bool
    reason_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.result_ref, "L6InvariantCheckResult.result_ref")
        ensure_ref_text(self.invariant_ref, "L6InvariantCheckResult.invariant_ref")
        ensure_ref_items(self.reason_refs, "L6InvariantCheckResult.reason_refs")
        ensure_ref_items(self.evidence_refs, "L6InvariantCheckResult.evidence_refs")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6InvariantSuite:
    suite_ref: str = "invariant:l6_common_invariant_suite"
    rules: tuple[L6InvariantRule, ...] = field(default_factory=tuple)
    result_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.suite_ref, "L6InvariantSuite.suite_ref")
        for rule in self.rules:
            if not isinstance(rule, L6InvariantRule):
                raise ValueError("L6InvariantSuite.rules must contain L6InvariantRule")
        ensure_ref_items(self.result_refs, "L6InvariantSuite.result_refs")
        ensure_schema_version(self.schema_version)


def default_l6_invariant_rules() -> tuple[L6InvariantRule, ...]:
    assertions = (
        ("invariant:l6_lifecycle_is_not_authorization", "forbid:lifecycle_as_authorization"),
        ("invariant:l6_active_is_not_permit", "forbid:active_as_permit"),
        ("invariant:l6_ready_for_orchestration_is_not_permit", "forbid:orchestration_ready_as_permit"),
        ("invariant:l6_event_is_not_execution", "forbid:event_as_execution"),
        ("invariant:l6_event_replay_is_not_action_replay", "forbid:event_replay_as_action_replay"),
        ("invariant:l6_projection_is_not_l2_fact", "forbid:projection_as_l2_fact"),
        ("invariant:l6_handoff_is_not_auto_merge", "forbid:handoff_as_auto_merge"),
        ("invariant:l6_handoff_is_not_direct_plugin_call", "forbid:handoff_direct_plugin_call"),
        ("invariant:l6_requirement_not_permission", "forbid:requirement_as_permission"),
        ("invariant:l6_compatibility_matrix_is_not_permit", "forbid:compatibility_matrix_as_permit"),
        ("invariant:l6_migration_plan_is_not_migration_execution", "forbid:migration_plan_as_execution"),
        ("invariant:l6_rollback_route_is_not_rollback_execution", "forbid:rollback_route_as_execution"),
        ("invariant:l6_hot_switch_readiness_is_not_hot_switch_execution", "forbid:hot_switch_readiness_as_execution"),
        ("invariant:l6_replay_compatibility_is_not_replay_execution", "forbid:replay_compatibility_as_execution"),
        ("invariant:l6_no_plugin_direct_import", "forbid:direct_plugin_import"),
        ("invariant:l6_no_plugin_direct_call", "forbid:direct_plugin_call"),
        ("invariant:l6_no_cross_plugin_state_write", "forbid:cross_plugin_state_write"),
        ("invariant:l6_no_parallel_runtime", "forbid:parallel_runtime"),
        ("invariant:l6_no_live_provider", "forbid:live_provider"),
        ("invariant:l6_no_raw_tool_call", "forbid:raw_tool_call"),
        ("invariant:l6_no_direct_l4_adapter_call", "forbid:direct_l4_adapter"),
        ("invariant:l6_no_direct_l2_write", "forbid:direct_l2_write"),
        ("invariant:l6_no_raw_secret", "forbid:raw_secret"),
        ("invariant:l6_public_projection_minimal_disclosure", "forbid:public_projection_leak"),
    )
    return tuple(L6InvariantRule(invariant_ref, assertion_ref) for invariant_ref, assertion_ref in assertions)
