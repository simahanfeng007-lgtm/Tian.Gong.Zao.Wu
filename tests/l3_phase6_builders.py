from l3_phase1_builders import typed
from l3_phase5_builders import build_l3_phase5_objects
from tiangong_kernel.l3_orchestration import (
    AffectiveBehaviorTendencyAdvice,
    AffectiveExpressionAdvice,
    AffectiveServiceRequest,
    AffectiveServiceRequestRef,
    AffectiveTendencyAdvice,
    AffectiveWeightAdjustmentHint,
    AffectiveWeightInputRef,
    CandidateEvidenceRef,
    CandidateProposalAdvice,
    CandidateProposalKind,
    CandidatePromotionAdvice,
    CandidateRejectAdvice,
    CandidateReviewRequestHint,
    CandidateRouteCandidate,
    CandidateSignalAdvice,
    ContextCarryoverAdvice,
    ContextCompressionNeedAdvice,
    ContextDropAdvice,
    ContextPriorityAdvice,
    ContextRetentionAdvice,
    ContextWindowAdvice,
    ExecutionResultContextAdvice,
    ExecutionToObservationAdvice,
    IntentObservationFeedbackAdvice,
    LearningCandidateAdvice,
    LearningEvidenceRef,
    LearningServiceRequest,
    LearningServiceRequestRef,
    LearningSignalAdvice,
    MemoryConflictReviewAdvice,
    MemoryPromotionSignalAdvice,
    MemoryRecallRequestHint,
    MemoryServiceRequest,
    MemoryServiceRequestRef,
    MemoryWriteSuggestion,
    ObservationEnvelope,
    ObservationEnvelopeStatus,
    ObservationFeedbackAdvice,
    ObservationFeedbackKind,
    ObservationResultRef,
    ObservationRoutingAdvice,
    ObservationTrustHint,
    RecommendationMode,
    RetrievalPriorityAdvice,
    RetrievalQueryHint,
    RetrievalScopeHint,
    RetrievalServiceRequest,
    RetrievalServiceRequestRef,
    RunObservationAdvice,
    RunSubsystemServiceAdvice,
    SkillToolContextCarryoverAdvice,
    StepObservationAdvice,
    StepSubsystemServiceAdvice,
    SubsystemServiceEnvelope,
    SubsystemServiceKind,
    SubsystemServiceRecommendation,
    SubsystemServiceRequest,
    SubsystemServiceRequestRef,
    SubsystemServiceRequestStatus,
    SubsystemServiceRequirementHint,
    SubsystemServiceRouteCandidate,
    SubsystemServiceStateTransitionAdvice,
    TaskObservationAdvice,
    TaskSubsystemServiceAdvice,
    TurnObservationAdvice,
    TurnSubsystemServiceAdvice,
    build_affective_need_score,
    build_candidate_learning_value_score,
    build_candidate_priority_score,
    build_candidate_route_ranking,
    build_context_compression_need_score,
    build_context_continuity_score,
    build_context_value_score,
    build_learning_need_score,
    build_learning_signal_value_score,
    build_memory_need_score,
    build_observation_completeness_score,
    build_observation_context_score_vector,
    build_observation_context_subsystem_route_ranking,
    build_observation_credibility_score,
    build_observation_relevance_score,
    build_retrieval_need_score,
    build_subsystem_service_readiness_score,
)


