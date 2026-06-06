from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError

from tiangong_kernel.l5_plugin_host import (
    PluginCapabilityTokenBoundaryDeclaration,
    PluginCredentialRequirementDeclaration,
    PluginPhase5DataGovernanceDeclaration,
    PluginDependencyDeclaration,
    PluginDependencyGraphSnapshot,
    PluginIsolationDeclaration,
    PluginPhase5AuditIndexBuilder,
    PluginPhase5BoundaryValidator,
    PluginPhase5ConflictKind,
    PluginPhase5ConflictSeverity,
    PluginPhase5PublicProjectionBuilder,
    PluginPhase5QualityGate,
    PluginPhase5SwitchBoundaryDeclaration,
    PluginResourceBoundaryDeclaration,
    PluginPhase5TrustBoundaryDeclaration,
)


def refs(prefix: str) -> tuple[str, ...]:
    return (f"{prefix}:ref",)


def common(**kw):
    data = dict(
        actor_ref="actor:l5_phase5",
        scope_ref="scope:l5_phase5",
        trace_ref="trace:l5_phase5",
        evidence_refs=("evidence:redacted_l5_phase5",),
        provenance_refs=("provenance:l5_phase5",),
        responsibility_chain_ref="responsibility:l5_phase5",
        accountability_ref="accountability:l5_phase5",
        tamper_evidence_ref="tamper:l5_phase5",
        risk_tags=("risk:declaration_only",),
    )
    data.update(kw)
    return data


def valid_isolation(**kw):
    data = dict(
        isolation_decl_ref="isolation:decl",
        registry_key_ref="registry_key:sample",
        lifecycle_ref="lifecycle:decl",
        mount_decl_ref="mount:decl",
        isolation_boundary_ref="boundary:isolation",
        sandbox_requirement_ref="sandbox_requirement:declared_only",
        containment_ref="containment:declared",
        quarantine_policy_ref="quarantine:policy_ref",
        side_effect_boundary_ref="side_effect:boundary",
        no_live_action_ref="no_live_action:declared",
        forbidden_action_refs=("forbidden:live_action",),
        required_policy_refs=("policy:isolation",),
        required_permission_refs=("permission:isolation_decl",),
        required_lease_refs=("lease:isolation_decl",),
        required_approval_ref="approval:isolation_decl",
        audit_decl_ref="audit:isolation_decl",
        **common(),
    )
    data.update(kw)
    return PluginIsolationDeclaration(**data)


def valid_dependency(**kw):
    data = dict(
        dependency_decl_ref="dependency:decl",
        registry_key_ref="registry_key:sample",
        dependency_refs=("dependency:core",),
        optional_dependency_refs=("dependency:optional",),
        incompatible_dependency_refs=("dependency:legacy",),
        dependency_policy_ref="policy:dependency",
        version_policy_ref="policy:version",
        compatibility_decl_ref="compatibility:decl",
        migration_ref="migration:decl",
        breaking_change_policy_ref="breaking_change:policy",
        dependency_graph_ref="dependency_graph:decl",
        dependency_snapshot_ref="dependency_graph_snapshot:decl",
        required_policy_refs=("policy:dependency",),
        audit_decl_ref="audit:dependency_decl",
        version_slot_ref="version_slot:stable",
        rollback_anchor_ref="rollback:dependency_anchor",
        transitive_dependency_policy_ref="policy:transitive_dependency",
        dependency_compatibility_matrix_ref="compatibility_matrix:decl",
        old_event_replay_compatibility_ref="replay:old_event_compat",
        upcast_policy_ref="policy:upcast",
        deprecation_policy_ref="policy:deprecation",
        minimum_migration_ref="migration:minimum",
        **common(),
    )
    data.update(kw)
    return PluginDependencyDeclaration(**data)


def valid_dependency_graph(**kw):
    data = dict(
        dependency_graph_snapshot_ref="dependency_graph_snapshot:decl",
        registry_key_refs=("registry_key:sample",),
        node_refs=("node:a", "node:b"),
        edge_refs=(("node:b", "node:a", "edge:requires"),),
        evidence_refs=("evidence:dependency_graph",),
        trace_ref="trace:dependency_graph",
        provenance_refs=("provenance:dependency_graph",),
        responsibility_chain_ref="responsibility:dependency_graph",
        tamper_evidence_ref="tamper:dependency_graph",
    )
    data.update(kw)
    return PluginDependencyGraphSnapshot(**data)


