from l3_phase1_builders import typed
from l3_phase7_builders import build_l3_phase7_objects
from tiangong_kernel.l3_orchestration import (
    BoundaryDecisionRef,
    DenialReasonRef,
    EvolutionServiceRequest,
    IterationServiceRequest,
    L3BoundaryComplianceReport,
    L3ClosureCheckKind,
    L3ClosureCheckRequest,
    L3ClosureCheckResult,
    L3FinalFreezeReadinessReport,
    L3ImportStabilityReport,
    L3NoDecisionGuaranteeReport,
    L3NoExecutionGuaranteeReport,
    L3NoSubsystemGuaranteeReport,
    L3SerializationStabilityReport,
    L3SnapshotCompatibilityReport,
    L3ToL4CompatibilityCheckResult,
    L3ToL4ExecutionBoundaryNote,
    L3ToL4ExecutionReadinessSummary,
    L3ToL4ExecutionRefBundle,
    L3ToL4ExecutionRequestBundle,
    L3ToL4ExpectedConsumerNote,
    L3ToL4HandoffEnvelope,
    L3ToL4InterfaceFreezeNote,
    L3ToL4NonExecutionGuarantee,
    L3ToL5BoundaryReadinessSummary,
    L3ToL5BoundaryRefBundle,
    L3ToL5BoundaryRequestBundle,
    L3ToL5CompatibilityCheckResult,
    L3ToL5ExpectedConsumerNote,
    L3ToL5HandoffEnvelope,
    L3ToL5InterfaceFreezeNote,
    L3ToL5NonDecisionGuarantee,
    L3ToL6CompatibilityCheckResult,
    L3ToL6ExpectedConsumerNote,
    L3ToL6HandoffEnvelope,
    L3ToL6InterfaceFreezeNote,
    L3ToL6NonImplementationGuarantee,
    L3ToL6SubsystemReadinessSummary,
    L3ToL6SubsystemRefBundle,
    L3ToL6SubsystemRequestBundle,
    L4PlanningPrerequisiteNote,
    L5BoundaryOpenQuestionNote,
    L5PlanningPrerequisiteNote,
    L6PlanningPrerequisiteNote,
    L6SubsystemOpenQuestionNote,
    ObservationServiceRequest,
    OrchestrationAuditRefProjection,
    OrchestrationBoundaryIndex,
    OrchestrationCompatibilityIndex,
    OrchestrationComponentIndex,
    OrchestrationHandoffIndex,
    OrchestrationIndexKind,
    OrchestrationMathBoundaryNote,
    OrchestrationMathCatalog,
    OrchestrationMathConsistencyReport,
    OrchestrationMathFreezeNote,
    OrchestrationMathIndex,
    OrchestrationMathProjection,
    OrchestrationMathSnapshotRef,
    OrchestrationModuleIndex,
    OrchestrationObjectFamilyIndex,
    OrchestrationProjection,
    OrchestrationProjectionConsistencyReport,
    OrchestrationProjectionEnvelope,
    OrchestrationProjectionIndex,
    OrchestrationProjectionKind,
    OrchestrationProjectionRef,
    OrchestrationPublicExportIndex,
    OrchestrationRankingCatalog,
    OrchestrationReasonCodeCatalog,
    OrchestrationRecommendationCatalog,
    OrchestrationRouteProjection,
    OrchestrationScoreCatalog,
    OrchestrationStageIndex,
    OrchestrationStateUpdateSuggestion,
    OrchestrationSummaryProjection,
    OrchestrationTraceProjection,
    OrchestrationWeightInputCatalog,
    PolicyDecisionRef,
    RecoveryServiceRequest,
    ValidationServiceRequest,
)


