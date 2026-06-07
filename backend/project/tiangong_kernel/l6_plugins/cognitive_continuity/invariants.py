"""L6 phase4 invariants for cognitive continuity."""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.invariants import L6InvariantRule, L6InvariantSeverity


def default_l6_phase4_invariant_rules() -> tuple[L6InvariantRule, ...]:
    invariant_refs = (
        "invariant:l6_phase4_cognitive_group_is_not_runtime",
        "invariant:l6_phase4_context_projection_is_not_prompt_injection",
        "invariant:l6_phase4_memory_candidate_is_not_write",
        "invariant:l6_phase4_forgetting_candidate_is_not_removal",
        "invariant:l6_phase4_user_forget_goes_to_review",
        "invariant:l6_phase4_tombstone_is_proposal_only",
        "invariant:l6_phase4_active_recall_suppression_is_proposal_only",
        "invariant:l6_phase4_belief_world_candidate_is_not_fact",
        "invariant:l6_phase4_cognitive_reentry_requires_l3_l5",
        "invariant:l6_phase4_affective_projection_is_not_fact",
        "invariant:l6_phase4_fatigue_projection_is_not_refusal_authority",
        "invariant:l6_phase4_humanized_refusal_requires_governance_reason",
        "invariant:l6_phase4_affective_public_projection_minimal",
        "invariant:l6_phase4_affective_score_is_not_decision",
        "invariant:l6_phase4_product_bridge_seed_is_inert",
    )
    return tuple(
        L6InvariantRule(ref, f"forbid:{ref.split(':', 1)[1]}", severity=L6InvariantSeverity.P0)
        for ref in invariant_refs
    )
