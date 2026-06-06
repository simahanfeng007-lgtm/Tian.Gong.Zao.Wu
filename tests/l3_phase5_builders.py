from l3_phase1_builders import typed
from l3_phase4_builders import build_l3_phase4_objects
from tiangong_kernel.l3_orchestration import (
    AuditRequirementHint,
    BoundaryCheckEnvelope,
    BoundaryCheckRequest,
    BoundaryCheckRequestRef,
    BoundaryClarificationPathAdvice,
    BoundaryConfirmationPathAdvice,
    BoundaryContextSnapshotRef,
    BoundaryDegradePathAdvice,
    BoundaryDenialPathAdvice,
    BoundaryEvidenceRef,
    BoundaryExecutionMathInput,
    BoundaryExecutionMathResult,
    BoundaryExecutionRecommendation,
    BoundaryExecutionStateTransitionSuggestion,
    BoundaryExecutionTransitionKind,
    BoundaryFallbackPathAdvice,
    BoundaryPendingAdvice,
    BoundaryPreparationAdvice,
    BoundaryRequestKind,
    BoundaryRequestStatus,
    BoundaryRequirementHint,
    BoundaryResumeAdvice,
    BoundaryRetryPathAdvice,
    BoundaryReviewAdvice,
    BoundaryReviewAdviceKind,
    BoundaryRouteCandidate,
    BoundaryRouteKind,
    ConfirmationRequest,
    ConfirmationRequestRef,
    CredentialRequirementHint,
    ExecutionAuditRef,
    ExecutionCancelRef,
    ExecutionDispatchRequest,
    ExecutionDispatchRequestRef,
    ExecutionFailureRef,
    ExecutionFailureRoutingAdvice,
    ExecutionFallbackAdvice,
    ExecutionObservationRef,
    ExecutionPlanRef,
    ExecutionPreconditionHint,
    ExecutionRequest,
    ExecutionRequestKind,
    ExecutionRequestRef,
    ExecutionResultRef,
    ExecutionResultRoutingAdvice,
    ExecutionResumeRef,
    ExecutionRetryAdvice,
    ExecutionRouteCandidate,
    ExecutionRouteKind,
    ExecutionStateTransitionAdvice,
    ExecutionStepRef,
    ExecutionTokenRef,
    IntentToBoundaryAdvice,
    IntentToExecutionPreparationAdvice,
    LeaseRequest,
    LeaseRequestRef,
    LifecycleTransitionIntent,
    OrchestrationLifecycleKind,
    PermissionReviewRequest,
    PermissionReviewRequestRef,
    RecommendationMode,
    RiskReviewRequest,
    RiskReviewRequestRef,
    RunBoundaryAdvice,
    RunExecutionAdvice,
    ScoreDirection,
    SkillToolBoundaryContextRef,
    SkillToolExecutionContextRef,
    StepBoundaryAdvice,
    StepExecutionAdvice,
    TaskBoundaryAdvice,
    TaskExecutionAdvice,
    TurnBoundaryAdvice,
    TurnExecutionAdvice,
    build_boundary_clarification_need_score,
    build_boundary_completeness_score,
    build_boundary_evidence_sufficiency_score,
    build_boundary_execution_score_vector,
    build_boundary_readiness_score,
    build_boundary_route_ranking,
    build_execution_precondition_completeness_score,
    build_execution_readiness_score,
    build_execution_route_ranking,
)


