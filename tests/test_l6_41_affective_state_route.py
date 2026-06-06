from __future__ import annotations

import pytest

from tiangong_agent_runtime.affective_execution_route import AffectiveExecutionRoute, AffectiveExecutionRouter
from tiangong_agent_runtime.affective_pressure_bridge import AffectivePressureSnapshot
from tiangong_agent_runtime.affective_state import (
    AffectiveStateEngine,
    SevenEmotionSignalSources,
    SixDesireSignalSources,
)


def test_l6_41_seven_emotions_and_six_desires_have_exact_signal_sources() -> None:
    emotion_sources = SevenEmotionSignalSources()
    desire_sources = SixDesireSignalSources()
    assert tuple(emotion_sources.public_dict()) == (
        "joy_reward_signal",
        "obstruction_violation_signal",
        "uncertainty_future_risk_signal",
        "reflection_load_signal",
        "loss_failure_signal",
        "threat_irreversible_signal",
        "novelty_prediction_error_signal",
    )
    assert tuple(desire_sources.public_dict()) == (
        "survival_resource_boundary_signal",
        "curiosity_knowledge_gap_signal",
        "achievement_goal_gap_signal",
        "connection_alignment_signal",
        "order_entropy_signal",
        "rest_fatigue_recovery_signal",
    )
    with pytest.raises(ValueError):
        SevenEmotionSignalSources(joy_reward_signal=True)
    with pytest.raises(ValueError):
        SixDesireSignalSources(rest_fatigue_recovery_signal=True)


def test_l6_41_affective_state_is_dynamic_and_human_like_but_hint_only() -> None:
    engine = AffectiveStateEngine()
    first = engine.evolve(
        SevenEmotionSignalSources(
            joy_reward_signal=0.9,
            reflection_load_signal=0.6,
            novelty_prediction_error_signal=0.2,
        ),
        SixDesireSignalSources(
            achievement_goal_gap_signal=0.9,
            connection_alignment_signal=0.7,
            order_entropy_signal=0.6,
        ),
    )
    second = engine.evolve(
        SevenEmotionSignalSources(
            obstruction_violation_signal=0.8,
            uncertainty_future_risk_signal=0.7,
            threat_irreversible_signal=0.6,
            reflection_load_signal=0.8,
        ),
        SixDesireSignalSources(
            survival_resource_boundary_signal=0.8,
            order_entropy_signal=0.9,
            rest_fatigue_recovery_signal=0.5,
        ),
        previous_state=first,
        elapsed_seconds=600,
    )
    assert second.digest != first.digest
    assert second.emotion_vector.anger > first.emotion_vector.anger
    assert second.emotion_vector.fear > first.emotion_vector.fear
    assert second.desire_vector.survival > first.desire_vector.survival
    assert second.language_logic.risk_explanation_density > first.language_logic.risk_explanation_density
    assert second.no_authorization is True
    assert second.no_refusal_authority is True
    assert second.no_tool_dispatch is True
    assert second.no_model_dispatch is True
    assert second.no_budget_mutation is True


def test_l6_41_pressure_bridge_computes_sources_without_side_effects() -> None:
    snapshot = AffectivePressureSnapshot(
        success_signal=0.2,
        obstruction_signal=0.6,
        uncertainty_signal=0.7,
        reflection_load_signal=0.8,
        irreversible_threat_signal=0.4,
        novelty_signal=0.6,
        resource_pressure_signal=0.5,
        knowledge_gap_signal=0.9,
        goal_gap_signal=0.7,
        entropy_signal=0.8,
        fatigue_signal=0.4,
    )
    emotion = snapshot.to_emotion_sources()
    desire = snapshot.to_desire_sources()
    assert emotion.uncertainty_future_risk_signal == 0.7
    assert desire.curiosity_knowledge_gap_signal > 0.8
    assert desire.rest_fatigue_recovery_signal > 0.4
    with pytest.raises(ValueError):
        AffectivePressureSnapshot(fatigue_signal=True)


def test_l6_41_execution_route_separates_language_logic_and_doing_mode() -> None:
    state = AffectiveStateEngine().evolve(
        SevenEmotionSignalSources(
            uncertainty_future_risk_signal=0.9,
            reflection_load_signal=0.9,
            threat_irreversible_signal=0.5,
        ),
        SixDesireSignalSources(
            achievement_goal_gap_signal=0.9,
            order_entropy_signal=0.9,
            rest_fatigue_recovery_signal=0.2,
        ),
    )
    route = AffectiveExecutionRouter().route(state)
    payload = route.public_dict()
    assert payload["planner_consumable"] is True
    assert payload["not_authorization"] is True
    assert payload["not_refusal"] is True
    assert payload["no_tool_dispatch"] is True
    assert payload["no_model_dispatch"] is True
    assert payload["no_budget_mutation"] is True
    assert payload["no_quality_gate_override"] is True
    assert payload["planner_hint"]["language_state_logic"]["risk_explanation_density"] > 0.4
    assert payload["planner_hint"]["doing_mode_logic"]["task_closure_bias"] > 0.4
    assert "同风险等级内" in payload["planner_hint"]["candidate_priority_hint"]


