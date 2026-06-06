from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l2_state import (
    ActionBiasState,
    AffectiveBoundaryState,
    AffectiveBoundaryStatus,
    AffectiveColorState,
    DesireTendencyKind,
    DesireTendencyState,
    DynamicDriveEvaluationRefState,
    DynamicDriveKind,
    DynamicWeightState,
    EmotionBaseState,
    EmotionKind,
    EmotionTransientState,
    ExecutionReadinessState,
    ExplorationPressureState,
    ExpressionBiasState,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    MathAssessmentStatus,
    MathConstraintKind,
    MathConstraintState,
    MathEvaluationState,
    MathFeatureKind,
    MathFeatureState,
    MathModelRefState,
    MathObjectiveKind,
    MathObjectiveState,
    MathRecommendationState,
    MathScoreState,
    PreferenceWeightState,
    RiskPressureState,
    StabilityPressureState,
    SystemDriveState,
)


def ref(index: int, prefix: str = "phase9") -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref(index), ref_type)


def identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase9 fixture")


def build_math_objects():
    feature_ref = typed(10, "math_feature")
    objective_ref = typed(11, "math_objective")
    constraint_ref = typed(12, "math_constraint")
    score_ref = typed(13, "math_score")
    evaluation_ref = typed(14, "math_evaluation")
    return {
        "feature": MathFeatureState(
            identity=identity(100, L2StateKind.MATH),
            status=status(),
            feature_id=feature_ref,
            feature_kind=MathFeatureKind.GOAL_FIT,
            source_state_refs=(typed(15, "run"),),
            numeric_value=0.8,
            normalized_value=0.8,
            confidence=0.9,
            weight_hint=0.6,
            summary="math feature fixture",
        ),
        "objective": MathObjectiveState(
            identity=identity(101, L2StateKind.MATH),
            status=status(),
            objective_id=objective_ref,
            objective_kind=MathObjectiveKind.QUALITY,
            target_value=1.0,
            priority_weight=0.7,
            tolerance=0.1,
            source_ref=typed(16, "goal"),
            summary="math objective fixture",
        ),
        "constraint": MathConstraintState(
            identity=identity(102, L2StateKind.MATH),
            status=status(),
            constraint_id=constraint_ref,
            constraint_kind=MathConstraintKind.L5_REVIEW_REQUIRED,
            hard=True,
            limit_value=1.0,
            current_value=0.3,
            boundary_ref=typed(17, "boundary"),
            summary="math constraint fixture",
        ),
        "score": MathScoreState(
            identity=identity(103, L2StateKind.MATH),
            status=status(),
            score_id=score_ref,
            target_ref=typed(18, "candidate"),
            feature_refs=(feature_ref,),
            objective_refs=(objective_ref,),
            constraint_refs=(constraint_ref,),
            raw_score=0.75,
            normalized_score=0.75,
            confidence=0.8,
            penalty_total=0.1,
            bonus_total=0.2,
            score_status=MathAssessmentStatus.AVAILABLE,
            summary="math score fixture",
        ),
        "evaluation": MathEvaluationState(
            identity=identity(104, L2StateKind.MATH),
            status=status(),
            evaluation_id=evaluation_ref,
            evaluator_ref=typed(19, "math_model"),
            input_state_refs=(typed(20, "candidate"),),
            feature_refs=(feature_ref,),
            objective_refs=(objective_ref,),
            constraint_refs=(constraint_ref,),
            score_refs=(score_ref,),
            ranking_refs=(typed(21, "ranking"),),
            confidence=0.8,
            evaluation_status=MathAssessmentStatus.AVAILABLE,
            summary="math evaluation fixture",
        ),
        "recommendation": MathRecommendationState(
            identity=identity(105, L2StateKind.MATH),
            status=status(),
            recommendation_id=typed(22, "math_recommendation"),
            evaluation_ref=evaluation_ref,
            recommended_target_ref=typed(23, "candidate"),
            alternative_target_refs=(typed(24, "candidate"),),
            rejected_target_refs=(typed(25, "candidate"),),
            reason_summary="math recommendation fixture",
            confidence=0.8,
            required_boundary_refs=(typed(26, "boundary"),),
            required_execution_refs=(typed(27, "execution_request"),),
            state_update_suggestion_refs=(typed(28, "state_update"),),
            recommendation_status=MathAssessmentStatus.PARTIAL,
        ),
        "model_ref": MathModelRefState(
            identity=identity(106, L2StateKind.MATH),
            status=status(),
            model_ref_id=typed(29, "math_model"),
            model_name="weighted_state_vector",
            model_kind="state_scoring",
            scope="l3_reference",
            owner_layer="L3",
            deterministic=True,
            summary="math model ref fixture",
        ),
    }