def build_l3_phase5_objects():
    phase4 = build_l3_phase4_objects()
    phase3 = phase4["phase3"]
    run_ref = phase4["run_ref"]
    task_ref = phase4["task_ref"]
    turn_ref = phase4["turn_ref"]
    step_ref = phase4["step_ref"]
    skill_ref = phase4["skill_ref"]
    tool_group_ref = phase4["tool_group_ref"]
    action_ref = phase4["action_intent_ref"]
    tool_intent_ref = phase4["tool_intent_ref"]
    model_intent_ref = phase4["model_intent_ref"]

    evidence = BoundaryEvidenceRef(
        evidence_ref=typed(1500, "boundary_evidence"),
        evidence_kind_hint="intent_and_tool_group_context",
        source_intent_ref=action_ref.intent_ref,
        summary="references intent context only",
        confidence=0.82,
    )
    snapshot = BoundaryContextSnapshotRef(
        snapshot_ref=typed(1501, "boundary_context_snapshot"),
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        intent_ref=action_ref.intent_ref,
        summary="context snapshot reference only",
    )
    requirement = BoundaryRequirementHint(
        hint_ref=typed(1502, "boundary_requirement_hint"),
        requirement_kind=BoundaryRequestKind.BOUNDARY_CHECK,
        required_field_names=("intent_ref", "tool_group_ref", "evidence_ref"),
        evidence_refs=(evidence,),
        reason_codes=("future_l5_review_context",),
        summary="prepare future boundary review context",
    )
    credential_hint = CredentialRequirementHint(
        hint_ref=typed(1503, "credential_requirement_hint"),
        credential_scope_hint="no_credential_read_in_l3",
        related_request_ref=typed(1504, "boundary_request"),
        reason_codes=("credential_review_is_future_l5_only",),
        summary="credential is only a future review hint",
    )
    audit_hint = AuditRequirementHint(
        hint_ref=typed(1505, "audit_requirement_hint"),
        audit_scope_hint="future_audit_record_only",
        related_request_ref=typed(1504, "boundary_request"),
        reason_codes=("audit_write_is_not_l3",),
        summary="audit is only a future hint",
    )
    boundary_ref = BoundaryCheckRequestRef(
        request_ref=typed(1504, "boundary_request"),
        model_intent_ref=model_intent_ref,
        tool_intent_ref=tool_intent_ref,
        action_intent_ref=action_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        skill_ref=skill_ref,
        tool_group_ref=tool_group_ref,
    )
    boundary_request = BoundaryCheckRequest(
        request_ref=boundary_ref,
        requested_review_kinds=(
            BoundaryRequestKind.BOUNDARY_CHECK,
            BoundaryRequestKind.RISK_REVIEW,
            BoundaryRequestKind.PERMISSION_REVIEW,
            BoundaryRequestKind.CONFIRMATION,
            BoundaryRequestKind.LEASE,
        ),
        evidence_refs=(evidence,),
        context_snapshot_refs=(snapshot,),
        requirement_hints=(requirement,),
        credential_requirement_hint=credential_hint,
        audit_requirement_hint=audit_hint,
        reason_summary="future L5 request object only",
    )
    boundary_envelope = BoundaryCheckEnvelope(
        envelope_ref=typed(1506, "boundary_envelope"),
        request=boundary_request,
        status=BoundaryRequestStatus.PREPARED,
        present_field_names=("intent_ref", "tool_group_ref", "evidence_ref"),
        missing_field_names=("confirmation_prompt",),
        readiness_hint=0.78,
        reason_summary="boundary request is prepared but still advisory",
    )
    risk_ref = RiskReviewRequestRef(
        request_ref=typed(1507, "risk_review_request"),
        boundary_request_ref=boundary_ref.request_ref,
        source_intent_ref=action_ref.intent_ref,
    )
    risk_request = RiskReviewRequest(
        request_ref=risk_ref,
        risk_factor_hints=("tool_exposure", "reversibility"),
        evidence_refs=(evidence,),
        reason_summary="risk review request only",
    )
    permission_ref = PermissionReviewRequestRef(
        request_ref=typed(1508, "permission_review_request"),
        boundary_request_ref=boundary_ref.request_ref,
        source_intent_ref=action_ref.intent_ref,
    )
    permission_request = PermissionReviewRequest(
        request_ref=permission_ref,
        required_permission_hints=("future_tool_group_use",),
        context_snapshot_refs=(snapshot,),
        reason_summary="permission review request only",
    )
    confirmation_ref = ConfirmationRequestRef(
        request_ref=typed(1509, "confirmation_request"),
        boundary_request_ref=boundary_ref.request_ref,
        source_intent_ref=action_ref.intent_ref,
    )
    confirmation_request = ConfirmationRequest(
        request_ref=confirmation_ref,
        confirmation_prompt_hints=("confirm future tool group use before L4",),
        required_acknowledgement_hints=("user acknowledgement would be future L5 concern",),
        reason_summary="confirmation request does not issue a ticket",
    )
    lease_ref = LeaseRequestRef(
        request_ref=typed(1510, "lease_request"),
        boundary_request_ref=boundary_ref.request_ref,
        source_tool_group_ref=tool_group_ref,
    )
    lease_request = LeaseRequest(
        request_ref=lease_ref,
        lease_subject_refs=(tool_group_ref,),
        requested_scope_hints=("future_tool_group_lease_review",),
        duration_hint="future_review_required",
        reason_summary="lease request does not grant lease",
    )
    boundary_prep = BoundaryPreparationAdvice(
        advice_ref=typed(1511, "boundary_preparation_advice"),
        envelope=boundary_envelope,
        requirement_hints=(requirement,),
        next_preparation_hint="collect_confirmation_prompt_hint",
        readiness_hint=0.78,
        reason_codes=("missing_confirmation_prompt",),
        reason_summary="prepare future L5 review only",
    )
    boundary_review = BoundaryReviewAdvice(
        advice_ref=typed(1512, "boundary_review_advice"),
        envelope=boundary_envelope,
        advice_kind=BoundaryReviewAdviceKind.PREPARE,
        preparation_advice=boundary_prep,
        confidence=0.8,
        reason_summary="boundary review advice only",
    )
    denial_path = BoundaryDenialPathAdvice(
        advice_ref=typed(1513, "boundary_denial_path_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.08,
        reason_codes=("not_preferred",),
        reason_summary="denial is only a path suggestion",
    )
    degrade_path = BoundaryDegradePathAdvice(
        advice_ref=typed(1514, "boundary_degrade_path_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.42,
        reason_codes=("missing_confirmation_prompt",),
        reason_summary="degrade is only a path suggestion",
    )
    confirm_path = BoundaryConfirmationPathAdvice(
        advice_ref=typed(1515, "boundary_confirmation_path_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.82,
        related_request_refs=(confirmation_ref.request_ref,),
        reason_codes=("confirmation_context_needed",),
        reason_summary="confirmation path suggestion only",
    )
    retry_path = BoundaryRetryPathAdvice(
        advice_ref=typed(1516, "boundary_retry_path_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.55,
        reason_codes=("retry_after_clarification",),
        reason_summary="retry is only a path suggestion",
    )
    clarify_path = BoundaryClarificationPathAdvice(
        advice_ref=typed(1517, "boundary_clarification_path_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.64,
        reason_codes=("clarify_confirmation_prompt",),
        reason_summary="clarification path suggestion only",
    )
    pending_path = BoundaryPendingAdvice(
        advice_ref=typed(1518, "boundary_pending_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.45,
        reason_codes=("waiting_for_future_l5",),
    )
    fallback_path = BoundaryFallbackPathAdvice(
        advice_ref=typed(1519, "boundary_fallback_path_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.38,
        reason_codes=("fallback_available",),
    )
    resume_path = BoundaryResumeAdvice(
        advice_ref=typed(1520, "boundary_resume_advice"),
        boundary_request_ref=boundary_ref.request_ref,
        priority_score=0.7,
        reason_codes=("resume_review_preparation",),
    )
    boundary_candidate_1 = BoundaryRouteCandidate(
        route_ref=typed(1521, "boundary_route"),
        route_kind=BoundaryRouteKind.CONFIRMATION_PATH,
        boundary_request_ref=boundary_ref.request_ref,
        readiness_score=0.86,
        evidence_score=0.9,
        clarification_need_score=0.18,
        caution_score=0.8,
        continuity_score=0.82,
        reason_codes=("confirmation path has enough context",),
    )
    boundary_candidate_2 = BoundaryRouteCandidate(
        route_ref=typed(1522, "boundary_route"),
        route_kind=BoundaryRouteKind.CLARIFICATION_PATH,
        boundary_request_ref=boundary_ref.request_ref,
        readiness_score=0.72,
        evidence_score=0.7,
        clarification_need_score=0.52,
        caution_score=0.78,
        continuity_score=0.76,
        reason_codes=("clarification remains possible",),
    )
    boundary_ranking = build_boundary_route_ranking(typed(1523, "boundary_route_ranking"), (boundary_candidate_2, boundary_candidate_1))

    plan_ref = ExecutionPlanRef(
        plan_ref=typed(1524, "execution_plan_ref"),
        source_intent_ref=action_ref.intent_ref,
    )
    execution_step = ExecutionStepRef(
        step_ref=typed(1525, "execution_step_ref"),
        plan_ref=plan_ref.plan_ref,
        step_label="future tool preparation step",
        sequence_index=0,
    )
    token_ref = ExecutionTokenRef(
        token_ref=typed(1526, "execution_token_ref"),
        source_boundary_request_ref=boundary_ref.request_ref,
    )
    precondition_hint = ExecutionPreconditionHint(
        hint_ref=typed(1527, "execution_precondition_hint"),
        required_precondition_refs=(confirmation_ref.request_ref, permission_ref.request_ref),
        satisfied_precondition_refs=(permission_ref.request_ref,),
        missing_precondition_refs=(confirmation_ref.request_ref,),
        precondition_score=0.5,
        reason_summary="confirmation remains future L5 concern",
    )
    execution_ref = ExecutionRequestRef(
        request_ref=typed(1528, "execution_request"),
        action_intent_ref=action_ref,
        tool_intent_ref=tool_intent_ref,
        boundary_request_ref=boundary_ref.request_ref,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
    )
    execution_request = ExecutionRequest(
        request_ref=execution_ref,
        execution_plan_ref=plan_ref,
        execution_step_refs=(execution_step,),
        precondition_hint=precondition_hint,
        execution_token_ref=token_ref,
        payload_field_names=("action_intent_ref", "tool_intent_ref", "boundary_request_ref"),
        missing_field_names=("future_confirmation_result",),
        reason_summary="future L4 request object only",
    )
    dispatch_ref = ExecutionDispatchRequestRef(
        request_ref=typed(1529, "execution_dispatch_request"),
        execution_request_ref=execution_ref.request_ref,
        boundary_request_ref=boundary_ref.request_ref,
    )
    dispatch_request = ExecutionDispatchRequest(
        request_ref=dispatch_ref,
        execution_request=execution_request,
        dispatch_precondition_refs=(permission_ref.request_ref, confirmation_ref.request_ref),
        readiness_hint=0.62,
        reason_summary="future L4 dispatch request only",
    )
    result_ref = ExecutionResultRef(
        result_ref=typed(1530, "execution_result_ref"),
        execution_request_ref=execution_ref.request_ref,
        summary="future result reference only",
    )
    failure_ref = ExecutionFailureRef(
        failure_ref=typed(1531, "execution_failure_ref"),
        execution_request_ref=execution_ref.request_ref,
        recoverable_hint=True,
        summary="future failure reference only",
    )
    resume_ref = ExecutionResumeRef(
        resume_ref=typed(1532, "execution_resume_ref"),
        execution_request_ref=execution_ref.request_ref,
    )
    cancel_ref = ExecutionCancelRef(
        cancel_ref=typed(1533, "execution_cancel_ref"),
        execution_request_ref=execution_ref.request_ref,
    )
    observation_ref = ExecutionObservationRef(
        observation_ref=typed(1534, "execution_observation_ref"),
        execution_request_ref=execution_ref.request_ref,
    )
    execution_audit_ref = ExecutionAuditRef(
        audit_ref=typed(1535, "execution_audit_ref"),
        execution_request_ref=execution_ref.request_ref,
    )
    result_routing = ExecutionResultRoutingAdvice(
        advice_ref=typed(1536, "execution_result_routing_advice"),
        result_ref=result_ref,
        observation_refs=(observation_ref,),
        audit_refs=(execution_audit_ref,),
        reason_summary="future result routing advice only",
    )
    retry_advice = ExecutionRetryAdvice(
        advice_ref=typed(1537, "execution_retry_advice"),
        execution_request_ref=execution_ref.request_ref,
        retry_condition_hints=("future boundary response is retryable",),
        retry_score=0.55,
        reason_summary="retry is not executed in L3",
    )
    fallback_advice = ExecutionFallbackAdvice(
        advice_ref=typed(1538, "execution_fallback_advice"),
        execution_request_ref=execution_ref.request_ref,
        fallback_path_hints=("future safe fallback",),
        fallback_score=0.42,
        reason_summary="fallback is not executed in L3",
    )
    failure_routing = ExecutionFailureRoutingAdvice(
        advice_ref=typed(1539, "execution_failure_routing_advice"),
        failure_ref=failure_ref,
        retry_advice_refs=(retry_advice.advice_ref,),
        fallback_advice_refs=(fallback_advice.advice_ref,),
        reason_summary="future failure routing advice only",
    )
    execution_candidate_1 = ExecutionRouteCandidate(
        route_ref=typed(1540, "execution_route"),
        route_kind=ExecutionRouteKind.WAIT_FOR_BOUNDARY,
        execution_request_ref=execution_ref.request_ref,
        readiness_score=0.7,
        precondition_score=precondition_hint.precondition_score,
        continuity_score=phase4["readiness_score"].value,
        reversibility_score=phase4["reversibility_hint"].reversibility_score,
        boundary_dependency_score=0.9,
        reason_codes=("future boundary response required",),
    )
    execution_candidate_2 = ExecutionRouteCandidate(
        route_ref=typed(1541, "execution_route"),
        route_kind=ExecutionRouteKind.PREPARE_DISPATCH,
        execution_request_ref=execution_ref.request_ref,
        readiness_score=0.62,
        precondition_score=precondition_hint.precondition_score,
        continuity_score=0.8,
        reversibility_score=0.76,
        boundary_dependency_score=0.58,
        reason_codes=("dispatch remains future L4",),
    )
    execution_ranking = build_execution_route_ranking(typed(1542, "execution_route_ranking"), (execution_candidate_2, execution_candidate_1))

    boundary_completeness = build_boundary_completeness_score(typed(1543, "boundary_completeness_score"), boundary_envelope)
    evidence_sufficiency = build_boundary_evidence_sufficiency_score(typed(1544, "boundary_evidence_sufficiency_score"), boundary_request, expected_evidence_count=1)
    clarification_need = build_boundary_clarification_need_score(
        typed(1545, "boundary_clarification_need_score"),
        boundary_completeness,
        evidence_sufficiency,
        affective_input=phase3["math_input"].affective_input,
        dynamic_drive_input=phase3["math_input"].dynamic_drive_input,
    )
    boundary_readiness = build_boundary_readiness_score(
        typed(1546, "boundary_readiness_score"),
        boundary_completeness,
        evidence_sufficiency,
        clarification_need,
    )
    precondition_score = build_execution_precondition_completeness_score(
        typed(1547, "execution_precondition_completeness_score"),
        precondition_hint,
    )
    execution_readiness = build_execution_readiness_score(
        typed(1548, "execution_readiness_score"),
        execution_request,
        precondition_score,
        boundary_readiness,
        continuity_score=phase4["route_candidate_1"].continuity_score,
        reversibility_score=phase4["reversibility_hint"].reversibility_score,
    )
    score_vector = build_boundary_execution_score_vector(
        typed(1549, "boundary_execution_score_vector"),
        (boundary_completeness, evidence_sufficiency, clarification_need, boundary_readiness, precondition_score, execution_readiness),
    )
    math_input = BoundaryExecutionMathInput(
        input_ref=typed(1550, "boundary_execution_math_input"),
        boundary_request_refs=(boundary_ref.request_ref,),
        execution_request_refs=(execution_ref.request_ref,),
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        intent_math_result=phase4["math_result"],
        skill_tool_math_result=phase3["math_result"],
        continuity_evaluation=phase4["phase3"]["math_input"].continuity_evaluation,
        affective_input=phase3["math_input"].affective_input,
        dynamic_drive_input=phase3["math_input"].dynamic_drive_input,
        future_l5_context_refs=(boundary_ref.request_ref,),
        future_l4_context_refs=(execution_ref.request_ref,),
        summary="boundary execution math input fixture",
    )
    math_result = BoundaryExecutionMathResult(
        result_ref=typed(1551, "boundary_execution_math_result"),
        math_input=math_input,
        score_vector=score_vector,
        boundary_route_ranking_ref=boundary_ranking.ranking_ref,
        execution_route_ranking_ref=execution_ranking.ranking_ref,
        confidence=0.8,
        reason_summary="boundary and execution math remains advisory",
    )
    recommendation = BoundaryExecutionRecommendation(
        recommendation_ref=typed(1552, "boundary_execution_recommendation"),
        math_result=math_result,
        recommendation_mode=RecommendationMode.SUGGEST,
        recommended_boundary_route_ref=boundary_ranking.top_route_ref,
        recommended_execution_route_ref=execution_ranking.top_route_ref,
        boundary_review_advice_refs=(boundary_review.advice_ref,),
        execution_preparation_advice_refs=(dispatch_ref.request_ref,),
        confidence=0.8,
        reason_summary="recommend future request preparation only",
    )
    boundary_context = SkillToolBoundaryContextRef(
        context_ref=typed(1553, "skill_tool_boundary_context_ref"),
        skill_ref=skill_ref,
        tool_group_ref=tool_group_ref,
        intent_ref=action_ref.intent_ref,
        boundary_request_ref=boundary_ref.request_ref,
        summary="skill tool boundary context reference only",
    )
    execution_context = SkillToolExecutionContextRef(
        context_ref=typed(1554, "skill_tool_execution_context_ref"),
        skill_ref=skill_ref,
        tool_group_ref=tool_group_ref,
        action_intent_ref=action_ref.intent_ref,
        execution_request_ref=execution_ref.request_ref,
        summary="skill tool execution context reference only",
    )
    intent_to_boundary = IntentToBoundaryAdvice(
        advice_ref=typed(1555, "intent_to_boundary_advice"),
        intent_ref=action_ref.intent_ref,
        boundary_request=boundary_request,
        boundary_context_refs=(boundary_context,),
        boundary_review_advice_refs=(boundary_review.advice_ref,),
        reason_summary="intent to boundary request advice only",
    )
    intent_to_execution = IntentToExecutionPreparationAdvice(
        advice_ref=typed(1556, "intent_to_execution_preparation_advice"),
        intent_ref=action_ref.intent_ref,
        execution_request=execution_request,
        execution_context_refs=(execution_context,),
        boundary_request_ref=boundary_ref.request_ref,
        reason_summary="intent to execution preparation advice only",
    )
    run_boundary = RunBoundaryAdvice(
        advice_ref=typed(1557, "run_boundary_advice"),
        run_ref=run_ref,
        boundary_route_ranking=boundary_ranking,
        boundary_review_advice=boundary_review,
        reason_summary="run boundary advice only",
    )
    task_boundary = TaskBoundaryAdvice(
        advice_ref=typed(1558, "task_boundary_advice"),
        task_ref=task_ref,
        boundary_request_ref=boundary_ref.request_ref,
        boundary_route_ranking_ref=boundary_ranking.ranking_ref,
        reason_summary="task boundary advice only",
    )
    turn_boundary = TurnBoundaryAdvice(
        advice_ref=typed(1559, "turn_boundary_advice"),
        turn_ref=turn_ref,
        boundary_request_ref=boundary_ref.request_ref,
        carryover_context_refs=(snapshot.snapshot_ref,),
        reason_summary="turn boundary advice only",
    )
    step_boundary = StepBoundaryAdvice(
        advice_ref=typed(1560, "step_boundary_advice"),
        step_ref=step_ref,
        boundary_request_ref=boundary_ref.request_ref,
        preparation_hint_refs=(requirement.hint_ref,),
        reason_summary="step boundary advice only",
    )
    run_execution = RunExecutionAdvice(
        advice_ref=typed(1561, "run_execution_advice"),
        run_ref=run_ref,
        execution_route_ranking=execution_ranking,
        dispatch_request=dispatch_request,
        reason_summary="run execution advice only",
    )
    task_execution = TaskExecutionAdvice(
        advice_ref=typed(1562, "task_execution_advice"),
        task_ref=task_ref,
        execution_request_ref=execution_ref.request_ref,
        execution_route_ranking_ref=execution_ranking.ranking_ref,
        reason_summary="task execution advice only",
    )
    turn_execution = TurnExecutionAdvice(
        advice_ref=typed(1563, "turn_execution_advice"),
        turn_ref=turn_ref,
        execution_request_ref=execution_ref.request_ref,
        carryover_context_refs=(snapshot.snapshot_ref,),
        reason_summary="turn execution advice only",
    )
    step_execution = StepExecutionAdvice(
        advice_ref=typed(1564, "step_execution_advice"),
        step_ref=step_ref,
        execution_request_ref=execution_ref.request_ref,
        precondition_hint_refs=(precondition_hint.hint_ref,),
        reason_summary="step execution advice only",
    )
    state_transition = BoundaryExecutionStateTransitionSuggestion(
        suggestion_ref=typed(1565, "boundary_execution_state_transition"),
        subject_ref=boundary_ref.request_ref,
        transition_kind=BoundaryExecutionTransitionKind.INTENT_TO_BOUNDARY,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.PREPARED,
        transition_intent=LifecycleTransitionIntent.CONTINUE_CURRENT_STEP,
        transition_score=0.8,
        related_advice_refs=(intent_to_boundary.advice_ref,),
        reason_summary="prepare future boundary request only",
    )
    execution_transition = ExecutionStateTransitionAdvice(
        advice_ref=typed(1566, "execution_state_transition"),
        execution_request_ref=execution_ref.request_ref,
        current_lifecycle=OrchestrationLifecycleKind.CREATED,
        suggested_lifecycle=OrchestrationLifecycleKind.WAITING,
        transition_intent=LifecycleTransitionIntent.WAIT_FOR_MISSING_STATE,
        transition_score=0.62,
        blocker_refs=(confirmation_ref.request_ref,),
        reason_summary="wait for future L5 confirmation reference",
    )

    return locals()