def build_l3_phase6_objects():
    phase5 = build_l3_phase5_objects()
    run_ref = phase5["run_ref"]
    task_ref = phase5["task_ref"]
    turn_ref = phase5["turn_ref"]
    step_ref = phase5["step_ref"]
    action_ref = phase5["action_ref"]
    skill_ref = phase5["skill_ref"]
    tool_group_ref = phase5["tool_group_ref"]
    execution_result_ref = phase5["result_ref"]
    execution_failure_ref = phase5["failure_ref"]

    observation_ref = ObservationResultRef(
        observation_ref=typed(1800, "observation_result"),
        source_execution_result_ref=execution_result_ref,
        source_execution_failure_ref=execution_failure_ref,
        observation_kind_hint="future_l4_result_observation_ref",
        summary="observation result reference only",
        confidence=0.82,
    )
    trust_hint = ObservationTrustHint(
        hint_ref=typed(1801, "observation_trust_hint"),
        observation_ref=observation_ref.observation_ref,
        trust_basis_refs=(execution_result_ref.result_ref,),
        trust_level_hint="high",
        reason_codes=("execution_result_linked",),
        summary="trust hint does not verify anything",
    )
    observation_envelope = ObservationEnvelope(
        envelope_ref=typed(1802, "observation_envelope"),
        observation_ref=observation_ref,
        status=ObservationEnvelopeStatus.READY_FOR_ROUTING_ADVICE,
        run_ref=run_ref,
        task_ref=task_ref,
        turn_ref=turn_ref,
        step_ref=step_ref,
        related_execution_result_refs=(execution_result_ref.result_ref,),
        trust_hints=(trust_hint,),
        present_field_names=("observation_ref", "run_ref", "step_ref"),
        missing_field_names=("human_review_summary",),
        reason_summary="observation envelope is a reference container only",
    )
    feedback_advice = ObservationFeedbackAdvice(
        advice_ref=typed(1803, "observation_feedback_advice"),
        envelope=observation_envelope,
        feedback_kind=ObservationFeedbackKind.ROUTE_TO_STEP,
        target_refs=(step_ref,),
        reason_codes=("step_feedback_target",),
        confidence=0.81,
        reason_summary="route observation ref back to step context",
    )
    routing_advice = ObservationRoutingAdvice(
        advice_ref=typed(1804, "observation_routing_advice"),
        observation_ref=observation_ref.observation_ref,
        target_scores=((step_ref, 0.88), (turn_ref, 0.72)),
        top_target_ref=step_ref,
        alternative_target_refs=(turn_ref,),
        reason_codes=("step_has_highest_observation_relevance",),
        confidence=0.8,
    )

    context_carryover = ContextCarryoverAdvice(
        advice_ref=typed(1810, "context_carryover_advice"),
        source_context_refs=(observation_ref.observation_ref, action_ref.intent_ref),
        target_context_ref=typed(1811, "context_ref"),
        value_hint=0.84,
        reason_codes=("observation_and_intent_context_are_relevant",),
        summary="carryover advice only",
    )
    context_window = ContextWindowAdvice(
        advice_ref=typed(1812, "context_window_advice"),
        window_ref=typed(1813, "context_window"),
        retained_context_refs=(context_carryover.target_context_ref,),
        dropped_context_refs=(typed(1814, "low_value_context"),),
        estimated_window_pressure=0.66,
        reason_codes=("moderate_window_pressure",),
    )
    compression_need = ContextCompressionNeedAdvice(
        advice_ref=typed(1815, "context_compression_need_advice"),
        context_refs=(context_carryover.target_context_ref,),
        compression_need_hint=0.66,
        reason_codes=("window_pressure_only",),
    )
    retention = ContextRetentionAdvice(
        advice_ref=typed(1816, "context_retention_advice"),
        context_refs=(context_carryover.target_context_ref,),
        retention_value_hint=0.82,
        reason_codes=("target_context_has_value",),
    )
    drop = ContextDropAdvice(
        advice_ref=typed(1817, "context_drop_advice"),
        context_refs=(typed(1814, "low_value_context"),),
        drop_suitability_hint=0.7,
        reason_codes=("low_value_context_only",),
    )
    priority = ContextPriorityAdvice(
        advice_ref=typed(1818, "context_priority_advice"),
        context_scores=((context_carryover.target_context_ref, 0.84), (typed(1814, "low_value_context"), 0.2)),
        top_context_ref=context_carryover.target_context_ref,
        reason_codes=("carryover_context_top",),
    )

    memory_ref = MemoryServiceRequestRef(
        request_ref=typed(1820, "memory_service_request"),
        source_context_ref=context_carryover.target_context_ref,
    )
    recall_hint = MemoryRecallRequestHint(
        hint_ref=typed(1821, "memory_recall_hint"),
        query_hint_refs=(context_carryover.target_context_ref,),
        reason_codes=("future_recall_may_help_continuity",),
    )
    write_suggestion = MemoryWriteSuggestion(
        suggestion_ref=typed(1822, "memory_write_suggestion"),
        candidate_content_refs=(observation_ref.observation_ref,),
        value_hint=0.78,
        reason_codes=("observation_result_may_be_useful_later",),
    )
    promotion = MemoryPromotionSignalAdvice(
        advice_ref=typed(1823, "memory_promotion_signal_advice"),
        memory_candidate_refs=(observation_ref.observation_ref,),
        promotion_value_hint=0.64,
        reason_codes=("reusable_signal",),
    )
    memory_conflict = MemoryConflictReviewAdvice(
        advice_ref=typed(1824, "memory_conflict_review_advice"),
        conflicting_memory_refs=(typed(1825, "memory_candidate_old"), observation_ref.observation_ref),
        reason_codes=("candidate_conflict_requires_future_review",),
    )
    memory_request = MemoryServiceRequest(
        request_ref=memory_ref,
        recall_hints=(recall_hint,),
        write_suggestions=(write_suggestion,),
        promotion_advices=(promotion,),
        conflict_review_advices=(memory_conflict,),
        reason_summary="memory service request object only",
    )

    retrieval_ref = RetrievalServiceRequestRef(
        request_ref=typed(1830, "retrieval_service_request"),
        source_context_ref=context_carryover.target_context_ref,
    )
    query_hint = RetrievalQueryHint(
        hint_ref=typed(1831, "retrieval_query_hint"),
        query_terms=("phase6 boundary", "observation feedback"),
        source_context_refs=(context_carryover.target_context_ref,),
        reason_codes=("missing_external_context_hint",),
    )
    scope_hint = RetrievalScopeHint(
        hint_ref=typed(1832, "retrieval_scope_hint"),
        scope_names=("project_docs",),
        excluded_scope_names=("network",),
        reason_codes=("future_scope_only",),
    )
    retrieval_priority = RetrievalPriorityAdvice(
        advice_ref=typed(1833, "retrieval_priority_advice"),
        request_ref=retrieval_ref.request_ref,
        priority_hint=0.72,
        reason_codes=("context_gap",),
    )
    retrieval_request = RetrievalServiceRequest(
        request_ref=retrieval_ref,
        query_hints=(query_hint,),
        scope_hints=(scope_hint,),
        priority_advices=(retrieval_priority,),
        reason_summary="retrieval service request object only",
    )

    learning_ref = LearningServiceRequestRef(
        request_ref=typed(1840, "learning_service_request"),
        source_signal_ref=observation_ref.observation_ref,
    )
    learning_evidence = LearningEvidenceRef(
        evidence_ref=typed(1841, "learning_evidence_ref"),
        source_observation_ref=observation_ref.observation_ref,
        summary="learning evidence reference only",
        confidence=0.78,
    )
    learning_signal = LearningSignalAdvice(
        advice_ref=typed(1842, "learning_signal_advice"),
        signal_refs=(observation_ref.observation_ref,),
        signal_value_hint=0.7,
        evidence_refs=(learning_evidence,),
        reason_codes=("repeatable_orchestration_signal",),
    )
    learning_candidate = LearningCandidateAdvice(
        advice_ref=typed(1843, "learning_candidate_advice"),
        candidate_refs=(typed(1844, "learning_candidate"),),
        learning_value_hint=0.72,
        evidence_refs=(learning_evidence,),
        reason_codes=("candidate_needs_future_learning_review",),
    )
    learning_request = LearningServiceRequest(
        request_ref=learning_ref,
        signal_advices=(learning_signal,),
        candidate_advices=(learning_candidate,),
        evidence_refs=(learning_evidence,),
        reason_summary="learning service request object only",
    )

    affective_ref = AffectiveServiceRequestRef(
        request_ref=typed(1850, "affective_service_request"),
        source_context_ref=context_carryover.target_context_ref,
    )
    affective_input_ref = AffectiveWeightInputRef(
        input_ref=typed(1851, "affective_weight_input_ref"),
        source_weight_input=phase5["phase3"]["math_input"].affective_input,
        summary="affective weight input reference only",
    )
    tendency = AffectiveTendencyAdvice(
        advice_ref=typed(1852, "affective_tendency_advice"),
        weight_input_ref=affective_input_ref.input_ref,
        tendency_score_hint=0.68,
        reason_codes=("context_preservation_tendency",),
    )
    expression = AffectiveExpressionAdvice(
        advice_ref=typed(1853, "affective_expression_advice"),
        expression_style_hint="clear_and_calm",
        directness_hint=0.72,
        warmth_hint=0.38,
        reason_codes=("expression_advice_only",),
    )
    behavior_tendency = AffectiveBehaviorTendencyAdvice(
        advice_ref=typed(1854, "affective_behavior_tendency_advice"),
        service_kind_hint=SubsystemServiceKind.MEMORY,
        tendency_score_hint=0.62,
        reason_codes=("service_priority_tendency_only",),
    )
    adjustment_hint = AffectiveWeightAdjustmentHint(
        hint_ref=typed(1855, "affective_weight_adjustment_hint"),
        weight_input_ref=affective_input_ref.input_ref,
        adjustment_value_hint=0.22,
        reason_codes=("future_review_only",),
    )
    affective_request = AffectiveServiceRequest(
        request_ref=affective_ref,
        weight_input_refs=(affective_input_ref,),
        tendency_advices=(tendency,),
        expression_advices=(expression,),
        behavior_tendency_advices=(behavior_tendency,),
        adjustment_hints=(adjustment_hint,),
        reason_summary="affective service request object only",
    )

    candidate_ref = typed(1860, "candidate_proposal")
    candidate_evidence = CandidateEvidenceRef(
        evidence_ref=typed(1861, "candidate_evidence_ref"),
        source_ref=observation_ref.observation_ref,
        summary="candidate evidence reference only",
        confidence=0.79,
    )
    candidate_signal = CandidateSignalAdvice(
        advice_ref=typed(1862, "candidate_signal_advice"),
        candidate_ref=candidate_ref,
        proposal_kind=CandidateProposalKind.LEARNING,
        signal_value_hint=0.74,
        evidence_refs=(candidate_evidence,),
        reason_codes=("learning_candidate_signal",),
    )
    candidate_review = CandidateReviewRequestHint(
        hint_ref=typed(1863, "candidate_review_request_hint"),
        candidate_ref=candidate_ref,
        evidence_refs=(candidate_evidence,),
        reason_codes=("future_candidate_review",),
    )
    candidate_proposal = CandidateProposalAdvice(
        advice_ref=typed(1864, "candidate_proposal_advice"),
        candidate_ref=candidate_ref,
        proposal_kind=CandidateProposalKind.LEARNING,
        signal_advices=(candidate_signal,),
        review_hints=(candidate_review,),
        evidence_refs=(candidate_evidence,),
        priority_hint=0.73,
        reason_summary="candidate proposal advice only",
    )
    candidate_promotion = CandidatePromotionAdvice(
        advice_ref=typed(1865, "candidate_promotion_advice"),
        candidate_ref=candidate_ref,
        promotion_value_hint=0.62,
        evidence_refs=(candidate_evidence,),
        reason_codes=("future_promotion_review",),
    )
    candidate_reject = CandidateRejectAdvice(
        advice_ref=typed(1866, "candidate_reject_advice"),
        candidate_ref=candidate_ref,
        reject_suitability_hint=0.15,
        reason_codes=("not_preferred",),
    )

    subsystem_requirement = SubsystemServiceRequirementHint(
        hint_ref=typed(1870, "subsystem_service_requirement_hint"),
        service_kind=SubsystemServiceKind.MEMORY,
        required_field_names=("source_context_ref", "reason_summary"),
        related_context_refs=(context_carryover.target_context_ref,),
        reason_codes=("future_service_context_required",),
        summary="future service requirement hint only",
    )
    subsystem_ref = SubsystemServiceRequestRef(
        request_ref=typed(1871, "subsystem_service_request"),
        service_kind=SubsystemServiceKind.MEMORY,
        source_run_ref=run_ref,
        source_task_ref=task_ref,
        source_turn_ref=turn_ref,
        source_step_ref=step_ref,
        source_observation_ref=observation_ref.observation_ref,
    )
    subsystem_request = SubsystemServiceRequest(
        request_ref=subsystem_ref,
        requirement_hints=(subsystem_requirement,),
        input_refs=(context_carryover.target_context_ref, observation_ref.observation_ref),
        expected_output_hints=("future_memory_review_summary",),
        reason_summary="subsystem service request object only",
    )
    subsystem_envelope = SubsystemServiceEnvelope(
        envelope_ref=typed(1872, "subsystem_service_envelope"),
        request=subsystem_request,
        status=SubsystemServiceRequestStatus.READY_FOR_FUTURE_SERVICE,
        present_field_names=("service_kind", "source_context_ref"),
        missing_field_names=("future_service_policy_ref",),
        readiness_hint=0.76,
        reason_summary="service envelope is advisory only",
    )
    subsystem_transition = SubsystemServiceStateTransitionAdvice(
        advice_ref=typed(1873, "subsystem_service_state_transition"),
        request_ref=subsystem_ref.request_ref,
        reason_codes=("ready_for_future_service_review",),
        confidence=0.76,
    )

    observation_credibility = build_observation_credibility_score(typed(1880, "observation_credibility_score"), observation_envelope)
    observation_relevance = build_observation_relevance_score(typed(1881, "observation_relevance_score"), observation_envelope, target_ref=step_ref)
    observation_completeness = build_observation_completeness_score(typed(1882, "observation_completeness_score"), observation_envelope)
    context_value = build_context_value_score(typed(1883, "context_value_score"), context_carryover)
    context_continuity = build_context_continuity_score(typed(1884, "context_continuity_score"), context_carryover)
    compression_score = build_context_compression_need_score(typed(1885, "context_compression_need_score"), context_window)
    memory_need = build_memory_need_score(typed(1886, "memory_need_score"), memory_request)
    retrieval_need = build_retrieval_need_score(typed(1887, "retrieval_need_score"), retrieval_request)
    learning_signal_value = build_learning_signal_value_score(typed(1888, "learning_signal_value_score"), learning_signal.advice_ref, 1, learning_signal.signal_value_hint)
    learning_need = build_learning_need_score(typed(1889, "learning_need_score"), learning_request)
    affective_need = build_affective_need_score(typed(1890, "affective_need_score"), affective_request)
    candidate_priority = build_candidate_priority_score(
        typed(1891, "candidate_priority_score"),
        candidate_proposal,
        affective_input=phase5["phase3"]["math_input"].affective_input,
        dynamic_drive_input=phase5["phase3"]["math_input"].dynamic_drive_input,
    )
    candidate_learning_value = build_candidate_learning_value_score(typed(1892, "candidate_learning_value_score"), candidate_proposal)
    subsystem_readiness = build_subsystem_service_readiness_score(
        typed(1893, "subsystem_service_readiness_score"),
        subsystem_envelope,
        affective_input=phase5["phase3"]["math_input"].affective_input,
        dynamic_drive_input=phase5["phase3"]["math_input"].dynamic_drive_input,
    )
    score_vector = build_observation_context_score_vector(
        typed(1894, "observation_context_score_vector"),
        (
            observation_credibility,
            observation_relevance,
            observation_completeness,
            context_value,
            context_continuity,
            compression_score,
            memory_need,
            retrieval_need,
            learning_signal_value,
            learning_need,
            affective_need,
            candidate_priority,
            candidate_learning_value,
            subsystem_readiness,
        ),
    )

    service_candidate_memory = SubsystemServiceRouteCandidate(
        candidate_ref=typed(1900, "subsystem_service_route_candidate"),
        service_kind=SubsystemServiceKind.MEMORY,
        target_request_ref=memory_ref.request_ref,
        priority_score=memory_need.value,
        reason_codes=("memory_need_score",),
    )
    service_candidate_retrieval = SubsystemServiceRouteCandidate(
        candidate_ref=typed(1901, "subsystem_service_route_candidate"),
        service_kind=SubsystemServiceKind.RETRIEVAL,
        target_request_ref=retrieval_ref.request_ref,
        priority_score=retrieval_need.value,
        reason_codes=("retrieval_need_score",),
    )
    candidate_route = CandidateRouteCandidate(
        route_ref=typed(1902, "candidate_route_candidate"),
        candidate_ref=candidate_ref,
        priority_score=candidate_priority.value,
        reason_codes=("candidate_priority_score",),
    )
    route_ranking = build_observation_context_subsystem_route_ranking(
        typed(1903, "observation_context_subsystem_route_ranking"),
        (service_candidate_memory, service_candidate_retrieval),
        (candidate_route,),
    )
    candidate_ranking = build_candidate_route_ranking(typed(1904, "candidate_route_ranking"), (candidate_route,))
    recommendation = SubsystemServiceRecommendation(
        recommendation_ref=typed(1905, "subsystem_service_recommendation"),
        math_result=None,
        route_ranking=route_ranking,
        recommendation_mode=RecommendationMode.SUGGEST,
        recommended_service_request_ref=route_ranking.top_target_ref,
        alternative_service_request_refs=(retrieval_ref.request_ref,),
        confidence=0.78,
        reason_summary="service recommendation is advice only",
    )

    execution_to_observation = ExecutionToObservationAdvice(
        advice_ref=typed(1910, "execution_to_observation_advice"),
        source_ref=execution_result_ref.result_ref,
        target_ref=observation_ref.observation_ref,
        observation_ref=observation_ref.observation_ref,
        reason_codes=("execution_result_reference_to_observation_reference",),
        confidence=0.82,
    )
    execution_result_context = ExecutionResultContextAdvice(
        advice_ref=typed(1911, "execution_result_context_advice"),
        source_ref=execution_result_ref.result_ref,
        context_ref=context_carryover.target_context_ref,
        reason_codes=("result_context_carryover",),
        confidence=0.8,
    )
    intent_observation_feedback = IntentObservationFeedbackAdvice(
        advice_ref=typed(1912, "intent_observation_feedback_advice"),
        source_ref=action_ref.intent_ref,
        observation_ref=observation_ref.observation_ref,
        reason_codes=("intent_linked_to_observation_feedback",),
        confidence=0.78,
    )
    skill_tool_context = SkillToolContextCarryoverAdvice(
        advice_ref=typed(1913, "skill_tool_context_carryover_advice"),
        source_ref=skill_ref,
        target_ref=tool_group_ref,
        context_ref=context_carryover.target_context_ref,
        reason_codes=("skill_tool_context_reference_only",),
        confidence=0.78,
    )
    run_observation = RunObservationAdvice(
        advice_ref=typed(1914, "run_observation_advice"),
        source_ref=run_ref,
        observation_ref=observation_ref.observation_ref,
        confidence=0.8,
    )
    task_observation = TaskObservationAdvice(
        advice_ref=typed(1915, "task_observation_advice"),
        source_ref=task_ref,
        observation_ref=observation_ref.observation_ref,
        confidence=0.8,
    )
    turn_observation = TurnObservationAdvice(
        advice_ref=typed(1916, "turn_observation_advice"),
        source_ref=turn_ref,
        observation_ref=observation_ref.observation_ref,
        confidence=0.8,
    )
    step_observation = StepObservationAdvice(
        advice_ref=typed(1917, "step_observation_advice"),
        source_ref=step_ref,
        observation_ref=observation_ref.observation_ref,
        confidence=0.8,
    )
    run_service = RunSubsystemServiceAdvice(
        advice_ref=typed(1918, "run_subsystem_service_advice"),
        source_ref=run_ref,
        service_request_ref=subsystem_ref.request_ref,
        service_kind=SubsystemServiceKind.MEMORY,
        confidence=0.78,
    )
    task_service = TaskSubsystemServiceAdvice(
        advice_ref=typed(1919, "task_subsystem_service_advice"),
        source_ref=task_ref,
        service_request_ref=subsystem_ref.request_ref,
        service_kind=SubsystemServiceKind.MEMORY,
        confidence=0.78,
    )
    turn_service = TurnSubsystemServiceAdvice(
        advice_ref=typed(1920, "turn_subsystem_service_advice"),
        source_ref=turn_ref,
        service_request_ref=subsystem_ref.request_ref,
        service_kind=SubsystemServiceKind.MEMORY,
        confidence=0.78,
    )
    step_service = StepSubsystemServiceAdvice(
        advice_ref=typed(1921, "step_subsystem_service_advice"),
        source_ref=step_ref,
        service_request_ref=subsystem_ref.request_ref,
        service_kind=SubsystemServiceKind.MEMORY,
        confidence=0.78,
    )

    return locals()
