from __future__ import annotations

from dataclasses import replace

from tiangong_kernel.l5_plugin_host import (
    PluginHealthSignalDeclaration,
    PluginHealthCheckDeclaration,
    PluginHealthValidator,
    PluginIsolationDispositionDeclaration,
    PluginRecoveryPermissionPreconditionDeclaration,
    PluginHotSwitchPermissionPreconditionDeclaration,
    PluginRollbackPermissionPreconditionDeclaration,
    PluginReplayPermissionPreconditionDeclaration,
    PluginPhase6QualityGateDecision,
    PluginPhase6ProjectionBuilder,
    PluginPhase6AuditIndexBuilder,
)


def base(**extra):
    data = dict(
        actor_ref="actor:l5_phase6_test",
        scope_ref="scope:l5_phase6_test",
        trace_ref="trace:l5_phase6_test",
        policy_ref="policy:l5_phase6_test",
        policy_refs=("policy:l5_phase6_test",),
        approval_ref="approval:l5_phase6_not_ticket",
        evidence_refs=("redacted_evidence:l5_phase6_test",),
        provenance_refs=("provenance:l5_phase6_test",),
        responsibility_chain_ref="responsibility:l5_phase6_test",
        accountability_ref="accountability:l5_phase6_test",
        tamper_evidence_ref="tamper:l5_phase6_test",
        risk_tags=("declaration_only",),
    )
    data.update(extra)
    return data


def signal(**extra):
    data = base(
        health_signal_ref="health_signal:demo",
        registry_key_ref="registry_key:demo",
        lifecycle_ref="lifecycle:demo",
        mount_decl_ref="mount:demo",
        isolation_boundary_ref="isolation_boundary:demo",
        trust_boundary_ref="trust_boundary:demo",
        resource_boundary_ref="resource_boundary:demo",
        signal_kind_ref="signal_kind:declared_health",
        signal_source_ref="signal_source:declaration",
        signal_semantics_ref="semantics:no_live_probe",
        health_status_kind_ref="health_status:declared_safe",
        no_live_probe_ref="guarantee:no_live_probe",
        no_metric_collection_ref="guarantee:no_metric_collection",
    )
    data.update(extra)
    return PluginHealthSignalDeclaration(**data)


def check(**extra):
    data = base(
        health_check_decl_ref="health_check:demo",
        registry_key_ref="registry_key:demo",
        health_signal_refs=("health_signal:demo",),
        readiness_decl_ref="readiness:declared",
        liveness_decl_ref="liveness:declared",
        safety_decl_ref="safety:declared",
        degradation_decl_ref="degradation:declared",
        recovery_needed_decl_ref="recovery_needed:declared",
        switch_blocking_decl_ref="switch_blocking:declared",
        rollback_needed_decl_ref="rollback_needed:declared",
        required_policy_refs=("policy:l5_phase6_health",),
        required_approval_ref="approval:l5_phase6_not_ticket",
        required_evidence_refs=("redacted_evidence:l5_phase6_health_check",),
        audit_decl_ref="audit:health_check",
        health_event_refs=("event:health_check_declared",),
    )
    data.update(extra)
    return PluginHealthCheckDeclaration(**data)


def health_report():
    return PluginHealthValidator().assess(health_signals=(signal(),), health_checks=(check(),))


def disposition(**extra):
    data = base(
        disposition_decl_ref="disposition:demo",
        registry_key_ref="registry_key:demo",
        lifecycle_ref="lifecycle:demo",
        mount_decl_ref="mount:demo",
        health_report_ref="report:l5_phase6_health",
        isolation_decl_ref="isolation:demo",
        trust_boundary_ref="trust_boundary:demo",
        disposition_kind_ref="disposition:hold_declared",
        quarantine_decl_ref="quarantine:declared_only",
        disable_decl_ref="disable:declared_only",
        degrade_decl_ref="degrade:declared_only",
        hold_decl_ref="hold:declared_only",
        block_mount_decl_ref="block_mount:declared_only",
        visibility_revoke_decl_ref="visibility_revoke:declared_only",
        side_effect_containment_ref="containment:declared_only",
        required_policy_refs=("policy:disposition",),
        required_approval_ref="approval:disposition_not_ticket",
        required_evidence_refs=("redacted_evidence:disposition",),
        audit_decl_ref="audit:disposition",
        disposition_event_refs=("event:disposition_declared",),
    )
    data.update(extra)
    return PluginIsolationDispositionDeclaration(**data)


