"""Affective invariants for L6 phase4."""

from __future__ import annotations

from tiangong_kernel.l6_plugins.common.invariants import L6InvariantRule, L6InvariantSeverity


def default_l6_phase4_affective_invariant_rules() -> tuple[L6InvariantRule, ...]:
    refs = (
        "invariant:l6_phase4_affective_projection_is_not_fact",
        "invariant:l6_phase4_fatigue_projection_no_refusal",
        "invariant:l6_phase4_humanized_refusal_requires_governance_reason",
        "invariant:l6_phase4_resource_pressure_not_fatigue",
        "invariant:l6_phase4_affective_pollution_no_removal",
        "invariant:l6_phase4_affective_memory_hint_no_write",
        "invariant:l6_phase4_seven_emotions_no_permission_bypass",
        "invariant:l6_phase4_six_desires_no_action_dispatch",
        "invariant:l6_phase4_affective_public_projection_redaction",
        "invariant:l6_phase4_affective_reentry_goes_through_l3_l5",
        "invariant:l6_phase4_affective_score_not_decision",
    )
    return tuple(L6InvariantRule(ref, f"forbid:{ref.split(':', 1)[1]}", severity=L6InvariantSeverity.P0) for ref in refs)
