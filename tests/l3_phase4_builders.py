from dataclasses import replace

from l3_phase1_builders import typed
from l3_phase3_builders import build_l3_phase3_objects
from tiangong_kernel.l3_orchestration import (
    ActionIntentAdvice,
    ActionIntentEnvelope,
    ActionIntentPreconditionHint,
    ActionIntentRef,
    ActionIntentReversibilityHint,
    ActionIntentStateTransitionAdvice,
    ActionIntentTargetRef,
    IntentClarificationQuestionAdvice,
    IntentConflictAdvice,
    IntentContinuityAdvice,
    IntentDegradePathAdvice,
    IntentEnvelopeStatus,
    IntentInterruptionAdvice,
    IntentKind,
    IntentMathInput,
    IntentMathResult,
    IntentMissingFieldAdvice,
    IntentRecommendation,
    IntentRejectPathAdvice,
    IntentResumeAdvice,
    IntentRetryPathAdvice,
    IntentRouteCandidate,
    IntentRouteKind,
    IntentRouteProjection,
    IntentStateTransitionSuggestion,
    IntentStructureValidationResult,
    IntentTransitionKind,
    IntentTransitionProjection,
    IntentValidationAdvice,
    LifecycleTransitionIntent,
    ModelIntentAdvice,
    ModelIntentAmbiguityAdvice,
    ModelIntentClarificationAdvice,
    ModelIntentDowngradeAdvice,
    ModelIntentEnvelope,
    ModelIntentRef,
    ModelIntentRejectionAdvice,
    ModelIntentStateTransitionAdvice,
    ModelIntentStructureHint,
    OrchestrationLifecycleKind,
    RecommendationMode,
    RunIntentAdvice,
    SkillIntentLinkAdvice,
    StepIntentAdvice,
    TaskIntentAdvice,
    ToolGroupIntentLinkAdvice,
    ToolIntentAdvice,
    ToolIntentBoundaryPreparationHint,
    ToolIntentDowngradeAdvice,
    ToolIntentEnvelope,
    ToolIntentMissingParameterAdvice,
    ToolIntentParameterSpecRef,
    ToolIntentRef,
    ToolIntentStateTransitionAdvice,
    TurnIntentAdvice,
    build_action_intent_completeness_score,
    build_action_intent_readiness_score,
    build_intent_ambiguity_score,
    build_intent_clarification_need_score,
    build_intent_degrade_score,
    build_intent_readiness_score,
    build_intent_route_ranking,
    build_intent_score_vector,
    build_model_intent_completeness_score,
    build_tool_intent_parameter_completeness_score,
    build_tool_intent_readiness_score,
    score_model_envelope_completeness,
)


