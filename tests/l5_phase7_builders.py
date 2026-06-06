from tiangong_kernel.l5_plugin_host import (
    GENERIC_HOST_PASS,
    GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION,
    GENERIC_HOST_BLOCK_TOOL_ONLY,
    PluginArtifactProductionMountBindingDeclaration,
    PluginCapabilityMountBindingDeclaration,
    PluginContractBindingDeclaration,
    PluginEventSubscriptionDeclaration,
    PluginGenericHostPrecheckReport,
    PluginGenericHostPrecheckValidator,
    PluginHookDeclaration,
    PluginHostBoundaryGateDeclaration,
    PluginHostBoundaryGateValidator,
    PluginHostGovernanceGateDeclaration,
    PluginL3HandoffDeclaration,
    PluginL4AdapterHandoffDeclaration,
    PluginL6EntryDeclaration,
    PluginPhase7AuditIndexBuilder,
    PluginPhase7ProjectionBuilder,
    PluginPhase7QualityGate,
    PluginRouteDeclaration,
    PluginServiceMountBindingDeclaration,
)


def generic_precheck():
    return PluginGenericHostPrecheckValidator().check(
        supports_plugin_kind=True,
        supports_capability_kind=True,
        supports_mount_kind=True,
        supports_contract_ref=True,
    )


def compatible_precheck():
    return PluginGenericHostPrecheckReport(result=GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION)


def tool_only_precheck():
    return PluginGenericHostPrecheckValidator().check(
        supports_plugin_kind=False,
        supports_capability_kind=False,
        supports_mount_kind=False,
        supports_contract_ref=False,
        tool_schema_only=True,
    )


def phase7_objects(include_production=True):
    objects = [
        PluginHostBoundaryGateDeclaration(),
        PluginL3HandoffDeclaration(),
        PluginL4AdapterHandoffDeclaration(),
        PluginL6EntryDeclaration(),
        PluginRouteDeclaration(),
        PluginHookDeclaration(),
        PluginEventSubscriptionDeclaration(),
        PluginContractBindingDeclaration(),
        PluginServiceMountBindingDeclaration(),
        PluginCapabilityMountBindingDeclaration(),
        PluginHostGovernanceGateDeclaration(),
    ]
    if include_production:
        objects.append(PluginArtifactProductionMountBindingDeclaration())
    return tuple(objects)


def phase7_validation_report(include_production=True, precheck=None):
    if precheck is None:
        precheck = compatible_precheck()
    return PluginHostBoundaryGateValidator().check(
        *phase7_objects(include_production=include_production),
        precheck=precheck,
        production_mount_enabled=include_production,
    )


def passing_quality_gate(include_production=True):
    return PluginPhase7QualityGate().decide(
        decision_ref="decision:l5_phase7:test",
        p0_count=0,
        p1_count=0,
        generic_plugin_host_precheck_passed=True,
        generic_plugin_host_precheck_result=GENERIC_HOST_PASS_WITH_COMPATIBLE_EXTENSION,
        production_mount_enabled=include_production,
        production_mount_binding_passed=include_production,
        product_artifact_factory_mount_ready=include_production,
        host_boundary_gate_passed=True,
        l3_handoff_boundary_passed=True,
        l4_handoff_boundary_passed=True,
        l6_entry_boundary_passed=True,
        route_declaration_passed=True,
        hook_declaration_passed=True,
        event_subscription_declaration_passed=True,
        contract_binding_passed=True,
        service_mount_binding_passed=True,
        capability_mount_binding_passed=True,
        governance_gate_passed=True,
        no_l3_bypass_passed=True,
        no_l4_bypass_passed=True,
        no_l6_implementation_passed=True,
        no_live_plugin_load_passed=True,
        no_live_tool_call_passed=True,
        no_live_artifact_build_passed=True,
        no_live_delivery_passed=True,
        phase6_compatibility_passed=True,
        phase5_compatibility_passed=True,
        phase4_lifecycle_compatibility_passed=True,
        phase3_registry_compatibility_passed=True,
        public_projection_safety_passed=True,
        public_projection_second_leak_test_passed=True,
        audit_evidence_chain_passed=True,
        forbidden_scan_passed=True,
        compileall_passed=True,
        collect_only_passed=True,
        targeted_pytest_passed=True,
        plugin_host_subset_passed=True,
        plugin_host_subset_non_empty=True,
        full_pytest_passed=True,
        hash_compare_passed=True,
        test_inventory_compare_passed=True,
        evidence_index_refs=("evidence:l5_phase7:test",),
        regression_index_refs=("regression:l5_phase7:test",),
    )


def phase7_projection():
    precheck = compatible_precheck()
    qg = passing_quality_gate()
    return PluginPhase7ProjectionBuilder().make_projection(
        precheck=precheck,
        quality_gate=qg,
        production_mount=PluginArtifactProductionMountBindingDeclaration(),
    )


def phase7_audit_index():
    qg = passing_quality_gate()
    return PluginPhase7AuditIndexBuilder().make_index(
        boundary_gate=PluginHostBoundaryGateDeclaration(),
        l3_handoff=PluginL3HandoffDeclaration(),
        l4_handoff=PluginL4AdapterHandoffDeclaration(),
        l6_entry=PluginL6EntryDeclaration(),
        production_mount=PluginArtifactProductionMountBindingDeclaration(),
        quality_gate=qg,
    )
