from l3_phase1_builders import typed
from tiangong_kernel.l4_execution import (
    L4BoundaryInvariantSuite,
    L4ClosureProjection,
    L4ComponentRegistrySummary,
    L4FinalFreezeReadinessReport,
    L4FinalQualityChecklist,
    L4ModuleInventory,
    L4NoBoundaryBypassGuarantee,
    L4NoL6ImplementationGuarantee,
    L4NoLegacyRuntimeGuarantee,
    L4NoLiveActionGuarantee,
    L4ObjectFamilyIndex,
    L4PublicExportMap,
    L4ToL5BoundaryFeedback,
    L4ToL5ConcurrencySummary,
    L4ToL5ExecutionAuditSummary,
    L4ToL5HandoffEnvelope,
    L4ToL5PermitConsumptionSummary,
    L4ToL5ResourceBudgetSummary,
    L4ToL6AdapterRequirement,
    L4ToL6ExecutionServiceNeed,
    L4ToL6ObservationRequirement,
    L4ToL6RecoveryRequirement,
    L4ToL6ReplayRequirement,
)


def phase8_ref(offset: int, ref_type: str):
    return typed(11000 + offset, ref_type)


def module_inventory():
    return L4ModuleInventory(inventory_ref=phase8_ref(1, "l4_module_inventory"))


def public_export_map():
    return L4PublicExportMap(export_map_ref=phase8_ref(2, "l4_public_export_map"))


def object_family_index():
    return L4ObjectFamilyIndex(object_family_index_ref=phase8_ref(3, "l4_object_family_index"))


def component_registry_summary():
    return L4ComponentRegistrySummary(
        component_registry_summary_ref=phase8_ref(4, "l4_component_registry_summary"),
        component_items=(("l4_action_grounding", "static_summary"), ("l4_execution", "closure_summary")),
    )


def boundary_invariant_suite():
    return L4BoundaryInvariantSuite(invariant_suite_ref=phase8_ref(5, "l4_boundary_invariant_suite"))


def no_live_action_guarantee():
    return L4NoLiveActionGuarantee(guarantee_ref=phase8_ref(6, "l4_no_live_action_guarantee"))


def no_boundary_bypass_guarantee():
    return L4NoBoundaryBypassGuarantee(guarantee_ref=phase8_ref(7, "l4_no_boundary_bypass_guarantee"))


def no_l6_implementation_guarantee():
    return L4NoL6ImplementationGuarantee(guarantee_ref=phase8_ref(8, "l4_no_l6_implementation_guarantee"))


def no_legacy_main_chain_guarantee():
    return L4NoLegacyRuntimeGuarantee(guarantee_ref=phase8_ref(9, "l4_no_legacy_main_chain_guarantee"))


def l5_handoff():
    return L4ToL5HandoffEnvelope(
        handoff_ref=phase8_ref(10, "l4_to_l5_handoff"),
        permit_ref=phase8_ref(11, "permit"),
        boundary_feedback_ref=phase8_ref(12, "boundary_feedback"),
        audit_requirement_ref=phase8_ref(13, "audit_requirement"),
        resource_budget_ref=phase8_ref(14, "resource_budget"),
        concurrency_scope_ref=phase8_ref(15, "concurrency_scope"),
        handoff_items=(("boundary", "future_l5_owned"),),
    )


def l5_audit_summary():
    return L4ToL5ExecutionAuditSummary(
        audit_summary_ref=phase8_ref(16, "l4_to_l5_audit_summary"),
        audit_requirement_ref=phase8_ref(13, "audit_requirement"),
        trace_ref=phase8_ref(17, "trace"),
        evidence_ref=phase8_ref(18, "evidence"),
        audit_items=(("audit", "summary_only"),),
    )


def l5_boundary_feedback():
    return L4ToL5BoundaryFeedback(
        feedback_ref=phase8_ref(19, "l4_to_l5_boundary_feedback"),
        boundary_feedback_ref=phase8_ref(12, "boundary_feedback"),
        permit_ref=phase8_ref(11, "permit"),
        failure_ref=phase8_ref(20, "failure"),
        feedback_items=(("scope", "mismatch_hint"),),
    )