def build_l3_phase4_objects():
    phase3 = build_l3_phase3_objects()
    phase2 = phase3["math_input"].continuity_evaluation
    run_ref = phase3["route_candidate_1"].run_ref
    task_ref = phase3["route_candidate_1"].task_ref
    turn_ref = phase3["route_candidate_1"].turn_ref
    step_ref = phase3["route_candidate_1"].step_ref
    skill_ref = phase3["skill_candidate_1"].skill_ref
    tool_group_ref = phase3["tool_candidate_1"].tool_group_ref
    tool_ref = phase3["tool_candidate_1"].tool_refs[0]

    model_intent_ref = ModelIntentRef(
        intent_ref=typed(1200, "model_intent"),
        source_turn_ref=turn_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        step_ref=step_ref,
        skill_ref=skill_ref,
        tool_group_ref=tool_group_ref,
        source_advice_refs=(phase3["selection_advice"].advice_ref,),
    )
    model_envelope = ModelIntentEnvelope(
        envelope_ref=typed(1201, "model_intent_envelope"),
        intent_ref=model_intent_ref,
        status=IntentEnvelopeStatus.PARTIAL,
        stated_goal="prepare a safe tool call intent",
        requested_capability_hint="code_edit_planning",
        provided_fields=("goal", "skill_ref", "tool_group_ref"),
        missing_fields=("target_parameters",),
        confidence=0.82,
    )
    model_structure = ModelIntentStructureHint(
        hint_ref=typed(1202, "model_intent_structure_hint"),
        intent_ref=model_intent_ref,
        expected_fields=("goal", "skill_ref", "tool_group_ref", "target_parameters"),
        missing_fields=("target_parameters",),
        structure_score=0.75,
        reason_summary="model intent structure is partial",
    )
    model_completeness = build_model_intent_completeness_score(
        typed(1203, "model_intent_completeness_score"),
        model_envelope,
        ("goal", "skill_ref", "tool_group_ref", "target_parameters"),
    )
    model_advice = ModelIntentAdvice(
        advice_ref=typed(1204, "model_intent_advice"),
        intent_envelope=model_envelope,
        structure_hint=model_structure,
        completeness_score=model_completeness,
        suggested_next_step="clarify_target_parameters",
        reason_summary="model intent needs target parameters",
        confidence=0.8,
    )
    model_ambiguity = ModelIntentAmbiguityAdvice(
        advice_ref=typed(1205, "model_intent_ambiguity_advice"),
        intent_ref=model_intent_ref,
        ambiguity_score=0.25,
        ambiguous_fields=("target_parameters",),
        reason_summary="target parameters not explicit",
    )
    model_clarification = ModelIntentClarificationAdvice(
        advice_ref=typed(1206, "model_intent_clarification_advice"),
        intent_ref=model_intent_ref,
        question_hints=("Which target parameters should be prepared?",),
        missing_field_names=("target_parameters",),
        clarification_priority=0.72,
        reason_summary="clarify before downstream review",
    )
    model_rejection = ModelIntentRejectionAdvice(
        advice_ref=typed(1207, "model_intent_rejection_advice"),
        intent_ref=model_intent_ref,
        rejection_reason_codes=("insufficient_structure_for_downstream_review",),
        rejection_score=0.1,
        reason_summary="reject path is low priority",
    )
    model_downgrade = ModelIntentDowngradeAdvice(
        advice_ref=typed(1208, "model_intent_downgrade_advice"),
        intent_ref=model_intent_ref,
        downgrade_score=0.36,
        preserved_context_refs=(model_envelope.envelope_ref,),
        reason_summary="downgrade to clarification if parameters stay missing",
    )
    model_transition = ModelIntentStateTransitionAdvice(
        advice_ref=typed(1209, "model_intent_state_transition"),
        intent_ref=model_intent_ref,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.WAITING,
        transition_intent=LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE,
        transition_score=0.68,
        blocker_refs=(model_clarification.advice_ref,),
        reason_summary="wait for missing parameters",
    )

    parameter_spec = ToolIntentParameterSpecRef(
        parameter_spec_ref=typed(1210, "tool_intent_parameter_spec"),
        parameter_name="target_path",
        required=True,
        expected_type_hint="string",
        source_tool_ref=tool_ref,
    )
    optional_spec = ToolIntentParameterSpecRef(
        parameter_spec_ref=typed(1211, "tool_intent_parameter_spec"),
        parameter_name="dry_run",
        required=False,
        expected_type_hint="bool",
        source_tool_ref=tool_ref,
    )
    tool_intent_ref = ToolIntentRef(
        intent_ref=typed(1212, "tool_intent"),
        tool_group_ref=tool_group_ref,
        tool_ref=tool_ref,
        model_intent_ref=model_intent_ref.intent_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        source_advice_refs=(phase3["release_advice"].advice_ref,),
    )
    tool_envelope = ToolIntentEnvelope(
        envelope_ref=typed(1213, "tool_intent_envelope"),
        intent_ref=tool_intent_ref,
        status=IntentEnvelopeStatus.PARTIAL,
        tool_name_hint="code_edit_prepare",
        parameter_spec_refs=(parameter_spec, optional_spec),
        provided_parameter_names=("dry_run",),
        missing_parameter_names=("target_path",),
        confidence=0.78,
    )
    tool_parameter_score = build_tool_intent_parameter_completeness_score(
        typed(1214, "tool_intent_parameter_completeness_score"),
        tool_envelope,
    )
    tool_readiness = build_tool_intent_readiness_score(
        typed(1215, "tool_intent_readiness_score"),
        tool_parameter_score,
        release_readiness=phase3["tool_candidate_1"].readiness_score,
    )
    tool_advice = ToolIntentAdvice(
        advice_ref=typed(1216, "tool_intent_advice"),
        intent_envelope=tool_envelope,
        parameter_score=tool_parameter_score,
        readiness_score=tool_readiness,
        reason_summary="tool intent needs required parameter",
        confidence=0.78,
    )
    missing_parameter_advice = ToolIntentMissingParameterAdvice(
        advice_ref=typed(1217, "tool_intent_missing_parameter_advice"),
        intent_ref=tool_intent_ref,
        missing_parameter_names=("target_path",),
        parameter_spec_refs=(parameter_spec,),
        clarification_hint="target_path is required before review preparation",
        priority=0.88,
    )
    boundary_hint = ToolIntentBoundaryPreparationHint(
        hint_ref=typed(1218, "tool_intent_boundary_preparation_hint"),
        intent_ref=tool_intent_ref,
        tool_group_ref=tool_group_ref,
        parameter_score_ref=tool_parameter_score.score_ref,
        required_review_context_refs=(tool_envelope.envelope_ref, phase3["release_advice"].advice_ref),
        preparation_reason_codes=("collect intent context only",),
        readiness_hint=tool_readiness.value,
    )
    tool_downgrade = ToolIntentDowngradeAdvice(
        advice_ref=typed(1219, "tool_intent_downgrade_advice"),
        intent_ref=tool_intent_ref,
        downgrade_score=0.52,
        preserved_context_refs=(tool_envelope.envelope_ref,),
        reason_summary="downgrade until required parameter exists",
    )
    tool_transition = ToolIntentStateTransitionAdvice(
        advice_ref=typed(1220, "tool_intent_state_transition"),
        intent_ref=tool_intent_ref,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.WAITING,
        transition_intent=LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE,
        transition_score=0.62,
        blocker_refs=(missing_parameter_advice.advice_ref,),
        reason_summary="tool intent waits for parameter",
    )

    action_target = ActionIntentTargetRef(
        target_ref=typed(1221, "action_target"),
        target_label="planned target path",
        target_kind_hint="file_path_ref",
    )
    action_intent_ref = ActionIntentRef(
        intent_ref=typed(1222, "action_intent"),
        action_label="prepare edit action",
        model_intent_ref=model_intent_ref.intent_ref,
        tool_intent_ref=tool_intent_ref.intent_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        source_advice_refs=(tool_advice.advice_ref,),
    )
    action_envelope = ActionIntentEnvelope(
        envelope_ref=typed(1223, "action_intent_envelope"),
        intent_ref=action_intent_ref,
        status=IntentEnvelopeStatus.STRUCTURED,
        action_summary="prepare edit action after review",
        target_refs=(action_target,),
        provided_fields=("action_label", "target_ref", "precondition_ref"),
        missing_fields=(),
        precondition_refs=(typed(1224, "action_precondition"),),
        confidence=0.84,
    )
    precondition_hint = ActionIntentPreconditionHint(
        hint_ref=typed(1225, "action_precondition_hint"),
        intent_ref=action_intent_ref,
        required_precondition_refs=action_envelope.precondition_refs,
        satisfied_precondition_refs=action_envelope.precondition_refs,
        missing_precondition_refs=(),
        precondition_score=1.0,
        reason_summary="precondition references are present",
    )
    action_completeness = build_action_intent_completeness_score(
        typed(1226, "action_intent_completeness_score"),
        action_envelope,
        ("action_label", "target_ref", "precondition_ref"),
    )
    reversibility_hint = ActionIntentReversibilityHint(
        hint_ref=typed(1227, "action_reversibility_hint"),
        intent_ref=action_intent_ref,
        reversibility_score=0.76,
        reversible_context_refs=(typed(1228, "reversible_context"),),
        reason_summary="path can preserve rollback context later",
    )
    action_readiness = build_action_intent_readiness_score(
        typed(1229, "action_intent_readiness_score"),
        action_completeness,
        precondition_hint,
        reversibility_hint,
    )
    action_advice = ActionIntentAdvice(
        advice_ref=typed(1230, "action_intent_advice"),
        intent_envelope=action_envelope,
        precondition_hint=precondition_hint,
        readiness_score=action_readiness,
        target_refs=(action_target,),
        reason_summary="action intent is prepared for later review only",
        confidence=0.82,
    )
    action_transition = ActionIntentStateTransitionAdvice(
        advice_ref=typed(1231, "action_intent_state_transition"),
        intent_ref=action_intent_ref,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.PREPARED,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        transition_score=0.78,
        reason_summary="action intent can be prepared as advice",
    )

    validation_result = IntentStructureValidationResult(
        result_ref=typed(1232, "intent_validation_result"),
        intent_ref=model_intent_ref.intent_ref,
        intent_kind=IntentKind.MODEL,
        valid_structure_hint=False,
        provided_fields=model_envelope.provided_fields,
        missing_fields=model_envelope.missing_fields,
        validation_score=model_completeness.value,
        reason_summary="model intent has one missing field",
    )
    validation_advice = IntentValidationAdvice(
        advice_ref=typed(1233, "intent_validation_advice"),
        validation_result=validation_result,
        suggested_path_refs=(model_clarification.advice_ref,),
        reason_summary="clarify missing field",
        confidence=0.8,
    )
    missing_field_advice = IntentMissingFieldAdvice(
        advice_ref=typed(1234, "intent_missing_field_advice"),
        intent_ref=model_intent_ref.intent_ref,
        missing_field_names=("target_parameters",),
        priority=0.82,
        clarification_hint="target parameters are needed",
    )
    conflict_advice = IntentConflictAdvice(
        advice_ref=typed(1235, "intent_conflict_advice"),
        intent_ref=model_intent_ref.intent_ref,
        conflict_score=0.0,
    )
    clarification_question = IntentClarificationQuestionAdvice(
        advice_ref=typed(1236, "intent_clarification_question_advice"),
        intent_ref=model_intent_ref.intent_ref,
        question_hints=("Which target parameters should be used?",),
        related_missing_fields=("target_parameters",),
        priority=0.82,
    )
    reject_path = IntentRejectPathAdvice(
        advice_ref=typed(1237, "intent_reject_path_advice"),
        intent_ref=model_intent_ref.intent_ref,
        reject_reason_codes=("not_required_now",),
        reject_score=0.08,
        reason_summary="rejection is low priority",
    )
    degrade_path = IntentDegradePathAdvice(
        advice_ref=typed(1238, "intent_degrade_path_advice"),
        intent_ref=model_intent_ref.intent_ref,
        degrade_score=0.38,
        preserved_context_refs=(model_envelope.envelope_ref,),
        reason_summary="degrade if missing data remains",
    )
    retry_path = IntentRetryPathAdvice(
        advice_ref=typed(1239, "intent_retry_path_advice"),
        intent_ref=model_intent_ref.intent_ref,
        retry_condition_hints=("target parameters supplied",),
        retry_score=0.7,
        reason_summary="retry after clarification",
    )
    generic_transition = IntentStateTransitionSuggestion(
        suggestion_ref=typed(1240, "intent_state_transition_suggestion"),
        intent_ref=model_intent_ref.intent_ref,
        intent_kind=IntentKind.MODEL,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.WAITING,
        transition_intent=LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE,
        transition_score=0.68,
        validation_advice_refs=(validation_advice.advice_ref,),
        reason_summary="wait for missing field",
    )

    generic_model_completeness = score_model_envelope_completeness(typed(1241, "intent_completeness_score"), model_envelope)
    ambiguity_score = build_intent_ambiguity_score(typed(1242, "intent_ambiguity_score"), 1, 4, 0.82)
    readiness_score = build_intent_readiness_score(
        typed(1243, "intent_readiness_score"),
        generic_model_completeness,
        ambiguity_score,
        continuity=phase2.continuity_index.value,
        reversibility=phase3["reversibility"].value,
    )
    degrade_score = build_intent_degrade_score(typed(1244, "intent_degrade_score"), ambiguity_score, generic_model_completeness)
    clarification_need = build_intent_clarification_need_score(
        typed(1245, "intent_clarification_need_score"),
        ambiguity_score,
        generic_model_completeness,
        affective_input=phase3["math_input"].affective_input,
        dynamic_drive_input=phase3["math_input"].dynamic_drive_input,
    )
    score_vector = build_intent_score_vector(
        typed(1246, "intent_score_vector"),
        (generic_model_completeness, ambiguity_score, readiness_score, degrade_score, clarification_need),
    )
    math_input = IntentMathInput(
        input_ref=typed(1247, "intent_math_input"),
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        model_intent_refs=(model_intent_ref.intent_ref,),
        tool_intent_refs=(tool_intent_ref.intent_ref,),
        action_intent_refs=(action_intent_ref.intent_ref,),
        continuity_evaluation=phase2,
        skill_tool_math_result=phase3["math_result"],
        affective_input=phase3["math_input"].affective_input,
        dynamic_drive_input=phase3["math_input"].dynamic_drive_input,
        stability_constraint_refs=(typed(1248, "stability_constraint"),),
        reversibility_constraint_refs=(typed(1249, "reversibility_constraint"),),
        summary="intent math input fixture",
    )
    route_candidate_1 = IntentRouteCandidate(
        route_ref=typed(1250, "intent_route"),
        route_kind=IntentRouteKind.PREPARE_ACTION_REVIEW,
        intent_kind=IntentKind.ACTION,
        model_intent_ref=model_intent_ref.intent_ref,
        tool_intent_ref=tool_intent_ref.intent_ref,
        action_intent_ref=action_intent_ref.intent_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        skill_ref=skill_ref,
        tool_group_ref=tool_group_ref,
        readiness_score=action_readiness.value,
        completeness_score=action_completeness.value,
        ambiguity_score=0.08,
        continuity_score=phase2.continuity_index.value,
        reversibility_score=reversibility_hint.reversibility_score,
        clarification_need_score=0.12,
        degrade_score=0.18,
        reason_codes=("action intent is structurally ready",),
    )
    route_candidate_2 = replace(
        route_candidate_1,
        route_ref=typed(1251, "intent_route"),
        route_kind=IntentRouteKind.CLARIFY_MODEL_INTENT,
        readiness_score=readiness_score.value,
        completeness_score=generic_model_completeness.value,
        ambiguity_score=ambiguity_score.value,
        clarification_need_score=clarification_need.value,
        degrade_score=degrade_score.value,
        reason_codes=("clarification path remains available",),
    )
    route_ranking = build_intent_route_ranking(
        typed(1252, "intent_route_ranking"),
        (route_candidate_2, route_candidate_1),
    )
    math_result = IntentMathResult(
        result_ref=typed(1253, "intent_math_result"),
        math_input=math_input,
        score_vector=score_vector,
        intent_route_ranking_ref=route_ranking.ranking_ref,
        validation_advice_refs=(validation_advice.advice_ref,),
        confidence=0.8,
        reason_summary="intent math result remains advisory",
    )
    recommendation = IntentRecommendation(
        recommendation_ref=typed(1254, "intent_recommendation"),
        math_result=math_result,
        recommendation_mode=RecommendationMode.SUGGEST,
        recommended_intent_ref=action_intent_ref.intent_ref,
        recommended_route_ref=route_ranking.top_route_ref,
        clarification_advice_refs=(model_clarification.advice_ref,),
        downgrade_advice_refs=(model_downgrade.advice_ref, tool_downgrade.advice_ref),
        boundary_preparation_hint_refs=(boundary_hint.hint_ref,),
        confidence=0.8,
        reason_summary="recommend intent route only",
    )

    run_intent_advice = RunIntentAdvice(
        advice_ref=typed(1255, "run_intent_advice"),
        run_ref=run_ref,
        route_ranking=route_ranking,
        reason_summary="run intent route advice",
    )
    task_intent_advice = TaskIntentAdvice(
        advice_ref=typed(1256, "task_intent_advice"),
        task_ref=task_ref,
        model_intent=model_intent_ref,
        tool_intent=tool_intent_ref,
        action_intent=action_intent_ref,
        route_ranking_ref=route_ranking.ranking_ref,
        reason_summary="task intent advice",
    )
    turn_intent_advice = TurnIntentAdvice(
        advice_ref=typed(1257, "turn_intent_advice"),
        turn_ref=turn_ref,
        model_intent=model_intent_ref,
        carryover_hint_refs=(phase3["run_skill_display"].advice_ref,),
        reason_summary="turn intent advice",
    )
    step_intent_advice = StepIntentAdvice(
        advice_ref=typed(1258, "step_intent_advice"),
        step_ref=step_ref,
        tool_intent=tool_intent_ref,
        action_intent=action_intent_ref,
        readiness_hint_ref=action_readiness.score_ref,
        reason_summary="step intent advice",
    )
    skill_link = SkillIntentLinkAdvice(
        advice_ref=typed(1259, "skill_intent_link_advice"),
        skill_selection_advice=phase3["selection_advice"],
        model_intent_ref=model_intent_ref.intent_ref,
        tool_intent_ref=tool_intent_ref.intent_ref,
        link_score=0.82,
        reason_summary="skill links to intent",
    )
    tool_group_link = ToolGroupIntentLinkAdvice(
        advice_ref=typed(1260, "tool_group_intent_link_advice"),
        tool_group_release_advice=phase3["release_advice"],
        tool_intent_ref=tool_intent_ref.intent_ref,
        action_intent_ref=action_intent_ref.intent_ref,
        link_score=0.8,
        reason_summary="tool group links to intent",
    )
    resume_advice = IntentResumeAdvice(
        advice_ref=typed(1261, "intent_resume_advice"),
        route_ranking=route_ranking,
        suggested_route_ref=route_ranking.top_route_ref,
        math_result_ref=math_result.result_ref,
        reason_summary="resume via ranked intent route",
    )
    interruption_advice = IntentInterruptionAdvice(
        advice_ref=typed(1262, "intent_interruption_advice"),
        blocker_refs=(missing_field_advice.advice_ref,),
        reason_summary="wait for missing target parameters",
    )
    continuity_advice = IntentContinuityAdvice(
        advice_ref=typed(1263, "intent_continuity_advice"),
        route_ranking=route_ranking,
        math_result=math_result,
        recommended_route_ref=route_ranking.top_route_ref,
        confidence=0.8,
        reason_summary="intent continuity advice",
    )
    route_projection = IntentRouteProjection(
        projection_ref=typed(1264, "intent_route_projection"),
        route_ranking_ref=route_ranking.ranking_ref,
        projected_model_intent_refs=(model_intent_ref.intent_ref,),
        projected_tool_intent_refs=(tool_intent_ref.intent_ref,),
        projected_action_intent_refs=(action_intent_ref.intent_ref,),
        future_l5_preparation_hint_refs=(boundary_hint.hint_ref,),
        future_l4_preparation_hint_refs=(typed(1265, "future_l4_preparation_hint"),),
        reason_summary="projection references future stages only",
    )
    transition_projection = IntentTransitionProjection(
        projection_ref=typed(1266, "intent_transition_projection"),
        subject_intent_ref=tool_intent_ref.intent_ref,
        subject_intent_kind=IntentKind.TOOL,
        transition_kind=IntentTransitionKind.INTENT_TO_BOUNDARY_PREPARATION_HINT,
        current_lifecycle=OrchestrationLifecycleKind.WAITING,
        suggested_lifecycle=OrchestrationLifecycleKind.PREPARED,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        transition_score=0.7,
        related_advice_refs=(tool_advice.advice_ref, boundary_hint.hint_ref),
        future_review_hint_refs=(boundary_hint.hint_ref,),
        reason_summary="projection only",
    )

    return locals()
