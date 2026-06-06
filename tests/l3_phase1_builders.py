from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.result import ok
from tiangong_kernel.l1_ports import PortDirection, PortIdentity, PortKind, PortName, PortPlane, PortRequest, PortVisibility
from tiangong_kernel.l2_state import (
    ActionBiasState,
    AffectiveColorState,
    DynamicDriveKind,
    DynamicWeightState,
    ExecutionReadinessState,
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
    MathObjectiveKind,
    MathObjectiveState,
    MathRecommendationState,
    MathScoreState,
    ProjectionStatus,
    RuntimeSliceProjectionState,
    SystemDriveState,
)
from tiangong_kernel.l3_orchestration import (
    AffectiveWeightInput,
    DynamicDriveInput,
    MathConstraintSet,
    MathEvaluation,
    MathFeatureVector,
    MathObjectiveVector,
    MathOrchestrationInput,
    MathRecommendation,
    MathScoreVector,
    OrchestrationContext,
    OrchestrationIdentity,
    OrchestrationObjectKind,
    OrchestrationPlan,
    OrchestrationRequest,
    OrchestrationRequestKind,
    OrchestrationResult,
    OrchestrationResultKind,
    OrchestrationStatus,
    OrchestrationStatusKind,
    OrchestrationStep,
    OrchestrationStepKind,
    RankingOrder,
    RecommendationMode,
    RouteRanking,
    ScoreDirection,
    StateTransitionAdvice,
)


def ref(index: int, prefix: str = "l3") -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref(index), ref_type)


def l2_identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed(index, kind.value), kind=kind)


def l2_status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="l3 phase1 fixture")


def orch_identity(index: int, kind: OrchestrationObjectKind) -> OrchestrationIdentity:
    return OrchestrationIdentity(orchestration_ref=typed(index, kind.value), object_kind=kind)


def orch_status(kind: OrchestrationStatusKind = OrchestrationStatusKind.DECLARED) -> OrchestrationStatus:
    return OrchestrationStatus(kind=kind, reason="l3 phase1 fixture", confidence=0.8)


def port_request() -> PortRequest:
    target_port = PortIdentity(
        port_id=ref(900, "port"),
        name=PortName("l3_phase1_target"),
        kind=PortKind.CONTROL,
        plane=PortPlane.CONTROL,
        direction=PortDirection.INBOUND,
        visibility=PortVisibility.INTERNAL,
    )
    return PortRequest(request_id=ref(901, "req"), target_port=target_port)


def build_l2_math_states():
    feature_ref = typed(10, "math_feature")
    objective_ref = typed(11, "math_objective")
    constraint_ref = typed(12, "math_constraint")
    score_ref = typed(13, "math_score")
    evaluation_ref = typed(14, "math_evaluation")
    return {
        "feature": MathFeatureState(
            identity=l2_identity(100, L2StateKind.MATH),
            status=l2_status(),
            feature_id=feature_ref,
            feature_kind=MathFeatureKind.GOAL_FIT,
            normalized_value=0.8,
            confidence=0.9,
            summary="feature fixture",
        ),
        "objective": MathObjectiveState(
            identity=l2_identity(101, L2StateKind.MATH),
            status=l2_status(),
            objective_id=objective_ref,
            objective_kind=MathObjectiveKind.QUALITY,
            target_value=1.0,
            priority_weight=0.7,
            tolerance=0.1,
            summary="objective fixture",
        ),
        "constraint": MathConstraintState(
            identity=l2_identity(102, L2StateKind.MATH),
            status=l2_status(),
            constraint_id=constraint_ref,
            constraint_kind=MathConstraintKind.L5_REVIEW_REQUIRED,
            hard=True,
            limit_value=1.0,
            current_value=0.4,
            summary="constraint fixture",
        ),
        "score": MathScoreState(
            identity=l2_identity(103, L2StateKind.MATH),
            status=l2_status(),
            score_id=score_ref,
            target_ref=typed(18, "candidate"),
            feature_refs=(feature_ref,),
            objective_refs=(objective_ref,),
            constraint_refs=(constraint_ref,),
            normalized_score=0.75,
            confidence=0.8,
            score_status=MathAssessmentStatus.AVAILABLE,
            summary="score fixture",
        ),
        "evaluation_state": MathEvaluationState(
            identity=l2_identity(104, L2StateKind.MATH),
            status=l2_status(),
            evaluation_id=evaluation_ref,
            feature_refs=(feature_ref,),
            objective_refs=(objective_ref,),
            constraint_refs=(constraint_ref,),
            score_refs=(score_ref,),
            confidence=0.8,
            evaluation_status=MathAssessmentStatus.AVAILABLE,
            summary="evaluation fixture",
        ),
        "recommendation_state": MathRecommendationState(
            identity=l2_identity(105, L2StateKind.MATH),
            status=l2_status(),
            recommendation_id=typed(22, "math_recommendation"),
            evaluation_ref=evaluation_ref,
            recommended_target_ref=typed(23, "candidate"),
            confidence=0.8,
            required_boundary_refs=(typed(26, "boundary"),),
            required_execution_refs=(typed(27, "execution_request"),),
            recommendation_status=MathAssessmentStatus.PARTIAL,
        ),
    }


