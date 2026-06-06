from __future__ import annotations

from types import SimpleNamespace

from tiangong_kernel.l5_plugin_host import (
    PluginAuditDeclaration,
    PluginCapabilityTokenDeclaration,
    PluginCompatibilityDeclaration,
    PluginCredentialDeclaration,
    PluginDataGovernanceDeclaration,
    PluginEntryReference,
    PluginManifestQualityGate,
    calculate_manifest_digest,
    PluginManifestSchema,
    PluginMountSurfaceDeclaration,
    PluginPermissionDeclaration,
    PluginResourceDeclaration,
    PluginRollbackDeclaration,
    PluginSignatureReference,
    PluginSourceTrustReference,
    PluginTrustBoundaryDeclaration,
    PluginVersionDeclaration,
)


def complete_manifest() -> SimpleNamespace:
    manifest = SimpleNamespace(
        plugin_id="plugin:l5_phase2_manifest",
        name="L5 phase 2 declaration",
        version="1.0.0",
        kind="declaration",
        declared_entry_ref="entry:l5_phase2",
        actor_ref="actor:l5_engineer",
        scope_ref="scope:l5_phase2",
        trace_ref="trace:l5_phase2",
        policy_ref="policy:l5_phase2",
        approval_ref="approval:l5_phase2",
        handoff_ref="handoff:l5_phase1",
        evidence_refs=("evidence:l5_phase2",),
        provenance_refs=("provenance:l5_phase2",),
        accountability_ref="accountability:l5_phase2",
        tamper_evidence_ref="tamper:l5_phase2",
        plugin_name="L5 phase 2 declaration",
        plugin_kind="declaration",
        schema_version="0.2",
        manifest_version="1.0.0",
        entry_ref=PluginEntryReference(entry_ref="entry:l5_phase2"),
        package_ref="package:l5_phase2",
        mount_surfaces=(
            PluginMountSurfaceDeclaration(
                surface_ref="surface:l5_phase2_skill",
                surface_kind="skill_surface",
                boundary_ref="boundary:tool",
            ),
        ),
        permission_decl=PluginPermissionDeclaration(
            required_permissions=("permission:read_refs",),
            risk_tags=("risk:declaration_only",),
            human_confirmation_required=True,
            lease_required=True,
            policy_refs=("policy:permission",),
        ),
        resource_decl=PluginResourceDeclaration(
            cpu_budget_ref="budget:cpu",
            memory_budget_ref="budget:memory",
            io_budget_ref="budget:io",
            network_budget_ref="budget:network",
            concurrency_budget_ref="budget:concurrency",
            rate_limit_ref="rate:l5_phase2",
            cost_budget_ref="budget:cost",
            run_budget_scope_ref="scope:run_budget",
            goal_budget_scope_ref="scope:goal_budget",
            actor_budget_scope_ref="scope:actor_budget",
            budget_owner_ref="owner:l5_host",
            quota_ref="quota:l5_phase2",
            resource_pressure_policy_ref="policy:pressure",
            degradation_policy_ref="policy:degrade",
            exhaustion_behavior_ref="policy:exhaustion",
            metering_policy_ref="policy:metering",
        ),
        credential_decl=PluginCredentialDeclaration(
            credential_handle_refs=("credential_handle:l5_phase2",),
            secret_scope_refs=("secret_scope:l5_phase2",),
            rotation_policy_ref="policy:rotation",
            credential_binding_refs=("binding:credential",),
            credential_purpose_refs=("purpose:credential_use",),
            credential_audience_refs=("audience:l5_host",),
            credential_revocation_ref="revocation:credential",
            credential_lease_ref="lease:credential",
        ),
        data_governance_decl=PluginDataGovernanceDeclaration(
            data_classification_refs=("data_classification:internal",),
            privacy_boundary_refs=("privacy_boundary:l5",),
            retention_policy_ref="retention:l5_phase2",
            external_disclosure_policy_ref="external_disclosure:none",
            taint_policy_ref="taint:l5_phase2",
            consent_refs=("consent:l5_phase2",),
            purpose_refs=("purpose:l5_phase2",),
            data_lifecycle_refs=("data_lifecycle:l5_phase2",),
        ),
        audit_decl=PluginAuditDeclaration(
            audit_event_kinds=("manifest_declared",),
            replay_policy_ref="replay:l5_phase2",
            responsibility_chain_ref="responsibility:l5_phase2",
            provenance_policy_ref="provenance_policy:l5_phase2",
            evidence_boundary_ref="evidence_boundary:l5_phase2",
            audit_retention_policy_ref="audit_retention:l5_phase2",
        ),
        version_decl=PluginVersionDeclaration(
            plugin_version="1.0.0",
            api_version="1.0.0",
            schema_version_text="0.2",
            compatibility_range="0.2.x",
            migration_ref="migration:none",
            version_slot_ref="version_slot:l5_phase2",
        ),
        rollback_decl=PluginRollbackDeclaration(
            rollback_anchor_ref="rollback_anchor:l5_phase2",
            rollback_policy_ref="rollback_policy:l5_phase2",
        ),
        compatibility_decl=PluginCompatibilityDeclaration(
            required_l0_l1_l2_l3_l4_l5_ranges=("L0-L5:current",),
            required_port_refs=("port:plugin_host",),
            required_state_refs=("state:plugin",),
            required_handoff_refs=("handoff:l4_to_l5",),
        ),
        capability_token_decl=PluginCapabilityTokenDeclaration(
            required_token_refs=("capability_token:declared",),
            token_scope_refs=("scope:capability",),
            lease_ref="lease:capability",
            expiry_ref="expiry:capability",
            revocation_check_ref="revocation:capability",
            delegation_policy_ref="delegation:l5_phase2",
            audience_ref="audience:l5_host",
        ),
        trust_boundary_decl=PluginTrustBoundaryDeclaration(
            host_boundary_ref="boundary:host",
            plugin_boundary_ref="boundary:plugin",
            data_boundary_refs=("boundary:data",),
            tool_boundary_refs=("boundary:tool",),
            network_boundary_refs=("boundary:network",),
            credential_boundary_refs=("boundary:credential",),
            external_disclosure_boundary_refs=("boundary:external_disclosure",),
        ),
        source_trust_ref=PluginSourceTrustReference(trust_ref="source_trust:l5_phase2"),
        signature_ref=PluginSignatureReference(signature_ref="signature:l5_phase2", digest_ref="digest:l5_phase2"),
        created_at_ref="created_at:l5_phase2",
        producer_ref="producer:l5_engineer",
        boundary_baseline_ref="boundary_baseline:l5_phase1",
        handoff_evidence_refs=("handoff_evidence:l5_phase1",),
        no_live_external_action_guarantee_ref="guarantee:no_live_external_action",
        no_l6_implementation_guarantee_ref="guarantee:no_l6_implementation",
        no_lower_layer_mutation_guarantee_ref="guarantee:no_lower_layer_mutation",
        no_legacy_runtime_guarantee_ref="guarantee:no_legacy_runtime",
        lifecycle_event_refs=("lifecycle_event:declared",),
        consent_refs=("consent:l5_phase2",),
        purpose_refs=("purpose:l5_phase2",),
        data_lifecycle_refs=("data_lifecycle:l5_phase2",),
        manifest_hash="",
    )
    manifest.manifest_hash = calculate_manifest_digest(manifest)
    return manifest


def clone_manifest(**updates) -> SimpleNamespace:
    data = vars(complete_manifest()).copy()
    data.update(updates)
    if "manifest_hash" not in updates:
        data["manifest_hash"] = ""
        cloned = SimpleNamespace(**data)
        cloned.manifest_hash = calculate_manifest_digest(cloned)
        return cloned
    return SimpleNamespace(**data)


def quality_gate() -> PluginManifestQualityGate:
    return PluginManifestQualityGate(
        gate_ref="quality_gate:l5_phase2",
        schema=PluginManifestSchema(schema_ref="schema:l5_phase2"),
    )


def mutable_manifest_namespace() -> SimpleNamespace:
    return clone_manifest()
