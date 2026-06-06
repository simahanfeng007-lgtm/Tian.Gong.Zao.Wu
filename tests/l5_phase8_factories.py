from tiangong_kernel.l5_plugin_host import (
    GENERIC_HOST_BLOCK_TOOL_ONLY,
    GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION,
    L5CapabilityReadinessMatrix,
    L5FinalQualityGateDecision,
)


def passing_quality_gate(**overrides):
    data = dict(
        phase1_passed=True,
        phase2_passed=True,
        phase3_passed=True,
        phase4_passed=True,
        phase5_passed=True,
        phase6_passed=True,
        phase7_passed=True,
        generic_plugin_host_precheck_passed=True,
        generic_plugin_host_precheck_result=GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION,
        product_artifact_factory_l5_ready=True,
        affective_plugin_l5_ready=True,
        affective_governance_matrix_passed=True,
        affective_capability_readiness_matrix_passed=True,
        affective_public_projection_passed=True,
        affective_l6_handoff_freeze_passed=True,
        affective_audit_binding_passed=True,
        affective_targeted_pytest_passed=True,
        no_affective_direct_execution_passed=True,
        no_affective_authorization_bypass_passed=True,
        no_affective_core_mutation_passed=True,
        l5_final_public_projection_passed=True,
        l5_l6_handoff_freeze_passed=True,
        governance_coverage_matrix_passed=True,
        capability_readiness_matrix_passed=True,
        no_live_plugin_execution_passed=True,
        no_live_l4_adapter_call_passed=True,
        no_live_tool_call_passed=True,
        no_live_artifact_build_passed=True,
        no_legacy_runtime_passed=True,
        no_l6_implementation_passed=True,
        public_projection_safety_passed=True,
        public_projection_second_leak_test_passed=True,
        context_belief_world_boundary_passed=True,
        context_safety_projection_passed=True,
        l6_context_assembler_precondition_passed=True,
        belief_event_precedence_passed=True,
        world_state_evidence_staleness_passed=True,
        tool_model_output_demotion_passed=True,
        memory_injection_boundary_passed=True,
        audit_evidence_chain_passed=True,
        forbidden_scan_passed=True,
        compileall_passed=True,
        collect_only_passed=True,
        targeted_pytest_passed=True,
        plugin_host_subset_passed=True,
        plugin_host_subset_non_empty=True,
        full_pytest_passed=True,
        hash_compare_l0_l4_passed=True,
        hash_compare_l5_phase1_phase7_passed=True,
        test_inventory_compare_passed=True,
        zip_integrity_passed=True,
    )
    data.update(overrides)
    return L5FinalQualityGateDecision(**data)


def blocked_product_matrix():
    return L5CapabilityReadinessMatrix(
        product_artifact_factory_precheck_result=GENERIC_HOST_BLOCK_TOOL_ONLY,
        artifact_factory_ready=False,
        product_builder_ready=False,
    )