def recovery_perm(**extra):
    data = base(
        recovery_permission_decl_ref="permission_precondition:recovery",
        registry_key_ref="registry_key:demo",
        recovery_plan_ref="recovery_plan:declared",
        recovery_point_ref="recovery_point:declared",
        checkpoint_ref="checkpoint:declared",
        rollback_anchor_ref="rollback_anchor:declared",
        validation_ref="validation:declared",
        regression_ref="regression:declared",
        isolation_disposition_ref="disposition:demo",
        credential_boundary_ref="credential_boundary:demo",
        data_governance_boundary_ref="data_boundary:demo",
        resource_boundary_ref="resource_boundary:demo",
        trust_boundary_ref="trust_boundary:demo",
        capability_token_boundary_ref="capability_token_boundary:demo",
        required_policy_refs=("policy:recovery_permission",),
        required_approval_ref="approval:recovery_not_ticket",
        required_lease_ref="lease:recovery_not_entity",
        required_evidence_refs=("redacted_evidence:recovery_permission",),
        permission_not_grant_ref="decl:not_a_recovery_grant",
        no_live_recovery_ref="guarantee:no_live_recovery",
        audit_decl_ref="audit:recovery_permission",
        recovery_permission_event_refs=("event:recovery_permission_declared",),
    )
    data.update(extra)
    return PluginRecoveryPermissionPreconditionDeclaration(**data)


def hot_switch_perm(**extra):
    data = base(
        hot_switch_permission_decl_ref="permission_precondition:hot_switch",
        registry_key_ref="registry_key:demo",
        hot_switch_decl_ref="hot_switch:declared",
        switch_boundary_decl_ref="switch_boundary:demo",
        switch_readiness_ref="switch_readiness:declared",
        pre_switch_checkpoint_ref="checkpoint:pre_switch_declared",
        post_switch_observation_ref="observation:post_switch_declared",
        switch_rollback_route_ref="rollback_route:switch_declared",
        dependency_compatibility_matrix_ref="compat_matrix:declared",
        credential_boundary_ref="credential_boundary:demo",
        data_governance_boundary_ref="data_boundary:demo",
        resource_boundary_ref="resource_boundary:demo",
        trust_boundary_ref="trust_boundary:demo",
        required_policy_refs=("policy:hot_switch_permission",),
        required_approval_ref="approval:hot_switch_not_ticket",
        required_lease_ref="lease:hot_switch_not_entity",
        required_evidence_refs=("redacted_evidence:hot_switch_permission",),
        permission_not_grant_ref="decl:not_a_hot_switch_grant",
        no_live_hot_switch_ref="guarantee:no_live_hot_switch",
        audit_decl_ref="audit:hot_switch_permission",
        hot_switch_permission_event_refs=("event:hot_switch_permission_declared",),
    )
    data.update(extra)
    return PluginHotSwitchPermissionPreconditionDeclaration(**data)


