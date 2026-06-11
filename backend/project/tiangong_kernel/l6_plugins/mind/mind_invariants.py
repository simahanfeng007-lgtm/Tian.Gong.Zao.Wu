"""L6 phase3 mind invariants."""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.invariants import L6InvariantRule


def default_l6_phase3_mind_invariant_rules() -> tuple[L6InvariantRule, ...]:
    assertions = (
        ("invariant:mind_plugin_is_not_runtime", "forbid:mind_plugin_as_runtime"),
        ("invariant:mind_state_is_not_l2_fact", "forbid:mind_state_as_l2_fact"),
        ("invariant:belief_is_not_fact", "forbid:belief_as_fact"),
        ("invariant:world_candidate_is_not_canonical_state", "forbid:world_candidate_as_canonical_state"),
        ("invariant:goal_priority_is_not_execution_plan", "forbid:goal_priority_as_plan"),
        ("invariant:attention_focus_is_not_interrupt_command", "forbid:attention_focus_as_interrupt"),
        ("invariant:affective_state_is_not_permission", "forbid:affective_state_as_permission"),
        ("invariant:fatigue_projection_is_not_refusal_authority", "forbid:fatigue_projection_as_refusal_authority"),
        ("invariant:requirement_is_not_authorization", "forbid:requirement_as_authorization"),
        ("invariant:projection_is_not_fact", "forbid:projection_as_fact"),
        ("invariant:readiness_is_not_permit", "forbid:readiness_as_permit"),
        ("invariant:quality_gate_is_not_permit", "forbid:quality_gate_as_permit"),
        ("invariant:event_is_not_execution", "forbid:event_as_execution"),
        ("invariant:handoff_is_not_auto_merge", "forbid:handoff_as_auto_merge"),
        ("invariant:score_is_not_decision", "forbid:score_as_decision"),
        ("invariant:suggestion_is_not_command", "forbid:suggestion_as_command"),
        ("invariant:no_live_model_call", "forbid:live_model_call"),
        ("invariant:no_raw_tool_call", "forbid:raw_tool_call"),
        ("invariant:no_direct_l4_adapter_call", "forbid:direct_l4_adapter"),
        ("invariant:no_direct_l2_write", "forbid:direct_l2_write"),
        ("invariant:no_direct_memory_write", "forbid:direct_memory_write"),
        ("invariant:no_direct_audit_write", "forbid:direct_audit_write"),
        ("invariant:no_direct_budget_charge", "forbid:direct_budget_charge"),
        ("invariant:no_raw_secret", "forbid:raw_secret"),
        ("invariant:no_provider_base_url_or_api_key", "forbid:provider_locator_or_key"),
        ("invariant:no_plugin_direct_import_call_state_write", "forbid:plugin_direct_coupling"),
        ("invariant:no_parallel_runtime", "forbid:parallel_runtime"),
        ("invariant:public_projection_minimal_disclosure", "forbid:public_projection_leak"),
        ("invariant:affective_refusal_requires_governance_reason", "forbid:affective_refusal_without_governance"),
        ("invariant:pollution_defense_is_not_value_dictatorship", "forbid:pollution_defense_as_value_dictatorship"),
    )
    return tuple(L6InvariantRule(invariant_ref, assertion_ref) for invariant_ref, assertion_ref in assertions)
