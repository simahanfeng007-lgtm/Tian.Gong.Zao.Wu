from l3_phase1_builders import typed
from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import (
    AffectiveDriveToRecoveryAdvice,
    CandidateChangeRef,
    CandidateEvidenceChainRef,
    CandidateEvolutionAdvice,
    CandidateExperimentAdvice,
    CandidateIterationAdvice,
    CandidatePatchRef,
    CandidateRecoveryAdvice,
    CandidateToValidationAdvice,
    CandidateValidationAdvice,
    CandidateVerificationRouteCandidate,
    CandidateVerificationRouteKind,
    DynamicDriveToExperimentAdvice,
    EvolutionBoundaryHint,
    EvolutionCandidateRef,
    EvolutionConstraintHint,
    EvolutionEvidenceRef,
    EvolutionFlowKind,
    EvolutionFlowRequest,
    EvolutionFlowRequestRef,
    EvolutionRouteCandidate,
    ExecutionFailureToRecoveryAdvice,
    ExperimentDesignHint,
    ExperimentEvidenceRef,
    ExperimentFlowKind,
    ExperimentFlowRequest,
    ExperimentFlowRequestRef,
    ExperimentHypothesisRef,
    ExperimentRiskAwarenessHint,
    ExperimentRouteCandidate,
    IterationCandidateRef,
    IterationChangeRef,
    IterationEvidenceRef,
    IterationEvolutionMathInput,
    IterationEvolutionMathResult,
    IterationEvolutionRecommendation,
    IterationEvolutionRouteRanking,
    IterationFlowKind,
    IterationFlowRequest,
    IterationFlowRequestRef,
    IterationRouteCandidate,
    LearningSignalToIterationAdvice,
    ObservationToValidationAdvice,
    RecoveryEnvelope,
    RecoveryEnvelopeStatus,
    RecoveryFallbackAdvice,
    RecoveryFlowAdvice,
    RecoveryFlowKind,
    RecoveryPreconditionHint,
    RecoveryRequest,
    RecoveryRequestRef,
    RecoveryRequirementHint,
    RecoveryResultRef,
    RecoveryRouteCandidate,
    RecoveryStateTransitionAdvice,
    RecoveryTargetRef,
    ReversibilityReviewAdvice,
    RollbackAdvice,
    RollbackImpactHint,
    RollbackPreconditionHint,
    RollbackTargetRef,
    RunRecoveryAdvice,
    RunValidationAdvice,
    SelfEvolutionFlowEntryAdvice,
    SelfImprovementBoundaryHint,
    SelfImprovementConstraintHint,
    SelfImprovementEvidenceRef,
    SelfImprovementFlowKind,
    SelfImprovementRouteCandidate,
    SelfImprovementSignalAdvice,
    SelfIterationFlowEntryAdvice,
    SelfLearningFlowEntryAdvice,
    StepRecoveryAdvice,
    StepValidationAdvice,
    TaskRecoveryAdvice,
    TaskValidationAdvice,
    TurnRecoveryAdvice,
    TurnValidationAdvice,
    ValidationConfidenceHint,
    ValidationConflictAdvice,
    ValidationEnvelope,
    ValidationEnvelopeStatus,
    ValidationEvidenceRef,
    ValidationFailureRef,
    ValidationFallbackAdvice,
    ValidationFlowAdvice,
    ValidationFlowKind,
    ValidationObservationRef,
    ValidationRecoveryMathInput,
    ValidationRecoveryMathResult,
    ValidationRecoveryRecommendation,
    ValidationRecoveryRouteRanking,
    ValidationRequest,
    ValidationRequestRef,
    ValidationRequirementHint,
    ValidationResultRef,
    ValidationResultStateTransitionAdvice,
    ValidationResultUseAdvice,
    ValidationRetryAdvice,
    ValidationRouteCandidate,
    ValidationStateTransitionAdvice,
    ValidationTargetRef,
    RecommendationMode,
    build_candidate_verification_route_ranking,
    build_evolution_pressure_score,
    build_evolution_route_ranking,
    build_experiment_route_ranking,
    build_experiment_value_score,
    build_iteration_evolution_score_vector,
    build_iteration_need_score,
    build_iteration_route_ranking,
    build_recovery_flow_priority_score,
    build_recovery_readiness_score,
    build_recovery_route_ranking,
    build_reversibility_score,
    build_rollback_need_score,
    build_self_improvement_readiness_score,
    build_self_improvement_route_ranking,
    build_validation_readiness_score,
    build_validation_recovery_score_vector,
    build_validation_route_ranking,
    build_validation_value_score,
)


