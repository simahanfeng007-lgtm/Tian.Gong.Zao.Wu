from dataclasses import replace

from l3_phase1_builders import typed
from l3_phase2_builders import build_l3_phase2_objects
from tiangong_kernel.l3_orchestration import (
    LifecycleTransitionIntent,
    OrchestrationLifecycleKind,
    RecommendationMode,
    ResumeAdviceKind,
    RunSkillDisplayAdvice,
    SkillActivationAdvice,
    SkillDeactivationAdvice,
    SkillDisplayAdvice,
    SkillDisplayCandidate,
    SkillDisplayRanking,
    SkillDisplayReasonCode,
    SkillMatchScore,
    SkillMismatchAdvice,
    SkillNeedClarificationAdvice,
    SkillRiskAwarenessHint,
    SkillSelectionAdvice,
    SkillStateTransitionAdvice,
    SkillToolContinuityAdvice,
    SkillToolInterruptionAdvice,
    SkillToolMathInput,
    SkillToolMathResult,
    SkillToolRecommendation,
    SkillToolResumeAdvice,
    SkillToolRouteCandidate,
    SkillToolRouteKind,
    SkillToolStateTransitionSuggestion,
    SkillToolTransitionKind,
    SkillVisibilityRequestRef,
    StabilityIndex,
    StepToolGroupReleaseAdvice,
    TaskSkillSelectionAdvice,
    ToolExposureCostScore,
    ToolGroupLeaseAdvice,
    ToolGroupMinimalReleaseAdvice,
    ToolGroupReasonCode,
    ToolGroupReleaseAdvice,
    ToolGroupReleaseCandidate,
    ToolGroupResolveRequestRef,
    ToolGroupStateTransitionAdvice,
    TurnSkillActivationAdvice,
    build_reversibility_index,
    build_skill_display_ranking,
    build_skill_match_score,
    build_skill_tool_math_score_vector,
    build_skill_tool_route_ranking,
    build_stability_index,
    build_tool_exposure_cost_score,
    build_tool_group_minimality_score,
    build_tool_group_release_ranking,
    build_tool_group_sufficiency_score,
)


