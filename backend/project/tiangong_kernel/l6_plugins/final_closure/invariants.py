"""L6 phase8 unified invariant suite."""
from __future__ import annotations
from dataclasses import dataclass, field
from .common import FinalClosureArtifactBase

L6_PHASE8_INVARIANTS = (
    "l6_is_not_runtime", "l6_plugin_is_not_executor", "requirement_is_not_permit", "readiness_is_not_authorization",
    "lifecycle_is_not_authorization", "event_is_not_execution", "projection_is_not_fact", "handoff_is_not_auto_merge",
    "score_is_not_decision", "suggestion_is_not_command", "candidate_is_not_execution", "review_request_is_not_execution",
    "quality_gate_is_not_permit", "public_projection_is_not_callable", "mind_state_is_not_l2_fact", "belief_candidate_is_not_fact",
    "world_candidate_is_not_canonical_state", "affective_state_is_not_permission", "fatigue_projection_is_not_refusal_authority",
    "memory_proposal_is_not_memory_write", "forgetting_candidate_is_not_delete", "governance_plugin_is_not_l5",
    "risk_projection_is_not_decision", "budget_requirement_is_not_allocation", "audit_requirement_is_not_audit_write",
    "credential_requirement_ref_is_not_secret_access", "product_seed_is_not_product_spec", "product_plan_candidate_is_not_execution_plan",
    "delivery_package_candidate_is_not_zip", "product_dispatch_intent_is_not_execution", "learning_need_review_is_not_learning_execution",
    "skill_candidate_is_not_registered_skill", "repair_plan_candidate_is_not_code_patch", "iteration_proposal_is_not_apply",
    "collaboration_plan_is_not_plugin_dispatch", "handoff_aggregation_is_not_auto_merge", "conflict_resolution_suggestion_is_not_decision",
    "no_live_model_call", "no_raw_tool_call", "no_direct_l4_adapter_call", "no_direct_file_write", "no_direct_zip_creation",
    "no_direct_test_execution", "no_direct_l2_write", "no_direct_memory_write", "no_direct_memory_delete", "no_direct_audit_write",
    "no_direct_budget_charge", "no_raw_secret", "no_provider_base_url_or_api_key", "no_plugin_direct_import_call_state_write",
    "no_parallel_runtime", "no_parallel_agent_scheduler", "no_old_runtime_or_abilitypackage_backflow", "public_projection_minimal_disclosure",
    "execution_first_does_not_bypass_hard_boundaries", "low_risk_should_continue", "reversible_candidate_should_continue",
    "governance_should_summarize_not_interrupt", "long_chain_should_degrade_not_abort", "confirmation_should_batch_when_safe",
    "product_delivery_should_continue_when_low_risk", "adaptive_failure_should_recover_not_abort", "l6_freeze_requires_planner_review",
    "final_freeze_requires_total_repair_after_planner_review", "full_pytest_must_not_be_faked",
)

@dataclass(frozen=True)
class L6Phase8InvariantSuite(FinalClosureArtifactBase):
    object_ref: str = "invariant:l6_phase8_unified_suite"
    invariant_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"invariant:{name}" for name in L6_PHASE8_INVARIANTS))
    def __post_init__(self) -> None:
        super().__post_init__()
        if len(self.invariant_refs) < 66: raise ValueError("Phase8 invariant suite must cover all global invariants")
