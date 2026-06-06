from __future__ import annotations

import copy

from tiangong_kernel.l5_plugin_host import (
    PluginLifecycleStateMachine,
    PluginLifecycleStatusKind,
    PluginLifecycleTransitionRule,
    PluginLifecycleValidator,
    PluginMountDeclaration,
    PluginLifecyclePublicProjectionBuilder,
    PluginSelfHealingDeclaration,
    PluginRecoveryPlanDeclaration,
    PluginSelfHealingValidator,
)
from tiangong_kernel.l5_plugin_host.registry_key import PluginRegistryKey
from tiangong_kernel.l5_plugin_host.registry_record import PluginRegistryRecord
from tiangong_kernel.l5_plugin_host.registry_snapshot import PluginRegistrySnapshot


def valid_transition(**kw):
    data = dict(
        transition_ref="transition:declared_to_registry",
        from_status_kind=PluginLifecycleStatusKind.DECLARED,
        to_status_kind=PluginLifecycleStatusKind.REGISTRY_VALIDATED,
        trigger_ref="trigger:manifest_reviewed",
        guard_refs=("guard:manifest_quality_gate",),
        required_policy_refs=("policy:l5_lifecycle",),
        required_approval_ref="approval:l5_phase4",
        required_evidence_refs=("evidence:lifecycle_transition",),
        audit_event_ref="audit_event:lifecycle_transition_declared",
        rollback_anchor_ref="rollback:declared",
        migration_ref="migration:declared",
        hot_switch_decl_ref="hot_switch:declared",
        replay_compatibility_ref="replay:declared",
        breaking_change_policy_ref="breaking_change:declared",
        switch_readiness_ref="switch_ready:declared",
        pre_switch_checkpoint_ref="checkpoint:pre_switch",
        post_switch_observation_ref="observation:post_switch",
        switch_rollback_route_ref="route:switch_rollback",
        compatibility_check_ref="compatibility:declared",
        breaking_change_check_ref="breaking_check:declared",
        severity="p3",
        reversible_declared=True,
        side_effect_free_declared=True,
        responsibility_chain_ref="responsibility:lifecycle_transition",
        actor_ref="actor:l5_tester",
        scope_ref="scope:l5_phase4",
        trace_ref="trace:lifecycle_transition",
        policy_ref="policy:l5_lifecycle",
        approval_ref="approval:l5_phase4",
        accountability_ref="accountability:l5_phase4",
        provenance_refs=("provenance:l5_phase4",),
        evidence_refs=("evidence:lifecycle_transition",),
        tamper_evidence_ref="tamper:lifecycle_transition",
        lifecycle_event_refs=("event:lifecycle_transition_declared",),
    )
    data.update(kw)
    return PluginLifecycleTransitionRule(**data)


def hot_switch_transition(**kw):
    return valid_transition(
        transition_ref="transition:enable_to_hot_switch",
        from_status_kind=PluginLifecycleStatusKind.ENABLE_DECLARED,
        to_status_kind=PluginLifecycleStatusKind.HOT_SWITCH_DECLARED,
        trigger_ref="trigger:hot_switch_requested",
        **kw,
    )


def migration_transition(**kw):
    return valid_transition(
        transition_ref="transition:enable_to_migration",
        from_status_kind=PluginLifecycleStatusKind.ENABLE_DECLARED,
        to_status_kind=PluginLifecycleStatusKind.MIGRATION_DECLARED,
        trigger_ref="trigger:migration_requested",
        **kw,
    )


def replay_transition(**kw):
    return valid_transition(
        transition_ref="transition:enable_to_replay",
        from_status_kind=PluginLifecycleStatusKind.ENABLE_DECLARED,
        to_status_kind=PluginLifecycleStatusKind.REPLAY_DECLARED,
        trigger_ref="trigger:replay_requested",
        **kw,
    )


def valid_state_machine(*rules, **kw):
    if not rules:
        rules = (valid_transition(),)
    data = dict(
        state_machine_ref="state_machine:l5_phase4",
        registry_snapshot_ref="snapshot:l5_phase3",
        lifecycle_version="decl-v1",
        allowed_transition_refs=tuple(rule.transition_ref for rule in rules),
        forbidden_transition_refs=("transition:runtime_execution",),
        transition_rules=tuple(rules),
        default_status_kind=PluginLifecycleStatusKind.DECLARED,
        terminal_status_kinds=(PluginLifecycleStatusKind.ARCHIVED_DECLARED,),
        evidence_refs=("evidence:state_machine",),
        policy_ref="policy:l5_lifecycle",
        trace_ref="trace:state_machine",
        tamper_evidence_ref="tamper:state_machine",
        responsibility_chain_ref="responsibility:state_machine",
        actor_ref="actor:l5_tester",
        scope_ref="scope:l5_phase4",
        approval_ref="approval:l5_phase4",
        accountability_ref="accountability:l5_phase4",
        provenance_refs=("provenance:l5_phase4",),
        lifecycle_event_refs=("event:state_machine_declared",),
    )
    data.update(kw)
    return PluginLifecycleStateMachine(**data)