def build_l3_phase3_objects():
    phase2 = build_l3_phase2_objects()
    phase1 = phase2["continuity_set"].affective_input
    dynamic_input = phase2["continuity_set"].dynamic_drive_input
    run_ref = phase2["run_ref"].run_ref
    task_ref = phase2["task_ref"].task_ref
    turn_ref = phase2["turn_ref"].turn_ref
    step_ref = phase2["step_candidate"].target_step_ref

    skill_ref_1 = typed(900, "skill_ref")
    skill_ref_2 = typed(901, "skill_ref")
    tool_group_ref_1 = typed(902, "tool_group_ref")
    tool_group_ref_2 = typed(903, "tool_group_ref")
    tool_ref_1 = typed(904, "tool_ref")
    tool_ref_2 = typed(905, "tool_ref")
    tool_ref_3 = typed(906, "tool_ref")

    visibility_request = SkillVisibilityRequestRef(
        request_ref=typed(910, "skill_visibility_request"),
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        source_context_ref=phase2["run_ref"].source_context_ref,
        objective_refs=(typed(911, "objective_ref"),),
        constraint_refs=(typed(912, "constraint_ref"),),
    )
    skill_candidate_1 = SkillDisplayCandidate(
        candidate_ref=typed(913, "skill_display_candidate"),
        skill_ref=skill_ref_1,
        request_ref=visibility_request.request_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        skill_label="stable skill",
        skill_summary="stable skill fixture",
        match_score=0.86,
        readiness_score=0.82,
        continuity_score=0.78,
        risk_awareness_hint=0.18,
        reason_codes=(SkillDisplayReasonCode.GOAL_MATCH, SkillDisplayReasonCode.CONTINUITY_MATCH),
    )
    skill_candidate_2 = SkillDisplayCandidate(
        candidate_ref=typed(914, "skill_display_candidate"),
        skill_ref=skill_ref_2,
        request_ref=visibility_request.request_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        skill_label="explore skill",
        skill_summary="explore skill fixture",
        match_score=0.74,
        readiness_score=0.72,
        continuity_score=0.68,
        risk_awareness_hint=0.35,
        reason_codes=(SkillDisplayReasonCode.GOAL_MATCH,),
    )
    skill_ranking = build_skill_display_ranking(
        typed(915, "skill_display_ranking"),
        (skill_candidate_2, skill_candidate_1),
        reason_summary="rank skill candidates",
    )
    display_advice = SkillDisplayAdvice(
        advice_ref=typed(916, "skill_display_advice"),
        request_ref=visibility_request,
        ranking=skill_ranking,
        display_candidate_refs=(skill_candidate_1.candidate_ref, skill_candidate_2.candidate_ref),
        l5_review_hint_refs=(typed(917, "l5_review_hint"),),
        reason_summary="display skill candidates",
    )
    selection_advice = SkillSelectionAdvice(
        advice_ref=typed(918, "skill_selection_advice"),
        selected_skill_ref=skill_ranking.top_ranked_skill_ref,
        ranking_ref=skill_ranking.ranking_ref,
        request_ref=visibility_request.request_ref,
        required_tool_group_refs=(tool_group_ref_1,),
        alternative_skill_refs=(skill_ref_2,),
        selection_score=skill_ranking.target_scores[0][1],
        confidence=0.8,
        reason_summary="select skill advice fixture",
    )
    activation_advice = SkillActivationAdvice(
        advice_ref=typed(919, "skill_activation_advice"),
        skill_ref=skill_ref_1,
        selection_advice_ref=selection_advice.advice_ref,
        suggested_lifecycle=OrchestrationLifecycleKind.PREPARED,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        activation_score=0.82,
        required_tool_group_refs=(tool_group_ref_1,),
        reason_summary="prepare skill for later stages",
    )
    deactivation_advice = SkillDeactivationAdvice(
        advice_ref=typed(920, "skill_deactivation_advice"),
        skill_ref=skill_ref_2,
        suggested_lifecycle=OrchestrationLifecycleKind.PAUSED,
        reason_codes=(SkillDisplayReasonCode.HIGH_EXPOSURE_CAUTION,),
        reason_summary="keep alternative paused",
    )
    mismatch_advice = SkillMismatchAdvice(
        advice_ref=typed(921, "skill_mismatch_advice"),
        skill_ref=skill_ref_2,
        mismatch_score=0.24,
        missing_goal_refs=(typed(922, "goal_ref"),),
        reason_codes=(SkillDisplayReasonCode.NEED_MORE_CONTEXT,),
        reason_summary="skill needs more context",
    )
    clarification_advice = SkillNeedClarificationAdvice(
        advice_ref=typed(923, "skill_clarification_advice"),
        request_ref=visibility_request.request_ref,
        ambiguous_skill_refs=(skill_ref_2,),
        missing_context_fields=("operator_goal_detail",),
        clarification_priority=0.42,
        reason_summary="clarify before selecting alternative",
    )
    skill_transition = SkillStateTransitionAdvice(
        advice_ref=typed(924, "skill_state_transition_advice"),
        skill_ref=skill_ref_1,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.PREPARED,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        transition_score=0.82,
        required_state_refs=(visibility_request.request_ref,),
        reason_summary="skill state transition advice fixture",
    )

    resolve_request = ToolGroupResolveRequestRef(
        request_ref=typed(930, "tool_group_resolve_request"),
        skill_ref=skill_ref_1,
        source_advice_ref=activation_advice.advice_ref,
        requested_tool_group_refs=(tool_group_ref_1, tool_group_ref_2),
        requested_tool_refs=(tool_ref_1, tool_ref_2),
        l5_review_hint_refs=(typed(931, "l5_review_hint"),),
    )
    tool_candidate_1 = ToolGroupReleaseCandidate(
        candidate_ref=typed(932, "tool_group_release_candidate"),
        tool_group_ref=tool_group_ref_1,
        skill_ref=skill_ref_1,
        tool_refs=(tool_ref_1, tool_ref_2),
        required_tool_refs=(tool_ref_1, tool_ref_2),
        optional_tool_refs=(),
        missing_tool_refs=(),
        minimality_score=0.9,
        sufficiency_score=0.86,
        exposure_cost_score=0.28,
        readiness_score=0.82,
        reason_codes=(ToolGroupReasonCode.SUFFICIENT_FOR_INTENT, ToolGroupReasonCode.MINIMAL_EXPOSURE),
    )
    tool_candidate_2 = ToolGroupReleaseCandidate(
        candidate_ref=typed(933, "tool_group_release_candidate"),
        tool_group_ref=tool_group_ref_2,
        skill_ref=skill_ref_1,
        tool_refs=(tool_ref_1, tool_ref_2, tool_ref_3),
        required_tool_refs=(tool_ref_1, tool_ref_2),
        optional_tool_refs=(tool_ref_3,),
        missing_tool_refs=(),
        minimality_score=0.62,
        sufficiency_score=0.9,
        exposure_cost_score=0.55,
        readiness_score=0.78,
        reason_codes=(ToolGroupReasonCode.SUFFICIENT_FOR_INTENT, ToolGroupReasonCode.HIGH_EXPOSURE_COST),
    )
    tool_ranking = build_tool_group_release_ranking(
        typed(934, "tool_group_release_ranking"),
        (tool_candidate_2, tool_candidate_1),
        reason_summary="rank tool group candidates",
    )
    release_advice = ToolGroupReleaseAdvice(
        advice_ref=typed(935, "tool_group_release_advice"),
        resolve_request_ref=resolve_request,
        release_ranking=tool_ranking,
        suggested_tool_group_ref=tool_ranking.top_tool_group_ref,
        release_candidate_refs=(tool_candidate_1.candidate_ref, tool_candidate_2.candidate_ref),
        l5_review_hint_refs=(typed(936, "l5_review_hint"),),
        reason_summary="release advice fixture only",
    )
    minimal_release_advice = ToolGroupMinimalReleaseAdvice(
        advice_ref=typed(937, "tool_group_minimal_release_advice"),
        tool_group_ref=tool_group_ref_1,
        kept_tool_refs=(tool_ref_1, tool_ref_2),
        omitted_tool_refs=(tool_ref_3,),
        minimality_score=0.9,
        sufficiency_score=0.86,
        reason_codes=(ToolGroupReasonCode.MINIMAL_EXPOSURE,),
        reason_summary="minimal release advice fixture",
    )
    lease_advice = ToolGroupLeaseAdvice(
        advice_ref=typed(938, "tool_group_lease_advice"),
        tool_group_ref=tool_group_ref_1,
        tool_refs=(tool_ref_1, tool_ref_2),
        lease_request_ref=typed(939, "tool_group_lease_request_hint"),
        required_review_refs=(typed(940, "l5_review_hint"),),
        reason_summary="lease request hint only",
    )
    tool_transition = ToolGroupStateTransitionAdvice(
        advice_ref=typed(941, "tool_group_state_transition_advice"),
        tool_group_ref=tool_group_ref_1,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.PREPARED,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        transition_score=0.8,
        required_review_refs=(typed(942, "l5_review_hint"),),
        reason_summary="tool group state transition fixture",
    )

    skill_match = build_skill_match_score(skill_candidate_1, typed(950, "skill_match_score"))
    skill_risk = SkillRiskAwarenessHint(
        score_ref=typed(951, "skill_risk_hint_score"),
        value=skill_candidate_1.risk_awareness_hint,
        confidence=0.8,
        reason_codes=("risk hint remains advisory",),
        evidence_refs=(skill_candidate_1.candidate_ref,),
    )
    tool_minimality = build_tool_group_minimality_score(tool_candidate_1, typed(952, "tool_group_minimality_score"))
    exposure_cost = build_tool_exposure_cost_score(
        tool_candidate_1,
        affective_input=phase1,
        dynamic_drive_input=dynamic_input,
        score_ref=typed(953, "tool_exposure_cost_score"),
    )
    sufficiency = build_tool_group_sufficiency_score(tool_candidate_1, typed(954, "tool_group_sufficiency_score"))
    reversibility = build_reversibility_index(0.84, exposure_cost, typed(955, "reversibility_index"))
    stability = build_stability_index(
        phase2["continuity_set"].continuity_index.value,
        skill_candidate_1.readiness_score,
        dynamic_input,
        typed(956, "stability_index"),
    )
    math_score_vector = build_skill_tool_math_score_vector(
        typed(957, "skill_tool_math_score_vector"),
        (skill_match, skill_risk, tool_minimality, exposure_cost, sufficiency, reversibility, stability),
    )
    math_input = SkillToolMathInput(
        input_ref=typed(958, "skill_tool_math_input"),
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        skill_candidate_refs=(skill_candidate_1.candidate_ref, skill_candidate_2.candidate_ref),
        tool_group_candidate_refs=(tool_candidate_1.candidate_ref, tool_candidate_2.candidate_ref),
        objective_vector=None,
        constraint_set=None,
        continuity_evaluation=phase2["continuity_set"],
        affective_input=phase1,
        dynamic_drive_input=dynamic_input,
        stability_constraint_refs=(typed(959, "stability_constraint_ref"),),
        reversibility_constraint_refs=(typed(960, "reversibility_constraint_ref"),),
        summary="skill tool math input fixture",
    )
    route_candidate_1 = SkillToolRouteCandidate(
        route_ref=typed(961, "skill_tool_route"),
        route_kind=SkillToolRouteKind.PREPARE_TOOL_GROUP,
        skill_ref=skill_ref_1,
        tool_group_ref=tool_group_ref_1,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        skill_score=skill_match.value,
        tool_group_score=sufficiency.value,
        continuity_score=phase2["continuity_set"].continuity_index.value,
        exposure_cost=exposure_cost.value,
        reversibility_score=reversibility.value,
        stability_score=stability.value,
        reason_codes=("best minimal sufficient route",),
    )
    route_candidate_2 = replace(
        route_candidate_1,
        route_ref=typed(962, "skill_tool_route"),
        tool_group_ref=tool_group_ref_2,
        tool_group_score=0.72,
        exposure_cost=0.55,
        reason_codes=("higher exposure alternative",),
    )
    route_ranking = build_skill_tool_route_ranking(
        typed(963, "skill_tool_route_ranking"),
        (route_candidate_2, route_candidate_1),
    )
    math_result = SkillToolMathResult(
        result_ref=typed(964, "skill_tool_math_result"),
        math_input=math_input,
        score_vector=math_score_vector,
        skill_route_ranking_ref=route_ranking.ranking_ref,
        tool_group_release_ranking=tool_ranking,
        confidence=0.8,
        reason_summary="skill tool math result fixture",
    )
    recommendation = SkillToolRecommendation(
        recommendation_ref=typed(965, "skill_tool_recommendation"),
        math_result=math_result,
        skill_selection_advice=selection_advice,
        tool_group_release_advice=release_advice,
        recommendation_mode=RecommendationMode.SUGGEST,
        confidence=0.8,
        reason_summary="recommendation remains advisory",
    )
    run_skill_display = RunSkillDisplayAdvice(
        advice_ref=typed(966, "run_skill_display_advice"),
        run_ref=run_ref,
        display_advice=display_advice,
        continuity_evaluation_ref=phase2["continuity_set"].evaluation_ref,
        reason_summary="run skill display fixture",
    )
    task_skill_selection = TaskSkillSelectionAdvice(
        advice_ref=typed(967, "task_skill_selection_advice"),
        task_ref=task_ref,
        selection_advice=selection_advice,
        route_ranking_ref=route_ranking.ranking_ref,
        reason_summary="task skill selection fixture",
    )
    turn_skill_activation = TurnSkillActivationAdvice(
        advice_ref=typed(968, "turn_skill_activation_advice"),
        turn_ref=turn_ref,
        activation_advice=activation_advice,
        reason_summary="turn skill activation fixture",
    )
    step_tool_release = StepToolGroupReleaseAdvice(
        advice_ref=typed(969, "step_tool_group_release_advice"),
        step_ref=step_ref,
        release_advice=release_advice,
        reason_summary="step tool group release fixture",
    )
    resume_advice = SkillToolResumeAdvice(
        advice_ref=typed(970, "skill_tool_resume_advice"),
        route_ranking=route_ranking,
        advice_kind=ResumeAdviceKind.RESUME_NEXT_STEP,
        suggested_route_ref=route_ranking.top_route_ref,
        math_result_ref=math_result.result_ref,
        reason_summary="skill tool resume fixture",
    )
    interruption_advice = SkillToolInterruptionAdvice(
        advice_ref=typed(971, "skill_tool_interruption_advice"),
        current_lifecycle=OrchestrationLifecycleKind.ACTIVE,
        suggested_lifecycle=OrchestrationLifecycleKind.WAITING,
        transition_intent=LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE,
        blocker_refs=(typed(972, "blocker_ref"),),
        reason_summary="wait for review fixture",
    )
    continuity_advice = SkillToolContinuityAdvice(
        advice_ref=typed(973, "skill_tool_continuity_advice"),
        continuity_evaluation=phase2["continuity_set"],
        route_ranking=route_ranking,
        math_result=math_result,
        recommended_route_ref=route_ranking.top_route_ref,
        confidence=0.8,
        reason_summary="skill tool continuity fixture",
    )
    transition_suggestion = SkillToolStateTransitionSuggestion(
        suggestion_ref=typed(974, "skill_tool_transition_suggestion"),
        subject_ref=skill_ref_1,
        transition_kind=SkillToolTransitionKind.SELECTION_TO_ACTIVATION,
        current_lifecycle=OrchestrationLifecycleKind.PREPARED,
        suggested_lifecycle=OrchestrationLifecycleKind.ACTIVE,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        transition_score=0.78,
        l2_update_suggestions=phase2["process_advice"].l2_state_update_suggestions,
        l5_review_hint_refs=(typed(975, "l5_review_hint"),),
        reason_summary="transition suggestion fixture",
    )

    return {
        "visibility_request": visibility_request,
        "skill_candidate_1": skill_candidate_1,
        "skill_candidate_2": skill_candidate_2,
        "skill_ranking": skill_ranking,
        "display_advice": display_advice,
        "selection_advice": selection_advice,
        "activation_advice": activation_advice,
        "deactivation_advice": deactivation_advice,
        "mismatch_advice": mismatch_advice,
        "clarification_advice": clarification_advice,
        "skill_transition": skill_transition,
        "resolve_request": resolve_request,
        "tool_candidate_1": tool_candidate_1,
        "tool_candidate_2": tool_candidate_2,
        "tool_ranking": tool_ranking,
        "release_advice": release_advice,
        "minimal_release_advice": minimal_release_advice,
        "lease_advice": lease_advice,
        "tool_transition": tool_transition,
        "skill_match": skill_match,
        "skill_risk": skill_risk,
        "tool_minimality": tool_minimality,
        "exposure_cost": exposure_cost,
        "sufficiency": sufficiency,
        "reversibility": reversibility,
        "stability": stability,
        "math_score_vector": math_score_vector,
        "math_input": math_input,
        "route_candidate_1": route_candidate_1,
        "route_candidate_2": route_candidate_2,
        "route_ranking": route_ranking,
        "math_result": math_result,
        "recommendation": recommendation,
        "run_skill_display": run_skill_display,
        "task_skill_selection": task_skill_selection,
        "turn_skill_activation": turn_skill_activation,
        "step_tool_release": step_tool_release,
        "resume_advice": resume_advice,
        "interruption_advice": interruption_advice,
        "continuity_advice": continuity_advice,
        "transition_suggestion": transition_suggestion,
    }
