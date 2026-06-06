from __future__ import annotations

from dataclasses import replace

from tiangong_kernel.l5_plugin_host import (
    PluginRegistryAuditEventRef,
    PluginRegistryAuditIndex,
    PluginRegistryConflictReport,
    PluginRegistryIndex,
    PluginRegistryKey,
    PluginRegistryNamespace,
    PluginRegistryQualityGate,
    PluginRegistryRecord,
    PluginRegistryRevision,
    PluginRegistryScope,
    PluginRegistrySnapshot,
    PluginRegistryValidator,
)


def registry_key(plugin_id="plugin:l5_phase3_demo", version_ref="version:1") -> PluginRegistryKey:
    return PluginRegistryKey(
        plugin_id=plugin_id,
        namespace="namespace:user_declared",
        plugin_kind="declaration",
        version_ref=version_ref,
        entry_ref="entry:l5_phase3_demo",
    )


def registry_namespace(policy="multi_version_allowed") -> PluginRegistryNamespace:
    return PluginRegistryNamespace(
        namespace_id="namespace:user_declared",
        namespace_kind="user_installed_declared",
        owner_ref="actor:l5_engineer",
        boundary_ref="boundary:l5_registry",
        uniqueness_policy=policy,
        version_policy_ref="version_policy:declared",
        alias_refs=("alias:stable",),
        channel_refs=("channel:stable",),
        revision_ref="revision:namespace",
    )


def registry_scope() -> PluginRegistryScope:
    return PluginRegistryScope(
        scope_id="scope:l5_phase3_registry",
        scope_kind="declaration_visibility",
        visible_to_refs=("actor:l5_engineer",),
        policy_refs=("policy:l5_registry",),
        handoff_refs=("handoff:l5_phase2",),
        boundary_ref="boundary:l5_scope",
    )


def complete_record(**updates) -> PluginRegistryRecord:
    data = dict(
        registry_record_ref="registry_record:l5_phase3_demo",
        registry_key=registry_key(),
        manifest_ref="manifest:l5_phase2_demo",
        manifest_hash="a" * 64,
        manifest_digest_value="a" * 64,
        package_ref="package:l5_phase2_demo",
        entry_ref="entry:l5_phase3_demo",
        source_trust_ref="source_trust:l5_phase2",
        signature_ref="signature:l5_phase2",
        permission_decl_ref="permission_decl:l5_phase2",
        resource_decl_ref="resource_decl:l5_phase2",
        credential_decl_ref="credential_decl:l5_phase2",
        data_governance_decl_ref="data_governance_decl:l5_phase2",
        audit_decl_ref="audit_decl:l5_phase2",
        version_decl_ref="version_decl:l5_phase2",
        rollback_decl_ref="rollback_decl:l5_phase2",
        compatibility_decl_ref="compatibility_decl:l5_phase2",
        capability_token_decl_ref="capability_token_decl:l5_phase2",
        trust_boundary_decl_ref="trust_boundary_decl:l5_phase2",
        hot_switch_decl_ref="hot_switch_decl:l5_phase3",
        migration_ref="migration:l5_phase3",
        upcast_policy_ref="upcast_policy:l5_phase3",
        replay_compatibility_ref="replay_compatibility:l5_phase3",
        breaking_change_policy_ref="breaking_change_policy:l5_phase3",
        version_slot_ref="version_slot:stable",
        rollback_anchor_ref="rollback_anchor:l5_phase3",
        schema_version_text="0.2",
        api_version="1.0",
        manifest_version="1.0.0",
        plugin_version_ref="version:1",
        plugin_version_text="1.0.0",
        alias_ref="alias:stable",
        channel_ref="channel:stable",
        status_ref="status:declared_only",
        created_at_ref="time:created",
        updated_at_ref="time:updated",
        mount_surface_refs=("surface:skill",),
        exclusive_mount_surface_refs=("surface:exclusive_skill",),
        permission_tags=("risk:declaration_only",),
        resource_tags=("resource:bounded",),
        summary="L5 phase3 registry declaration only",
        forbidden_scan_report_ref="forbidden_scan:l5_phase3",
        forbidden_scan_summary="no blocking findings",
        actor_ref="actor:l5_engineer",
        scope_ref="scope:l5_phase3_registry",
        trace_ref="trace:l5_phase3_registry",
        policy_ref="policy:l5_registry",
        approval_ref="approval:l5_phase3",
        responsibility_chain_ref="responsibility:l5_phase3",
        accountability_ref="accountability:l5_phase3",
        provenance_refs=("provenance:l5_phase2",),
        evidence_refs=("evidence:l5_phase3_registry",),
        tamper_evidence_ref="tamper:l5_phase3_registry",
    )
    data.update(updates)
    return PluginRegistryRecord(**data)


def complete_snapshot(records=None, **updates) -> PluginRegistrySnapshot:
    data = dict(
        snapshot_ref="registry_snapshot:l5_phase3",
        records=tuple(records if records is not None else (complete_record(),)),
        revision_ref="revision:l5_phase3",
        base_snapshot_ref="snapshot:l5_phase2_baseline",
        delta_baseline_ref="delta_baseline:l5_phase2",
        actor_ref="actor:l5_engineer",
        scope_ref="scope:l5_phase3_registry",
        trace_ref="trace:l5_phase3_registry",
        policy_ref="policy:l5_registry",
        approval_ref="approval:l5_phase3",
        handoff_ref="handoff:l5_phase2_to_l5_phase3",
        responsibility_chain_ref="responsibility:l5_phase3",
        evidence_refs=("evidence:l5_phase3_snapshot",),
        provenance_refs=("provenance:l5_phase2",),
        accountability_ref="accountability:l5_phase3",
        tamper_evidence_ref="tamper:l5_phase3_snapshot",
        summary="L5 phase3 declaration registry snapshot",
    )
    data.update(updates)
    return PluginRegistrySnapshot(**data)


def conflict_report(snapshot=None) -> PluginRegistryConflictReport:
    snapshot = snapshot or complete_snapshot()
    return PluginRegistryValidator(validator_ref="validator:l5_phase3").validate(snapshot, (registry_namespace(),))


def quality_gate() -> PluginRegistryQualityGate:
    return PluginRegistryQualityGate(gate_ref="quality_gate:l5_phase3")


def audit_index() -> PluginRegistryAuditIndex:
    event = PluginRegistryAuditEventRef(
        event_ref="audit_event:registry_snapshot_created",
        event_kind="registry_snapshot_created",
        trace_ref="trace:l5_phase3_registry",
        evidence_ref="evidence:l5_phase3_registry",
        responsibility_chain_ref="responsibility:l5_phase3",
        summary="snapshot declaration created",
    )
    return PluginRegistryAuditIndex(audit_index_ref="audit_index:l5_phase3", events=(event,), evidence_refs=("evidence:audit_index",))