def valid_credential(**kw):
    data = dict(
        credential_decl_ref="credential:decl",
        registry_key_ref="registry_key:sample",
        credential_kind_ref="credential_kind:api_ref_only",
        credential_policy_ref="credential_policy:redacted",
        credential_scope_ref="credential_scope:opaque",
        redaction_policy_ref="redaction:required",
        approval_ref="approval:credential_decl",
        lease_ref="lease:credential_decl",
        audit_decl_ref="audit:credential_decl",
        data_boundary_ref="data_boundary:credential",
        storage_boundary_ref="storage_boundary:redacted",
        forbidden_plaintext_ref="forbidden:plaintext_secret",
        credential_handle_refs=("credential_handle_ref:opaque_decl",),
        credential_binding_refs=("credential_binding:decl",),
        credential_purpose_refs=("purpose:credential_use",),
        credential_audience_refs=("audience:plugin_host",),
        credential_revocation_ref="revocation:credential_check_ref",
        credential_lease_ref="lease:credential_decl",
        value_absent_required=True,
        redacted_required=True,
        credential_rotation_boundary_ref="credential_rotation:boundary",
        migration_credential_policy_ref="policy:credential_migration",
        replay_credential_policy_ref="policy:credential_replay",
        old_credential_redaction_policy_ref="policy:old_credential_redaction",
        credential_rebinding_prohibition_ref="prohibit:credential_rebinding",
        **common(),
    )
    data.update(kw)
    return PluginCredentialRequirementDeclaration(**data)


def valid_data_governance(**kw):
    data = dict(
        data_governance_decl_ref="data_governance:decl",
        registry_key_ref="registry_key:sample",
        data_category_refs=("data_category:privacy",),
        privacy_boundary_ref="privacy_boundary:decl",
        data_minimization_ref="minimization:decl",
        retention_policy_ref="retention:policy",
        deletion_policy_ref="deletion:policy",
        lineage_ref="lineage:decl",
        data_access_policy_ref="policy:data_access_decl",
        storage_policy_ref="policy:storage_decl",
        export_policy_ref="policy:export_decl",
        redaction_policy_ref="policy:redaction",
        audit_decl_ref="audit:data_governance_decl",
        consent_refs=("consent:ref",),
        purpose_refs=("purpose:data_processing",),
        data_lifecycle_refs=("lifecycle:collect_use_delete",),
        data_subject_category_refs=("subject_category:user",),
        processing_basis_refs=("processing_basis:consent",),
        cross_boundary_transfer_refs=("transfer:decl",),
        external_disclosure_boundary_refs=("external_disclosure:boundary",),
        minimization_policy_ref="policy:minimization",
        migration_data_boundary_ref="data_boundary:migration",
        replay_data_minimization_ref="minimization:replay",
        old_event_redaction_policy_ref="policy:old_event_redaction",
        schema_upcast_data_policy_ref="policy:schema_upcast_data",
        rollback_data_boundary_ref="data_boundary:rollback",
        checkpoint_data_policy_ref="policy:checkpoint_data",
        observation_data_policy_ref="policy:observation_data",
        **common(),
    )
    data.update(kw)
    return PluginPhase5DataGovernanceDeclaration(**data)


def valid_resource(**kw):
    data = dict(
        resource_boundary_decl_ref="resource_boundary:decl",
        registry_key_ref="registry_key:sample",
        cpu_budget_ref="budget:cpu",
        memory_budget_ref="budget:memory",
        storage_budget_ref="budget:storage",
        network_budget_ref="budget:network",
        token_budget_ref="budget:token",
        tool_budget_ref="budget:tool",
        rate_limit_policy_ref="policy:rate_limit",
        quota_policy_ref="policy:quota",
        burst_policy_ref="policy:burst",
        cost_policy_ref="policy:cost",
        budget_ledger_ref="budget_ledger:decl",
        audit_decl_ref="audit:resource_boundary",
        manifest_resource_decl_ref="manifest_resource:decl",
        phase2_resource_decl_ref="phase2_resource:decl",
        resource_decl_digest_ref="digest:resource_decl",
        resource_decl_schema_version_ref="schema:resource_decl_v1",
        run_budget_scope_ref="budget_scope:run",
        goal_budget_scope_ref="budget_scope:goal",
        actor_budget_scope_ref="budget_scope:actor",
        budget_owner_ref="budget_owner:actor_ref",
        quota_scope_ref="quota_scope:decl",
        concurrency_budget_ref="budget:concurrency",
        io_budget_ref="budget:io",
        model_call_budget_ref="budget:model_call",
        external_call_budget_ref="budget:external_call",
        metering_policy_ref="policy:metering",
        resource_pressure_policy_ref="policy:resource_pressure",
        degradation_policy_ref="policy:degradation",
        exhaustion_behavior_ref="behavior:exhaustion_decl",
        high_permission_budget_policy_ref="policy:high_permission_budget_expand_with_approval",
        budget_expansion_policy_ref="policy:budget_expansion",
        switch_budget_freeze_ref="switch_budget:freeze_decl",
        rollback_budget_guard_ref="rollback_budget:guard_decl",
        migration_resource_delta_ref="resource_delta:migration_decl",
        replay_resource_guard_ref="resource_guard:replay_decl",
        checkpoint_resource_policy_ref="policy:checkpoint_resource",
        observation_resource_policy_ref="policy:observation_resource",
        **common(),
    )
    data.update(kw)
    return PluginResourceBoundaryDeclaration(**data)