def valid_mount(**kw):
    data = dict(
        mount_decl_ref="mount_decl:sample",
        registry_key_ref="registry_key:sample",
        lifecycle_ref="lifecycle:sample",
        host_surface_ref="surface:control_decl",
        mount_point_ref="mount:opaque_decl_ref",
        boundary_ref="boundary:l5_mount",
        scope_ref="scope:l5_phase4",
        visible_to_refs=("visible:public_projection",),
        policy_refs=("policy:l5_mount",),
        permission_decl_refs=("permission:decl",),
        resource_decl_refs=("resource:decl",),
        credential_decl_refs=("credential:redacted_decl",),
        data_governance_decl_refs=("data_governance:decl",),
        audit_decl_ref="audit:mount_decl",
        health_decl_ref="health:decl",
        rollback_anchor_ref="rollback:anchor",
        version_slot_ref="version_slot:stable",
        migration_ref="migration:decl",
        hot_switch_decl_ref="hot_switch:decl",
        replay_compatibility_ref="replay:compat",
        breaking_change_policy_ref="breaking_change:policy",
        switch_readiness_ref="switch_ready:decl",
        pre_switch_checkpoint_ref="checkpoint:pre_switch",
        post_switch_observation_ref="observation:post_switch",
        switch_rollback_route_ref="route:switch_rollback",
        compatibility_check_ref="compatibility:decl",
        breaking_change_check_ref="breaking_change:check",
        evidence_refs=("evidence:mount_decl",),
        trace_ref="trace:mount_decl",
        responsibility_chain_ref="responsibility:mount_decl",
        actor_ref="actor:l5_tester",
        approval_ref="approval:l5_phase4",
        accountability_ref="accountability:mount_decl",
        provenance_refs=("provenance:l5_phase4",),
        tamper_evidence_ref="tamper:mount_decl",
        mount_event_kind_refs=("event:mount_declared",),
        summary="safe declaration summary",
    )
    data.update(kw)
    return PluginMountDeclaration(**data)


def validate_lifecycle(sm=None, mounts=None):
    validator = PluginLifecycleValidator("validator:l5_phase4")
    return validator.validate_declarations(sm or valid_state_machine(), mounts if mounts is not None else (valid_mount(),))


def valid_self_healing(**kw):
    data = dict(
        self_healing_decl_ref="self_healing:decl",
        registry_key_ref="registry_key:sample",
        lifecycle_ref="lifecycle:sample",
        mount_decl_ref="mount_decl:sample",
        failure_ref="failure:decl",
        fault_ref="fault:decl",
        diagnosis_ref="diagnosis:decl",
        root_cause_ref="root_cause:decl",
        recovery_plan_ref="recovery_plan:decl",
        checkpoint_ref="checkpoint:decl",
        recovery_point_ref="recovery_point:decl",
        rollback_anchor_ref="rollback:anchor",
        transaction_ref="transaction:decl",
        compensation_ref="compensation:decl",
        validation_ref="validation:decl",
        regression_ref="regression:decl",
        postmortem_ref="postmortem:decl",
        repair_suggestion_ref="repair_suggestion:decl",
        required_policy_refs=("policy:self_healing",),
        required_permission_refs=("permission:self_healing",),
        required_lease_refs=("lease:self_healing",),
        required_approval_ref="approval:self_healing",
        audit_decl_ref="audit:self_healing",
        evidence_refs=("evidence:self_healing",),
        trace_ref="trace:self_healing",
        responsibility_chain_ref="responsibility:self_healing",
        severity="p2",
        reversible_declared=True,
        side_effect_free_declared=True,
        actor_ref="actor:l5_tester",
        scope_ref="scope:l5_phase4",
        accountability_ref="accountability:self_healing",
        provenance_refs=("provenance:self_healing",),
        tamper_evidence_ref="tamper:self_healing",
        event_kind_refs=("event:self_healing_declared",),
    )
    data.update(kw)
    return PluginSelfHealingDeclaration(**data)