def build_l3_phase7_objects():
    phase6 = build_l3_phase6_objects()
    run_ref = phase6["run_ref"]
    task_ref = phase6["task_ref"]
    turn_ref = phase6["turn_ref"]
    step_ref = phase6["step_ref"]
    observation = phase6["observation_ref"]
    execution_failure = phase6["execution_failure_ref"]
    candidate = phase6["candidate_proposal"]
    candidate_score = phase6["candidate_priority"]

    target = ValidationTargetRef(target_ref=step_ref, target_kind_hint="step_result_review", summary="validate future step outcome")
    evidence = ValidationEvidenceRef(evidence_ref=observation.observation_ref, evidence_kind_hint="observation_ref", confidence_hint=0.82)
    requirement = ValidationRequirementHint(hint_ref=typed(1900, "validation_requirement_hint"), required_target_refs=(step_ref,), required_evidence_refs=(evidence.evidence_ref,), reason_codes=("target_and_evidence_required",))
    validation_ref = ValidationRequestRef(request_ref=typed(1901, "validation_request"), source_ref=observation.observation_ref)
    validation_request = ValidationRequest(request_ref=validation_ref, target_refs=(target,), evidence_refs=(evidence,), requirement_hints=(requirement,), present_field_names=("target", "evidence"), missing_field_names=("future_report_ref",), reason_summary="validation request is pure")
    validation_envelope = ValidationEnvelope(envelope_ref=typed(1902, "validation_envelope"), request=validation_request, status=ValidationEnvelopeStatus.READY_FOR_ADVICE, run_ref=run_ref, task_ref=task_ref, turn_ref=turn_ref, step_ref=step_ref, candidate_refs=(candidate.candidate_ref,), present_field_names=("request",), missing_field_names=("future_result",))
    validation_flow = ValidationFlowAdvice(advice_ref=typed(1903, "validation_flow_advice"), envelope=validation_envelope, flow_kind=ValidationFlowKind.REQUEST_REVIEW, target_refs=(step_ref,), reason_codes=("observation_needs_review",), confidence=0.81)
    validation_value = build_validation_value_score(typed(1904, "validation_value_score"), evidence_count=1)
    validation_readiness = build_validation_readiness_score(typed(1905, "validation_readiness_score"), present_count=2, missing_count=1)
    validation_state = ValidationStateTransitionAdvice(advice_ref=typed(1906, "validation_state_transition"), validation_request_ref=validation_ref.request_ref, reason_codes=("validation_ready",), confidence=0.8)
    validation_result = ValidationResultRef(result_ref=typed(1907, "validation_result_ref"), validation_request_ref=validation_ref.request_ref, confidence_hint=0.77)
    validation_failure = ValidationFailureRef(failure_ref=typed(1908, "validation_failure_ref"), validation_request_ref=validation_ref.request_ref)
    validation_observation = ValidationObservationRef(observation_ref=typed(1909, "validation_observation_ref"), result_ref=validation_result)
    validation_confidence = ValidationConfidenceHint(hint_ref=typed(1910, "validation_confidence_hint"), result_ref=validation_result.result_ref, confidence_hint=0.77)
    validation_conflict = ValidationConflictAdvice(advice_ref=typed(1911, "validation_conflict_advice"), conflicting_result_refs=(validation_result.result_ref, validation_failure.failure_ref), reason_codes=("future_result_conflict",), confidence=0.65)
    validation_retry = ValidationRetryAdvice(advice_ref=typed(1912, "validation_retry_advice"), validation_request_ref=validation_ref.request_ref, retry_target_refs=(step_ref,), reason_codes=("retry_is_only_advice",), confidence=0.62)
    validation_fallback = ValidationFallbackAdvice(advice_ref=typed(1913, "validation_fallback_advice"), fallback_target_refs=(task_ref,), reason_codes=("fallback_to_task_review",), confidence=0.61)
    validation_ranking = build_validation_route_ranking(typed(1914, "validation_route_ranking"), (ValidationRouteCandidate(route_ref=typed(1915, "validation_route"), route_kind=ValidationFlowKind.REQUEST_REVIEW, score=0.82), ValidationRouteCandidate(route_ref=typed(1916, "validation_route"), route_kind=ValidationFlowKind.WAIT_FOR_EVIDENCE, score=0.55)))
    validation_use = ValidationResultUseAdvice(advice_ref=typed(1917, "validation_result_use_advice"), result_ref=validation_result.result_ref, reason_codes=("future_state_review",), confidence=0.72)
    validation_result_state = ValidationResultStateTransitionAdvice(advice_ref=typed(1918, "validation_result_state_transition"), result_ref=validation_result.result_ref, reason_codes=("result_ref_ready",), confidence=0.73)

    recovery_target = RecoveryTargetRef(target_ref=execution_failure.failure_ref, target_kind_hint="execution_failure_ref")
    recovery_requirement = RecoveryRequirementHint(hint_ref=typed(1920, "recovery_requirement_hint"), required_refs=(execution_failure.failure_ref,), reason_codes=("failure_ref_required",))
    recovery_precondition = RecoveryPreconditionHint(hint_ref=typed(1921, "recovery_precondition_hint"), precondition_refs=(validation_result.result_ref,), readiness_hint=0.7, reason_codes=("validation_result_ref_available",))
    recovery_ref = RecoveryRequestRef(request_ref=typed(1922, "recovery_request"), source_failure_ref=execution_failure.failure_ref)
    recovery_request = RecoveryRequest(request_ref=recovery_ref, target_refs=(recovery_target,), requirement_hints=(recovery_requirement,), precondition_hints=(recovery_precondition,), reason_summary="recovery request is pure")
    recovery_envelope = RecoveryEnvelope(envelope_ref=typed(1923, "recovery_envelope"), request=recovery_request, status=RecoveryEnvelopeStatus.READY_FOR_ADVICE, related_validation_refs=(validation_result.result_ref,), related_failure_refs=(execution_failure.failure_ref,), present_field_names=("failure", "precondition"), missing_field_names=("future_recovery_result",))
    recovery_flow = RecoveryFlowAdvice(advice_ref=typed(1924, "recovery_flow_advice"), envelope=recovery_envelope, flow_kind=RecoveryFlowKind.REQUEST_RECOVERY_REVIEW, target_refs=(execution_failure.failure_ref,), reason_codes=("failure_needs_recovery_review",), confidence=0.79)
    recovery_priority = build_recovery_flow_priority_score(typed(1925, "recovery_priority_score"), failure_count=1, reversibility_value=0.8)
    recovery_readiness = build_recovery_readiness_score(typed(1926, "recovery_readiness_score"), precondition_value=0.7)
    rollback_need = build_rollback_need_score(typed(1927, "rollback_need_score"), failure_pressure=0.75, reversibility_value=0.82)
    reversibility = build_reversibility_score(typed(1928, "reversibility_score"), reversible_hint=0.85, impact_hint=0.2)
    rollback_target = RollbackTargetRef(target_ref=execution_failure.failure_ref)
    rollback_precondition = RollbackPreconditionHint(hint_ref=typed(1929, "rollback_precondition_hint"), required_refs=(validation_result.result_ref,), readiness_hint=0.66)
    rollback_impact = RollbackImpactHint(hint_ref=typed(1930, "rollback_impact_hint"), impact_refs=(step_ref,), impact_level_hint=0.2)
    rollback_advice = RollbackAdvice(advice_ref=typed(1931, "rollback_advice"), target_refs=(rollback_target,), precondition_hints=(rollback_precondition,), impact_hints=(rollback_impact,), rollback_need_score=rollback_need, reason_codes=("rollback_is_review_advice",))
    reversibility_review = ReversibilityReviewAdvice(advice_ref=typed(1932, "reversibility_review_advice"), target_refs=(execution_failure.failure_ref,), reversibility_score=reversibility, reason_codes=("reversibility_review_only",))
    recovery_fallback = RecoveryFallbackAdvice(advice_ref=typed(1933, "recovery_fallback_advice"), fallback_target_refs=(task_ref,), reason_codes=("fallback_review_only",), confidence=0.63)
    recovery_ranking = build_recovery_route_ranking(typed(1934, "recovery_route_ranking"), (RecoveryRouteCandidate(route_ref=typed(1935, "recovery_route"), route_kind=RecoveryFlowKind.REQUEST_RECOVERY_REVIEW, score=0.8), RecoveryRouteCandidate(route_ref=typed(1936, "recovery_route"), route_kind=RecoveryFlowKind.WAIT_FOR_STABLE_EVIDENCE, score=0.51)))
    recovery_result = RecoveryResultRef(result_ref=typed(1937, "recovery_result_ref"), recovery_request_ref=recovery_ref.request_ref)
    recovery_state = RecoveryStateTransitionAdvice(advice_ref=typed(1938, "recovery_state_transition"), recovery_request_ref=recovery_ref.request_ref, reason_codes=("recovery_ready",), confidence=0.76)

    hypothesis = ExperimentHypothesisRef(hypothesis_ref=typed(1940, "experiment_hypothesis"), summary="future experiment hypothesis ref")
    experiment_evidence = ExperimentEvidenceRef(evidence_ref=typed(1941, "experiment_evidence"), confidence_hint=0.66)
    design_hint = ExperimentDesignHint(hint_ref=typed(1942, "experiment_design_hint"), hypothesis_refs=(hypothesis.hypothesis_ref,), reason_codes=("design_review_only",))
    risk_hint = ExperimentRiskAwarenessHint(hint_ref=typed(1943, "experiment_risk_hint"), risk_awareness_hint=0.35, reason_codes=("risk_awareness_only",))
    experiment_value = build_experiment_value_score(typed(1944, "experiment_value_score"), learning_signal_value=0.82, evidence_value=0.66)
    experiment_request = ExperimentFlowRequest(request_ref=ExperimentFlowRequestRef(request_ref=typed(1945, "experiment_request"), source_candidate_ref=candidate.candidate_ref), design_hints=(design_hint,), hypothesis_refs=(hypothesis,), evidence_refs=(experiment_evidence,), risk_awareness_hints=(risk_hint,), value_score=experiment_value)
    experiment_ranking = build_experiment_route_ranking(typed(1946, "experiment_route_ranking"), (ExperimentRouteCandidate(route_ref=typed(1947, "experiment_route"), route_kind=ExperimentFlowKind.REQUEST_DESIGN_REVIEW, score=0.77), ExperimentRouteCandidate(route_ref=typed(1948, "experiment_route"), route_kind=ExperimentFlowKind.WAIT_FOR_VALIDATION, score=0.59)))

    iteration_candidate = IterationCandidateRef(candidate_ref=candidate.candidate_ref)
    iteration_change = IterationChangeRef(change_ref=typed(1950, "iteration_change"))
    iteration_evidence = IterationEvidenceRef(evidence_ref=validation_result.result_ref, confidence_hint=0.77)
    iteration_need = build_iteration_need_score(typed(1951, "iteration_need_score"), candidate_score, validation_value)
    iteration_request = IterationFlowRequest(request_ref=IterationFlowRequestRef(request_ref=typed(1952, "iteration_request"), source_candidate_ref=candidate.candidate_ref), candidate_refs=(iteration_candidate,), change_refs=(iteration_change,), evidence_refs=(iteration_evidence,), need_score=iteration_need)
    iteration_ranking = build_iteration_route_ranking(typed(1953, "iteration_route_ranking"), (IterationRouteCandidate(route_ref=typed(1954, "iteration_route"), route_kind=IterationFlowKind.REQUEST_CANDIDATE_REVIEW, score=0.79), IterationRouteCandidate(route_ref=typed(1955, "iteration_route"), route_kind=IterationFlowKind.FALLBACK_TO_EXPERIMENT, score=0.5)))

    evolution_pressure = build_evolution_pressure_score(typed(1960, "evolution_pressure_score"), iteration_need, stability_pressure=0.35)
    evolution_candidate = EvolutionCandidateRef(candidate_ref=typed(1961, "evolution_candidate"))
    evolution_evidence = EvolutionEvidenceRef(evidence_ref=validation_result.result_ref, confidence_hint=0.72)
    evolution_boundary = EvolutionBoundaryHint(hint_ref=typed(1962, "evolution_boundary_hint"), boundary_refs=(typed(1963, "architecture_boundary"),))
    evolution_constraint = EvolutionConstraintHint(hint_ref=typed(1964, "evolution_constraint_hint"), constraint_refs=(typed(1965, "safety_constraint"),))
    evolution_request = EvolutionFlowRequest(request_ref=EvolutionFlowRequestRef(request_ref=typed(1966, "evolution_request"), source_candidate_ref=candidate.candidate_ref), candidate_refs=(evolution_candidate,), evidence_refs=(evolution_evidence,), boundary_hints=(evolution_boundary,), constraint_hints=(evolution_constraint,), pressure_score=evolution_pressure)
    evolution_ranking = build_evolution_route_ranking(typed(1967, "evolution_route_ranking"), (EvolutionRouteCandidate(route_ref=typed(1968, "evolution_route"), route_kind=EvolutionFlowKind.REQUEST_BOUNDARY_REVIEW, score=0.74), EvolutionRouteCandidate(route_ref=typed(1969, "evolution_route"), route_kind=EvolutionFlowKind.WAIT_FOR_STABILITY_EVIDENCE, score=0.62)))

    self_evidence = SelfImprovementEvidenceRef(evidence_ref=validation_result.result_ref, confidence_hint=0.77)
    self_constraint = SelfImprovementConstraintHint(hint_ref=typed(1970, "self_improvement_constraint"), constraint_refs=(typed(1965, "safety_constraint"),))
    self_boundary = SelfImprovementBoundaryHint(hint_ref=typed(1971, "self_improvement_boundary"), boundary_refs=(typed(1963, "architecture_boundary"),))
    self_score = build_self_improvement_readiness_score(typed(1972, "self_improvement_readiness_score"), evidence_value=0.77, boundary_constraint_value=0.8)
    self_signal = SelfImprovementSignalAdvice(advice_ref=typed(1973, "self_improvement_signal_advice"), signal_refs=(candidate.candidate_ref,), reason_codes=("candidate_signal_only",), confidence=0.75)
    self_learning = SelfLearningFlowEntryAdvice(advice_ref=typed(1974, "self_learning_entry"), evidence_refs=(self_evidence,), constraint_hints=(self_constraint,), boundary_hints=(self_boundary,), readiness_score=self_score, reason_codes=("learning_entry_only",))
    self_iteration = SelfIterationFlowEntryAdvice(advice_ref=typed(1975, "self_iteration_entry"), evidence_refs=(self_evidence,), constraint_hints=(self_constraint,), boundary_hints=(self_boundary,), readiness_score=self_score, reason_codes=("iteration_entry_only",))
    self_evolution = SelfEvolutionFlowEntryAdvice(advice_ref=typed(1976, "self_evolution_entry"), evidence_refs=(self_evidence,), constraint_hints=(self_constraint,), boundary_hints=(self_boundary,), readiness_score=self_score, reason_codes=("evolution_entry_only",))
    self_ranking = build_self_improvement_route_ranking(typed(1977, "self_improvement_route_ranking"), (SelfImprovementRouteCandidate(route_ref=typed(1978, "self_improvement_route"), flow_kind=SelfImprovementFlowKind.SELF_ITERATION, score=0.78), SelfImprovementRouteCandidate(route_ref=typed(1979, "self_improvement_route"), flow_kind=SelfImprovementFlowKind.SELF_EVOLUTION, score=0.52)))

    change_ref = CandidateChangeRef(change_ref=typed(1980, "candidate_change"), summary="candidate change ref only")
    patch_ref = CandidatePatchRef(patch_ref=typed(1981, "candidate_patch_ref"), summary="future patch ref only")
    evidence_chain = CandidateEvidenceChainRef(chain_ref=typed(1982, "candidate_evidence_chain"), evidence_refs=(validation_result.result_ref, observation.observation_ref), confidence_hint=0.74)
    candidate_validation = CandidateValidationAdvice(advice_ref=typed(1983, "candidate_validation_advice"), candidate_change_ref=change_ref, evidence_chain_ref=evidence_chain, reason_codes=("candidate_validation_review",), confidence=0.75)
    candidate_recovery = CandidateRecoveryAdvice(advice_ref=typed(1984, "candidate_recovery_advice"), candidate_change_ref=change_ref, evidence_chain_ref=evidence_chain, reason_codes=("candidate_recovery_review",), confidence=0.7)
    candidate_experiment = CandidateExperimentAdvice(advice_ref=typed(1985, "candidate_experiment_advice"), candidate_change_ref=change_ref, evidence_chain_ref=evidence_chain, reason_codes=("candidate_experiment_review",), confidence=0.73)
    candidate_iteration = CandidateIterationAdvice(advice_ref=typed(1986, "candidate_iteration_advice"), candidate_change_ref=change_ref, evidence_chain_ref=evidence_chain, reason_codes=("candidate_iteration_review",), confidence=0.76)
    candidate_evolution = CandidateEvolutionAdvice(advice_ref=typed(1987, "candidate_evolution_advice"), candidate_change_ref=change_ref, evidence_chain_ref=evidence_chain, reason_codes=("candidate_evolution_review",), confidence=0.58)
    candidate_ranking = build_candidate_verification_route_ranking(typed(1988, "candidate_verification_ranking"), (CandidateVerificationRouteCandidate(route_ref=typed(1989, "candidate_verification_route"), route_kind=CandidateVerificationRouteKind.VALIDATE_FIRST, score=0.82), CandidateVerificationRouteCandidate(route_ref=typed(1990, "candidate_verification_route"), route_kind=CandidateVerificationRouteKind.EVOLUTION_REVIEW, score=0.48)))

    validation_recovery_vector = build_validation_recovery_score_vector(typed(1991, "validation_recovery_score_vector"), validation_value, validation_readiness, recovery_priority, rollback_need, reversibility)
    validation_math_input = ValidationRecoveryMathInput(input_ref=typed(1992, "validation_recovery_math_input"), validation_request_refs=(validation_ref.request_ref,), recovery_request_refs=(recovery_ref.request_ref,), observation_result_refs=(observation.observation_ref,), execution_failure_refs=(execution_failure.failure_ref,), candidate_refs=(candidate.candidate_ref,), affective_input=phase6["phase5"]["phase3"]["math_input"].affective_input, dynamic_drive_input=phase6["phase5"]["phase3"]["math_input"].dynamic_drive_input, summary="validation recovery math input ref only")
    validation_math_result = ValidationRecoveryMathResult(result_ref=typed(1993, "validation_recovery_math_result"), math_input=validation_math_input, score_vector=validation_recovery_vector, validation_route_ranking_ref=validation_ranking.ranking_ref, recovery_route_ranking_ref=recovery_ranking.ranking_ref, confidence=0.74)
    validation_recovery_ranking = ValidationRecoveryRouteRanking(ranking_ref=typed(1994, "validation_recovery_route_ranking"), validation_ranking=validation_ranking, recovery_ranking=recovery_ranking, top_route_ref=validation_ranking.top_route_ref, reason_summary="validation then recovery ranking")
    validation_recovery_recommendation = ValidationRecoveryRecommendation(recommendation_ref=typed(1995, "validation_recovery_recommendation"), math_result=validation_math_result, route_ranking=validation_recovery_ranking, recommended_validation_ref=validation_ref.request_ref, recommended_recovery_ref=recovery_ref.request_ref, reason_codes=("advice_only",), confidence=0.75)

    iteration_evolution_vector = build_iteration_evolution_score_vector(typed(1996, "iteration_evolution_score_vector"), experiment_value, iteration_need, evolution_pressure, self_score)
    iteration_math_input = IterationEvolutionMathInput(input_ref=typed(1997, "iteration_evolution_math_input"), experiment_request_refs=(experiment_request.request_ref.request_ref,), iteration_request_refs=(iteration_request.request_ref.request_ref,), evolution_request_refs=(evolution_request.request_ref.request_ref,), self_improvement_entry_refs=(self_iteration.advice_ref,), candidate_refs=(candidate.candidate_ref,), affective_input=phase6["phase5"]["phase3"]["math_input"].affective_input, dynamic_drive_input=phase6["phase5"]["phase3"]["math_input"].dynamic_drive_input, summary="iteration evolution math input ref only")
    iteration_math_result = IterationEvolutionMathResult(result_ref=typed(1998, "iteration_evolution_math_result"), math_input=iteration_math_input, score_vector=iteration_evolution_vector, experiment_route_ranking_ref=experiment_ranking.ranking_ref, iteration_route_ranking_ref=iteration_ranking.ranking_ref, evolution_route_ranking_ref=evolution_ranking.ranking_ref, confidence=0.73)
    iteration_evolution_ranking = IterationEvolutionRouteRanking(ranking_ref=typed(1999, "iteration_evolution_route_ranking"), experiment_ranking=experiment_ranking, iteration_ranking=iteration_ranking, evolution_ranking=evolution_ranking, self_improvement_ranking=self_ranking, candidate_verification_ranking=candidate_ranking, top_route_ref=iteration_ranking.top_route_ref, reason_summary="iteration route has highest score")
    iteration_evolution_recommendation = IterationEvolutionRecommendation(recommendation_ref=typed(2000, "iteration_evolution_recommendation"), math_result=iteration_math_result, route_ranking=iteration_evolution_ranking, recommended_experiment_ref=experiment_request.request_ref.request_ref, recommended_iteration_ref=iteration_request.request_ref.request_ref, recommended_evolution_ref=evolution_request.request_ref.request_ref, reason_codes=("advice_only",), confidence=0.72)

    transition_examples = (
        ObservationToValidationAdvice(advice_ref=typed(2001, "observation_to_validation"), source_refs=(observation.observation_ref,), target_refs=(validation_ref.request_ref,), reason_codes=("observation_needs_validation",), confidence=0.8),
        ExecutionFailureToRecoveryAdvice(advice_ref=typed(2002, "execution_failure_to_recovery"), source_refs=(execution_failure.failure_ref,), target_refs=(recovery_ref.request_ref,), reason_codes=("failure_needs_recovery",), confidence=0.79),
        CandidateToValidationAdvice(advice_ref=typed(2003, "candidate_to_validation"), source_refs=(candidate.candidate_ref,), target_refs=(validation_ref.request_ref,), confidence=0.74),
        LearningSignalToIterationAdvice(advice_ref=typed(2004, "learning_signal_to_iteration"), source_refs=(candidate.candidate_ref,), target_refs=(iteration_request.request_ref.request_ref,), confidence=0.73),
        AffectiveDriveToRecoveryAdvice(advice_ref=typed(2005, "affective_drive_to_recovery"), source_refs=(typed(2006, "affective_ref"),), target_refs=(recovery_ref.request_ref,), confidence=0.65),
        DynamicDriveToExperimentAdvice(advice_ref=typed(2007, "dynamic_drive_to_experiment"), source_refs=(typed(2008, "dynamic_drive_ref"),), target_refs=(experiment_request.request_ref.request_ref,), confidence=0.66),
        RunValidationAdvice(advice_ref=typed(2009, "run_validation"), source_refs=(run_ref,), target_refs=(validation_ref.request_ref,), confidence=0.72),
        TaskValidationAdvice(advice_ref=typed(2010, "task_validation"), source_refs=(task_ref,), target_refs=(validation_ref.request_ref,), confidence=0.72),
        TurnValidationAdvice(advice_ref=typed(2011, "turn_validation"), source_refs=(turn_ref,), target_refs=(validation_ref.request_ref,), confidence=0.72),
        StepValidationAdvice(advice_ref=typed(2012, "step_validation"), source_refs=(step_ref,), target_refs=(validation_ref.request_ref,), confidence=0.72),
        RunRecoveryAdvice(advice_ref=typed(2013, "run_recovery"), source_refs=(run_ref,), target_refs=(recovery_ref.request_ref,), confidence=0.7),
        TaskRecoveryAdvice(advice_ref=typed(2014, "task_recovery"), source_refs=(task_ref,), target_refs=(recovery_ref.request_ref,), confidence=0.7),
        TurnRecoveryAdvice(advice_ref=typed(2015, "turn_recovery"), source_refs=(turn_ref,), target_refs=(recovery_ref.request_ref,), confidence=0.7),
        StepRecoveryAdvice(advice_ref=typed(2016, "step_recovery"), source_refs=(step_ref,), target_refs=(recovery_ref.request_ref,), confidence=0.7),
    )

    return locals()
