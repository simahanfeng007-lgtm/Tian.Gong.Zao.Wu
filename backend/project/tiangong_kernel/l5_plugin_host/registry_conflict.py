"""L5 phase 3 registry conflict report data shells."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


class PluginRegistryConflictSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    P3 = "p3"
    P2 = "p2"
    P1 = "p1"
    P0 = "p0"


class PluginRegistryConflictKind(str, Enum):
    DUPLICATE_PLUGIN_ID = "duplicate_plugin_id"
    DUPLICATE_REGISTRY_KEY = "duplicate_registry_key"
    NAMESPACE_COLLISION = "namespace_collision"
    MANIFEST_HASH_MISMATCH = "manifest_hash_mismatch"
    SCHEMA_VERSION_MISMATCH = "schema_version_mismatch"
    MANIFEST_VERSION_CONFLICT = "manifest_version_conflict"
    PLUGIN_VERSION_CONFLICT = "plugin_version_conflict"
    ENTRY_REF_CONFLICT = "entry_ref_conflict"
    MOUNT_SURFACE_CONFLICT = "mount_surface_conflict"
    PERMISSION_DECL_CONFLICT = "permission_decl_conflict"
    RESOURCE_DECL_CONFLICT = "resource_decl_conflict"
    CREDENTIAL_DECL_CONFLICT = "credential_decl_conflict"
    DATA_GOVERNANCE_CONFLICT = "data_governance_conflict"
    AUDIT_DECL_CONFLICT = "audit_decl_conflict"
    ROLLBACK_DECL_CONFLICT = "rollback_decl_conflict"
    COMPATIBILITY_DECL_CONFLICT = "compatibility_decl_conflict"
    SOURCE_TRUST_CONFLICT = "source_trust_conflict"
    SIGNATURE_REF_CONFLICT = "signature_ref_conflict"
    LEGACY_RUNTIME_CONFLICT = "legacy_runtime_conflict"
    L6_IMPLEMENTATION_CONFLICT = "l6_implementation_conflict"
    LIVE_ACTION_CONFLICT = "live_action_conflict"
    HOT_SWITCH_DECL_CONFLICT = "hot_switch_decl_conflict"
    MIGRATION_DECL_CONFLICT = "migration_decl_conflict"
    REPLAY_COMPATIBILITY_CONFLICT = "replay_compatibility_conflict"
    BREAKING_CHANGE_CONFLICT = "breaking_change_conflict"
    RESPONSIBILITY_CHAIN_CONFLICT = "responsibility_chain_conflict"

    # L5 phase 4 lifecycle and mount declaration conflicts.
    LIFECYCLE_ILLEGAL_TRANSITION_CONFLICT = "lifecycle_illegal_transition_conflict"
    LIFECYCLE_MISSING_GUARD_CONFLICT = "lifecycle_missing_guard_conflict"
    LIFECYCLE_MISSING_POLICY_CONFLICT = "lifecycle_missing_policy_conflict"
    LIFECYCLE_MISSING_AUDIT_CONFLICT = "lifecycle_missing_audit_conflict"
    LIFECYCLE_MISSING_EVIDENCE_CONFLICT = "lifecycle_missing_evidence_conflict"
    LIFECYCLE_EXECUTION_METHOD_CONFLICT = "lifecycle_execution_method_conflict"
    LIFECYCLE_STATUS_RUNTIME_CONFLICT = "lifecycle_status_runtime_conflict"
    LIFECYCLE_HOT_SWITCH_EXECUTION_CONFLICT = "lifecycle_hot_switch_execution_conflict"
    LIFECYCLE_MIGRATION_EXECUTION_CONFLICT = "lifecycle_migration_execution_conflict"
    LIFECYCLE_REPLAY_EXECUTION_CONFLICT = "lifecycle_replay_execution_conflict"
    LIFECYCLE_MISSING_HOT_SWITCH_DECL_CONFLICT = "lifecycle_missing_hot_switch_decl_conflict"
    LIFECYCLE_MISSING_MIGRATION_REF_CONFLICT = "lifecycle_missing_migration_ref_conflict"
    LIFECYCLE_MISSING_REPLAY_COMPATIBILITY_CONFLICT = "lifecycle_missing_replay_compatibility_conflict"
    LIFECYCLE_MISSING_BREAKING_CHANGE_POLICY_CONFLICT = "lifecycle_missing_breaking_change_policy_conflict"
    LIFECYCLE_MISSING_SWITCH_READINESS_CONFLICT = "lifecycle_missing_switch_readiness_conflict"
    LIFECYCLE_MISSING_PRE_SWITCH_CHECKPOINT_CONFLICT = "lifecycle_missing_pre_switch_checkpoint_conflict"
    LIFECYCLE_MISSING_POST_SWITCH_OBSERVATION_CONFLICT = "lifecycle_missing_post_switch_observation_conflict"
    LIFECYCLE_MISSING_SWITCH_ROLLBACK_ROUTE_CONFLICT = "lifecycle_missing_switch_rollback_route_conflict"
    LIFECYCLE_MISSING_COMPATIBILITY_CHECK_CONFLICT = "lifecycle_missing_compatibility_check_conflict"
    LIFECYCLE_MISSING_BREAKING_CHANGE_CHECK_CONFLICT = "lifecycle_missing_breaking_change_check_conflict"
    MOUNT_BOUNDARY_CONFLICT = "mount_boundary_conflict"
    MOUNT_SCOPE_CONFLICT = "mount_scope_conflict"
    MOUNT_PERMISSION_DECL_CONFLICT = "mount_permission_decl_conflict"
    MOUNT_RESOURCE_DECL_CONFLICT = "mount_resource_decl_conflict"
    MOUNT_CREDENTIAL_DECL_CONFLICT = "mount_credential_decl_conflict"
    MOUNT_DATA_GOVERNANCE_DECL_CONFLICT = "mount_data_governance_decl_conflict"
    MOUNT_AUDIT_DECL_CONFLICT = "mount_audit_decl_conflict"
    MOUNT_PUBLIC_PROJECTION_LEAK_CONFLICT = "mount_public_projection_leak_conflict"
    MOUNT_LIVE_ENTRY_CONFLICT = "mount_live_entry_conflict"
    MOUNT_L6_IMPLEMENTATION_CONFLICT = "mount_l6_implementation_conflict"
    MOUNT_MISSING_SWITCH_READINESS_CONFLICT = "mount_missing_switch_readiness_conflict"
    MOUNT_MISSING_PRE_SWITCH_CHECKPOINT_CONFLICT = "mount_missing_pre_switch_checkpoint_conflict"
    MOUNT_MISSING_POST_SWITCH_OBSERVATION_CONFLICT = "mount_missing_post_switch_observation_conflict"
    MOUNT_MISSING_SWITCH_ROLLBACK_ROUTE_CONFLICT = "mount_missing_switch_rollback_route_conflict"
    FORBIDDEN_DYNAMIC_LOADER_CONFLICT = "forbidden_dynamic_loader_conflict"
    SELF_HEALING_MISSING_FAILURE_REF_CONFLICT = "self_healing_missing_failure_ref_conflict"
    SELF_HEALING_MISSING_FAULT_REF_CONFLICT = "self_healing_missing_fault_ref_conflict"
    SELF_HEALING_MISSING_DIAGNOSIS_REF_CONFLICT = "self_healing_missing_diagnosis_ref_conflict"
    SELF_HEALING_MISSING_ROOT_CAUSE_REF_CONFLICT = "self_healing_missing_root_cause_ref_conflict"
    SELF_HEALING_MISSING_RECOVERY_PLAN_CONFLICT = "self_healing_missing_recovery_plan_conflict"
    SELF_HEALING_MISSING_CHECKPOINT_CONFLICT = "self_healing_missing_checkpoint_conflict"
    SELF_HEALING_MISSING_RECOVERY_POINT_CONFLICT = "self_healing_missing_recovery_point_conflict"
    SELF_HEALING_MISSING_TRANSACTION_CONFLICT = "self_healing_missing_transaction_conflict"
    SELF_HEALING_MISSING_COMPENSATION_CONFLICT = "self_healing_missing_compensation_conflict"
    SELF_HEALING_MISSING_AUDIT_CONFLICT = "self_healing_missing_audit_conflict"
    SELF_HEALING_MISSING_EVIDENCE_CONFLICT = "self_healing_missing_evidence_conflict"
    SELF_HEALING_MISSING_VALIDATION_CONFLICT = "self_healing_missing_validation_conflict"
    SELF_HEALING_MISSING_REGRESSION_CONFLICT = "self_healing_missing_regression_conflict"
    SELF_HEALING_LIVE_RECOVERY_EXECUTION_CONFLICT = "self_healing_live_recovery_execution_conflict"
    SELF_HEALING_LIVE_DIAGNOSIS_EXECUTION_CONFLICT = "self_healing_live_diagnosis_execution_conflict"
    SELF_HEALING_LIVE_REPAIR_EXECUTION_CONFLICT = "self_healing_live_repair_execution_conflict"
    SELF_HEALING_CODE_PATCH_CONFLICT = "self_healing_code_patch_conflict"
    SELF_HEALING_CHECKPOINT_EXECUTION_CONFLICT = "self_healing_checkpoint_execution_conflict"
    SELF_HEALING_TRANSACTION_EXECUTION_CONFLICT = "self_healing_transaction_execution_conflict"
    SELF_HEALING_COMPENSATION_EXECUTION_CONFLICT = "self_healing_compensation_execution_conflict"
    SELF_HEALING_POSTMORTEM_PERSISTENCE_CONFLICT = "self_healing_postmortem_persistence_conflict"
    SELF_HEALING_PUBLIC_PROJECTION_LEAK_CONFLICT = "self_healing_public_projection_leak_conflict"


@dataclass(frozen=True, slots=True)
class PluginRegistryConflict:
    conflict_ref: str
    kind: PluginRegistryConflictKind
    severity: PluginRegistryConflictSeverity
    message: str
    affected_record_refs: tuple[str, ...] = field(default_factory=tuple)
    field_path: str = ""
    blocking: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase3_registry"
    detected_by_ref: str = "detector:l5_phase3_registry_validator"
    trace_ref: str = ""
    responsibility_chain_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.conflict_ref, "PluginRegistryConflict.conflict_ref")
        if not isinstance(self.kind, PluginRegistryConflictKind):
            raise ValueError("PluginRegistryConflict.kind must be PluginRegistryConflictKind")
        if not isinstance(self.severity, PluginRegistryConflictSeverity):
            raise ValueError("PluginRegistryConflict.severity must be PluginRegistryConflictSeverity")
        ensure_short_text(self.message, "PluginRegistryConflict.message")
        ensure_ref_items(self.affected_record_refs, "PluginRegistryConflict.affected_record_refs")
        ensure_short_text(self.field_path, "PluginRegistryConflict.field_path", 256)
        ensure_bool(self.blocking, "PluginRegistryConflict.blocking")
        if self.severity in (PluginRegistryConflictSeverity.P0, PluginRegistryConflictSeverity.P1) and not self.blocking:
            raise ValueError("P0/P1 registry conflicts must be blocking")
        ensure_ref_items(self.evidence_refs, "PluginRegistryConflict.evidence_refs")
        ensure_ref_text(self.rule_source_ref, "PluginRegistryConflict.rule_source_ref")
        ensure_ref_text(self.detected_by_ref, "PluginRegistryConflict.detected_by_ref")
        ensure_ref_text(self.trace_ref, "PluginRegistryConflict.trace_ref", required=False)
        ensure_ref_text(self.responsibility_chain_ref, "PluginRegistryConflict.responsibility_chain_ref", required=False)
        ensure_schema_version(self.schema_version, "PluginRegistryConflict.schema_version")


@dataclass(frozen=True, slots=True)
class PluginRegistryConflictReport:
    report_ref: str
    conflicts: tuple[PluginRegistryConflict, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase3_registry"
    detected_by_ref: str = "detector:l5_phase3_registry_validator"
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    observed_summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.report_ref, "PluginRegistryConflictReport.report_ref")
        for conflict in self.conflicts:
            if not isinstance(conflict, PluginRegistryConflict):
                raise ValueError("PluginRegistryConflictReport.conflicts must contain PluginRegistryConflict")
        for name in ("rule_source_ref", "detected_by_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryConflictReport.{name}")
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryConflictReport.{name}", required=False)
        ensure_ref_items(self.provenance_refs, "PluginRegistryConflictReport.provenance_refs")
        ensure_ref_items(self.evidence_refs, "PluginRegistryConflictReport.evidence_refs")
        ensure_short_text(self.observed_summary, "PluginRegistryConflictReport.observed_summary")
        ensure_schema_version(self.schema_version, "PluginRegistryConflictReport.schema_version")

    @property
    def p0_count(self) -> int:
        return sum(1 for item in self.conflicts if item.severity is PluginRegistryConflictSeverity.P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for item in self.conflicts if item.severity is PluginRegistryConflictSeverity.P1)

    @property
    def p2_count(self) -> int:
        return sum(1 for item in self.conflicts if item.severity is PluginRegistryConflictSeverity.P2)

    @property
    def p3_count(self) -> int:
        return sum(1 for item in self.conflicts if item.severity is PluginRegistryConflictSeverity.P3)

    @property
    def passed(self) -> bool:
        return not any(item.blocking for item in self.conflicts)