def rollback_perm(**extra):
    data = base(
        rollback_permission_decl_ref="permission_precondition:rollback",
        registry_key_ref="registry_key:demo",
        rollback_anchor_ref="rollback_anchor:declared",
        rollback_route_ref="rollback_route:declared",
        recovery_point_ref="recovery_point:declared",
        checkpoint_ref="checkpoint:declared",
        dependency_decl_ref="dependency:declared",
        data_governance_boundary_ref="data_boundary:demo",
        resource_boundary_ref="resource_boundary:demo",
        credential_boundary_ref="credential_boundary:demo",
        trust_boundary_ref="trust_boundary:demo",
        validation_ref="validation:declared",
        regression_ref="regression:declared",
        required_policy_refs=("policy:rollback_permission",),
        required_approval_ref="approval:rollback_not_ticket",
        required_lease_ref="lease:rollback_not_entity",
        required_evidence_refs=("redacted_evidence:rollback_permission",),
        permission_not_grant_ref="decl:not_a_rollback_grant",
        no_live_rollback_ref="guarantee:no_live_rollback",
        audit_decl_ref="audit:rollback_permission",
        rollback_permission_event_refs=("event:rollback_permission_declared",),
    )
    data.update(extra)
    return PluginRollbackPermissionPreconditionDeclaration(**data)


def replay_perm(**extra):
    data = base(
        replay_permission_decl_ref="permission_precondition:replay",
        registry_key_ref="registry_key:demo",
        replay_compatibility_ref="replay_compatibility:declared",
        old_event_replay_compatibility_ref="old_event_replay:declared",
        data_governance_boundary_ref="data_boundary:demo",
        replay_data_minimization_ref="data_minimization:replay_declared",
        old_event_redaction_policy_ref="redaction:old_event_declared",
        resource_boundary_ref="resource_boundary:demo",
        replay_resource_guard_ref="resource_guard:replay_declared",
        credential_boundary_ref="credential_boundary:demo",
        replay_credential_policy_ref="credential_policy:replay_declared",
        required_policy_refs=("policy:replay_permission",),
        required_approval_ref="approval:replay_not_ticket",
        required_lease_ref="lease:replay_not_entity",
        required_evidence_refs=("redacted_evidence:replay_permission",),
        permission_not_grant_ref="decl:not_a_replay_grant",
        no_live_replay_ref="guarantee:no_live_replay",
        audit_decl_ref="audit:replay_permission",
        replay_permission_event_refs=("event:replay_permission_declared",),
    )
    data.update(extra)
    return PluginReplayPermissionPreconditionDeclaration(**data)


def quality_gate(**extra):
    data = dict(
        decision_ref="quality_gate:l5_phase6",
        p0_count=0,
        p1_count=0,
        p2_count=0,
        p3_count=0,
        health_declaration_passed=True,
        health_assessment_passed=True,
        health_no_live_probe_passed=True,
        isolation_disposition_declaration_passed=True,
        isolation_no_live_disposition_passed=True,
        recovery_permission_precondition_passed=True,
        hot_switch_permission_precondition_passed=True,
        rollback_permission_precondition_passed=True,
        replay_permission_precondition_passed=True,
        permission_not_grant_passed=True,
        phase5_boundary_compatibility_passed=True,
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
        blocking_reasons=(),
        evidence_index_refs=("evidence_index:l5_phase6",),
        regression_index_refs=("regression_index:l5_phase6",),
        actor_ref="actor:l5_phase6_test",
        scope_ref="scope:l5_phase6_test",
        trace_ref="trace:l5_phase6_quality_gate",
        policy_ref="policy:l5_phase6_quality_gate",
        approval_ref="approval:l5_phase6_not_ticket",
        provenance_refs=("provenance:l5_phase6_quality_gate",),
        responsibility_chain_ref="responsibility:l5_phase6_quality_gate",
        accountability_ref="accountability:l5_phase6_quality_gate",
        tamper_evidence_ref="tamper:l5_phase6_quality_gate",
    )
    data.update(extra)
    return PluginPhase6QualityGateDecision(**data)


def projection():
    return PluginPhase6ProjectionBuilder().make_projection(
        health_report=health_report(),
        disposition=disposition(),
        recovery_permission=recovery_perm(),
        hot_switch_permission=hot_switch_perm(),
        rollback_permission=rollback_perm(),
        replay_permission=replay_perm(),
        quality_gate=quality_gate(),
    )


def audit_index():
    return PluginPhase6AuditIndexBuilder().make_index(
        health_report=health_report(),
        projection=projection(),
        quality_gate=quality_gate(),
    )