def build_l3_phase8_objects():
    phase7 = build_l3_phase7_objects()
    phase6 = phase7["phase6"]
    phase5 = phase6["phase5"]

    component_index = OrchestrationComponentIndex(
        index_ref=typed(2100, "l3_component_index"),
        component_names=("foundation", "run_task_turn_step", "skill_tool", "intent", "boundary_execution", "observation_context", "validation_recovery", "closure"),
        summary="component index is a pure catalog",
    )
    module_index = OrchestrationModuleIndex(
        index_ref=typed(2101, "l3_module_index"),
        module_names=("orchestration_projection", "orchestration_component_index", "orchestration_math_catalog", "l3_to_l4_handoff", "l3_to_l5_handoff", "l3_to_l6_handoff", "l3_closure_check"),
    )
    public_export_index = OrchestrationPublicExportIndex(
        index_ref=typed(2102, "l3_public_export_index"),
        exported_names=("OrchestrationProjection", "L3ToL4HandoffEnvelope", "L3ToL5HandoffEnvelope", "L3ToL6HandoffEnvelope", "L3ClosureCheckResult"),
    )
    compatibility_index = OrchestrationCompatibilityIndex(
        index_ref=typed(2103, "l3_compatibility_index"),
        compatible_stage_names=("phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7"),
        compatibility_score=1.0,
    )
    stage_index = OrchestrationStageIndex(
        index_ref=typed(2104, "l3_stage_index"),
        stage_names=("phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7", "phase8"),
        completed_stage_names=("phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7"),
    )
    family_index = OrchestrationObjectFamilyIndex(
        index_ref=typed(2105, "l3_family_index"),
        object_family_names=("projection", "component_index", "math_catalog", "handoff", "closure_check"),
        representative_object_names=("OrchestrationProjection", "OrchestrationMathCatalog", "L3ClosureCheckResult"),
    )
    boundary_index = OrchestrationBoundaryIndex(
        index_ref=typed(2106, "l3_boundary_index"),
        allowed_terms=("request", "ref", "advice", "hint", "score", "ranking", "projection", "handoff"),
        forbidden_capability_names=("real_execution", "real_boundary_result", "real_subsystem_service"),
        non_execution_guarantees=("no_model_call", "no_tool_call", "no_external_action"),
    )
    math_index = OrchestrationMathIndex(
        index_ref=typed(2107, "l3_math_index"),
        score_names=("ContinuityIndex", "SkillMatchScore", "IntentReadinessScore", "BoundaryReadinessScore", "ObservationCredibilityScore", "ValidationValueScore"),
        ranking_names=("RouteRanking", "SkillToolRouteRanking", "IntentRouteRanking", "BoundaryRouteRanking", "ObservationContextSubsystemRouteRanking"),
        recommendation_names=("MathRecommendation", "SkillToolRecommendation", "BoundaryExecutionRecommendation", "SubsystemServiceRecommendation"),
    )
    projection_index = OrchestrationProjectionIndex(
        index_ref=typed(2108, "l3_projection_index"),
        projection_object_names=("OrchestrationSummaryProjection", "OrchestrationMathProjection", "OrchestrationRouteProjection"),
        projection_target_hints=("future_l2_state_record",),
    )
    handoff_index = OrchestrationHandoffIndex(
        index_ref=typed(2109, "l3_handoff_index"),
        handoff_names=("L3ToL4HandoffEnvelope", "L3ToL5HandoffEnvelope", "L3ToL6HandoffEnvelope"),
        target_layer_hints=("future_l4", "future_l5", "future_l6"),
    )

    score_catalog = OrchestrationScoreCatalog(
        catalog_ref=typed(2110, "l3_score_catalog"),
        score_object_names=("ContinuityIndex", "ExecutionReadinessScore", "LearningSignalValueScore", "EvolutionPressureScore"),
    )
    ranking_catalog = OrchestrationRankingCatalog(
        catalog_ref=typed(2111, "l3_ranking_catalog"),
        ranking_object_names=("RouteRanking", "BoundaryRouteRanking", "ExecutionRouteRanking", "ValidationRecoveryRouteRanking"),
    )
    recommendation_catalog = OrchestrationRecommendationCatalog(
        catalog_ref=typed(2112, "l3_recommendation_catalog"),
        recommendation_object_names=("MathRecommendation", "BoundaryExecutionRecommendation", "ValidationRecoveryRecommendation"),
        advice_object_names=("SkillDisplayAdvice", "IntentValidationAdvice", "RollbackAdvice"),
        suggestion_object_names=("OrchestrationStateUpdateSuggestion",),
    )
    reason_catalog = OrchestrationReasonCodeCatalog(
        catalog_ref=typed(2113, "l3_reason_catalog"),
        reason_codes=("advice_only", "projection_only", "handoff_only", "no_real_execution"),
    )
    weight_catalog = OrchestrationWeightInputCatalog(
        catalog_ref=typed(2114, "l3_weight_catalog"),
        affective_weight_names=("exploration_weight", "caution_weight", "persistence_weight"),
        dynamic_drive_weight_names=("priority_weight", "stability_pressure_weight", "risk_pressure_weight"),
    )
    math_boundary_note = OrchestrationMathBoundaryNote(note_ref=typed(2115, "l3_math_boundary_note"))
    math_catalog = OrchestrationMathCatalog(
        catalog_ref=typed(2116, "l3_math_catalog"),
        input_object_names=("MathOrchestrationInput", "SkillToolMathInput", "IntentMathInput", "BoundaryExecutionMathInput", "ObservationFeedbackMathInput", "ValidationRecoveryMathInput"),
        result_object_names=("MathEvaluation", "SkillToolMathResult", "IntentMathResult", "BoundaryExecutionMathResult", "ObservationFeedbackMathResult", "ValidationRecoveryMathResult"),
        score_catalog_ref=score_catalog.catalog_ref,
        ranking_catalog_ref=ranking_catalog.catalog_ref,
        recommendation_catalog_ref=recommendation_catalog.catalog_ref,
    )
    math_report = OrchestrationMathConsistencyReport(
        report_ref=typed(2117, "l3_math_consistency_report"),
        checked_score_names=score_catalog.score_object_names,
        consistency_score=1.0,
    )
    math_snapshot = OrchestrationMathSnapshotRef(
        snapshot_ref=typed(2118, "l3_math_snapshot"),
        source_catalog_refs=(math_catalog.catalog_ref,),
        stable_hash_hint="stable_snapshot_ref_only",
    )
    math_freeze = OrchestrationMathFreezeNote(
        note_ref=typed(2119, "l3_math_freeze_note"),
        frozen_catalog_refs=(math_catalog.catalog_ref, score_catalog.catalog_ref, ranking_catalog.catalog_ref),
    )

    projection_ref = OrchestrationProjectionRef(
        projection_ref=typed(2120, "l3_projection"),
        projection_kind=OrchestrationProjectionKind.SUMMARY,
        source_ref=phase7["validation_ref"].request_ref,
    )
    state_update = OrchestrationStateUpdateSuggestion(
        suggestion_ref=typed(2121, "l3_state_update_suggestion"),
        subject_ref=phase7["validation_ref"].request_ref,
        suggested_field_names=("latest_validation_request_ref", "latest_recovery_request_ref"),
        reason_codes=("l2_record_only",),
        confidence=0.9,
    )
    summary_projection = OrchestrationSummaryProjection(
        projection_ref=projection_ref,
        run_ref=phase7["run_ref"],
        task_ref=phase7["task_ref"],
        turn_ref=phase7["turn_ref"],
        step_ref=phase7["step_ref"],
        component_refs=(component_index.index_ref, math_catalog.catalog_ref),
        summary="L3 closure summary projection only",
        confidence=0.95,
    )
    math_projection = OrchestrationMathProjection(
        projection_ref=OrchestrationProjectionRef(typed(2122, "l3_math_projection"), OrchestrationProjectionKind.MATH),
        score_vectors=(phase7["validation_recovery_vector"], phase7["iteration_evolution_vector"]),
        score_refs=(score_catalog.catalog_ref,),
        ranking_refs=(ranking_catalog.catalog_ref,),
        recommendation_refs=(recommendation_catalog.catalog_ref,),
        reason_codes=("math_catalog_ready",),
        confidence=0.93,
    )
    route_projection = OrchestrationRouteProjection(
        projection_ref=OrchestrationProjectionRef(typed(2123, "l3_route_projection"), OrchestrationProjectionKind.ROUTE),
        route_scores=((phase7["validation_ranking"].top_route_ref, 0.82), (phase7["recovery_ranking"].top_route_ref, 0.8)),
        top_route_ref=phase7["validation_ranking"].top_route_ref,
        alternative_route_refs=(phase7["recovery_ranking"].top_route_ref,),
        reason_codes=("validation_route_top",),
        confidence=0.9,
    )
    trace_projection = OrchestrationTraceProjection(
        projection_ref=OrchestrationProjectionRef(typed(2124, "l3_trace_projection"), OrchestrationProjectionKind.TRACE),
        trace_refs=(typed(2125, "trace_ref"),),
        event_refs=(typed(2126, "event_ref"),),
        summary="trace refs only",
    )
    audit_projection = OrchestrationAuditRefProjection(
        projection_ref=OrchestrationProjectionRef(typed(2127, "l3_audit_projection"), OrchestrationProjectionKind.AUDIT_REF),
        audit_ref_hints=(typed(2128, "audit_ref_hint"),),
        summary="audit refs only",
    )
    projection = OrchestrationProjection(
        projection_ref=projection_ref,
        summary_projection=summary_projection,
        math_projection=math_projection,
        route_projection=route_projection,
        trace_projection=trace_projection,
        audit_ref_projection=audit_projection,
        state_update_suggestions=(state_update,),
    )
    projection_envelope = OrchestrationProjectionEnvelope(
        envelope_ref=typed(2129, "l3_projection_envelope"),
        projection=projection,
        source_refs=(phase7["validation_ref"].request_ref, phase7["recovery_ref"].request_ref),
        reason_codes=("closure_projection_ready",),
    )
    projection_report = OrchestrationProjectionConsistencyReport(
        report_ref=typed(2130, "l3_projection_consistency_report"),
        checked_projection_refs=(projection_ref.projection_ref,),
        reason_codes=("projection_ref_present",),
        consistency_score=1.0,
    )

    l4_request_bundle = L3ToL4ExecutionRequestBundle(
        bundle_ref=typed(2140, "l3_l4_request_bundle"),
        execution_requests=(phase5["execution_request"],),
        dispatch_requests=(phase5["dispatch_request"],),
        request_refs=(phase5["execution_ref"].request_ref, phase5["dispatch_ref"].request_ref),
    )
    l4_ref_bundle = L3ToL4ExecutionRefBundle(
        bundle_ref=typed(2141, "l3_l4_ref_bundle"),
        plan_refs=(phase5["plan_ref"],),
        step_refs=(phase5["execution_step"],),
        token_refs=(phase5["token_ref"],),
        result_refs=(phase5["result_ref"],),
        failure_refs=(phase5["failure_ref"],),
        resume_refs=(phase5["resume_ref"],),
        cancel_refs=(phase5["cancel_ref"],),
    )
    l4_readiness = L3ToL4ExecutionReadinessSummary(
        summary_ref=typed(2142, "l3_l4_readiness"),
        request_bundle_ref=l4_request_bundle.bundle_ref,
        readiness_score=0.86,
        reason_codes=("request_refs_present",),
    )
    l4_boundary_note = L3ToL4ExecutionBoundaryNote(note_ref=typed(2143, "l3_l4_boundary_note"))
    l4_guarantee = L3ToL4NonExecutionGuarantee(guarantee_ref=typed(2144, "l3_l4_non_execution"))
    l4_consumer = L3ToL4ExpectedConsumerNote(note_ref=typed(2145, "l3_l4_consumer_note"))
    l4_freeze = L3ToL4InterfaceFreezeNote(note_ref=typed(2146, "l3_l4_freeze"), frozen_object_names=("ExecutionRequest", "ExecutionDispatchRequest", "ExecutionResultRef", "ExecutionFailureRef"))
    l4_compat = L3ToL4CompatibilityCheckResult(result_ref=typed(2147, "l3_l4_compat"), checked_object_names=l4_freeze.frozen_object_names, compatibility_score=1.0)
    l4_prereq = L4PlanningPrerequisiteNote(note_ref=typed(2148, "l4_prereq"))
    l4_envelope = L3ToL4HandoffEnvelope(envelope_ref=typed(2149, "l3_l4_envelope"), request_bundle=l4_request_bundle, ref_bundle=l4_ref_bundle, readiness_summary=l4_readiness, boundary_note=l4_boundary_note, non_execution_guarantee=l4_guarantee, expected_consumer_note=l4_consumer, freeze_note=l4_freeze)

    boundary_decision_ref = BoundaryDecisionRef(decision_ref=typed(2150, "boundary_decision_ref"), source_request_ref=phase5["boundary_ref"].request_ref)
    policy_decision_ref = PolicyDecisionRef(decision_ref=typed(2151, "policy_decision_ref"))
    denial_reason_ref = DenialReasonRef(reason_ref=typed(2152, "denial_reason_ref"), source_request_ref=phase5["boundary_ref"].request_ref)
    l5_request_bundle = L3ToL5BoundaryRequestBundle(
        bundle_ref=typed(2153, "l3_l5_request_bundle"),
        boundary_requests=(phase5["boundary_request"],),
        risk_review_requests=(phase5["risk_request"],),
        permission_review_requests=(phase5["permission_request"],),
        confirmation_requests=(phase5["confirmation_request"],),
        lease_requests=(phase5["lease_request"],),
        request_refs=(phase5["boundary_ref"].request_ref,),
    )
    l5_ref_bundle = L3ToL5BoundaryRefBundle(bundle_ref=typed(2154, "l3_l5_ref_bundle"), boundary_decision_refs=(boundary_decision_ref,), policy_decision_refs=(policy_decision_ref,), denial_reason_refs=(denial_reason_ref,))
    l5_readiness = L3ToL5BoundaryReadinessSummary(summary_ref=typed(2155, "l3_l5_readiness"), request_bundle_ref=l5_request_bundle.bundle_ref, readiness_score=0.84, evidence_sufficiency_score=0.82, reason_codes=("boundary_request_ready",))
    l5_guarantee = L3ToL5NonDecisionGuarantee(guarantee_ref=typed(2156, "l3_l5_non_decision"))
    l5_consumer = L3ToL5ExpectedConsumerNote(note_ref=typed(2157, "l3_l5_consumer_note"))
    l5_freeze = L3ToL5InterfaceFreezeNote(note_ref=typed(2158, "l3_l5_freeze"), frozen_object_names=("BoundaryCheckRequest", "RiskReviewRequest", "PermissionReviewRequest", "ConfirmationRequest", "LeaseRequest"))
    l5_compat = L3ToL5CompatibilityCheckResult(result_ref=typed(2159, "l3_l5_compat"), checked_object_names=l5_freeze.frozen_object_names, compatibility_score=1.0)
    l5_prereq = L5PlanningPrerequisiteNote(note_ref=typed(2160, "l5_prereq"))
    l5_open = L5BoundaryOpenQuestionNote(note_ref=typed(2161, "l5_open_question"), question_hints=("ticket_shape_future_l5",))
    l5_envelope = L3ToL5HandoffEnvelope(envelope_ref=typed(2162, "l3_l5_envelope"), request_bundle=l5_request_bundle, ref_bundle=l5_ref_bundle, readiness_summary=l5_readiness, non_decision_guarantee=l5_guarantee, expected_consumer_note=l5_consumer, freeze_note=l5_freeze)

    observation_service = ObservationServiceRequest(request_ref=typed(2170, "observation_service_request"), source_ref=phase6["observation_ref"].observation_ref)
    validation_service = ValidationServiceRequest(request_ref=typed(2171, "validation_service_request"), source_ref=phase7["validation_ref"].request_ref)
    recovery_service = RecoveryServiceRequest(request_ref=typed(2172, "recovery_service_request"), source_ref=phase7["recovery_ref"].request_ref)
    iteration_service = IterationServiceRequest(request_ref=typed(2173, "iteration_service_request"), source_ref=phase7["iteration_request"].request_ref.request_ref)
    evolution_service = EvolutionServiceRequest(request_ref=typed(2174, "evolution_service_request"), source_ref=phase7["evolution_request"].request_ref.request_ref)
    l6_request_bundle = L3ToL6SubsystemRequestBundle(
        bundle_ref=typed(2175, "l3_l6_request_bundle"),
        subsystem_requests=(phase6["subsystem_request"],),
        memory_requests=(phase6["memory_request"],),
        retrieval_requests=(phase6["retrieval_request"],),
        learning_requests=(phase6["learning_request"],),
        affective_requests=(phase6["affective_request"],),
        observation_requests=(observation_service,),
        validation_requests=(validation_service,),
        recovery_requests=(recovery_service,),
        iteration_requests=(iteration_service,),
        evolution_requests=(evolution_service,),
    )
    l6_ref_bundle = L3ToL6SubsystemRefBundle(bundle_ref=typed(2176, "l3_l6_ref_bundle"), result_refs=(), failure_refs=())
    l6_readiness = L3ToL6SubsystemReadinessSummary(summary_ref=typed(2177, "l3_l6_readiness"), request_bundle_ref=l6_request_bundle.bundle_ref, readiness_score=0.83, reason_codes=("service_request_refs_present",))
    l6_guarantee = L3ToL6NonImplementationGuarantee(guarantee_ref=typed(2178, "l3_l6_non_implementation"))
    l6_consumer = L3ToL6ExpectedConsumerNote(note_ref=typed(2179, "l3_l6_consumer_note"))
    l6_freeze = L3ToL6InterfaceFreezeNote(note_ref=typed(2180, "l3_l6_freeze"), frozen_object_names=("SubsystemServiceRequest", "MemoryServiceRequest", "RetrievalServiceRequest", "LearningServiceRequest", "AffectiveServiceRequest"))
    l6_compat = L3ToL6CompatibilityCheckResult(result_ref=typed(2181, "l3_l6_compat"), checked_object_names=l6_freeze.frozen_object_names, compatibility_score=1.0)
    l6_prereq = L6PlanningPrerequisiteNote(note_ref=typed(2182, "l6_prereq"))
    l6_open = L6SubsystemOpenQuestionNote(note_ref=typed(2183, "l6_open_question"), question_hints=("service_result_shape_future_l6",))
    l6_envelope = L3ToL6HandoffEnvelope(envelope_ref=typed(2184, "l3_l6_envelope"), request_bundle=l6_request_bundle, ref_bundle=l6_ref_bundle, readiness_summary=l6_readiness, non_implementation_guarantee=l6_guarantee, expected_consumer_note=l6_consumer, freeze_note=l6_freeze)

    closure_request = L3ClosureCheckRequest(request_ref=typed(2190, "l3_closure_request"), requested_check_kinds=tuple(L3ClosureCheckKind), target_stage_names=("phase1", "phase2", "phase3", "phase4", "phase5", "phase6", "phase7", "phase8"))
    closure_result = L3ClosureCheckResult(result_ref=typed(2191, "l3_closure_result"), request_ref=closure_request.request_ref, passed_check_kinds=tuple(L3ClosureCheckKind), readiness_score=1.0)
    boundary_report = L3BoundaryComplianceReport(report_ref=typed(2192, "l3_boundary_report"), compliant=True, compliance_score=1.0, guarantee_refs=(l4_guarantee.guarantee_ref, l5_guarantee.guarantee_ref, l6_guarantee.guarantee_ref))
    import_report = L3ImportStabilityReport(report_ref=typed(2193, "l3_import_report"), imported_object_names=("OrchestrationProjection", "L3ToL4HandoffEnvelope", "L3FinalFreezeReadinessReport"), stability_score=1.0)
    serialization_report = L3SerializationStabilityReport(report_ref=typed(2194, "l3_serialization_report"), serialized_object_refs=(projection_ref.projection_ref,), stable_hash_refs=(math_snapshot.snapshot_ref,), stability_score=1.0)
    snapshot_report = L3SnapshotCompatibilityReport(report_ref=typed(2195, "l3_snapshot_report"), snapshot_refs=(math_snapshot.snapshot_ref,), compatibility_score=1.0)
    no_execution_report = L3NoExecutionGuaranteeReport(report_ref=typed(2196, "l3_no_execution_report"))
    no_decision_report = L3NoDecisionGuaranteeReport(report_ref=typed(2197, "l3_no_decision_report"))
    no_subsystem_report = L3NoSubsystemGuaranteeReport(report_ref=typed(2198, "l3_no_subsystem_report"))
    freeze_report = L3FinalFreezeReadinessReport(report_ref=typed(2199, "l3_final_freeze_report"), closure_result_ref=closure_result.result_ref, boundary_report_ref=boundary_report.report_ref, import_report_ref=import_report.report_ref, serialization_report_ref=serialization_report.report_ref, snapshot_report_ref=snapshot_report.report_ref, readiness_score=1.0)

    return locals()
