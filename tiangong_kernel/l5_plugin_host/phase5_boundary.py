"""L5 phase 5 boundary declaration shells.

This module is deliberately inert. It models isolation, dependency, credential,
data-governance, resource, capability-token, trust, and switch boundaries as
immutable declarations only. It does not load plugins, create sandboxes, install
packages, read credentials, access data, allocate resources, call lower-layer action surfaces,
write registries, or implement L6 business plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ._common import (
    L5_PLUGIN_HOST_SCHEMA_VERSION,
    ensure_bool,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    ensure_short_text,
    stable_digest,
    stable_primitive,
)
from .phase2_common import suspicious_credential_value_paths


PHASE5_PHASE = "L5_PHASE5"

_EXECUTION_METHOD_NAMES = frozenset(
    (
        "apply",
        "execute",
        "run",
        "start",
        "stop",
        "mount",
        "unmount",
        "enable",
        "disable",
        "isolate",
        "quarantine",
        "install",
        "import",
        "fetch_secret",
        "read_data",
        "allocate",
        "reserve",
        "commit",
        "mutate",
        "transition_to",
        "validate_and_apply",
        "auto_fix",
        "repair",
        "rollback",
        "hot_switch",
        "migrate",
        "replay",
        "recover",
        "patch",
    )
)

_LIVE_LOCATOR_FRAGMENTS = (
    "://",
    "file://",
    "http://",
    "https://",
    "ws://",
    "wss://",
    "postgres://",
    "mysql://",
    "mongodb://",
    "redis://",
    "module:function",
    "subprocess",
    "os.system",
    "Path.write_text",
    "Path.unlink",
    "shutil.rmtree",
    "$(",
    "`",
)

_LIVE_FIELD_NAMES = frozenset(
    (
        "sandbox_instance",
        "process_id",
        "thread_id",
        "container_id",
        "vm_id",
        "namespace_handle",
        "file_descriptor",
        "network_handle",
        "raw_value",
        "token_value",
        "secret_value",
        "api_key_value",
        "password_value",
        "decrypted_value",
        "env_value",
        "credential_file_path",
        "raw_data",
        "data_blob",
        "file_path",
        "database_uri",
        "table_name",
        "query_string",
        "user_identity_plaintext",
        "allocated_cpu",
        "allocated_memory",
        "live_quota",
        "live_limiter",
        "budget_account_object",
        "access_token",
        "refresh_token_value",
        "private_key",
        "signing_key",
    )
)

_UNBOUNDED_WORDS = ("unbounded", "infinite", "unlimited", "no_limit", "free_budget", "bypass_budget", "ignore_quota", "skip_metering")


class PluginPhase5ConflictSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    P3 = "p3"
    P2 = "p2"
    P1 = "p1"
    P0 = "p0"


class PluginPhase5ConflictKind(str, Enum):
    ISOLATION_MISSING_BOUNDARY_CONFLICT = "isolation_missing_boundary_conflict"
    ISOLATION_MISSING_SANDBOX_REQUIREMENT_CONFLICT = "isolation_missing_sandbox_requirement_conflict"
    ISOLATION_MISSING_SIDE_EFFECT_BOUNDARY_CONFLICT = "isolation_missing_side_effect_boundary_conflict"
    ISOLATION_MISSING_NO_LIVE_ACTION_CONFLICT = "isolation_missing_no_live_action_conflict"
    ISOLATION_MISSING_AUDIT_CONFLICT = "isolation_missing_audit_conflict"
    ISOLATION_MISSING_EVIDENCE_CONFLICT = "isolation_missing_evidence_conflict"
    ISOLATION_MISSING_POLICY_CONFLICT = "isolation_missing_policy_conflict"
    ISOLATION_LIVE_SANDBOX_EXECUTION_CONFLICT = "isolation_live_sandbox_execution_conflict"
    ISOLATION_LIVE_QUARANTINE_EXECUTION_CONFLICT = "isolation_live_quarantine_execution_conflict"
    ISOLATION_PUBLIC_PROJECTION_LEAK_CONFLICT = "isolation_public_projection_leak_conflict"
    DEPENDENCY_MISSING_DEPENDENCY_POLICY_CONFLICT = "dependency_missing_dependency_policy_conflict"
    DEPENDENCY_MISSING_VERSION_POLICY_CONFLICT = "dependency_missing_version_policy_conflict"
    DEPENDENCY_MISSING_COMPATIBILITY_DECL_CONFLICT = "dependency_missing_compatibility_decl_conflict"
    DEPENDENCY_MISSING_GRAPH_SNAPSHOT_CONFLICT = "dependency_missing_graph_snapshot_conflict"
    DEPENDENCY_CYCLE_DECLARED_CONFLICT = "dependency_cycle_declared_conflict"
    DEPENDENCY_INCOMPATIBLE_DECLARED_CONFLICT = "dependency_incompatible_declared_conflict"
    DEPENDENCY_MISSING_EVIDENCE_CONFLICT = "dependency_missing_evidence_conflict"
    DEPENDENCY_LIVE_INSTALL_CONFLICT = "dependency_live_install_conflict"
    DEPENDENCY_LIVE_IMPORT_CONFLICT = "dependency_live_import_conflict"
    DEPENDENCY_PUBLIC_PROJECTION_LEAK_CONFLICT = "dependency_public_projection_leak_conflict"
    DEPENDENCY_MISSING_VERSION_SLOT_CONFLICT = "dependency_missing_version_slot_conflict"
    DEPENDENCY_MISSING_ROLLBACK_ANCHOR_CONFLICT = "dependency_missing_rollback_anchor_conflict"
    DEPENDENCY_MISSING_TRANSITIVE_POLICY_CONFLICT = "dependency_missing_transitive_policy_conflict"
    DEPENDENCY_MISSING_COMPATIBILITY_MATRIX_CONFLICT = "dependency_missing_compatibility_matrix_conflict"
    DEPENDENCY_MISSING_OLD_EVENT_REPLAY_COMPATIBILITY_CONFLICT = "dependency_missing_old_event_replay_compatibility_conflict"
    DEPENDENCY_MISSING_UPCAST_POLICY_CONFLICT = "dependency_missing_upcast_policy_conflict"
    CREDENTIAL_MISSING_POLICY_CONFLICT = "credential_missing_policy_conflict"
    CREDENTIAL_MISSING_SCOPE_CONFLICT = "credential_missing_scope_conflict"
    CREDENTIAL_MISSING_REDACTION_POLICY_CONFLICT = "credential_missing_redaction_policy_conflict"
    CREDENTIAL_MISSING_APPROVAL_CONFLICT = "credential_missing_approval_conflict"
    CREDENTIAL_MISSING_LEASE_CONFLICT = "credential_missing_lease_conflict"
    CREDENTIAL_MISSING_AUDIT_CONFLICT = "credential_missing_audit_conflict"
    CREDENTIAL_MISSING_EVIDENCE_CONFLICT = "credential_missing_evidence_conflict"
    CREDENTIAL_PLAINTEXT_SECRET_CONFLICT = "credential_plaintext_secret_conflict"
    CREDENTIAL_LIVE_ACCESS_CONFLICT = "credential_live_access_conflict"
    CREDENTIAL_PUBLIC_PROJECTION_LEAK_CONFLICT = "credential_public_projection_leak_conflict"
    CREDENTIAL_MISSING_BINDING_CONFLICT = "credential_missing_binding_conflict"
    CREDENTIAL_MISSING_PURPOSE_CONFLICT = "credential_missing_purpose_conflict"
    CREDENTIAL_MISSING_REVOCATION_CONFLICT = "credential_missing_revocation_conflict"
    DATA_GOVERNANCE_MISSING_CATEGORY_CONFLICT = "data_governance_missing_category_conflict"
    DATA_GOVERNANCE_MISSING_PRIVACY_BOUNDARY_CONFLICT = "data_governance_missing_privacy_boundary_conflict"
    DATA_GOVERNANCE_MISSING_MINIMIZATION_CONFLICT = "data_governance_missing_minimization_conflict"
    DATA_GOVERNANCE_MISSING_RETENTION_POLICY_CONFLICT = "data_governance_missing_retention_policy_conflict"
    DATA_GOVERNANCE_MISSING_DELETION_POLICY_CONFLICT = "data_governance_missing_deletion_policy_conflict"
    DATA_GOVERNANCE_MISSING_LINEAGE_CONFLICT = "data_governance_missing_lineage_conflict"
    DATA_GOVERNANCE_MISSING_AUDIT_CONFLICT = "data_governance_missing_audit_conflict"
    DATA_GOVERNANCE_LIVE_DATA_ACCESS_CONFLICT = "data_governance_live_data_access_conflict"
    DATA_GOVERNANCE_LIVE_DATA_WRITE_CONFLICT = "data_governance_live_data_write_conflict"
    DATA_GOVERNANCE_PUBLIC_PROJECTION_LEAK_CONFLICT = "data_governance_public_projection_leak_conflict"
    DATA_GOVERNANCE_MISSING_CONSENT_CONFLICT = "data_governance_missing_consent_conflict"
    DATA_GOVERNANCE_MISSING_PURPOSE_CONFLICT = "data_governance_missing_purpose_conflict"
    DATA_GOVERNANCE_MISSING_LIFECYCLE_CONFLICT = "data_governance_missing_lifecycle_conflict"
    DATA_GOVERNANCE_MISSING_EXTERNAL_DISCLOSURE_BOUNDARY_CONFLICT = "data_governance_missing_external_disclosure_boundary_conflict"
    RESOURCE_MISSING_QUOTA_POLICY_CONFLICT = "resource_missing_quota_policy_conflict"
    RESOURCE_MISSING_RATE_LIMIT_POLICY_CONFLICT = "resource_missing_rate_limit_policy_conflict"
    RESOURCE_MISSING_BUDGET_LEDGER_CONFLICT = "resource_missing_budget_ledger_conflict"
    RESOURCE_MISSING_COST_POLICY_CONFLICT = "resource_missing_cost_policy_conflict"
    RESOURCE_MISSING_AUDIT_CONFLICT = "resource_missing_audit_conflict"
    RESOURCE_MISSING_EVIDENCE_CONFLICT = "resource_missing_evidence_conflict"
    RESOURCE_LIVE_ALLOCATION_CONFLICT = "resource_live_allocation_conflict"
    RESOURCE_LIVE_BUDGET_DECREMENT_CONFLICT = "resource_live_budget_decrement_conflict"
    RESOURCE_LIVE_LIMITER_CONFLICT = "resource_live_limiter_conflict"
    RESOURCE_PUBLIC_PROJECTION_LEAK_CONFLICT = "resource_public_projection_leak_conflict"
    RESOURCE_PHASE2_DECL_MISSING_CONFLICT = "resource_phase2_decl_missing_conflict"
    RESOURCE_PHASE2_PHASE5_MISMATCH_CONFLICT = "resource_phase2_phase5_mismatch_conflict"
    RESOURCE_DECL_DIGEST_MISMATCH_CONFLICT = "resource_decl_digest_mismatch_conflict"
    RESOURCE_DECL_SCHEMA_VERSION_MISMATCH_CONFLICT = "resource_decl_schema_version_mismatch_conflict"
    RESOURCE_BOUNDARY_COMPLETION_WITHOUT_EVIDENCE_CONFLICT = "resource_boundary_completion_without_evidence_conflict"
    RESOURCE_MISSING_BUDGET_OWNER_CONFLICT = "resource_missing_budget_owner_conflict"
    RESOURCE_MISSING_RUN_BUDGET_SCOPE_CONFLICT = "resource_missing_run_budget_scope_conflict"
    RESOURCE_MISSING_GOAL_BUDGET_SCOPE_CONFLICT = "resource_missing_goal_budget_scope_conflict"
    RESOURCE_MISSING_ACTOR_BUDGET_SCOPE_CONFLICT = "resource_missing_actor_budget_scope_conflict"
    RESOURCE_MISSING_METERING_POLICY_CONFLICT = "resource_missing_metering_policy_conflict"
    RESOURCE_MISSING_RESOURCE_PRESSURE_POLICY_CONFLICT = "resource_missing_resource_pressure_policy_conflict"
    RESOURCE_MISSING_DEGRADATION_POLICY_CONFLICT = "resource_missing_degradation_policy_conflict"
    RESOURCE_MISSING_EXHAUSTION_BEHAVIOR_CONFLICT = "resource_missing_exhaustion_behavior_conflict"
    RESOURCE_UNBOUNDED_BUDGET_DECLARED_CONFLICT = "resource_unbounded_budget_declared_conflict"
    RESOURCE_HIGH_PERMISSION_BYPASSES_BUDGET_CONFLICT = "resource_high_permission_bypasses_budget_conflict"
    RESOURCE_HIGH_PERMISSION_BYPASSES_QUOTA_CONFLICT = "resource_high_permission_bypasses_quota_conflict"
    RESOURCE_HIGH_PERMISSION_BYPASSES_RATE_LIMIT_CONFLICT = "resource_high_permission_bypasses_rate_limit_conflict"
    RESOURCE_HIGH_PERMISSION_BYPASSES_COST_RECORD_CONFLICT = "resource_high_permission_bypasses_cost_record_conflict"
    RESOURCE_PHASE2_PHASE5_CONSISTENCY_CONFLICT = "resource_phase2_phase5_consistency_conflict"
    RESOURCE_BOUNDARY_DIGEST_UNSTABLE_CONFLICT = "resource_boundary_digest_unstable_conflict"
    RESOURCE_MISSING_SWITCH_BUDGET_FREEZE_CONFLICT = "resource_missing_switch_budget_freeze_conflict"
    RESOURCE_MISSING_ROLLBACK_BUDGET_GUARD_CONFLICT = "resource_missing_rollback_budget_guard_conflict"
    RESOURCE_MISSING_MIGRATION_RESOURCE_DELTA_CONFLICT = "resource_missing_migration_resource_delta_conflict"
    CAPABILITY_TOKEN_MISSING_BOUNDARY_CONFLICT = "capability_token_missing_boundary_conflict"
    CAPABILITY_TOKEN_MISSING_SCOPE_CONFLICT = "capability_token_missing_scope_conflict"
    CAPABILITY_TOKEN_MISSING_LEASE_CONFLICT = "capability_token_missing_lease_conflict"
    CAPABILITY_TOKEN_MISSING_EXPIRY_CONFLICT = "capability_token_missing_expiry_conflict"
    CAPABILITY_TOKEN_MISSING_REVOCATION_CONFLICT = "capability_token_missing_revocation_conflict"
    CAPABILITY_TOKEN_MISSING_AUDIT_CONFLICT = "capability_token_missing_audit_conflict"
    CAPABILITY_TOKEN_LIVE_ISSUANCE_CONFLICT = "capability_token_live_issuance_conflict"
    CAPABILITY_TOKEN_LIVE_VALIDATION_CONFLICT = "capability_token_live_validation_conflict"
    CAPABILITY_TOKEN_PLAINTEXT_TOKEN_CONFLICT = "capability_token_plaintext_token_conflict"
    CAPABILITY_TOKEN_USED_AS_PERMISSION_GRANT_CONFLICT = "capability_token_used_as_permission_grant_conflict"
    TRUST_BOUNDARY_MISSING_HOST_BOUNDARY_CONFLICT = "trust_boundary_missing_host_boundary_conflict"
    TRUST_BOUNDARY_MISSING_PLUGIN_BOUNDARY_CONFLICT = "trust_boundary_missing_plugin_boundary_conflict"
    TRUST_BOUNDARY_MISSING_DATA_BOUNDARY_CONFLICT = "trust_boundary_missing_data_boundary_conflict"
    TRUST_BOUNDARY_MISSING_CREDENTIAL_BOUNDARY_CONFLICT = "trust_boundary_missing_credential_boundary_conflict"
    TRUST_BOUNDARY_MISSING_NETWORK_BOUNDARY_CONFLICT = "trust_boundary_missing_network_boundary_conflict"
    TRUST_BOUNDARY_MISSING_TOOL_BOUNDARY_CONFLICT = "trust_boundary_missing_tool_boundary_conflict"
    TRUST_BOUNDARY_MISSING_EXTERNAL_DISCLOSURE_BOUNDARY_CONFLICT = "trust_boundary_missing_external_disclosure_boundary_conflict"
    TRUST_BOUNDARY_USED_AS_LIVE_SANDBOX_CONFLICT = "trust_boundary_used_as_live_sandbox_conflict"
    TRUST_BOUNDARY_USED_AS_PERMISSION_GRANT_CONFLICT = "trust_boundary_used_as_permission_grant_conflict"
    TRUST_BOUNDARY_PUBLIC_PROJECTION_LEAK_CONFLICT = "trust_boundary_public_projection_leak_conflict"
    SWITCH_BOUNDARY_MISSING_HOT_SWITCH_REF_CONFLICT = "switch_boundary_missing_hot_switch_ref_conflict"
    SWITCH_BOUNDARY_MISSING_READINESS_REF_CONFLICT = "switch_boundary_missing_readiness_ref_conflict"
    SWITCH_BOUNDARY_MISSING_CHECKPOINT_REF_CONFLICT = "switch_boundary_missing_checkpoint_ref_conflict"
    SWITCH_BOUNDARY_MISSING_OBSERVATION_REF_CONFLICT = "switch_boundary_missing_observation_ref_conflict"
    SWITCH_BOUNDARY_MISSING_ROLLBACK_ROUTE_REF_CONFLICT = "switch_boundary_missing_rollback_route_ref_conflict"
    SWITCH_BOUNDARY_MISSING_ISOLATION_BOUNDARY_CONFLICT = "switch_boundary_missing_isolation_boundary_conflict"
    SWITCH_BOUNDARY_MISSING_DEPENDENCY_BOUNDARY_CONFLICT = "switch_boundary_missing_dependency_boundary_conflict"
    SWITCH_BOUNDARY_MISSING_CREDENTIAL_BOUNDARY_CONFLICT = "switch_boundary_missing_credential_boundary_conflict"
    SWITCH_BOUNDARY_MISSING_DATA_BOUNDARY_CONFLICT = "switch_boundary_missing_data_boundary_conflict"
    SWITCH_BOUNDARY_MISSING_RESOURCE_BOUNDARY_CONFLICT = "switch_boundary_missing_resource_boundary_conflict"
    PHASE5_SWITCH_BOUNDARY_USED_AS_LIVE_SWITCH_CONFLICT = "phase5_switch_boundary_used_as_live_switch_conflict"
    PHASE4_MOUNT_USED_AS_LIVE_MOUNT_CONFLICT = "phase4_mount_used_as_live_mount_conflict"
    PHASE4_LIFECYCLE_USED_AS_RUNTIME_STATE_CONFLICT = "phase4_lifecycle_used_as_runtime_state_conflict"
    PHASE3_REGISTRY_USED_AS_RUNTIME_REGISTRY_CONFLICT = "phase3_registry_used_as_runtime_registry_conflict"
    PHASE3_DELTA_USED_AS_EXECUTABLE_PATCH_CONFLICT = "phase3_delta_used_as_executable_patch_conflict"
    PHASE5_BOUNDARY_USED_AS_PERMISSION_GRANT_CONFLICT = "phase5_boundary_used_as_permission_grant_conflict"
    PHASE5_CREDENTIAL_USED_AS_SECRET_ACCESS_CONFLICT = "phase5_credential_used_as_secret_access_conflict"
    PHASE5_RESOURCE_USED_AS_LIVE_QUOTA_CONFLICT = "phase5_resource_used_as_live_quota_conflict"
    PHASE5_DATA_POLICY_USED_AS_DATA_ACCESS_CONFLICT = "phase5_data_policy_used_as_data_access_conflict"
    PUBLIC_PROJECTION_LEAK_CONFLICT = "public_projection_leak_conflict"
    FORBIDDEN_LIVE_EXECUTION_CONFLICT = "forbidden_live_execution_conflict"
    AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT = "audit_evidence_chain_missing_conflict"


@dataclass(frozen=True, slots=True)
class PluginPhase5Conflict:
    conflict_ref: str
    kind: PluginPhase5ConflictKind
    severity: PluginPhase5ConflictSeverity
    message: str
    field_path: str = ""
    blocking: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase5_boundary"
    detected_by_ref: str = "detector:l5_phase5_boundary_validator"

    def __post_init__(self) -> None:
        ensure_ref_text(self.conflict_ref, "PluginPhase5Conflict.conflict_ref")
        if not isinstance(self.kind, PluginPhase5ConflictKind):
            raise ValueError("PluginPhase5Conflict.kind must be PluginPhase5ConflictKind")
        if not isinstance(self.severity, PluginPhase5ConflictSeverity):
            raise ValueError("PluginPhase5Conflict.severity must be PluginPhase5ConflictSeverity")
        ensure_short_text(self.message, "PluginPhase5Conflict.message")
        ensure_short_text(self.field_path, "PluginPhase5Conflict.field_path", 256)
        ensure_bool(self.blocking, "PluginPhase5Conflict.blocking")
        ensure_ref_items(self.evidence_refs, "PluginPhase5Conflict.evidence_refs")
        ensure_ref_text(self.rule_source_ref, "PluginPhase5Conflict.rule_source_ref")
        ensure_ref_text(self.detected_by_ref, "PluginPhase5Conflict.detected_by_ref")
        if self.severity in (PluginPhase5ConflictSeverity.P0, PluginPhase5ConflictSeverity.P1) and not self.blocking:
            raise ValueError("P0/P1 phase5 conflicts must be blocking")


def _tuple(value: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, tuple):
        return tuple(value)
    if isinstance(value, list):
        return tuple(value)
    raise ValueError("expected tuple/list declaration refs")


def _stable_tuple(items: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(sorted(items, key=lambda item: stable_digest(item)))


def _digest_dataclass(obj: Any, digest_fields: tuple[str, ...] = tuple()) -> str:
    primitive = stable_primitive(obj)
    if isinstance(primitive, dict):
        for field_name in digest_fields:
            primitive.pop(field_name, None)
    return stable_digest(primitive)


def _has_ref(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_refs(values: tuple[str, ...]) -> bool:
    return isinstance(values, tuple) and len(values) > 0 and all(isinstance(item, str) and bool(item.strip()) for item in values)


def _check_ref_tuple(values: tuple[str, ...], field_name: str) -> None:
    ensure_ref_items(values, field_name)


def _text_is_live_locator(text: str) -> bool:
    if not isinstance(text, str):
        return False
    stripped = text.strip()
    lowered = stripped.lower()
    if any(fragment.lower() in lowered for fragment in _LIVE_LOCATOR_FRAGMENTS):
        return True
    if stripped.startswith(("/", "./", "../", "~", "C:\\", "D:\\")):
        return True
    if stripped.endswith((".py", ".sh", ".bat", ".exe", ".dll", ".so")):
        return True
    if "/" in stripped or "\\" in stripped:
        return True
    if stripped.count(".") >= 2 and ":" in stripped:
        return True
    return False


def _walk_values(value: Any) -> tuple[str, ...]:
    primitive = stable_primitive(value)
    hits: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            hits.append(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)

    walk(primitive)
    return tuple(hits)


def has_live_locator(value: Any) -> bool:
    return any(_text_is_live_locator(item) for item in _walk_values(value))


def has_unbounded_resource_text(value: Any) -> bool:
    return any(any(word in item.lower() for word in _UNBOUNDED_WORDS) for item in _walk_values(value))


def has_forbidden_phase5_method(obj: Any) -> bool:
    return any(callable(getattr(obj, name, None)) for name in _EXECUTION_METHOD_NAMES)


def has_forbidden_phase5_field_name(obj: Any) -> bool:
    if hasattr(obj, "__dataclass_fields__"):
        return any(name in _LIVE_FIELD_NAMES for name in obj.__dataclass_fields__)
    return False


def public_text_is_safe(value: Any) -> bool:
    if has_live_locator(value):
        return False
    if suspicious_credential_value_paths(value):
        return False
    lowered = "\n".join(_walk_values(value)).lower()
    forbidden = (
        "raw_value",
        "token_value",
        "secret_value",
        "api_key_value",
        "password_value",
        "decrypted_value",
        "env_value",
        "database_uri",
        "shell command",
        "module:function",
    )
    return not any(item in lowered for item in forbidden)


@dataclass(frozen=True, slots=True)
class _Phase5Base:
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    source_layer: str = "L5_PHASE5"
    severity: str = "p3"
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    least_privilege_declared: bool = True
    deny_by_default_declared: bool = True
    declaration_not_authorization_ref: str = "decl:not_authorization"
    permission_grant_prohibited_ref: str = "prohibit:permission_grant"
    live_action_prohibited_ref: str = "prohibit:live_action"

    def _check_base(self, class_name: str) -> None:
        for name in ("actor_ref", "scope_ref", "trace_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref", "source_layer"):
            ensure_ref_text(getattr(self, name), f"{class_name}.{name}", required=False)
        for name in ("evidence_refs", "provenance_refs", "risk_tags"):
            ensure_ref_items(getattr(self, name), f"{class_name}.{name}")
        for name in ("least_privilege_declared", "deny_by_default_declared"):
            ensure_bool(getattr(self, name), f"{class_name}.{name}")
        for name in ("declaration_not_authorization_ref", "permission_grant_prohibited_ref", "live_action_prohibited_ref"):
            ensure_ref_text(getattr(self, name), f"{class_name}.{name}", required=False)
        ensure_short_text(self.severity, f"{class_name}.severity", 32)


@dataclass(frozen=True, slots=True)
class PluginIsolationDeclaration(_Phase5Base):
    isolation_decl_ref: str = ""
    registry_key_ref: str = ""
    lifecycle_ref: str = ""
    mount_decl_ref: str = ""
    isolation_boundary_ref: str = ""
    sandbox_requirement_ref: str = ""
    containment_ref: str = ""
    quarantine_policy_ref: str = ""
    side_effect_boundary_ref: str = ""
    no_live_action_ref: str = ""
    forbidden_action_refs: tuple[str, ...] = field(default_factory=tuple)
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_permission_refs: tuple[str, ...] = field(default_factory=tuple)
    required_lease_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    audit_decl_ref: str = ""
    isolation_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginIsolationDeclaration")
        for name in ("isolation_decl_ref", "registry_key_ref", "lifecycle_ref", "mount_decl_ref"):
            ensure_ref_text(getattr(self, name), f"PluginIsolationDeclaration.{name}", required=False)
        for name in ("isolation_boundary_ref", "sandbox_requirement_ref", "containment_ref", "quarantine_policy_ref", "side_effect_boundary_ref", "no_live_action_ref", "required_approval_ref", "audit_decl_ref"):
            ensure_ref_text(getattr(self, name), f"PluginIsolationDeclaration.{name}", required=False)
        for name in ("forbidden_action_refs", "required_policy_refs", "required_permission_refs", "required_lease_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginIsolationDeclaration.{name}")
        if not self.isolation_digest:
            object.__setattr__(self, "isolation_digest", _digest_dataclass(self, ("isolation_digest",)))


@dataclass(frozen=True, slots=True)
class PluginDependencyDeclaration(_Phase5Base):
    dependency_decl_ref: str = ""
    registry_key_ref: str = ""
    dependency_refs: tuple[str, ...] = field(default_factory=tuple)
    optional_dependency_refs: tuple[str, ...] = field(default_factory=tuple)
    incompatible_dependency_refs: tuple[str, ...] = field(default_factory=tuple)
    dependency_policy_ref: str = ""
    version_policy_ref: str = ""
    compatibility_decl_ref: str = ""
    migration_ref: str = ""
    breaking_change_policy_ref: str = ""
    dependency_graph_ref: str = ""
    dependency_snapshot_ref: str = ""
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_decl_ref: str = ""
    version_slot_ref: str = ""
    rollback_anchor_ref: str = ""
    transitive_dependency_policy_ref: str = ""
    dependency_compatibility_matrix_ref: str = ""
    old_event_replay_compatibility_ref: str = ""
    upcast_policy_ref: str = ""
    deprecation_policy_ref: str = ""
    minimum_migration_ref: str = ""
    dependency_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginDependencyDeclaration")
        for name in ("dependency_decl_ref", "registry_key_ref", "dependency_policy_ref", "version_policy_ref", "compatibility_decl_ref", "migration_ref", "breaking_change_policy_ref", "dependency_graph_ref", "dependency_snapshot_ref", "audit_decl_ref", "version_slot_ref", "rollback_anchor_ref", "transitive_dependency_policy_ref", "dependency_compatibility_matrix_ref", "old_event_replay_compatibility_ref", "upcast_policy_ref", "deprecation_policy_ref", "minimum_migration_ref"):
            ensure_ref_text(getattr(self, name), f"PluginDependencyDeclaration.{name}", required=False)
        for name in ("dependency_refs", "optional_dependency_refs", "incompatible_dependency_refs", "required_policy_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginDependencyDeclaration.{name}")
        if not self.dependency_digest:
            object.__setattr__(self, "dependency_digest", _digest_dataclass(self, ("dependency_digest",)))


@dataclass(frozen=True, slots=True)
class PluginDependencyGraphSnapshot:
    dependency_graph_snapshot_ref: str
    registry_key_refs: tuple[str, ...] = field(default_factory=tuple)
    node_refs: tuple[str, ...] = field(default_factory=tuple)
    edge_refs: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)
    cycle_conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    incompatible_conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    missing_dependency_conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = ""
    tamper_evidence_ref: str = ""
    graph_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.dependency_graph_snapshot_ref, "PluginDependencyGraphSnapshot.dependency_graph_snapshot_ref")
        for name in ("registry_key_refs", "node_refs", "cycle_conflict_refs", "incompatible_conflict_refs", "missing_dependency_conflict_refs", "evidence_refs", "provenance_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginDependencyGraphSnapshot.{name}")
        normalized_edges = tuple(sorted((str(a), str(b), str(c)) for a, b, c in self.edge_refs))
        object.__setattr__(self, "edge_refs", normalized_edges)
        for name in ("trace_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginDependencyGraphSnapshot.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginDependencyGraphSnapshot.schema_version")
        if not self.graph_digest:
            object.__setattr__(self, "graph_digest", _digest_dataclass(self, ("graph_digest",)))


@dataclass(frozen=True, slots=True)
class PluginCredentialRequirementDeclaration(_Phase5Base):
    credential_decl_ref: str = ""
    registry_key_ref: str = ""
    credential_kind_ref: str = ""
    credential_policy_ref: str = ""
    credential_scope_ref: str = ""
    redaction_policy_ref: str = ""
    approval_ref: str = ""
    lease_ref: str = ""
    audit_decl_ref: str = ""
    data_boundary_ref: str = ""
    storage_boundary_ref: str = ""
    forbidden_plaintext_ref: str = ""
    credential_handle_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_binding_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_purpose_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_audience_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_revocation_ref: str = ""
    credential_lease_ref: str = ""
    value_absent_required: bool = True
    redacted_required: bool = True
    no_credential_acquisition_ref: str = "no_credential_acquisition:declared"
    no_credential_resolution_ref: str = "no_credential_resolution:declared"
    credential_rotation_boundary_ref: str = ""
    migration_credential_policy_ref: str = ""
    replay_credential_policy_ref: str = ""
    old_credential_redaction_policy_ref: str = ""
    credential_rebinding_prohibition_ref: str = ""
    credential_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginCredentialRequirementDeclaration")
        for name in ("credential_decl_ref", "registry_key_ref", "credential_kind_ref", "credential_policy_ref", "credential_scope_ref", "redaction_policy_ref", "approval_ref", "lease_ref", "audit_decl_ref", "data_boundary_ref", "storage_boundary_ref", "forbidden_plaintext_ref", "credential_revocation_ref", "credential_lease_ref", "no_credential_acquisition_ref", "no_credential_resolution_ref", "credential_rotation_boundary_ref", "migration_credential_policy_ref", "replay_credential_policy_ref", "old_credential_redaction_policy_ref", "credential_rebinding_prohibition_ref"):
            ensure_ref_text(getattr(self, name), f"PluginCredentialRequirementDeclaration.{name}", required=False)
        for name in ("credential_handle_refs", "credential_binding_refs", "credential_purpose_refs", "credential_audience_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginCredentialRequirementDeclaration.{name}")
        ensure_bool(self.value_absent_required, "PluginCredentialRequirementDeclaration.value_absent_required")
        ensure_bool(self.redacted_required, "PluginCredentialRequirementDeclaration.redacted_required")
        if not self.credential_digest:
            object.__setattr__(self, "credential_digest", _digest_dataclass(self, ("credential_digest",)))


@dataclass(frozen=True, slots=True)
class PluginDataGovernanceDeclaration(_Phase5Base):
    data_governance_decl_ref: str = ""
    registry_key_ref: str = ""
    data_category_refs: tuple[str, ...] = field(default_factory=tuple)
    privacy_boundary_ref: str = ""
    data_minimization_ref: str = ""
    retention_policy_ref: str = ""
    deletion_policy_ref: str = ""
    lineage_ref: str = ""
    data_access_policy_ref: str = ""
    storage_policy_ref: str = ""
    export_policy_ref: str = ""
    redaction_policy_ref: str = ""
    audit_decl_ref: str = ""
    consent_refs: tuple[str, ...] = field(default_factory=tuple)
    purpose_refs: tuple[str, ...] = field(default_factory=tuple)
    data_lifecycle_refs: tuple[str, ...] = field(default_factory=tuple)
    data_subject_category_refs: tuple[str, ...] = field(default_factory=tuple)
    processing_basis_refs: tuple[str, ...] = field(default_factory=tuple)
    cross_boundary_transfer_refs: tuple[str, ...] = field(default_factory=tuple)
    external_disclosure_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    minimization_policy_ref: str = ""
    migration_data_boundary_ref: str = ""
    replay_data_minimization_ref: str = ""
    old_event_redaction_policy_ref: str = ""
    schema_upcast_data_policy_ref: str = ""
    rollback_data_boundary_ref: str = ""
    checkpoint_data_policy_ref: str = ""
    observation_data_policy_ref: str = ""
    data_governance_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginDataGovernanceDeclaration")
        for name in ("data_governance_decl_ref", "registry_key_ref", "privacy_boundary_ref", "data_minimization_ref", "retention_policy_ref", "deletion_policy_ref", "lineage_ref", "data_access_policy_ref", "storage_policy_ref", "export_policy_ref", "redaction_policy_ref", "audit_decl_ref", "minimization_policy_ref", "migration_data_boundary_ref", "replay_data_minimization_ref", "old_event_redaction_policy_ref", "schema_upcast_data_policy_ref", "rollback_data_boundary_ref", "checkpoint_data_policy_ref", "observation_data_policy_ref"):
            ensure_ref_text(getattr(self, name), f"PluginDataGovernanceDeclaration.{name}", required=False)
        for name in ("data_category_refs", "consent_refs", "purpose_refs", "data_lifecycle_refs", "data_subject_category_refs", "processing_basis_refs", "cross_boundary_transfer_refs", "external_disclosure_boundary_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginDataGovernanceDeclaration.{name}")
        if not self.data_governance_digest:
            object.__setattr__(self, "data_governance_digest", _digest_dataclass(self, ("data_governance_digest",)))


@dataclass(frozen=True, slots=True)
class PluginResourceBoundaryDeclaration(_Phase5Base):
    resource_boundary_decl_ref: str = ""
    registry_key_ref: str = ""
    cpu_budget_ref: str = ""
    memory_budget_ref: str = ""
    storage_budget_ref: str = ""
    network_budget_ref: str = ""
    token_budget_ref: str = ""
    tool_budget_ref: str = ""
    rate_limit_policy_ref: str = ""
    quota_policy_ref: str = ""
    burst_policy_ref: str = ""
    cost_policy_ref: str = ""
    budget_ledger_ref: str = ""
    audit_decl_ref: str = ""
    manifest_resource_decl_ref: str = ""
    phase2_resource_decl_ref: str = ""
    resource_decl_digest_ref: str = ""
    resource_decl_schema_version_ref: str = ""
    run_budget_scope_ref: str = ""
    goal_budget_scope_ref: str = ""
    actor_budget_scope_ref: str = ""
    budget_owner_ref: str = ""
    quota_scope_ref: str = ""
    concurrency_budget_ref: str = ""
    io_budget_ref: str = ""
    model_call_budget_ref: str = ""
    external_call_budget_ref: str = ""
    metering_policy_ref: str = ""
    resource_pressure_policy_ref: str = ""
    degradation_policy_ref: str = ""
    exhaustion_behavior_ref: str = ""
    high_permission_budget_policy_ref: str = ""
    budget_expansion_policy_ref: str = ""
    switch_budget_freeze_ref: str = ""
    rollback_budget_guard_ref: str = ""
    migration_resource_delta_ref: str = ""
    replay_resource_guard_ref: str = ""
    checkpoint_resource_policy_ref: str = ""
    observation_resource_policy_ref: str = ""
    resource_boundary_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginResourceBoundaryDeclaration")
        for name in (
            "resource_boundary_decl_ref", "registry_key_ref", "cpu_budget_ref", "memory_budget_ref", "storage_budget_ref", "network_budget_ref", "token_budget_ref", "tool_budget_ref", "rate_limit_policy_ref", "quota_policy_ref", "burst_policy_ref", "cost_policy_ref", "budget_ledger_ref", "audit_decl_ref", "manifest_resource_decl_ref", "phase2_resource_decl_ref", "resource_decl_digest_ref", "resource_decl_schema_version_ref", "run_budget_scope_ref", "goal_budget_scope_ref", "actor_budget_scope_ref", "budget_owner_ref", "quota_scope_ref", "concurrency_budget_ref", "io_budget_ref", "model_call_budget_ref", "external_call_budget_ref", "metering_policy_ref", "resource_pressure_policy_ref", "degradation_policy_ref", "exhaustion_behavior_ref", "high_permission_budget_policy_ref", "budget_expansion_policy_ref", "switch_budget_freeze_ref", "rollback_budget_guard_ref", "migration_resource_delta_ref", "replay_resource_guard_ref", "checkpoint_resource_policy_ref", "observation_resource_policy_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginResourceBoundaryDeclaration.{name}", required=False)
        if not self.resource_boundary_digest:
            object.__setattr__(self, "resource_boundary_digest", _digest_dataclass(self, ("resource_boundary_digest",)))


@dataclass(frozen=True, slots=True)
class PluginCapabilityTokenBoundaryDeclaration(_Phase5Base):
    capability_token_boundary_decl_ref: str = ""
    registry_key_ref: str = ""
    capability_token_decl_ref: str = ""
    token_scope_refs: tuple[str, ...] = field(default_factory=tuple)
    token_lease_ref: str = ""
    token_expiry_ref: str = ""
    token_revocation_ref: str = ""
    delegation_policy_ref: str = ""
    audience_ref: str = ""
    issuer_ref: str = ""
    subject_ref: str = ""
    no_token_issuance_ref: str = "no_token_issuance:declared"
    no_token_refresh_ref: str = "no_token_refresh:declared"
    no_token_revocation_execution_ref: str = "no_token_revocation_execution:declared"
    no_token_validation_execution_ref: str = "no_token_validation_execution:declared"
    audit_decl_ref: str = ""
    policy_ref: str = ""
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    capability_token_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginCapabilityTokenBoundaryDeclaration")
        for name in ("capability_token_boundary_decl_ref", "registry_key_ref", "capability_token_decl_ref", "token_lease_ref", "token_expiry_ref", "token_revocation_ref", "delegation_policy_ref", "audience_ref", "issuer_ref", "subject_ref", "no_token_issuance_ref", "no_token_refresh_ref", "no_token_revocation_execution_ref", "no_token_validation_execution_ref", "audit_decl_ref", "policy_ref"):
            ensure_ref_text(getattr(self, name), f"PluginCapabilityTokenBoundaryDeclaration.{name}", required=False)
        for name in ("token_scope_refs", "policy_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginCapabilityTokenBoundaryDeclaration.{name}")
        if not self.capability_token_digest:
            object.__setattr__(self, "capability_token_digest", _digest_dataclass(self, ("capability_token_digest",)))


@dataclass(frozen=True, slots=True)
class PluginTrustBoundaryDeclaration(_Phase5Base):
    trust_boundary_decl_ref: str = ""
    registry_key_ref: str = ""
    host_boundary_ref: str = ""
    plugin_boundary_ref: str = ""
    data_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    resource_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    network_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    external_disclosure_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    recovery_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    lifecycle_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    mount_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_ref: str = ""
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    trust_boundary_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginTrustBoundaryDeclaration")
        for name in ("trust_boundary_decl_ref", "registry_key_ref", "host_boundary_ref", "plugin_boundary_ref", "policy_ref"):
            ensure_ref_text(getattr(self, name), f"PluginTrustBoundaryDeclaration.{name}", required=False)
        for name in ("data_boundary_refs", "credential_boundary_refs", "resource_boundary_refs", "network_boundary_refs", "tool_boundary_refs", "external_disclosure_boundary_refs", "audit_boundary_refs", "recovery_boundary_refs", "lifecycle_boundary_refs", "mount_boundary_refs", "policy_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginTrustBoundaryDeclaration.{name}")
        if not self.trust_boundary_digest:
            object.__setattr__(self, "trust_boundary_digest", _digest_dataclass(self, ("trust_boundary_digest",)))


@dataclass(frozen=True, slots=True)
class PluginPhase5SwitchBoundaryDeclaration(_Phase5Base):
    switch_boundary_decl_ref: str = ""
    registry_key_ref: str = ""
    lifecycle_ref: str = ""
    mount_decl_ref: str = ""
    hot_switch_decl_ref: str = ""
    switch_readiness_ref: str = ""
    pre_switch_checkpoint_ref: str = ""
    post_switch_observation_ref: str = ""
    switch_rollback_route_ref: str = ""
    migration_ref: str = ""
    replay_compatibility_ref: str = ""
    breaking_change_policy_ref: str = ""
    isolation_boundary_ref: str = ""
    dependency_decl_ref: str = ""
    credential_boundary_ref: str = ""
    data_governance_boundary_ref: str = ""
    resource_boundary_ref: str = ""
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    audit_decl_ref: str = ""
    switch_boundary_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginPhase5SwitchBoundaryDeclaration")
        for name in (
            "switch_boundary_decl_ref", "registry_key_ref", "lifecycle_ref", "mount_decl_ref", "hot_switch_decl_ref", "switch_readiness_ref", "pre_switch_checkpoint_ref", "post_switch_observation_ref", "switch_rollback_route_ref", "migration_ref", "replay_compatibility_ref", "breaking_change_policy_ref", "isolation_boundary_ref", "dependency_decl_ref", "credential_boundary_ref", "data_governance_boundary_ref", "resource_boundary_ref", "required_approval_ref", "audit_decl_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginPhase5SwitchBoundaryDeclaration.{name}", required=False)
        _check_ref_tuple(self.required_policy_refs, "PluginPhase5SwitchBoundaryDeclaration.required_policy_refs")
        if not self.switch_boundary_digest:
            object.__setattr__(self, "switch_boundary_digest", _digest_dataclass(self, ("switch_boundary_digest",)))


@dataclass(frozen=True, slots=True)
class PluginPhase5BoundaryValidationReport:
    report_ref: str
    checked_isolation_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_dependency_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_credential_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_data_governance_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_resource_boundary_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_capability_token_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_trust_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_switch_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    conflicts: tuple[PluginPhase5Conflict, ...] = field(default_factory=tuple)
    phase: str = PHASE5_PHASE
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    passed: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase5_boundary"
    detected_by_ref: str = "detector:l5_phase5_boundary_validator"
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    report_digest: str = ""

    def __post_init__(self) -> None:
        ensure_ref_text(self.report_ref, "PluginPhase5BoundaryValidationReport.report_ref")
        for item in self.conflicts:
            if not isinstance(item, PluginPhase5Conflict):
                raise ValueError("conflicts must contain PluginPhase5Conflict")
        counts = {
            PluginPhase5ConflictSeverity.P0: sum(1 for item in self.conflicts if item.severity is PluginPhase5ConflictSeverity.P0),
            PluginPhase5ConflictSeverity.P1: sum(1 for item in self.conflicts if item.severity is PluginPhase5ConflictSeverity.P1),
            PluginPhase5ConflictSeverity.P2: sum(1 for item in self.conflicts if item.severity is PluginPhase5ConflictSeverity.P2),
            PluginPhase5ConflictSeverity.P3: sum(1 for item in self.conflicts if item.severity is PluginPhase5ConflictSeverity.P3),
        }
        object.__setattr__(self, "p0_count", counts[PluginPhase5ConflictSeverity.P0])
        object.__setattr__(self, "p1_count", counts[PluginPhase5ConflictSeverity.P1])
        object.__setattr__(self, "p2_count", counts[PluginPhase5ConflictSeverity.P2])
        object.__setattr__(self, "p3_count", counts[PluginPhase5ConflictSeverity.P3])
        object.__setattr__(self, "passed", counts[PluginPhase5ConflictSeverity.P0] == 0 and counts[PluginPhase5ConflictSeverity.P1] == 0)
        if not self.blocking_reasons:
            object.__setattr__(self, "blocking_reasons", tuple(item.message for item in self.conflicts if item.blocking))
        for name in ("checked_isolation_decl_refs", "checked_dependency_decl_refs", "checked_credential_decl_refs", "checked_data_governance_decl_refs", "checked_resource_boundary_decl_refs", "checked_capability_token_boundary_refs", "checked_trust_boundary_refs", "checked_switch_boundary_refs", "blocking_reasons", "evidence_refs", "provenance_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginPhase5BoundaryValidationReport.{name}")
        for name in ("rule_source_ref", "detected_by_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginPhase5BoundaryValidationReport.{name}", required=False if name not in ("rule_source_ref", "detected_by_ref") else True)
        if not self.report_digest:
            object.__setattr__(self, "report_digest", _digest_dataclass(self, ("report_digest",)))


@dataclass(frozen=True, slots=True)
class PluginPhase5QualityGateDecision:
    decision_ref: str
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    isolation_declaration_passed: bool = False
    dependency_declaration_passed: bool = False
    credential_declaration_passed: bool = False
    data_governance_declaration_passed: bool = False
    resource_boundary_declaration_passed: bool = False
    lifecycle_phase4_compatibility_passed: bool = False
    registry_phase3_compatibility_passed: bool = False
    no_live_sandbox_passed: bool = False
    no_live_dependency_install_passed: bool = False
    no_live_credential_access_passed: bool = False
    no_live_data_access_passed: bool = False
    no_live_resource_allocation_passed: bool = False
    public_projection_safety_passed: bool = False
    public_projection_second_leak_test_passed: bool = False
    audit_evidence_chain_passed: bool = False
    forbidden_scan_passed: bool = False
    full_pytest_passed: bool = False
    compileall_passed: bool = False
    collect_only_passed: bool = False
    targeted_pytest_passed: bool = False
    plugin_host_subset_passed: bool = False
    plugin_host_subset_non_empty: bool = False
    hash_compare_passed: bool = False
    test_inventory_compare_passed: bool = False
    phase2_phase5_resource_consistency_passed: bool = False
    run_goal_actor_budget_scope_passed: bool = False
    budget_owner_passed: bool = False
    no_unbounded_resource_passed: bool = False
    high_permission_budget_not_bypass_passed: bool = False
    resource_pressure_policy_passed: bool = False
    degradation_policy_passed: bool = False
    exhaustion_behavior_passed: bool = False
    metering_policy_passed: bool = False
    credential_handle_ref_safety_passed: bool = False
    credential_binding_passed: bool = False
    credential_purpose_passed: bool = False
    credential_revocation_passed: bool = False
    data_consent_passed: bool = False
    data_purpose_passed: bool = False
    data_lifecycle_passed: bool = False
    capability_token_boundary_passed: bool = False
    capability_token_scope_lease_time_revocation_passed: bool = False
    trust_boundary_passed: bool = False
    trust_boundary_public_projection_safety_passed: bool = False
    switch_boundary_passed: bool = False
    allow_enter_l5_phase6: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_index_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase5_quality_gate"
    detected_by_ref: str = "detector:l5_phase5_quality_gate"
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    phase: str = PHASE5_PHASE

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "PluginPhase5QualityGateDecision.decision_ref")
        required_bools = (
            self.p0_count == 0,
            self.p1_count == 0,
            self.compileall_passed,
            self.collect_only_passed,
            self.targeted_pytest_passed,
            self.plugin_host_subset_passed,
            self.plugin_host_subset_non_empty,
            self.full_pytest_passed,
            self.forbidden_scan_passed,
            self.hash_compare_passed,
            self.test_inventory_compare_passed,
            self.isolation_declaration_passed,
            self.dependency_declaration_passed,
            self.credential_declaration_passed,
            self.data_governance_declaration_passed,
            self.resource_boundary_declaration_passed,
            self.lifecycle_phase4_compatibility_passed,
            self.registry_phase3_compatibility_passed,
            self.no_live_sandbox_passed,
            self.no_live_dependency_install_passed,
            self.no_live_credential_access_passed,
            self.no_live_data_access_passed,
            self.no_live_resource_allocation_passed,
            self.public_projection_safety_passed,
            self.public_projection_second_leak_test_passed,
            self.audit_evidence_chain_passed,
            self.phase2_phase5_resource_consistency_passed,
            self.run_goal_actor_budget_scope_passed,
            self.budget_owner_passed,
            self.no_unbounded_resource_passed,
            self.high_permission_budget_not_bypass_passed,
            self.resource_pressure_policy_passed,
            self.degradation_policy_passed,
            self.exhaustion_behavior_passed,
            self.metering_policy_passed,
            self.credential_handle_ref_safety_passed,
            self.credential_binding_passed,
            self.credential_purpose_passed,
            self.credential_revocation_passed,
            self.data_consent_passed,
            self.data_purpose_passed,
            self.data_lifecycle_passed,
            self.capability_token_boundary_passed,
            self.capability_token_scope_lease_time_revocation_passed,
            self.trust_boundary_passed,
            self.trust_boundary_public_projection_safety_passed,
            self.switch_boundary_passed,
        )
        derived = all(required_bools)
        object.__setattr__(self, "allow_enter_l5_phase6", derived)
        for name in ("blocking_reasons", "evidence_index_refs", "regression_index_refs", "provenance_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginPhase5QualityGateDecision.{name}")
        for name in ("rule_source_ref", "detected_by_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginPhase5QualityGateDecision.{name}", required=False if name not in ("rule_source_ref", "detected_by_ref") else True)


@dataclass(frozen=True, slots=True)
class PluginPhase5PublicProjection:
    projection_ref: str
    phase: str = PHASE5_PHASE
    registry_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    lifecycle_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    mount_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    isolation_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    dependency_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    credential_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    data_governance_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    resource_boundary_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    capability_token_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    trust_boundary_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    switch_boundary_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    conflict_counts: tuple[tuple[str, int], ...] = field(default_factory=tuple)
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    status_text: str = "declaration_only"
    redacted_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    handoff_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    trace_ref: str = ""
    responsibility_chain_ref: str = ""
    redaction_state: str = "redacted"
    projection_digest: str = ""

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "PluginPhase5PublicProjection.projection_ref")
        for name in ("registry_summary", "lifecycle_summary", "mount_summary", "isolation_summary", "dependency_summary", "credential_summary", "data_governance_summary", "resource_boundary_summary", "capability_token_summary", "trust_boundary_summary", "switch_boundary_summary", "quality_gate_summary", "handoff_summary"):
            pairs = getattr(self, name)
            if not isinstance(pairs, tuple):
                raise ValueError(f"PluginPhase5PublicProjection.{name} must be tuple")
            for key, value in pairs:
                ensure_ref_text(key, f"PluginPhase5PublicProjection.{name}.key")
                ensure_short_text(value, f"PluginPhase5PublicProjection.{name}.value")
        for name in ("risk_tags", "redacted_evidence_refs"):
            _check_ref_tuple(getattr(self, name), f"PluginPhase5PublicProjection.{name}")
        ensure_short_text(self.status_text, "PluginPhase5PublicProjection.status_text")
        ensure_short_text(self.redaction_state, "PluginPhase5PublicProjection.redaction_state")
        ensure_ref_text(self.trace_ref, "PluginPhase5PublicProjection.trace_ref", required=False)
        ensure_ref_text(self.responsibility_chain_ref, "PluginPhase5PublicProjection.responsibility_chain_ref", required=False)
        if not public_text_is_safe(self):
            raise ValueError("PluginPhase5PublicProjection contains unsafe disclosure")
        if not self.projection_digest:
            object.__setattr__(self, "projection_digest", _digest_dataclass(self, ("projection_digest",)))


@dataclass(frozen=True, slots=True)
class PluginPhase5AuditIndex:
    audit_index_ref: str
    registry_key_refs: tuple[str, ...] = field(default_factory=tuple)
    isolation_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    dependency_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    data_governance_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    resource_boundary_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    capability_token_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    trust_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    switch_boundary_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_report_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_report_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_decision_refs: tuple[str, ...] = field(default_factory=tuple)
    public_projection_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    lifecycle_event_refs: tuple[str, ...] = field(default_factory=tuple)
    mount_event_refs: tuple[str, ...] = field(default_factory=tuple)
    boundary_event_refs: tuple[str, ...] = field(default_factory=tuple)
    isolation_event_refs: tuple[str, ...] = field(default_factory=tuple)
    dependency_event_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_event_refs: tuple[str, ...] = field(default_factory=tuple)
    data_governance_event_refs: tuple[str, ...] = field(default_factory=tuple)
    resource_boundary_event_refs: tuple[str, ...] = field(default_factory=tuple)
    switch_boundary_event_refs: tuple[str, ...] = field(default_factory=tuple)
    capability_token_event_refs: tuple[str, ...] = field(default_factory=tuple)
    trust_boundary_event_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_event_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_event_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_event_ref: str = ""
    handoff_event_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    phase: str = PHASE5_PHASE
    audit_digest: str = ""

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_index_ref, "PluginPhase5AuditIndex.audit_index_ref")
        for name in (
            "registry_key_refs", "isolation_decl_refs", "dependency_decl_refs", "credential_decl_refs", "data_governance_decl_refs", "resource_boundary_decl_refs", "capability_token_boundary_refs", "trust_boundary_refs", "switch_boundary_refs", "validation_report_refs", "conflict_report_refs", "quality_gate_decision_refs", "public_projection_refs", "evidence_refs", "provenance_refs", "lifecycle_event_refs", "mount_event_refs", "boundary_event_refs", "isolation_event_refs", "dependency_event_refs", "credential_event_refs", "data_governance_event_refs", "resource_boundary_event_refs", "switch_boundary_event_refs", "capability_token_event_refs", "trust_boundary_event_refs", "conflict_event_refs", "validation_event_refs",
        ):
            _check_ref_tuple(getattr(self, name), f"PluginPhase5AuditIndex.{name}")
        for name in ("quality_gate_event_ref", "handoff_event_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginPhase5AuditIndex.{name}", required=False)
        if not self.audit_digest:
            object.__setattr__(self, "audit_digest", _digest_dataclass(self, ("audit_digest",)))


class PluginPhase5BoundaryValidator:
    """Pure checker for explicit phase 5 declarations."""

    def __init__(self, validator_ref: str = "validator:l5_phase5_boundary") -> None:
        ensure_ref_text(validator_ref, "PluginPhase5BoundaryValidator.validator_ref")
        self.validator_ref = validator_ref

    def inspect_boundaries(
        self,
        *,
        isolation_decls: tuple[PluginIsolationDeclaration, ...] = tuple(),
        dependency_decls: tuple[PluginDependencyDeclaration, ...] = tuple(),
        dependency_graphs: tuple[PluginDependencyGraphSnapshot, ...] = tuple(),
        credential_decls: tuple[PluginCredentialRequirementDeclaration, ...] = tuple(),
        data_governance_decls: tuple[PluginDataGovernanceDeclaration, ...] = tuple(),
        resource_decls: tuple[PluginResourceBoundaryDeclaration, ...] = tuple(),
        capability_token_decls: tuple[PluginCapabilityTokenBoundaryDeclaration, ...] = tuple(),
        trust_boundary_decls: tuple[PluginTrustBoundaryDeclaration, ...] = tuple(),
        switch_boundary_decls: tuple[PluginPhase5SwitchBoundaryDeclaration, ...] = tuple(),
    ) -> PluginPhase5BoundaryValidationReport:
        conflicts: list[PluginPhase5Conflict] = []

        def add(kind: PluginPhase5ConflictKind, severity: PluginPhase5ConflictSeverity, message: str, field_path: str, evidence_refs: tuple[str, ...] = tuple()) -> None:
            conflicts.append(
                PluginPhase5Conflict(
                    conflict_ref=f"phase5_conflict:{kind.value}:{len(conflicts)+1}",
                    kind=kind,
                    severity=severity,
                    message=message,
                    field_path=field_path,
                    blocking=severity in (PluginPhase5ConflictSeverity.P0, PluginPhase5ConflictSeverity.P1),
                    evidence_refs=evidence_refs,
                )
            )

        for decl in isolation_decls:
            self._check_common(decl, "isolation", add)
            if not _has_ref(decl.isolation_boundary_ref):
                add(PluginPhase5ConflictKind.ISOLATION_MISSING_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "isolation boundary ref is required", "isolation_boundary_ref", decl.evidence_refs)
            if not _has_ref(decl.sandbox_requirement_ref):
                add(PluginPhase5ConflictKind.ISOLATION_MISSING_SANDBOX_REQUIREMENT_CONFLICT, PluginPhase5ConflictSeverity.P2, "sandbox requirement ref is required", "sandbox_requirement_ref", decl.evidence_refs)
            if not _has_ref(decl.side_effect_boundary_ref):
                add(PluginPhase5ConflictKind.ISOLATION_MISSING_SIDE_EFFECT_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "side effect boundary ref is required", "side_effect_boundary_ref", decl.evidence_refs)
            if not _has_ref(decl.no_live_action_ref):
                add(PluginPhase5ConflictKind.ISOLATION_MISSING_NO_LIVE_ACTION_CONFLICT, PluginPhase5ConflictSeverity.P1, "no-live-action ref is required", "no_live_action_ref", decl.evidence_refs)
            if has_live_locator(decl):
                add(PluginPhase5ConflictKind.ISOLATION_LIVE_SANDBOX_EXECUTION_CONFLICT, PluginPhase5ConflictSeverity.P0, "isolation declaration contains live locator", "isolation", decl.evidence_refs)

        for decl in dependency_decls:
            self._check_common(decl, "dependency", add)
            if not _has_ref(decl.dependency_policy_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_DEPENDENCY_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P1, "dependency policy ref is required", "dependency_policy_ref", decl.evidence_refs)
            if not _has_ref(decl.version_policy_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_VERSION_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P1, "version policy ref is required", "version_policy_ref", decl.evidence_refs)
            if not _has_ref(decl.compatibility_decl_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_COMPATIBILITY_DECL_CONFLICT, PluginPhase5ConflictSeverity.P1, "compatibility declaration ref is required", "compatibility_decl_ref", decl.evidence_refs)
            if not _has_ref(decl.dependency_snapshot_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_GRAPH_SNAPSHOT_CONFLICT, PluginPhase5ConflictSeverity.P1, "dependency graph snapshot ref is required", "dependency_snapshot_ref", decl.evidence_refs)
            if not _has_ref(decl.version_slot_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_VERSION_SLOT_CONFLICT, PluginPhase5ConflictSeverity.P2, "version slot ref is required", "version_slot_ref", decl.evidence_refs)
            if not _has_ref(decl.rollback_anchor_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_ROLLBACK_ANCHOR_CONFLICT, PluginPhase5ConflictSeverity.P2, "rollback anchor ref is required", "rollback_anchor_ref", decl.evidence_refs)
            if not _has_ref(decl.dependency_compatibility_matrix_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_COMPATIBILITY_MATRIX_CONFLICT, PluginPhase5ConflictSeverity.P2, "compatibility matrix ref is required", "dependency_compatibility_matrix_ref", decl.evidence_refs)
            if not _has_ref(decl.old_event_replay_compatibility_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_OLD_EVENT_REPLAY_COMPATIBILITY_CONFLICT, PluginPhase5ConflictSeverity.P2, "old event replay compatibility ref is required", "old_event_replay_compatibility_ref", decl.evidence_refs)
            if not _has_ref(decl.upcast_policy_ref):
                add(PluginPhase5ConflictKind.DEPENDENCY_MISSING_UPCAST_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P2, "upcast policy ref is required", "upcast_policy_ref", decl.evidence_refs)
            if has_live_locator(decl):
                add(PluginPhase5ConflictKind.DEPENDENCY_LIVE_IMPORT_CONFLICT, PluginPhase5ConflictSeverity.P0, "dependency declaration contains live locator", "dependency", decl.evidence_refs)

        for graph in dependency_graphs:
            if has_live_locator(graph):
                add(PluginPhase5ConflictKind.DEPENDENCY_LIVE_IMPORT_CONFLICT, PluginPhase5ConflictSeverity.P0, "dependency graph contains live locator", "dependency_graph", graph.evidence_refs)

        for decl in credential_decls:
            self._check_common(decl, "credential", add)
            if not _has_ref(decl.credential_policy_ref):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential policy ref is required", "credential_policy_ref", decl.evidence_refs)
            if not _has_ref(decl.credential_scope_ref):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_SCOPE_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential scope ref is required", "credential_scope_ref", decl.evidence_refs)
            if not _has_ref(decl.redaction_policy_ref):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_REDACTION_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P1, "redaction policy ref is required", "redaction_policy_ref", decl.evidence_refs)
            if not _has_ref(decl.approval_ref):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_APPROVAL_CONFLICT, PluginPhase5ConflictSeverity.P1, "approval ref is required", "approval_ref", decl.evidence_refs)
            if not _has_ref(decl.lease_ref) or not _has_ref(decl.credential_lease_ref):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_LEASE_CONFLICT, PluginPhase5ConflictSeverity.P1, "lease refs are required", "lease_ref", decl.evidence_refs)
            if not _has_refs(decl.credential_handle_refs):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_SCOPE_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential handle refs are required", "credential_handle_refs", decl.evidence_refs)
            if not _has_refs(decl.credential_binding_refs):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_BINDING_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential binding refs are required", "credential_binding_refs", decl.evidence_refs)
            if not _has_refs(decl.credential_purpose_refs):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_PURPOSE_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential purpose refs are required", "credential_purpose_refs", decl.evidence_refs)
            if not _has_ref(decl.credential_revocation_ref):
                add(PluginPhase5ConflictKind.CREDENTIAL_MISSING_REVOCATION_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential revocation ref is required", "credential_revocation_ref", decl.evidence_refs)
            if not decl.value_absent_required or not decl.redacted_required:
                add(PluginPhase5ConflictKind.CREDENTIAL_PLAINTEXT_SECRET_CONFLICT, PluginPhase5ConflictSeverity.P0, "credential value absence and redaction are required", "value_absent_required", decl.evidence_refs)
            if suspicious_credential_value_paths(decl) or has_live_locator(decl):
                add(PluginPhase5ConflictKind.CREDENTIAL_PLAINTEXT_SECRET_CONFLICT, PluginPhase5ConflictSeverity.P0, "credential declaration contains unsafe value or locator", "credential", decl.evidence_refs)

        for decl in data_governance_decls:
            self._check_common(decl, "data_governance", add)
            if not _has_refs(decl.data_category_refs):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_CATEGORY_CONFLICT, PluginPhase5ConflictSeverity.P1, "data category refs are required", "data_category_refs", decl.evidence_refs)
            if not _has_ref(decl.privacy_boundary_ref):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_PRIVACY_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "privacy boundary ref is required", "privacy_boundary_ref", decl.evidence_refs)
            if not _has_ref(decl.data_minimization_ref) or not _has_ref(decl.minimization_policy_ref):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_MINIMIZATION_CONFLICT, PluginPhase5ConflictSeverity.P1, "minimization refs are required", "data_minimization_ref", decl.evidence_refs)
            if not _has_ref(decl.retention_policy_ref):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_RETENTION_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P1, "retention policy ref is required", "retention_policy_ref", decl.evidence_refs)
            if not _has_ref(decl.deletion_policy_ref):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_DELETION_POLICY_CONFLICT, PluginPhase5ConflictSeverity.P1, "deletion policy ref is required", "deletion_policy_ref", decl.evidence_refs)
            if not _has_ref(decl.lineage_ref):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_LINEAGE_CONFLICT, PluginPhase5ConflictSeverity.P1, "lineage ref is required", "lineage_ref", decl.evidence_refs)
            if not _has_refs(decl.consent_refs):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_CONSENT_CONFLICT, PluginPhase5ConflictSeverity.P1, "consent refs are required", "consent_refs", decl.evidence_refs)
            if not _has_refs(decl.purpose_refs):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_PURPOSE_CONFLICT, PluginPhase5ConflictSeverity.P1, "purpose refs are required", "purpose_refs", decl.evidence_refs)
            if not _has_refs(decl.data_lifecycle_refs):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_LIFECYCLE_CONFLICT, PluginPhase5ConflictSeverity.P1, "data lifecycle refs are required", "data_lifecycle_refs", decl.evidence_refs)
            if not _has_refs(decl.external_disclosure_boundary_refs):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_MISSING_EXTERNAL_DISCLOSURE_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "external disclosure boundary refs are required", "external_disclosure_boundary_refs", decl.evidence_refs)
            if has_live_locator(decl) or suspicious_credential_value_paths(decl):
                add(PluginPhase5ConflictKind.DATA_GOVERNANCE_LIVE_DATA_ACCESS_CONFLICT, PluginPhase5ConflictSeverity.P0, "data governance declaration contains live locator or secret-like value", "data_governance", decl.evidence_refs)

        for decl in resource_decls:
            self._check_common(decl, "resource", add)
            for field_name, kind in (
                ("quota_policy_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_QUOTA_POLICY_CONFLICT),
                ("rate_limit_policy_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_RATE_LIMIT_POLICY_CONFLICT),
                ("budget_ledger_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_BUDGET_LEDGER_CONFLICT),
                ("cost_policy_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_COST_POLICY_CONFLICT),
                ("budget_owner_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_BUDGET_OWNER_CONFLICT),
                ("run_budget_scope_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_RUN_BUDGET_SCOPE_CONFLICT),
                ("goal_budget_scope_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_GOAL_BUDGET_SCOPE_CONFLICT),
                ("actor_budget_scope_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_ACTOR_BUDGET_SCOPE_CONFLICT),
                ("metering_policy_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_METERING_POLICY_CONFLICT),
                ("resource_pressure_policy_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_RESOURCE_PRESSURE_POLICY_CONFLICT),
                ("degradation_policy_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_DEGRADATION_POLICY_CONFLICT),
                ("exhaustion_behavior_ref", PluginPhase5ConflictKind.RESOURCE_MISSING_EXHAUSTION_BEHAVIOR_CONFLICT),
            ):
                if not _has_ref(getattr(decl, field_name)):
                    add(kind, PluginPhase5ConflictSeverity.P1, f"{field_name} is required", field_name, decl.evidence_refs)
            if not _has_ref(decl.phase2_resource_decl_ref):
                add(PluginPhase5ConflictKind.RESOURCE_PHASE2_DECL_MISSING_CONFLICT, PluginPhase5ConflictSeverity.P1, "phase2 resource declaration ref is required", "phase2_resource_decl_ref", decl.evidence_refs)
            if has_unbounded_resource_text(decl):
                add(PluginPhase5ConflictKind.RESOURCE_UNBOUNDED_BUDGET_DECLARED_CONFLICT, PluginPhase5ConflictSeverity.P0, "unbounded resource semantics are forbidden", "resource", decl.evidence_refs)
            if has_live_locator(decl):
                add(PluginPhase5ConflictKind.RESOURCE_LIVE_ALLOCATION_CONFLICT, PluginPhase5ConflictSeverity.P0, "resource declaration contains live locator", "resource", decl.evidence_refs)

        for decl in capability_token_decls:
            self._check_common(decl, "capability_token", add)
            if not _has_ref(decl.capability_token_boundary_decl_ref):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "capability token boundary ref is required", "capability_token_boundary_decl_ref", decl.evidence_refs)
            if not _has_refs(decl.token_scope_refs):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_SCOPE_CONFLICT, PluginPhase5ConflictSeverity.P1, "token scope refs are required", "token_scope_refs", decl.evidence_refs)
            if not _has_ref(decl.token_lease_ref):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_LEASE_CONFLICT, PluginPhase5ConflictSeverity.P1, "token lease ref is required", "token_lease_ref", decl.evidence_refs)
            if not _has_ref(decl.token_expiry_ref):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_EXPIRY_CONFLICT, PluginPhase5ConflictSeverity.P1, "token expiry ref is required", "token_expiry_ref", decl.evidence_refs)
            if not _has_ref(decl.token_revocation_ref):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_REVOCATION_CONFLICT, PluginPhase5ConflictSeverity.P1, "token revocation ref is required", "token_revocation_ref", decl.evidence_refs)
            if not _has_ref(decl.audit_decl_ref):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_MISSING_AUDIT_CONFLICT, PluginPhase5ConflictSeverity.P1, "token audit decl ref is required", "audit_decl_ref", decl.evidence_refs)
            if suspicious_credential_value_paths(decl) or has_live_locator(decl):
                add(PluginPhase5ConflictKind.CAPABILITY_TOKEN_PLAINTEXT_TOKEN_CONFLICT, PluginPhase5ConflictSeverity.P0, "capability token boundary contains unsafe value", "capability_token", decl.evidence_refs)

        for decl in trust_boundary_decls:
            self._check_common(decl, "trust_boundary", add)
            if not _has_ref(decl.host_boundary_ref):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_HOST_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "host boundary ref is required", "host_boundary_ref", decl.evidence_refs)
            if not _has_ref(decl.plugin_boundary_ref):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_PLUGIN_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "plugin boundary ref is required", "plugin_boundary_ref", decl.evidence_refs)
            if not _has_refs(decl.data_boundary_refs):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_DATA_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "data boundary refs are required", "data_boundary_refs", decl.evidence_refs)
            if not _has_refs(decl.credential_boundary_refs):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_CREDENTIAL_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "credential boundary refs are required", "credential_boundary_refs", decl.evidence_refs)
            if not _has_refs(decl.network_boundary_refs):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_NETWORK_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "network boundary refs are required", "network_boundary_refs", decl.evidence_refs)
            if not _has_refs(decl.tool_boundary_refs):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_TOOL_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "tool boundary refs are required", "tool_boundary_refs", decl.evidence_refs)
            if not _has_refs(decl.external_disclosure_boundary_refs):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_MISSING_EXTERNAL_DISCLOSURE_BOUNDARY_CONFLICT, PluginPhase5ConflictSeverity.P1, "external disclosure boundary refs are required", "external_disclosure_boundary_refs", decl.evidence_refs)
            if has_live_locator(decl):
                add(PluginPhase5ConflictKind.TRUST_BOUNDARY_USED_AS_LIVE_SANDBOX_CONFLICT, PluginPhase5ConflictSeverity.P0, "trust boundary contains live locator", "trust_boundary", decl.evidence_refs)

        for decl in switch_boundary_decls:
            self._check_common(decl, "switch_boundary", add)
            for field_name, kind in (
                ("hot_switch_decl_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_HOT_SWITCH_REF_CONFLICT),
                ("switch_readiness_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_READINESS_REF_CONFLICT),
                ("pre_switch_checkpoint_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_CHECKPOINT_REF_CONFLICT),
                ("post_switch_observation_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_OBSERVATION_REF_CONFLICT),
                ("switch_rollback_route_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_ROLLBACK_ROUTE_REF_CONFLICT),
                ("isolation_boundary_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_ISOLATION_BOUNDARY_CONFLICT),
                ("dependency_decl_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_DEPENDENCY_BOUNDARY_CONFLICT),
                ("credential_boundary_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_CREDENTIAL_BOUNDARY_CONFLICT),
                ("data_governance_boundary_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_DATA_BOUNDARY_CONFLICT),
                ("resource_boundary_ref", PluginPhase5ConflictKind.SWITCH_BOUNDARY_MISSING_RESOURCE_BOUNDARY_CONFLICT),
            ):
                if not _has_ref(getattr(decl, field_name)):
                    add(kind, PluginPhase5ConflictSeverity.P1, f"{field_name} is required", field_name, decl.evidence_refs)
            if has_live_locator(decl):
                add(PluginPhase5ConflictKind.PHASE5_SWITCH_BOUNDARY_USED_AS_LIVE_SWITCH_CONFLICT, PluginPhase5ConflictSeverity.P0, "switch boundary contains live locator", "switch_boundary", decl.evidence_refs)

        return PluginPhase5BoundaryValidationReport(
            report_ref="phase5_validation:boundary",
            checked_isolation_decl_refs=tuple(item.isolation_decl_ref for item in isolation_decls),
            checked_dependency_decl_refs=tuple(item.dependency_decl_ref for item in dependency_decls),
            checked_credential_decl_refs=tuple(item.credential_decl_ref for item in credential_decls),
            checked_data_governance_decl_refs=tuple(item.data_governance_decl_ref for item in data_governance_decls),
            checked_resource_boundary_decl_refs=tuple(item.resource_boundary_decl_ref for item in resource_decls),
            checked_capability_token_boundary_refs=tuple(item.capability_token_boundary_decl_ref for item in capability_token_decls),
            checked_trust_boundary_refs=tuple(item.trust_boundary_decl_ref for item in trust_boundary_decls),
            checked_switch_boundary_refs=tuple(item.switch_boundary_decl_ref for item in switch_boundary_decls),
            conflicts=tuple(conflicts),
            actor_ref="actor:l5_phase5_validator",
            scope_ref="scope:l5_phase5",
            trace_ref="trace:l5_phase5_validation",
            policy_ref="policy:l5_phase5",
            approval_ref="approval:l5_phase5_declaration_only",
            evidence_refs=("evidence:l5_phase5_validation",),
            provenance_refs=("provenance:l5_phase5",),
            responsibility_chain_ref="responsibility:l5_phase5_validation",
            accountability_ref="accountability:l5_phase5_validation",
            tamper_evidence_ref="tamper:l5_phase5_validation",
        )

    def _check_common(self, decl: _Phase5Base, label: str, add: Any) -> None:
        checks = (
            (decl.actor_ref, "actor_ref"),
            (decl.scope_ref, "scope_ref"),
            (decl.trace_ref, "trace_ref"),
            (decl.responsibility_chain_ref, "responsibility_chain_ref"),
            (decl.accountability_ref, "accountability_ref"),
            (decl.tamper_evidence_ref, "tamper_evidence_ref"),
        )
        for value, field_name in checks:
            if not _has_ref(value):
                add(PluginPhase5ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase5ConflictSeverity.P1, f"{label} missing {field_name}", field_name, decl.evidence_refs)
        if not _has_refs(decl.evidence_refs):
            add(PluginPhase5ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase5ConflictSeverity.P1, f"{label} missing evidence_refs", "evidence_refs", decl.evidence_refs)
        if not _has_refs(decl.provenance_refs):
            add(PluginPhase5ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase5ConflictSeverity.P1, f"{label} missing provenance_refs", "provenance_refs", decl.evidence_refs)
        if not decl.least_privilege_declared or not decl.deny_by_default_declared:
            add(PluginPhase5ConflictKind.PHASE5_BOUNDARY_USED_AS_PERMISSION_GRANT_CONFLICT, PluginPhase5ConflictSeverity.P1, f"{label} must declare least privilege and deny by default", "least_privilege_declared", decl.evidence_refs)
        if has_forbidden_phase5_method(decl) or has_forbidden_phase5_field_name(decl):
            add(PluginPhase5ConflictKind.FORBIDDEN_LIVE_EXECUTION_CONFLICT, PluginPhase5ConflictSeverity.P0, f"{label} exposes forbidden method or field", label, decl.evidence_refs)


class PluginPhase5QualityGate:
    def decide(
        self,
        report: PluginPhase5BoundaryValidationReport,
        *,
        compileall_passed: bool,
        collect_only_passed: bool,
        targeted_pytest_passed: bool,
        plugin_host_subset_passed: bool,
        plugin_host_subset_non_empty: bool,
        full_pytest_passed: bool,
        forbidden_scan_passed: bool,
        hash_compare_passed: bool,
        test_inventory_compare_passed: bool,
        public_projection_safety_passed: bool = True,
        public_projection_second_leak_test_passed: bool = True,
        lifecycle_phase4_compatibility_passed: bool = True,
        registry_phase3_compatibility_passed: bool = True,
        phase2_phase5_resource_consistency_passed: bool = True,
    ) -> PluginPhase5QualityGateDecision:
        passed = report.passed
        return PluginPhase5QualityGateDecision(
            decision_ref="quality_gate:l5_phase5",
            p0_count=report.p0_count,
            p1_count=report.p1_count,
            p2_count=report.p2_count,
            p3_count=report.p3_count,
            isolation_declaration_passed=passed,
            dependency_declaration_passed=passed,
            credential_declaration_passed=passed,
            data_governance_declaration_passed=passed,
            resource_boundary_declaration_passed=passed,
            lifecycle_phase4_compatibility_passed=lifecycle_phase4_compatibility_passed,
            registry_phase3_compatibility_passed=registry_phase3_compatibility_passed,
            no_live_sandbox_passed=passed,
            no_live_dependency_install_passed=passed,
            no_live_credential_access_passed=passed,
            no_live_data_access_passed=passed,
            no_live_resource_allocation_passed=passed,
            public_projection_safety_passed=public_projection_safety_passed,
            public_projection_second_leak_test_passed=public_projection_second_leak_test_passed,
            audit_evidence_chain_passed=passed,
            forbidden_scan_passed=forbidden_scan_passed,
            full_pytest_passed=full_pytest_passed,
            compileall_passed=compileall_passed,
            collect_only_passed=collect_only_passed,
            targeted_pytest_passed=targeted_pytest_passed,
            plugin_host_subset_passed=plugin_host_subset_passed,
            plugin_host_subset_non_empty=plugin_host_subset_non_empty,
            hash_compare_passed=hash_compare_passed,
            test_inventory_compare_passed=test_inventory_compare_passed,
            phase2_phase5_resource_consistency_passed=phase2_phase5_resource_consistency_passed,
            run_goal_actor_budget_scope_passed=passed,
            budget_owner_passed=passed,
            no_unbounded_resource_passed=passed,
            high_permission_budget_not_bypass_passed=passed,
            resource_pressure_policy_passed=passed,
            degradation_policy_passed=passed,
            exhaustion_behavior_passed=passed,
            metering_policy_passed=passed,
            credential_handle_ref_safety_passed=passed,
            credential_binding_passed=passed,
            credential_purpose_passed=passed,
            credential_revocation_passed=passed,
            data_consent_passed=passed,
            data_purpose_passed=passed,
            data_lifecycle_passed=passed,
            capability_token_boundary_passed=passed,
            capability_token_scope_lease_time_revocation_passed=passed,
            trust_boundary_passed=passed,
            trust_boundary_public_projection_safety_passed=public_projection_safety_passed,
            switch_boundary_passed=passed,
            blocking_reasons=report.blocking_reasons,
            evidence_index_refs=("evidence_index:l5_phase5",),
            regression_index_refs=("regression_index:l5_phase5",),
            actor_ref=report.actor_ref,
            scope_ref=report.scope_ref,
            trace_ref=report.trace_ref,
            policy_ref=report.policy_ref,
            approval_ref=report.approval_ref,
            provenance_refs=report.provenance_refs,
            responsibility_chain_ref=report.responsibility_chain_ref,
            accountability_ref=report.accountability_ref,
            tamper_evidence_ref=report.tamper_evidence_ref,
        )


class PluginPhase5PublicProjectionBuilder:
    def make_projection(
        self,
        *,
        isolation: PluginIsolationDeclaration,
        dependency: PluginDependencyDeclaration,
        credential: PluginCredentialRequirementDeclaration,
        data_governance: PluginDataGovernanceDeclaration,
        resource: PluginResourceBoundaryDeclaration,
        capability_token: PluginCapabilityTokenBoundaryDeclaration,
        trust_boundary: PluginTrustBoundaryDeclaration,
        switch_boundary: PluginPhase5SwitchBoundaryDeclaration,
        quality_gate: PluginPhase5QualityGateDecision | None = None,
    ) -> PluginPhase5PublicProjection:
        summary = PluginPhase5PublicProjection(
            projection_ref="projection:l5_phase5",
            isolation_summary=(("isolation_boundary_ref", isolation.isolation_boundary_ref), ("sandbox_requirement_ref", isolation.sandbox_requirement_ref), ("no_live_action_ref", isolation.no_live_action_ref)),
            dependency_summary=(("dependency_policy_ref", dependency.dependency_policy_ref), ("version_policy_ref", dependency.version_policy_ref), ("dependency_count", str(len(dependency.dependency_refs))), ("graph_digest", dependency.dependency_snapshot_ref)),
            credential_summary=(("credential_kind_ref", credential.credential_kind_ref), ("credential_policy_ref", credential.credential_policy_ref), ("redaction_state", "redacted"), ("boundary_ref", credential.data_boundary_ref), ("required_approval_ref", credential.approval_ref)),
            data_governance_summary=(("data_category_count", str(len(data_governance.data_category_refs))), ("privacy_boundary_ref", data_governance.privacy_boundary_ref), ("retention_policy_ref", data_governance.retention_policy_ref), ("deletion_policy_ref", data_governance.deletion_policy_ref), ("minimization_ref", data_governance.data_minimization_ref), ("lineage_ref", data_governance.lineage_ref)),
            resource_boundary_summary=(("cpu_budget_ref", resource.cpu_budget_ref), ("memory_budget_ref", resource.memory_budget_ref), ("token_budget_ref", resource.token_budget_ref), ("quota_policy_ref", resource.quota_policy_ref), ("rate_limit_policy_ref", resource.rate_limit_policy_ref), ("budget_ledger_ref", resource.budget_ledger_ref)),
            capability_token_summary=(("capability_token_boundary_decl_ref", capability_token.capability_token_boundary_decl_ref), ("token_scope_count", str(len(capability_token.token_scope_refs))), ("lease_ref", capability_token.token_lease_ref), ("expiry_ref", capability_token.token_expiry_ref), ("revocation_ref", capability_token.token_revocation_ref)),
            trust_boundary_summary=(("trust_boundary_decl_ref", trust_boundary.trust_boundary_decl_ref), ("host_boundary_ref", trust_boundary.host_boundary_ref), ("plugin_boundary_ref", trust_boundary.plugin_boundary_ref), ("trust_boundary_digest", trust_boundary.trust_boundary_digest)),
            switch_boundary_summary=(("switch_boundary_decl_ref", switch_boundary.switch_boundary_decl_ref), ("hot_switch_decl_ref", switch_boundary.hot_switch_decl_ref), ("switch_readiness_ref", switch_boundary.switch_readiness_ref), ("blocking_reason_count", "0")),
            conflict_counts=(("p0", str(quality_gate.p0_count) if quality_gate else "0"), ("p1", str(quality_gate.p1_count) if quality_gate else "0")),
            risk_tags=tuple(sorted(set(isolation.risk_tags + dependency.risk_tags + credential.risk_tags + data_governance.risk_tags + resource.risk_tags))),
            redacted_evidence_refs=("redacted_evidence:l5_phase5",),
            quality_gate_summary=(("allow_enter_l5_phase6", str(quality_gate.allow_enter_l5_phase6) if quality_gate else "unknown"),),
            handoff_summary=(("phase6_consumable", "boundary declarations only"),),
            trace_ref="trace:l5_phase5_projection",
            responsibility_chain_ref="responsibility:l5_phase5_projection",
        )
        return summary


class PluginPhase5AuditIndexBuilder:
    def make_index(
        self,
        *,
        report: PluginPhase5BoundaryValidationReport,
        projection: PluginPhase5PublicProjection,
        quality_gate: PluginPhase5QualityGateDecision,
    ) -> PluginPhase5AuditIndex:
        return PluginPhase5AuditIndex(
            audit_index_ref="audit_index:l5_phase5",
            validation_report_refs=(report.report_ref,),
            conflict_report_refs=(report.report_ref,),
            quality_gate_decision_refs=(quality_gate.decision_ref,),
            public_projection_refs=(projection.projection_ref,),
            evidence_refs=report.evidence_refs,
            provenance_refs=report.provenance_refs,
            lifecycle_event_refs=("event:lifecycle_refs_read_only",),
            mount_event_refs=("event:mount_refs_read_only",),
            boundary_event_refs=("event:phase5_boundary_declared",),
            isolation_event_refs=("event:isolation_declared",),
            dependency_event_refs=("event:dependency_declared",),
            credential_event_refs=("event:credential_declared",),
            data_governance_event_refs=("event:data_governance_declared",),
            resource_boundary_event_refs=("event:resource_boundary_declared",),
            switch_boundary_event_refs=("event:switch_boundary_declared",),
            capability_token_event_refs=("event:capability_token_boundary_declared",),
            trust_boundary_event_refs=("event:trust_boundary_declared",),
            conflict_event_refs=("event:phase5_conflicts_checked",),
            validation_event_refs=("event:phase5_validation_completed",),
            quality_gate_event_ref="event:phase5_quality_gate_decided",
            handoff_event_ref="event:phase5_handoff_declared",
            actor_ref=report.actor_ref,
            scope_ref=report.scope_ref,
            trace_ref=report.trace_ref,
            policy_ref=report.policy_ref,
            approval_ref=report.approval_ref,
            responsibility_chain_ref=report.responsibility_chain_ref,
            accountability_ref=report.accountability_ref,
            tamper_evidence_ref=report.tamper_evidence_ref,
        )


__all__ = (
    "PHASE5_PHASE",
    "PluginCapabilityTokenBoundaryDeclaration",
    "PluginCredentialRequirementDeclaration",
    "PluginDataGovernanceDeclaration",
    "PluginDependencyDeclaration",
    "PluginDependencyGraphSnapshot",
    "PluginIsolationDeclaration",
    "PluginPhase5AuditIndex",
    "PluginPhase5AuditIndexBuilder",
    "PluginPhase5BoundaryValidationReport",
    "PluginPhase5BoundaryValidator",
    "PluginPhase5Conflict",
    "PluginPhase5ConflictKind",
    "PluginPhase5ConflictSeverity",
    "PluginPhase5PublicProjection",
    "PluginPhase5PublicProjectionBuilder",
    "PluginPhase5QualityGate",
    "PluginPhase5QualityGateDecision",
    "PluginPhase5SwitchBoundaryDeclaration",
    "PluginResourceBoundaryDeclaration",
    "PluginTrustBoundaryDeclaration",
    "has_forbidden_phase5_field_name",
    "has_forbidden_phase5_method",
    "has_live_locator",
    "has_unbounded_resource_text",
    "public_text_is_safe",
)