def l5_permit_consumption():
    return L4ToL5PermitConsumptionSummary(
        permit_consumption_summary_ref=phase8_ref(21, "l4_to_l5_permit_consumption"),
        permit_ref=phase8_ref(11, "permit"),
        action_ref=phase8_ref(22, "action"),
        consumption_items=(("permit", "ref_consumed_by_path"),),
    )


def l5_resource_summary():
    return L4ToL5ResourceBudgetSummary(
        resource_budget_summary_ref=phase8_ref(23, "l4_to_l5_resource_summary"),
        resource_budget_ref=phase8_ref(14, "resource_budget"),
        usage_report_ref=phase8_ref(24, "usage_report"),
        failure_ref=phase8_ref(20, "failure"),
        resource_items=(("budget", "summary_only"),),
    )


def l5_concurrency_summary():
    return L4ToL5ConcurrencySummary(
        concurrency_summary_ref=phase8_ref(25, "l4_to_l5_concurrency_summary"),
        concurrency_scope_ref=phase8_ref(15, "concurrency_scope"),
        isolation_context_ref=phase8_ref(26, "isolation_context"),
        lock_ref=phase8_ref(27, "lock"),
        concurrency_items=(("concurrency", "future_l5_policy"),),
    )


def l6_adapter_requirement():
    return L4ToL6AdapterRequirement(
        adapter_requirement_ref=phase8_ref(28, "l4_to_l6_adapter_requirement"),
        adapter_descriptor_ref=phase8_ref(29, "adapter_descriptor"),
        capability_descriptor_ref=phase8_ref(30, "adapter_capability"),
        risk_surface_ref=phase8_ref(31, "adapter_risk_surface"),
        priority_items=(("adapter", "future_l6"),),
    )


def l6_observation_requirement():
    return L4ToL6ObservationRequirement(
        observation_requirement_ref=phase8_ref(32, "l4_to_l6_observation_requirement"),
        observation_ref=phase8_ref(33, "observation"),
        evidence_ref=phase8_ref(18, "evidence"),
        observation_items=(("observation", "future_l6"),),
    )


def l6_recovery_requirement():
    return L4ToL6RecoveryRequirement(
        recovery_requirement_ref=phase8_ref(34, "l4_to_l6_recovery_requirement"),
        failure_ref=phase8_ref(20, "failure"),
        rollback_intent_ref=phase8_ref(35, "rollback_intent"),
        recovery_items=(("recovery", "future_l6"),),
    )


def l6_replay_requirement():
    return L4ToL6ReplayRequirement(
        replay_requirement_ref=phase8_ref(36, "l4_to_l6_replay_requirement"),
        replay_summary_ref=phase8_ref(37, "replay_summary"),
        determinism_hint_ref=phase8_ref(38, "determinism_hint"),
        idempotency_hint_ref=phase8_ref(39, "idempotency_hint"),
        replay_items=(("replay", "future_l6"),),
    )


def l6_execution_service_need():
    return L4ToL6ExecutionServiceNeed(
        execution_service_need_ref=phase8_ref(40, "l4_to_l6_execution_service_need"),
        need_items=(("service", "requirement_only"),),
    )


def final_freeze_readiness():
    return L4FinalFreezeReadinessReport(
        readiness_report_ref=phase8_ref(41, "l4_final_freeze_readiness"),
        test_result_items=(("phase8", "pending_or_passed"),),
        risk_items=(("P0", "none_known"),),
    )


def final_quality_checklist():
    return L4FinalQualityChecklist(quality_checklist_ref=phase8_ref(42, "l4_final_quality_checklist"))


def closure_projection():
    return L4ClosureProjection(
        closure_projection_ref=phase8_ref(43, "l4_closure_projection"),
        l3_handoff_ref=phase8_ref(44, "l3_handoff"),
        l5_handoff_ref=l5_handoff().handoff_ref,
        l6_handoff_ref=phase8_ref(45, "l6_handoff"),
        projection_items=(("closure", "projection_only"),),
    )