def build_l2_affective_states():
    return {
        "action_bias": ActionBiasState(
            identity=l2_identity(200, L2StateKind.AFFECTIVE),
            status=l2_status(),
            action_bias_id=typed(40, "action_bias"),
            exploration_weight=0.5,
            caution_weight=0.6,
            persistence_weight=0.8,
            learning_weight=0.9,
            stability_weight=0.8,
            summary="action bias fixture",
        ),
        "color": AffectiveColorState(
            identity=l2_identity(201, L2StateKind.AFFECTIVE),
            status=l2_status(),
            color_id=typed(41, "affective_color"),
            action_bias_ref=typed(40, "action_bias"),
            total_intensity=0.7,
            confidence=0.8,
            summary="color fixture",
        ),
    }


def build_l2_dynamic_states():
    weight = DynamicWeightState(
        identity=l2_identity(300, L2StateKind.DYNAMIC_DRIVE),
        status=l2_status(),
        weight_id=typed(70, "dynamic_weight"),
        drive_kind=DynamicDriveKind.LEARNING,
        value=0.7,
        confidence=0.8,
        summary="dynamic weight fixture",
    )
    return {
        "weight": weight,
        "drive": SystemDriveState(
            identity=l2_identity(301, L2StateKind.DYNAMIC_DRIVE),
            status=l2_status(),
            drive_id=typed(71, "system_drive"),
            target_system="l3_orchestration",
            weight_refs=(weight.identity.state_ref,),
            dominant_drive_kind=DynamicDriveKind.LEARNING,
            confidence=0.8,
            summary="system drive fixture",
        ),
        "readiness": ExecutionReadinessState(
            identity=l2_identity(302, L2StateKind.DYNAMIC_DRIVE),
            status=l2_status(),
            readiness_id=typed(72, "readiness"),
            readiness_score=0.4,
            confidence=0.7,
            required_boundary_refs=(typed(73, "boundary"),),
            missing_requirements=("boundary_review",),
            summary="readiness fixture",
        ),
    }