def valid_capability_token(**kw):
    data = dict(
        capability_token_boundary_decl_ref="capability_token_boundary:decl",
        registry_key_ref="registry_key:sample",
        capability_token_decl_ref="capability_token:decl",
        token_scope_refs=("token_scope:decl",),
        token_lease_ref="token_lease:decl",
        token_expiry_ref="token_expiry:decl",
        token_revocation_ref="token_revocation:decl",
        delegation_policy_ref="policy:delegation",
        audience_ref="audience:plugin_host",
        issuer_ref="issuer:ref",
        subject_ref="subject:ref",
        audit_decl_ref="audit:capability_token",
        policy_ref="policy:capability_token",
        policy_refs=("policy:capability_token",),
        **common(),
    )
    data.update(kw)
    return PluginCapabilityTokenBoundaryDeclaration(**data)


def valid_trust_boundary(**kw):
    data = dict(
        trust_boundary_decl_ref="trust_boundary:decl",
        registry_key_ref="registry_key:sample",
        host_boundary_ref="boundary:host",
        plugin_boundary_ref="boundary:plugin",
        data_boundary_refs=("boundary:data",),
        credential_boundary_refs=("boundary:credential",),
        resource_boundary_refs=("boundary:resource",),
        network_boundary_refs=("boundary:network",),
        tool_boundary_refs=("boundary:tool",),
        external_disclosure_boundary_refs=("boundary:external_disclosure",),
        audit_boundary_refs=("boundary:audit",),
        recovery_boundary_refs=("boundary:recovery",),
        lifecycle_boundary_refs=("boundary:lifecycle",),
        mount_boundary_refs=("boundary:mount",),
        policy_ref="policy:trust_boundary",
        policy_refs=("policy:trust_boundary",),
        **common(),
    )
    data.update(kw)
    return PluginPhase5TrustBoundaryDeclaration(**data)


def valid_switch_boundary(**kw):
    data = dict(
        switch_boundary_decl_ref="switch_boundary:decl",
        registry_key_ref="registry_key:sample",
        lifecycle_ref="lifecycle:decl",
        mount_decl_ref="mount:decl",
        hot_switch_decl_ref="hot_switch:decl",
        switch_readiness_ref="switch_readiness:decl",
        pre_switch_checkpoint_ref="checkpoint:pre_switch",
        post_switch_observation_ref="observation:post_switch",
        switch_rollback_route_ref="switch_rollback:route",
        migration_ref="migration:decl",
        replay_compatibility_ref="replay:compat",
        breaking_change_policy_ref="policy:breaking_change",
        isolation_boundary_ref="boundary:isolation",
        dependency_decl_ref="dependency:decl",
        credential_boundary_ref="boundary:credential",
        data_governance_boundary_ref="boundary:data_governance",
        resource_boundary_ref="boundary:resource",
        required_policy_refs=("policy:switch_boundary",),
        required_approval_ref="approval:switch_boundary",
        audit_decl_ref="audit:switch_boundary",
        **common(),
    )
    data.update(kw)
    return PluginPhase5SwitchBoundaryDeclaration(**data)


def all_valid_declarations():
    return dict(
        isolation_decls=(valid_isolation(),),
        dependency_decls=(valid_dependency(),),
        dependency_graphs=(valid_dependency_graph(),),
        credential_decls=(valid_credential(),),
        data_governance_decls=(valid_data_governance(),),
        resource_decls=(valid_resource(),),
        capability_token_decls=(valid_capability_token(),),
        trust_boundary_decls=(valid_trust_boundary(),),
        switch_boundary_decls=(valid_switch_boundary(),),
    )


def validate_all(**overrides):
    data = all_valid_declarations()
    data.update(overrides)
    return PluginPhase5BoundaryValidator().inspect_boundaries(**data)


def full_quality_gate(report=None, **kw):
    report = report or validate_all()
    defaults = dict(
        compileall_passed=True,
        collect_only_passed=True,
        targeted_pytest_passed=True,
        plugin_host_subset_passed=True,
        plugin_host_subset_non_empty=True,
        full_pytest_passed=True,
        forbidden_scan_passed=True,
        hash_compare_passed=True,
        test_inventory_compare_passed=True,
    )
    defaults.update(kw)
    return PluginPhase5QualityGate().decide(report, **defaults)


def valid_projection():
    gate = full_quality_gate()
    return PluginPhase5PublicProjectionBuilder().make_projection(
        isolation=valid_isolation(),
        dependency=valid_dependency(),
        credential=valid_credential(),
        data_governance=valid_data_governance(),
        resource=valid_resource(),
        capability_token=valid_capability_token(),
        trust_boundary=valid_trust_boundary(),
        switch_boundary=valid_switch_boundary(),
        quality_gate=gate,
    )


def valid_audit_index():
    report = validate_all()
    gate = full_quality_gate(report)
    projection = valid_projection()
    return PluginPhase5AuditIndexBuilder().make_index(report=report, projection=projection, quality_gate=gate)


__all__ = [name for name in globals() if name.startswith("valid_") or name in {"validate_all", "full_quality_gate", "all_valid_declarations", "FrozenInstanceError", "copy"}]