def build_affective_objects():
    base_ref = typed(40, "emotion_base")
    transient_ref = typed(41, "emotion_transient")
    desire_ref = typed(42, "desire")
    expression_ref = typed(43, "expression_bias")
    action_ref = typed(44, "action_bias")
    color_ref = typed(45, "affective_color")
    return {
        "base": EmotionBaseState(
            identity=identity(200, L2StateKind.AFFECTIVE),
            status=status(),
            base_id=base_ref,
            emotion_weights=(("curiosity", 0.7), ("caution", 0.4)),
            stability=0.8,
            source_ref=typed(46, "source"),
            summary="emotion base fixture",
        ),
        "transient": EmotionTransientState(
            identity=identity(201, L2StateKind.AFFECTIVE),
            status=status(),
            transient_id=transient_ref,
            emotion_kind=EmotionKind.CURIOSITY,
            intensity=0.6,
            decay_hint=0.2,
            source_ref=typed(47, "observation"),
            confidence=0.8,
            summary="emotion transient fixture",
        ),
        "desire": DesireTendencyState(
            identity=identity(202, L2StateKind.AFFECTIVE),
            status=status(),
            desire_id=desire_ref,
            tendency_kind=DesireTendencyKind.LEARNING,
            intensity=0.7,
            priority_hint=0.6,
            source_ref=typed(48, "learning_signal"),
            confidence=0.8,
            summary="desire fixture",
        ),
        "expression_bias": ExpressionBiasState(
            identity=identity(203, L2StateKind.AFFECTIVE),
            status=status(),
            expression_bias_id=expression_ref,
            warmth_weight=0.3,
            clarity_weight=0.9,
            brevity_weight=0.7,
            encouragement_weight=0.2,
            caution_tone_weight=0.6,
            directness_weight=0.8,
            summary="expression bias fixture",
        ),
        "action_bias": ActionBiasState(
            identity=identity(204, L2StateKind.AFFECTIVE),
            status=status(),
            action_bias_id=action_ref,
            exploration_weight=0.5,
            caution_weight=0.6,
            persistence_weight=0.8,
            repair_weight=0.7,
            learning_weight=0.9,
            stability_weight=0.8,
            confirmation_preference_weight=0.6,
            summary="action bias fixture",
        ),
        "color": AffectiveColorState(
            identity=identity(205, L2StateKind.AFFECTIVE),
            status=status(),
            color_id=color_ref,
            base_ref=base_ref,
            transient_refs=(transient_ref,),
            desire_refs=(desire_ref,),
            expression_bias_ref=expression_ref,
            action_bias_ref=action_ref,
            total_intensity=0.7,
            stability_hint=0.8,
            confidence=0.8,
            summary="affective color fixture",
        ),
        "boundary": AffectiveBoundaryState(
            identity=identity(206, L2StateKind.AFFECTIVE),
            status=status(),
            boundary_id=typed(49, "affective_boundary"),
            affective_refs=(color_ref,),
            boundary_status=AffectiveBoundaryStatus.ENFORCED_BY_BOUNDARY,
            summary="affective boundary fixture",
        ),
    }


def build_dynamic_drive_objects():
    weight_ref = typed(70, "dynamic_weight")
    drive_ref = typed(71, "system_drive")
    pressure_ref = typed(72, "pressure")
    readiness_ref = typed(73, "readiness")
    return {
        "weight": DynamicWeightState(
            identity=identity(300, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            weight_id=weight_ref,
            drive_kind=DynamicDriveKind.LEARNING,
            value=0.7,
            source_refs=(typed(74, "math_evaluation"),),
            confidence=0.8,
            active=True,
            summary="dynamic weight fixture",
        ),
        "system_drive": SystemDriveState(
            identity=identity(301, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            drive_id=drive_ref,
            target_system="l3_orchestration",
            weight_refs=(weight_ref,),
            dominant_drive_kind=DynamicDriveKind.LEARNING,
            drive_balance_hint="learning dominant",
            confidence=0.8,
            summary="system drive fixture",
        ),
        "preference": PreferenceWeightState(
            identity=identity(302, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            preference_id=typed(75, "preference"),
            preference_kind="quality_first",
            weight_value=0.9,
            source_ref=typed(76, "user_alignment"),
            stability_hint=0.8,
            confidence=0.9,
            summary="preference fixture",
        ),
        "stability_pressure": StabilityPressureState(
            identity=identity(303, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            pressure_id=pressure_ref,
            target_refs=(typed(77, "candidate"),),
            pressure_value=0.5,
            instability_sources=(typed(78, "issue"),),
            recommended_bias_hint="prefer conservative ordering",
            confidence=0.8,
            summary="stability pressure fixture",
        ),
        "risk_pressure": RiskPressureState(
            identity=identity(304, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            pressure_id=typed(79, "pressure"),
            target_refs=(typed(80, "candidate"),),
            risk_value=0.4,
            risk_source_refs=(typed(81, "risk"),),
            l5_review_need_hint="review before later execution",
            confidence=0.8,
            summary="risk pressure fixture",
        ),
        "exploration_pressure": ExplorationPressureState(
            identity=identity(305, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            pressure_id=typed(82, "pressure"),
            target_refs=(typed(83, "candidate"),),
            novelty_value=0.6,
            information_gain_hint=0.7,
            learning_value_hint=0.8,
            confidence=0.8,
            summary="exploration pressure fixture",
        ),
        "readiness": ExecutionReadinessState(
            identity=identity(306, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            readiness_id=readiness_ref,
            target_refs=(typed(84, "candidate"),),
            required_boundary_refs=(typed(85, "boundary"),),
            required_execution_refs=(typed(86, "execution_request"),),
            required_context_refs=(typed(87, "context"),),
            readiness_score=0.5,
            missing_requirements=("boundary_review",),
            confidence=0.8,
            summary="readiness fixture",
        ),
        "evaluation_ref": DynamicDriveEvaluationRefState(
            identity=identity(307, L2StateKind.DYNAMIC_DRIVE),
            status=status(),
            evaluation_ref_id=typed(88, "dynamic_drive_evaluation"),
            math_evaluation_ref=typed(89, "math_evaluation"),
            system_drive_ref=drive_ref,
            affective_color_ref=typed(90, "affective_color"),
            target_refs=(typed(91, "candidate"),),
            summary="dynamic drive evaluation fixture",
        ),
    }


def build_all_phase9_objects():
    result = {}
    result.update({f"math_{key}": value for key, value in build_math_objects().items()})
    result.update({f"affective_{key}": value for key, value in build_affective_objects().items()})
    result.update({f"dynamic_{key}": value for key, value in build_dynamic_drive_objects().items()})
    return result