def test_l6_41_rest_and_fatigue_only_pace_long_chain_not_refuse_or_charge_budget() -> None:
    state = AffectiveStateEngine().evolve(
        SevenEmotionSignalSources(reflection_load_signal=0.6, loss_failure_signal=0.3),
        SixDesireSignalSources(
            survival_resource_boundary_signal=0.6,
            achievement_goal_gap_signal=0.4,
            order_entropy_signal=0.5,
            rest_fatigue_recovery_signal=0.95,
        ),
    )
    route = AffectiveExecutionRouter().route(state)
    assert route.dominant_desire == "rest"
    assert route.planner_hint.long_chain_pacing_hint > 0.5
    assert route.planner_hint.not_refusal is True
    assert route.planner_hint.no_budget_mutation is True
    assert "不得拒绝合法请求" in route.planner_hint.candidate_priority_hint
    with pytest.raises(ValueError):
        AffectiveExecutionRoute(
            route_id="affective_route:bad",
            state_digest=state.digest,
            dominant_emotion=state.dominant_emotion,
            dominant_desire=state.dominant_desire,
            planner_hint=route.planner_hint,
            not_refusal=False,
        )


def test_l6_41_soul_baseline_plus_temporary_delta_equals_current_total() -> None:
    from tiangong_agent_runtime.affective_state import AffectiveBaseline, SoulAffectiveProfile

    baseline = AffectiveBaseline.from_soul_profile(
        SoulAffectiveProfile(
            soul_ref="affective:soul_profile:test_high_order",
            warmth=0.70,
            boundary_sensitivity=0.45,
            reflection_depth=0.82,
            resilience=0.66,
            novelty_openness=0.58,
            achievement_drive=0.78,
            connection_drive=0.60,
            order_drive=0.90,
            recovery_preference=0.20,
        )
    )
    state = AffectiveStateEngine().evolve(
        SevenEmotionSignalSources(
            joy_reward_signal=0.90,
            reflection_load_signal=0.85,
            novelty_prediction_error_signal=0.40,
        ),
        SixDesireSignalSources(
            achievement_goal_gap_signal=0.95,
            order_entropy_signal=0.88,
            connection_alignment_signal=0.72,
        ),
        soul_baseline=baseline,
    )
    assert state.affective_baseline.digest == baseline.digest
    assert state.affective_baseline.from_soul is True
    assert state.affective_baseline.raw_soul_visible is False
    assert state.composition_rule == "current_total = clamp01(soul_baseline + temporary_delta)"
    assert state.emotion_vector.joy == pytest.approx(
        min(1.0, max(0.0, baseline.emotion_baseline.joy + state.emotion_temporary_delta.joy))
    )
    assert state.desire_vector.achievement == pytest.approx(
        min(1.0, max(0.0, baseline.desire_baseline.achievement + state.desire_temporary_delta.achievement))
    )
    assert state.language_logic.no_permission_effect is True
    assert state.doing_logic.same_risk_ranking_only is True


def test_l6_41_soul_edit_resets_old_temporary_fluctuation() -> None:
    from tiangong_agent_runtime.affective_state import AffectiveBaseline, SoulAffectiveProfile

    baseline_a = AffectiveBaseline.from_soul_profile(
        SoulAffectiveProfile(soul_ref="affective:soul_profile:a", achievement_drive=0.90, order_drive=0.85)
    )
    baseline_b = AffectiveBaseline.from_soul_profile(
        SoulAffectiveProfile(soul_ref="affective:soul_profile:b", recovery_preference=0.80, achievement_drive=0.30)
    )
    engine = AffectiveStateEngine()
    first = engine.evolve(
        SevenEmotionSignalSources(joy_reward_signal=0.95, reflection_load_signal=0.80),
        SixDesireSignalSources(achievement_goal_gap_signal=0.95, order_entropy_signal=0.90),
        soul_baseline=baseline_a,
    )
    second = engine.evolve(
        SevenEmotionSignalSources(loss_failure_signal=0.20, reflection_load_signal=0.50),
        SixDesireSignalSources(rest_fatigue_recovery_signal=0.95),
        soul_baseline=baseline_b,
        previous_state=first,
        elapsed_seconds=60,
    )
    assert second.affective_baseline.digest == baseline_b.digest
    assert second.emotion_temporary_delta.joy < first.emotion_temporary_delta.joy
    assert second.desire_vector.rest > first.desire_vector.rest
    assert second.no_authorization is True
    assert second.no_refusal_authority is True