def valid_recovery_plan(**kw):
    data = dict(
        recovery_plan_ref="recovery_plan:decl",
        failure_ref="failure:decl",
        fault_ref="fault:decl",
        diagnosis_ref="diagnosis:decl",
        root_cause_ref="root_cause:decl",
        recovery_strategy_ref="recovery_strategy:decl",
        checkpoint_ref="checkpoint:decl",
        recovery_point_ref="recovery_point:decl",
        rollback_anchor_ref="rollback:anchor",
        transaction_ref="transaction:decl",
        compensation_ref="compensation:decl",
        validation_ref="validation:decl",
        regression_ref="regression:decl",
        audit_decl_ref="audit:recovery_plan",
        evidence_refs=("evidence:recovery_plan",),
        policy_refs=("policy:recovery_plan",),
        approval_ref="approval:recovery_plan",
        responsibility_chain_ref="responsibility:recovery_plan",
        risk_tags=("risk:declarative_only",),
        actor_ref="actor:l5_tester",
        scope_ref="scope:l5_phase4",
        trace_ref="trace:recovery_plan",
        accountability_ref="accountability:recovery_plan",
        provenance_refs=("provenance:recovery_plan",),
        tamper_evidence_ref="tamper:recovery_plan",
    )
    data.update(kw)
    return PluginRecoveryPlanDeclaration(**data)


def validate_self_healing(decls=None, plans=None):
    validator = PluginSelfHealingValidator("validator:self_healing")
    return validator.inspect_declarations(decls if decls is not None else (valid_self_healing(),), plans if plans is not None else (valid_recovery_plan(),))


def valid_phase3_snapshot():
    key = PluginRegistryKey("plugin.alpha", "user", "tool_group", version_text="1.0.0")
    record = PluginRegistryRecord(
        registry_record_ref="record:alpha",
        registry_key=key,
        manifest_ref="manifest:alpha",
        manifest_hash="a" * 64,
        manifest_digest_value="a" * 64,
        package_ref="package:alpha",
        entry_ref="entry:alpha",
        source_trust_ref="source:trust",
        signature_ref="signature:ref",
        permission_decl_ref="permission:decl",
        resource_decl_ref="resource:decl",
        credential_decl_ref="credential:decl",
        data_governance_decl_ref="data:decl",
        audit_decl_ref="audit:decl",
        version_decl_ref="version:decl",
        rollback_decl_ref="rollback:decl",
        compatibility_decl_ref="compat:decl",
        capability_token_decl_ref="capability_token:decl",
        trust_boundary_decl_ref="trust_boundary:decl",
        hot_switch_decl_ref="hot_switch:decl",
        migration_ref="migration:decl",
        upcast_policy_ref="upcast:policy",
        replay_compatibility_ref="replay:decl",
        breaking_change_policy_ref="breaking_change:policy",
        version_slot_ref="slot:stable",
        rollback_anchor_ref="rollback:anchor",
        schema_version_text="0.2",
        api_version="api:v1",
        manifest_version="manifest:v1",
        plugin_version_ref="plugin_version:1",
        status_ref="status:declared_only",
        mount_surface_refs=("surface:control",),
        permission_tags=("risk:low",),
        resource_tags=("budget:low",),
        actor_ref="actor:l5_tester",
        scope_ref="scope:l5_phase4",
        trace_ref="trace:record",
        policy_ref="policy:record",
        approval_ref="approval:record",
        responsibility_chain_ref="responsibility:record",
        accountability_ref="accountability:record",
        provenance_refs=("provenance:record",),
        evidence_refs=("evidence:record",),
        tamper_evidence_ref="tamper:record",
    )
    return PluginRegistrySnapshot(
        snapshot_ref="snapshot:l5_phase3",
        records=(record,),
        revision_ref="revision:phase3",
        actor_ref="actor:l5_tester",
        scope_ref="scope:l5_phase4",
        trace_ref="trace:snapshot",
        policy_ref="policy:snapshot",
        approval_ref="approval:snapshot",
        responsibility_chain_ref="responsibility:snapshot",
        evidence_refs=("evidence:snapshot",),
        provenance_refs=("provenance:snapshot",),
        accountability_ref="accountability:snapshot",
        tamper_evidence_ref="tamper:snapshot",
    )


def projection_for_valid():
    return PluginLifecyclePublicProjectionBuilder("builder:l5_phase4").build_projection(valid_state_machine(), (valid_mount(),), (valid_self_healing(),), (valid_recovery_plan(),))


def deep_copy(obj):
    return copy.deepcopy(obj)