def build_l3_objects():
    math_states = build_l2_math_states()
    affective_states = build_l2_affective_states()
    dynamic_states = build_l2_dynamic_states()
    feature_vector = MathFeatureVector(
        vector_ref=typed(500, "math_feature_vector"),
        feature_entries=((MathFeatureKind.GOAL_FIT, 0.8),),
        source_feature_refs=(math_states["feature"].feature_id,),
        confidence=0.8,
    )
    objective_vector = MathObjectiveVector(
        vector_ref=typed(501, "math_objective_vector"),
        objective_entries=((MathObjectiveKind.QUALITY, 0.7),),
        objective_refs=(math_states["objective"].objective_id,),
        confidence=0.8,
    )
    constraint_set = MathConstraintSet(
        constraint_set_ref=typed(502, "math_constraint_set"),
        constraint_entries=((MathConstraintKind.L5_REVIEW_REQUIRED, 1.0, True),),
        constraint_refs=(math_states["constraint"].constraint_id,),
        confidence=0.8,
    )
    affective_input = AffectiveWeightInput(
        input_ref=typed(503, "affective_weight_input"),
        affective_color=affective_states["color"],
        action_bias=affective_states["action_bias"],
        affective_refs=(affective_states["color"].identity.state_ref,),
        exploration_weight=0.5,
        caution_weight=0.6,
        persistence_weight=0.8,
        learning_weight=0.9,
        stability_weight=0.8,
        confidence=0.8,
    )
    dynamic_input = DynamicDriveInput(
        input_ref=typed(504, "dynamic_drive_input"),
        dynamic_weights=(dynamic_states["weight"],),
        system_drive=dynamic_states["drive"],
        readiness=dynamic_states["readiness"],
        dynamic_drive_refs=(dynamic_states["weight"].identity.state_ref,),
        priority_weight=0.7,
        stability_pressure_weight=0.5,
        risk_pressure_weight=0.4,
        exploration_pressure_weight=0.6,
        confidence=0.8,
    )
    runtime_slice = RuntimeSliceProjectionState(
        identity=l2_identity(600, L2StateKind.PROJECTION),
        status=l2_status(),
        slice_id=typed(601, "runtime_slice"),
        math_state_ref=math_states["evaluation_state"].identity.state_ref,
        affective_state_ref=affective_states["color"].identity.state_ref,
        dynamic_drive_ref=dynamic_states["weight"].identity.state_ref,
        projection_status=ProjectionStatus.PARTIAL,
    )
    math_input = MathOrchestrationInput(
        input_ref=typed(505, "math_orchestration_input"),
        feature_vector=feature_vector,
        objective_vector=objective_vector,
        constraint_set=constraint_set,
        math_features=(math_states["feature"],),
        math_objectives=(math_states["objective"],),
        math_constraints=(math_states["constraint"],),
        math_scores=(math_states["score"],),
        math_state_refs=(math_states["evaluation_state"].identity.state_ref,),
        affective_input=affective_input,
        dynamic_drive_input=dynamic_input,
        runtime_slice_projection=runtime_slice,
    )
    score_vector = MathScoreVector(
        score_ref=typed(506, "math_score_vector"),
        score_entries=(("goal_fit", 0.8, ScoreDirection.BENEFIT),),
        source_score_refs=(math_states["score"].score_id,),
        normalized_score=0.75,
        confidence=0.8,
        penalty_total=0.1,
        bonus_total=0.2,
    )
    evaluation = MathEvaluation(
        evaluation_ref=typed(507, "math_evaluation"),
        input_value=math_input,
        score_vector=score_vector,
        source_evaluation_state=math_states["evaluation_state"],
        confidence=0.8,
        evaluation_status=MathAssessmentStatus.AVAILABLE,
    )
    ranking = RouteRanking(
        ranking_ref=typed(508, "route_ranking"),
        target_scores=((typed(23, "candidate"), 0.75),),
        order=RankingOrder.HIGHER_SCORE_FIRST,
        top_ranked_target_ref=typed(23, "candidate"),
        confidence=0.8,
        reason_summary="ranking fixture",
    )
    transition_advice = StateTransitionAdvice(
        advice_ref=typed(509, "state_transition_advice"),
        subject_state_ref=typed(23, "candidate"),
        suggested_status=L2StateStatusKind.WAITING,
        source_ranking_ref=ranking.ranking_ref,
        boundary_review_refs=(typed(26, "boundary"),),
        confidence=0.8,
        reason_summary="transition fixture",
    )
    recommendation = MathRecommendation(
        recommendation_ref=typed(510, "math_recommendation"),
        evaluation=evaluation,
        route_ranking=ranking,
        source_recommendation_state=math_states["recommendation_state"],
        recommendation_mode=RecommendationMode.SUGGEST,
        recommended_target_ref=typed(23, "candidate"),
        boundary_review_refs=(typed(26, "boundary"),),
        l4_request_hint_refs=(typed(27, "execution_request"),),
        state_transition_advice_refs=(transition_advice.advice_ref,),
        confidence=0.8,
        reason_summary="recommendation fixture",
    )
    request = OrchestrationRequest(
        identity=orch_identity(700, OrchestrationObjectKind.REQUEST),
        status=orch_status(),
        request_kind=OrchestrationRequestKind.MATH_ASSESSMENT,
        inbound_request=port_request(),
        l2_state_refs=(math_states["evaluation_state"].identity.state_ref,),
        summary="request fixture",
    )
    context = OrchestrationContext(
        identity=orch_identity(701, OrchestrationObjectKind.CONTEXT),
        status=orch_status(),
        request_ref=request.identity.orchestration_ref,
        runtime_slice_projection=runtime_slice,
        math_state_refs=(math_states["evaluation_state"].identity.state_ref,),
        affective_state_refs=(affective_states["color"].identity.state_ref,),
        dynamic_drive_refs=(dynamic_states["weight"].identity.state_ref,),
    )
    step = OrchestrationStep(
        identity=orch_identity(702, OrchestrationObjectKind.STEP),
        status=orch_status(OrchestrationStatusKind.PREPARED),
        step_ref=typed(703, "orchestration_step"),
        step_kind=OrchestrationStepKind.PREPARE_MATH_INPUT,
        input_refs=(math_input.input_ref,),
        output_refs=(evaluation.evaluation_ref,),
        summary="step fixture",
    )
    plan = OrchestrationPlan(
        identity=orch_identity(704, OrchestrationObjectKind.PLAN),
        status=orch_status(OrchestrationStatusKind.PREPARED),
        plan_ref=typed(705, "orchestration_plan"),
        request_ref=request.identity.orchestration_ref,
        context_ref=context.identity.orchestration_ref,
        steps=(step,),
        route_ranking_refs=(ranking.ranking_ref,),
        transition_advice_refs=(transition_advice.advice_ref,),
        summary="plan fixture",
    )
    result = OrchestrationResult(
        identity=orch_identity(706, OrchestrationObjectKind.RESULT),
        status=orch_status(OrchestrationStatusKind.ADVISED),
        result_kind=OrchestrationResultKind.MATH_RECOMMENDATION_READY,
        plan_ref=plan.plan_ref,
        core_result=ok(typed(510, "math_recommendation")),
        output_refs=(recommendation.recommendation_ref,),
        recommendation_refs=(recommendation.recommendation_ref,),
        transition_advice_refs=(transition_advice.advice_ref,),
        summary="result fixture",
    )
    return {
        "feature_vector": feature_vector,
        "objective_vector": objective_vector,
        "constraint_set": constraint_set,
        "affective_input": affective_input,
        "dynamic_input": dynamic_input,
        "math_input": math_input,
        "score_vector": score_vector,
        "evaluation": evaluation,
        "ranking": ranking,
        "transition_advice": transition_advice,
        "recommendation": recommendation,
        "request": request,
        "context": context,
        "step": step,
        "plan": plan,
        "result": result,
    }
