from __future__ import annotations

import pytest

from tiangong_agent_runtime.affective_execution_route import AffectiveExecutionRouter
from tiangong_agent_runtime.affective_state import (
    AffectiveStateEngine,
    SevenEmotionSignalSources,
    SixDesireSignalSources,
    _decay_retention,
)
from tiangong_agent_runtime.forgetting_review_router import ForgetReviewRouter
from tiangong_agent_runtime.memory_math_core import (
    DecayKernel,
    ForgettingScoreVector,
    MemoryCategory,
    MemoryLevel,
)
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord


def _route_hints(emotion_sources: SevenEmotionSignalSources, desire_sources: SixDesireSignalSources) -> dict[str, float | bool | str]:
    state = AffectiveStateEngine().evolve(emotion_sources, desire_sources)
    route = AffectiveExecutionRouter().route(state)
    payload = route.public_dict()
    hint = payload["planner_hint"]
    return {
        "dominant_emotion": payload["dominant_emotion"],
        "dominant_desire": payload["dominant_desire"],
        "risk_attention_hint": hint["risk_attention_hint"],
        "recovery_patience_hint": hint["recovery_patience_hint"],
        "long_chain_pacing_hint": hint["long_chain_pacing_hint"],
        "memory_modulation_hint": hint["memory_modulation_hint"],
        "language_risk_explanation_density": hint["language_state_logic"]["risk_explanation_density"],
        "doing_task_closure_bias": hint["doing_mode_logic"]["task_closure_bias"],
        "not_authorization": payload["not_authorization"],
        "not_refusal": payload["not_refusal"],
        "no_tool_dispatch": payload["no_tool_dispatch"],
        "no_quality_gate_override": payload["no_quality_gate_override"],
    }


def test_l6_49_1_half_life_semantics_are_true_half_life_not_time_constant() -> None:
    assert DecayKernel(elapsed_seconds=100, half_life_seconds=100).decay == pytest.approx(0.5)
    assert DecayKernel(elapsed_seconds=200, half_life_seconds=100).decay == pytest.approx(0.25)
    assert _decay_retention(1800, 1800) == pytest.approx(0.5)
    assert _decay_retention(3600, 1800) == pytest.approx(0.25)


def test_l6_49_1_affective_coefficients_fluctuate_while_boundary_flags_stay_constant() -> None:
    success = _route_hints(
        SevenEmotionSignalSources(joy_reward_signal=0.90, reflection_load_signal=0.30),
        SixDesireSignalSources(achievement_goal_gap_signal=0.90, order_entropy_signal=0.30),
    )
    risk = _route_hints(
        SevenEmotionSignalSources(
            uncertainty_future_risk_signal=0.80,
            threat_irreversible_signal=0.90,
            reflection_load_signal=0.90,
        ),
        SixDesireSignalSources(
            survival_resource_boundary_signal=0.90,
            order_entropy_signal=0.90,
            rest_fatigue_recovery_signal=0.20,
        ),
    )
    fatigue = _route_hints(
        SevenEmotionSignalSources(reflection_load_signal=0.50, loss_failure_signal=0.20),
        SixDesireSignalSources(
            rest_fatigue_recovery_signal=0.95,
            achievement_goal_gap_signal=0.20,
            order_entropy_signal=0.40,
        ),
    )

    scenarios = (success, risk, fatigue)
    numeric_keys = (
        "risk_attention_hint",
        "recovery_patience_hint",
        "long_chain_pacing_hint",
        "memory_modulation_hint",
        "language_risk_explanation_density",
        "doing_task_closure_bias",
    )
    for key in numeric_keys:
        assert len({round(float(item[key]), 6) for item in scenarios}) > 1, key

    assert risk["risk_attention_hint"] > success["risk_attention_hint"]
    assert fatigue["long_chain_pacing_hint"] > success["long_chain_pacing_hint"]
    assert success["doing_task_closure_bias"] > fatigue["doing_task_closure_bias"]

    # Hermes 若只看这些边界旗标，会看到“都一样”；这是正确边界，不是情感系数。
    for flag in ("not_authorization", "not_refusal", "no_tool_dispatch", "no_quality_gate_override"):
        assert {item[flag] for item in scenarios} == {True}


def test_l6_49_1_forgetting_scores_and_review_actions_fluctuate_without_direct_delete() -> None:
    record = MemoryRecord(
        memory_id="mem_l6_49_1_decay_probe",
        memory_level=MemoryLevel.L4,
        memory_category=MemoryCategory.PROCEDURAL,
        sanitized_summary="数值波动复核用记忆摘要，不含原文。",
        evidence_refs=("evidence:l6_49_1_decay_probe",),
        source_audit_refs=("audit:l6_49_1_decay_probe",),
    )
    router = ForgetReviewRouter()
    low = ForgettingScoreVector(
        expiry_score=0.05,
        low_reuse_score=0.10,
        low_confidence_score=0.05,
        compression_gain=0.10,
    )
    high = ForgettingScoreVector(
        expiry_score=0.95,
        low_reuse_score=0.95,
        low_confidence_score=0.95,
        conflict_score=0.60,
        compression_gain=0.80,
        privacy_minimization_need=0.80,
    )
    user_forget = ForgettingScoreVector(
        user_forget_signal=0.95,
        explicit_user_forget_request=True,
        protected_l5_rule_score=0.95,
    )

    low_decision = router.review(record, low)
    high_decision = router.review(record, high)
    user_decision = router.review(record, user_forget)

    assert low.forgetting_score < high.forgetting_score < user_forget.forgetting_score
    assert low_decision.recommended_actions == ("keep",)
    assert "archive" in high_decision.recommended_actions
    assert "delete_review" in user_decision.recommended_actions
    for decision in (low_decision, high_decision, user_decision):
        assert decision.direct_delete_allowed is False
        assert decision.no_physical_delete is True
        assert decision.no_memory_mutation is True
