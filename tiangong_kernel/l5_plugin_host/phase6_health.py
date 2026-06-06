"""L5 phase 6 health, disposition, and permission-precondition declarations.

This module is deliberately inert. It models health signals, health-check
requirements, isolation-disposition declarations, and recovery / hot-switch /
rollback / replay permission preconditions as immutable declaration records only.
It does not probe, ping, connect, read logs, collect metrics, isolate plugins,
change registries, issue permits, issue leases, create tickets, load plugins,
run code, recover, roll back, hot-switch, replay, migrate, create checkpoints,
start observers, or implement L6 business plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ._common import ensure_bool, ensure_ref_items, ensure_ref_text, ensure_short_text, stable_digest, stable_primitive
from .phase2_common import suspicious_credential_value_paths


PHASE6_PHASE = "L5_PHASE6"

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
        "recover",
        "rollback",
        "hot_switch",
        "replay",
        "migrate",
        "checkpoint",
        "observe",
        "probe",
        "ping",
        "connect",
        "collect",
        "read_log",
        "read_metric",
        "issue_permit",
        "issue_lease",
        "issue_ticket",
        "mint_token",
        "validate_token",
        "commit",
        "mutate",
        "transition_to",
        "validate_and_apply",
        "auto_fix",
        "repair",
        "healthcheck",
        "create_checkpoint",
        "restore",
        "apply_patch",
    )
)

_LIVE_FIELD_NAMES = frozenset(
    (
        "metric_value",
        "live_metric",
        "process_id",
        "port",
        "endpoint",
        "url",
        "socket",
        "database_uri",
        "log_path",
        "raw_log",
        "raw_metric",
        "permit_object",
        "lease_object",
        "confirmation_ticket_object",
        "token_object",
        "plugin_entry",
        "checkpoint_payload",
        "recovery_patch",
        "rollback_patch",
        "replay_event_payload",
        "migration_script",
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
    "shell command",
    "BEGIN PRIVATE KEY",
    "BEGIN CERTIFICATE",
)


class PluginPhase6ConflictSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    P3 = "p3"
    P2 = "p2"
    P1 = "p1"
    P0 = "p0"


class PluginPhase6ConflictKind(str, Enum):
    HEALTH_MISSING_SIGNAL_REF_CONFLICT = "health_missing_signal_ref_conflict"
    HEALTH_MISSING_SIGNAL_SEMANTICS_CONFLICT = "health_missing_signal_semantics_conflict"
    HEALTH_MISSING_STATUS_KIND_CONFLICT = "health_missing_status_kind_conflict"
    HEALTH_MISSING_NO_LIVE_PROBE_CONFLICT = "health_missing_no_live_probe_conflict"
    HEALTH_MISSING_EVIDENCE_CONFLICT = "health_missing_evidence_conflict"
    HEALTH_MISSING_AUDIT_CONFLICT = "health_missing_audit_conflict"
    HEALTH_LIVE_PROBE_CONFLICT = "health_live_probe_conflict"
    HEALTH_LIVE_METRIC_COLLECTION_CONFLICT = "health_live_metric_collection_conflict"
    HEALTH_LIVE_LOG_READ_CONFLICT = "health_live_log_read_conflict"
    HEALTH_LIVE_MONITORING_CONNECTION_CONFLICT = "health_live_monitoring_connection_conflict"
    HEALTH_PUBLIC_PROJECTION_LEAK_CONFLICT = "health_public_projection_leak_conflict"
    HEALTH_CHECK_MISSING_READINESS_DECL_CONFLICT = "health_check_missing_readiness_decl_conflict"
    HEALTH_CHECK_MISSING_LIVENESS_DECL_CONFLICT = "health_check_missing_liveness_decl_conflict"
    HEALTH_CHECK_MISSING_SAFETY_DECL_CONFLICT = "health_check_missing_safety_decl_conflict"
    HEALTH_CHECK_MISSING_REQUIRED_POLICY_CONFLICT = "health_check_missing_required_policy_conflict"
    HEALTH_CHECK_MISSING_REQUIRED_EVIDENCE_CONFLICT = "health_check_missing_required_evidence_conflict"
    HEALTH_CHECK_EXEC_CONFLICT = "health_check_exec_conflict"
    HEALTH_CHECK_OBSERVER_START_CONFLICT = "health_check_observer_start_conflict"
    HEALTH_CHECK_MUTATES_INPUT_CONFLICT = "health_check_mutates_input_conflict"
    DISPOSITION_MISSING_KIND_CONFLICT = "disposition_missing_kind_conflict"
    DISPOSITION_MISSING_HEALTH_REPORT_CONFLICT = "disposition_missing_health_report_conflict"
    DISPOSITION_MISSING_ISOLATION_BOUNDARY_CONFLICT = "disposition_missing_isolation_boundary_conflict"
    DISPOSITION_MISSING_POLICY_CONFLICT = "disposition_missing_policy_conflict"
    DISPOSITION_MISSING_APPROVAL_CONFLICT = "disposition_missing_approval_conflict"
    DISPOSITION_MISSING_EVIDENCE_CONFLICT = "disposition_missing_evidence_conflict"
    DISPOSITION_LIVE_ISOLATE_CONFLICT = "disposition_live_isolate_conflict"
    DISPOSITION_LIVE_QUARANTINE_CONFLICT = "disposition_live_quarantine_conflict"
    DISPOSITION_LIVE_DISABLE_CONFLICT = "disposition_live_disable_conflict"
    DISPOSITION_LIVE_DEGRADE_CONFLICT = "disposition_live_degrade_conflict"
    DISPOSITION_REGISTRY_MUTATION_CONFLICT = "disposition_registry_mutation_conflict"
    DISPOSITION_LIFECYCLE_MUTATION_CONFLICT = "disposition_lifecycle_mutation_conflict"
    DISPOSITION_PUBLIC_PROJECTION_LEAK_CONFLICT = "disposition_public_projection_leak_conflict"
    RECOVERY_PERMISSION_MISSING_RECOVERY_PLAN_CONFLICT = "recovery_permission_missing_recovery_plan_conflict"
    RECOVERY_PERMISSION_MISSING_CHECKPOINT_CONFLICT = "recovery_permission_missing_checkpoint_conflict"
    RECOVERY_PERMISSION_MISSING_RECOVERY_POINT_CONFLICT = "recovery_permission_missing_recovery_point_conflict"
    RECOVERY_PERMISSION_MISSING_ROLLBACK_ANCHOR_CONFLICT = "recovery_permission_missing_rollback_anchor_conflict"
    RECOVERY_PERMISSION_MISSING_VALIDATION_CONFLICT = "recovery_permission_missing_validation_conflict"
    RECOVERY_PERMISSION_MISSING_REGRESSION_CONFLICT = "recovery_permission_missing_regression_conflict"
    RECOVERY_PERMISSION_MISSING_POLICY_CONFLICT = "recovery_permission_missing_policy_conflict"
    RECOVERY_PERMISSION_MISSING_APPROVAL_CONFLICT = "recovery_permission_missing_approval_conflict"
    RECOVERY_PERMISSION_MISSING_LEASE_CONFLICT = "recovery_permission_missing_lease_conflict"
    RECOVERY_PERMISSION_MISSING_EVIDENCE_CONFLICT = "recovery_permission_missing_evidence_conflict"
    RECOVERY_PERMISSION_USED_AS_GRANT_CONFLICT = "recovery_permission_used_as_grant_conflict"
    RECOVERY_LIVE_EXECUTION_CONFLICT = "recovery_live_execution_conflict"
    HOT_SWITCH_PERMISSION_MISSING_SWITCH_BOUNDARY_CONFLICT = "hot_switch_permission_missing_switch_boundary_conflict"
    HOT_SWITCH_PERMISSION_MISSING_READINESS_CONFLICT = "hot_switch_permission_missing_readiness_conflict"
    HOT_SWITCH_PERMISSION_MISSING_PRE_CHECKPOINT_CONFLICT = "hot_switch_permission_missing_pre_checkpoint_conflict"
    HOT_SWITCH_PERMISSION_MISSING_POST_OBSERVATION_CONFLICT = "hot_switch_permission_missing_post_observation_conflict"
    HOT_SWITCH_PERMISSION_MISSING_ROLLBACK_ROUTE_CONFLICT = "hot_switch_permission_missing_rollback_route_conflict"
    HOT_SWITCH_PERMISSION_MISSING_DEPENDENCY_COMPATIBILITY_CONFLICT = "hot_switch_permission_missing_dependency_compatibility_conflict"
    HOT_SWITCH_PERMISSION_MISSING_RESOURCE_BOUNDARY_CONFLICT = "hot_switch_permission_missing_resource_boundary_conflict"
    HOT_SWITCH_PERMISSION_MISSING_CREDENTIAL_BOUNDARY_CONFLICT = "hot_switch_permission_missing_credential_boundary_conflict"
    HOT_SWITCH_PERMISSION_MISSING_DATA_BOUNDARY_CONFLICT = "hot_switch_permission_missing_data_boundary_conflict"
    HOT_SWITCH_PERMISSION_USED_AS_GRANT_CONFLICT = "hot_switch_permission_used_as_grant_conflict"
    HOT_SWITCH_LIVE_EXECUTION_CONFLICT = "hot_switch_live_execution_conflict"
    ROLLBACK_PERMISSION_MISSING_ANCHOR_CONFLICT = "rollback_permission_missing_anchor_conflict"
    ROLLBACK_PERMISSION_MISSING_ROUTE_CONFLICT = "rollback_permission_missing_route_conflict"
    ROLLBACK_PERMISSION_MISSING_CHECKPOINT_CONFLICT = "rollback_permission_missing_checkpoint_conflict"
    ROLLBACK_PERMISSION_MISSING_RECOVERY_POINT_CONFLICT = "rollback_permission_missing_recovery_point_conflict"
    ROLLBACK_PERMISSION_MISSING_VALIDATION_CONFLICT = "rollback_permission_missing_validation_conflict"
    ROLLBACK_PERMISSION_MISSING_REGRESSION_CONFLICT = "rollback_permission_missing_regression_conflict"
    ROLLBACK_PERMISSION_MISSING_POLICY_CONFLICT = "rollback_permission_missing_policy_conflict"
    ROLLBACK_PERMISSION_MISSING_APPROVAL_CONFLICT = "rollback_permission_missing_approval_conflict"
    ROLLBACK_PERMISSION_USED_AS_GRANT_CONFLICT = "rollback_permission_used_as_grant_conflict"
    ROLLBACK_LIVE_EXECUTION_CONFLICT = "rollback_live_execution_conflict"
    REPLAY_PERMISSION_MISSING_COMPATIBILITY_CONFLICT = "replay_permission_missing_compatibility_conflict"
    REPLAY_PERMISSION_MISSING_OLD_EVENT_REDACTION_CONFLICT = "replay_permission_missing_old_event_redaction_conflict"
    REPLAY_PERMISSION_MISSING_DATA_MINIMIZATION_CONFLICT = "replay_permission_missing_data_minimization_conflict"
    REPLAY_PERMISSION_MISSING_RESOURCE_GUARD_CONFLICT = "replay_permission_missing_resource_guard_conflict"
    REPLAY_PERMISSION_MISSING_CREDENTIAL_POLICY_CONFLICT = "replay_permission_missing_credential_policy_conflict"
    REPLAY_PERMISSION_MISSING_POLICY_CONFLICT = "replay_permission_missing_policy_conflict"
    REPLAY_PERMISSION_MISSING_EVIDENCE_CONFLICT = "replay_permission_missing_evidence_conflict"
    REPLAY_PERMISSION_USED_AS_GRANT_CONFLICT = "replay_permission_used_as_grant_conflict"
    REPLAY_LIVE_EXECUTION_CONFLICT = "replay_live_execution_conflict"
    PHASE5_BOUNDARY_USED_AS_LIVE_PERMISSION_CONFLICT = "phase5_boundary_used_as_live_permission_conflict"
    PHASE5_QUALITY_GATE_USED_AS_EXECUTION_AUTHORIZATION_CONFLICT = "phase5_quality_gate_used_as_execution_authorization_conflict"
    PHASE5_SWITCH_BOUNDARY_USED_AS_LIVE_SWITCH_CONFLICT = "phase5_switch_boundary_used_as_live_switch_conflict"
    PHASE5_RESOURCE_BOUNDARY_USED_AS_LIVE_QUOTA_CONFLICT = "phase5_resource_boundary_used_as_live_quota_conflict"
    PHASE5_CREDENTIAL_BOUNDARY_USED_AS_LIVE_CREDENTIAL_CONFLICT = "phase5_credential_boundary_used_as_live_credential_conflict"
    PHASE5_DATA_GOVERNANCE_USED_AS_LIVE_DATA_ACCESS_CONFLICT = "phase5_data_governance_used_as_live_data_access_conflict"
    PHASE4_LIFECYCLE_USED_AS_RUNTIME_STATE_CONFLICT = "phase4_lifecycle_used_as_runtime_state_conflict"
    PHASE3_REGISTRY_USED_AS_RUNTIME_REGISTRY_CONFLICT = "phase3_registry_used_as_runtime_registry_conflict"
    L6_PLUGIN_IMPLEMENTATION_CONFLICT = "l6_plugin_implementation_conflict"
    LEGACY_RUNTIME_CONFLICT = "legacy_runtime_conflict"
    AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT = "audit_evidence_chain_missing_conflict"
    PUBLIC_PROJECTION_LEAK_CONFLICT = "public_projection_leak_conflict"


def _tuple(value: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, tuple):
        return tuple(value)
    if isinstance(value, list):
        return tuple(value)
    raise ValueError("expected tuple/list declaration refs")


def _has_ref(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_refs(values: tuple[str, ...]) -> bool:
    return isinstance(values, tuple) and len(values) > 0 and all(isinstance(item, str) and bool(item.strip()) for item in values)


def _check_refs(values: tuple[str, ...], field_name: str) -> None:
    ensure_ref_items(values, field_name)


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


def has_live_health_or_permission_locator(value: Any) -> bool:
    for item in _walk_values(value):
        stripped = item.strip()
        lowered = stripped.lower()
        if any(fragment.lower() in lowered for fragment in _LIVE_LOCATOR_FRAGMENTS):
            return True
        if stripped.startswith(("/", "./", "../", "~", "C:\\", "D:\\")):
            return True
        if stripped.endswith((".log", ".py", ".sh", ".bat", ".exe", ".sql")):
            return True
        if "/" in stripped or "\\" in stripped:
            return True
        if lowered.startswith(("token=", "api_key=", "password=", "secret=", "bearer ", "sk-", "akia")):
            return True
    return False


def phase6_public_text_is_safe(value: Any) -> bool:
    if has_live_health_or_permission_locator(value):
        return False
    if suspicious_credential_value_paths(value):
        return False
    lowered = "\n".join(_walk_values(value)).lower()
    forbidden = (
        "metric_value",
        "live_metric",
        "process_id",
        "database_uri",
        "raw_log",
        "raw_metric",
        "permit object",
        "lease object",
        "confirmation ticket",
        "token object",
        "checkpoint payload",
        "rollback patch",
        "replay event payload",
        "migration script",
    )
    return not any(item in lowered for item in forbidden)


def has_forbidden_phase6_method(obj: Any) -> bool:
    return any(callable(getattr(obj, name, None)) for name in _EXECUTION_METHOD_NAMES)


def has_forbidden_phase6_field_name(obj: Any) -> bool:
    if hasattr(obj, "__dataclass_fields__"):
        return any(name in _LIVE_FIELD_NAMES for name in obj.__dataclass_fields__)
    return False


def phase6_declaration_digest(value: Any, digest_fields: tuple[str, ...] = tuple()) -> str:
    payload = stable_primitive(value)
    if isinstance(payload, dict):
        for field_name in digest_fields + (
            "report_digest",
            "disposition_digest",
            "permission_digest",
            "audit_digest",
            "projection_digest",
        ):
            payload.pop(field_name, None)
    return stable_digest(payload)


@dataclass(frozen=True, slots=True)
class PluginPhase6Conflict:
    conflict_ref: str
    kind: PluginPhase6ConflictKind
    severity: PluginPhase6ConflictSeverity
    message: str
    field_path: str = ""
    blocking: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase6_health_permission"
    detected_by_ref: str = "detector:l5_phase6_validator"

    def __post_init__(self) -> None:
        ensure_ref_text(self.conflict_ref, "PluginPhase6Conflict.conflict_ref")
        if not isinstance(self.kind, PluginPhase6ConflictKind):
            raise ValueError("PluginPhase6Conflict.kind must be PluginPhase6ConflictKind")
        if not isinstance(self.severity, PluginPhase6ConflictSeverity):
            raise ValueError("PluginPhase6Conflict.severity must be PluginPhase6ConflictSeverity")
        ensure_short_text(self.message, "PluginPhase6Conflict.message")
        ensure_short_text(self.field_path, "PluginPhase6Conflict.field_path", 256)
        ensure_bool(self.blocking, "PluginPhase6Conflict.blocking")
        ensure_ref_items(self.evidence_refs, "PluginPhase6Conflict.evidence_refs")
        ensure_ref_text(self.rule_source_ref, "PluginPhase6Conflict.rule_source_ref")
        ensure_ref_text(self.detected_by_ref, "PluginPhase6Conflict.detected_by_ref")
        if self.severity in (PluginPhase6ConflictSeverity.P0, PluginPhase6ConflictSeverity.P1) and not self.blocking:
            raise ValueError("P0/P1 phase6 conflicts must be blocking")


@dataclass(frozen=True, slots=True)
class _Phase6Base:
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    approval_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    source_layer: str = PHASE6_PHASE
    severity: str = "p3"
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    redaction_state: str = "redacted"

    def _check_base(self, class_name: str) -> None:
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref", "source_layer", "redaction_state"):
            ensure_ref_text(getattr(self, name), f"{class_name}.{name}", required=False)
        for name in ("policy_refs", "evidence_refs", "provenance_refs", "risk_tags"):
            ensure_ref_items(getattr(self, name), f"{class_name}.{name}")
        ensure_short_text(self.severity, f"{class_name}.severity", 32)


def _base_missing(obj: Any) -> tuple[str, ...]:
    missing: list[str] = []
    for name in ("actor_ref", "scope_ref", "trace_ref", "evidence_refs", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
        value = getattr(obj, name, "")
        if isinstance(value, tuple):
            if not _has_refs(value):
                missing.append(name)
        elif not _has_ref(value):
            missing.append(name)
    policy_ref = getattr(obj, "policy_ref", "")
    policy_refs = getattr(obj, "policy_refs", tuple())
    if not _has_ref(policy_ref) and not _has_refs(policy_refs):
        missing.append("policy_ref/policy_refs")
    return tuple(missing)


def _conflict(kind: PluginPhase6ConflictKind, severity: PluginPhase6ConflictSeverity, field_path: str, message: str, evidence_refs: tuple[str, ...] = tuple()) -> PluginPhase6Conflict:
    return PluginPhase6Conflict(
        conflict_ref=f"conflict:l5_phase6:{kind.value}:{field_path or 'root'}",
        kind=kind,
        severity=severity,
        message=message,
        field_path=field_path,
        blocking=severity in (PluginPhase6ConflictSeverity.P0, PluginPhase6ConflictSeverity.P1),
        evidence_refs=evidence_refs,
    )


@dataclass(frozen=True, slots=True)
class PluginHealthSignalDeclaration(_Phase6Base):
    health_signal_ref: str = ""
    registry_key_ref: str = ""
    lifecycle_ref: str = ""
    mount_decl_ref: str = ""
    isolation_boundary_ref: str = ""
    trust_boundary_ref: str = ""
    resource_boundary_ref: str = ""
    signal_kind_ref: str = ""
    signal_source_ref: str = ""
    signal_semantics_ref: str = ""
    health_status_kind_ref: str = ""
    no_live_probe_ref: str = ""
    no_metric_collection_ref: str = ""
    health_signal_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginHealthSignalDeclaration")
        for name in ("health_signal_ref", "registry_key_ref", "lifecycle_ref", "mount_decl_ref", "isolation_boundary_ref", "trust_boundary_ref", "resource_boundary_ref", "signal_kind_ref", "signal_source_ref", "signal_semantics_ref", "health_status_kind_ref", "no_live_probe_ref", "no_metric_collection_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHealthSignalDeclaration.{name}", required=False)
        if not self.health_signal_digest:
            object.__setattr__(self, "health_signal_digest", phase6_declaration_digest(self, ("health_signal_digest",)))


@dataclass(frozen=True, slots=True)
class PluginHealthCheckDeclaration(_Phase6Base):
    health_check_decl_ref: str = ""
    registry_key_ref: str = ""
    health_signal_refs: tuple[str, ...] = field(default_factory=tuple)
    readiness_decl_ref: str = ""
    liveness_decl_ref: str = ""
    safety_decl_ref: str = ""
    degradation_decl_ref: str = ""
    recovery_needed_decl_ref: str = ""
    switch_blocking_decl_ref: str = ""
    rollback_needed_decl_ref: str = ""
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    required_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_decl_ref: str = ""
    health_event_refs: tuple[str, ...] = field(default_factory=tuple)
    health_check_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginHealthCheckDeclaration")
        for name in ("health_check_decl_ref", "registry_key_ref", "readiness_decl_ref", "liveness_decl_ref", "safety_decl_ref", "degradation_decl_ref", "recovery_needed_decl_ref", "switch_blocking_decl_ref", "rollback_needed_decl_ref", "required_approval_ref", "audit_decl_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHealthCheckDeclaration.{name}", required=False)
        for name in ("health_signal_refs", "required_policy_refs", "required_evidence_refs", "health_event_refs"):
            _check_refs(getattr(self, name), f"PluginHealthCheckDeclaration.{name}")
        if not self.health_check_digest:
            object.__setattr__(self, "health_check_digest", phase6_declaration_digest(self, ("health_check_digest",)))


@dataclass(frozen=True, slots=True)
class PluginHealthAssessmentReport(_Phase6Base):
    report_ref: str = ""
    phase: str = PHASE6_PHASE + "_HEALTH"
    checked_health_signal_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_health_check_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_registry_key_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    passed: bool = False
    health_summary_refs: tuple[str, ...] = field(default_factory=tuple)
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase6_health"
    detected_by_ref: str = "detector:l5_phase6_health_validator"
    report_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginHealthAssessmentReport")
        ensure_ref_text(self.report_ref, "PluginHealthAssessmentReport.report_ref", required=False)
        ensure_short_text(self.phase, "PluginHealthAssessmentReport.phase", 64)
        for name in ("checked_health_signal_refs", "checked_health_check_decl_refs", "checked_registry_key_refs", "conflict_refs", "health_summary_refs", "blocking_reasons"):
            _check_refs(getattr(self, name), f"PluginHealthAssessmentReport.{name}")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"PluginHealthAssessmentReport.{name} must be non-negative int")
        ensure_bool(self.passed, "PluginHealthAssessmentReport.passed")
        ensure_ref_text(self.rule_source_ref, "PluginHealthAssessmentReport.rule_source_ref")
        ensure_ref_text(self.detected_by_ref, "PluginHealthAssessmentReport.detected_by_ref")
        if self.passed and (self.p0_count or self.p1_count):
            raise ValueError("PluginHealthAssessmentReport cannot pass with P0/P1")
        if not self.report_digest:
            object.__setattr__(self, "report_digest", phase6_declaration_digest(self, ("report_digest",)))


@dataclass(frozen=True, slots=True)
class PluginIsolationDispositionDeclaration(_Phase6Base):
    disposition_decl_ref: str = ""
    registry_key_ref: str = ""
    lifecycle_ref: str = ""
    mount_decl_ref: str = ""
    health_report_ref: str = ""
    isolation_decl_ref: str = ""
    trust_boundary_ref: str = ""
    disposition_kind_ref: str = ""
    quarantine_decl_ref: str = ""
    disable_decl_ref: str = ""
    degrade_decl_ref: str = ""
    hold_decl_ref: str = ""
    block_mount_decl_ref: str = ""
    visibility_revoke_decl_ref: str = ""
    side_effect_containment_ref: str = ""
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    required_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_decl_ref: str = ""
    disposition_event_refs: tuple[str, ...] = field(default_factory=tuple)
    disposition_digest: str = ""

    def __post_init__(self) -> None:
        self._check_base("PluginIsolationDispositionDeclaration")
        for name in ("disposition_decl_ref", "registry_key_ref", "lifecycle_ref", "mount_decl_ref", "health_report_ref", "isolation_decl_ref", "trust_boundary_ref", "disposition_kind_ref", "quarantine_decl_ref", "disable_decl_ref", "degrade_decl_ref", "hold_decl_ref", "block_mount_decl_ref", "visibility_revoke_decl_ref", "side_effect_containment_ref", "required_approval_ref", "audit_decl_ref"):
            ensure_ref_text(getattr(self, name), f"PluginIsolationDispositionDeclaration.{name}", required=False)
        for name in ("required_policy_refs", "required_evidence_refs", "disposition_event_refs"):
            _check_refs(getattr(self, name), f"PluginIsolationDispositionDeclaration.{name}")
        if not self.disposition_digest:
            object.__setattr__(self, "disposition_digest", phase6_declaration_digest(self, ("disposition_digest",)))


@dataclass(frozen=True, slots=True)
class _PermissionPreconditionBase(_Phase6Base):
    registry_key_ref: str = ""
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    required_lease_ref: str = ""
    required_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    permission_not_grant_ref: str = "decl:permission_precondition_not_grant"
    audit_decl_ref: str = ""
    permission_digest: str = ""

    def _check_permission_base(self, class_name: str) -> None:
        self._check_base(class_name)
        for name in ("registry_key_ref", "required_approval_ref", "required_lease_ref", "permission_not_grant_ref", "audit_decl_ref"):
            ensure_ref_text(getattr(self, name), f"{class_name}.{name}", required=False)
        for name in ("required_policy_refs", "required_evidence_refs"):
            _check_refs(getattr(self, name), f"{class_name}.{name}")


@dataclass(frozen=True, slots=True)
class PluginRecoveryPermissionPreconditionDeclaration(_PermissionPreconditionBase):
    recovery_permission_decl_ref: str = ""
    recovery_plan_ref: str = ""
    recovery_point_ref: str = ""
    checkpoint_ref: str = ""
    rollback_anchor_ref: str = ""
    validation_ref: str = ""
    regression_ref: str = ""
    isolation_disposition_ref: str = ""
    credential_boundary_ref: str = ""
    data_governance_boundary_ref: str = ""
    resource_boundary_ref: str = ""
    trust_boundary_ref: str = ""
    capability_token_boundary_ref: str = ""
    no_live_recovery_ref: str = ""
    recovery_permission_event_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self._check_permission_base("PluginRecoveryPermissionPreconditionDeclaration")
        for name in ("recovery_permission_decl_ref", "recovery_plan_ref", "recovery_point_ref", "checkpoint_ref", "rollback_anchor_ref", "validation_ref", "regression_ref", "isolation_disposition_ref", "credential_boundary_ref", "data_governance_boundary_ref", "resource_boundary_ref", "trust_boundary_ref", "capability_token_boundary_ref", "no_live_recovery_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRecoveryPermissionPreconditionDeclaration.{name}", required=False)
        _check_refs(self.recovery_permission_event_refs, "PluginRecoveryPermissionPreconditionDeclaration.recovery_permission_event_refs")
        if not self.permission_digest:
            object.__setattr__(self, "permission_digest", phase6_declaration_digest(self, ("permission_digest",)))


@dataclass(frozen=True, slots=True)
class PluginHotSwitchPermissionPreconditionDeclaration(_PermissionPreconditionBase):
    hot_switch_permission_decl_ref: str = ""
    hot_switch_decl_ref: str = ""
    switch_boundary_decl_ref: str = ""
    switch_readiness_ref: str = ""
    pre_switch_checkpoint_ref: str = ""
    post_switch_observation_ref: str = ""
    switch_rollback_route_ref: str = ""
    dependency_compatibility_matrix_ref: str = ""
    credential_boundary_ref: str = ""
    data_governance_boundary_ref: str = ""
    resource_boundary_ref: str = ""
    trust_boundary_ref: str = ""
    no_live_hot_switch_ref: str = ""
    hot_switch_permission_event_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self._check_permission_base("PluginHotSwitchPermissionPreconditionDeclaration")
        for name in ("hot_switch_permission_decl_ref", "hot_switch_decl_ref", "switch_boundary_decl_ref", "switch_readiness_ref", "pre_switch_checkpoint_ref", "post_switch_observation_ref", "switch_rollback_route_ref", "dependency_compatibility_matrix_ref", "credential_boundary_ref", "data_governance_boundary_ref", "resource_boundary_ref", "trust_boundary_ref", "no_live_hot_switch_ref"):
            ensure_ref_text(getattr(self, name), f"PluginHotSwitchPermissionPreconditionDeclaration.{name}", required=False)
        _check_refs(self.hot_switch_permission_event_refs, "PluginHotSwitchPermissionPreconditionDeclaration.hot_switch_permission_event_refs")
        if not self.permission_digest:
            object.__setattr__(self, "permission_digest", phase6_declaration_digest(self, ("permission_digest",)))


@dataclass(frozen=True, slots=True)
class PluginRollbackPermissionPreconditionDeclaration(_PermissionPreconditionBase):
    rollback_permission_decl_ref: str = ""
    rollback_anchor_ref: str = ""
    rollback_route_ref: str = ""
    recovery_point_ref: str = ""
    checkpoint_ref: str = ""
    dependency_decl_ref: str = ""
    data_governance_boundary_ref: str = ""
    resource_boundary_ref: str = ""
    credential_boundary_ref: str = ""
    trust_boundary_ref: str = ""
    validation_ref: str = ""
    regression_ref: str = ""
    no_live_rollback_ref: str = ""
    rollback_permission_event_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self._check_permission_base("PluginRollbackPermissionPreconditionDeclaration")
        for name in ("rollback_permission_decl_ref", "rollback_anchor_ref", "rollback_route_ref", "recovery_point_ref", "checkpoint_ref", "dependency_decl_ref", "data_governance_boundary_ref", "resource_boundary_ref", "credential_boundary_ref", "trust_boundary_ref", "validation_ref", "regression_ref", "no_live_rollback_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRollbackPermissionPreconditionDeclaration.{name}", required=False)
        _check_refs(self.rollback_permission_event_refs, "PluginRollbackPermissionPreconditionDeclaration.rollback_permission_event_refs")
        if not self.permission_digest:
            object.__setattr__(self, "permission_digest", phase6_declaration_digest(self, ("permission_digest",)))


@dataclass(frozen=True, slots=True)
class PluginReplayPermissionPreconditionDeclaration(_PermissionPreconditionBase):
    replay_permission_decl_ref: str = ""
    replay_compatibility_ref: str = ""
    old_event_replay_compatibility_ref: str = ""
    data_governance_boundary_ref: str = ""
    replay_data_minimization_ref: str = ""
    old_event_redaction_policy_ref: str = ""
    resource_boundary_ref: str = ""
    replay_resource_guard_ref: str = ""
    credential_boundary_ref: str = ""
    replay_credential_policy_ref: str = ""
    no_live_replay_ref: str = ""
    replay_permission_event_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self._check_permission_base("PluginReplayPermissionPreconditionDeclaration")
        for name in ("replay_permission_decl_ref", "replay_compatibility_ref", "old_event_replay_compatibility_ref", "data_governance_boundary_ref", "replay_data_minimization_ref", "old_event_redaction_policy_ref", "resource_boundary_ref", "replay_resource_guard_ref", "credential_boundary_ref", "replay_credential_policy_ref", "no_live_replay_ref"):
            ensure_ref_text(getattr(self, name), f"PluginReplayPermissionPreconditionDeclaration.{name}", required=False)
        _check_refs(self.replay_permission_event_refs, "PluginReplayPermissionPreconditionDeclaration.replay_permission_event_refs")
        if not self.permission_digest:
            object.__setattr__(self, "permission_digest", phase6_declaration_digest(self, ("permission_digest",)))


def _count_conflicts(conflicts: tuple[PluginPhase6Conflict, ...]) -> tuple[int, int, int, int]:
    return (
        sum(1 for item in conflicts if item.severity == PluginPhase6ConflictSeverity.P0),
        sum(1 for item in conflicts if item.severity == PluginPhase6ConflictSeverity.P1),
        sum(1 for item in conflicts if item.severity == PluginPhase6ConflictSeverity.P2),
        sum(1 for item in conflicts if item.severity == PluginPhase6ConflictSeverity.P3),
    )


def _conflict_refs(conflicts: tuple[PluginPhase6Conflict, ...]) -> tuple[str, ...]:
    return tuple(item.conflict_ref for item in conflicts)


class PluginHealthValidator:
    """Pure health declaration validator; returns reports only."""

    def assess(
        self,
        *,
        health_signals: tuple[PluginHealthSignalDeclaration, ...],
        health_checks: tuple[PluginHealthCheckDeclaration, ...],
        report_ref: str = "report:l5_phase6_health",
    ) -> PluginHealthAssessmentReport:
        conflicts: list[PluginPhase6Conflict] = []
        for signal in health_signals:
            conflicts.extend(self._signal_conflicts(signal))
        for check in health_checks:
            conflicts.extend(self._check_conflicts(check))
        p0, p1, p2, p3 = _count_conflicts(tuple(conflicts))
        passed = p0 == 0 and p1 == 0
        return PluginHealthAssessmentReport(
            report_ref=report_ref,
            checked_health_signal_refs=tuple(signal.health_signal_ref for signal in health_signals),
            checked_health_check_decl_refs=tuple(check.health_check_decl_ref for check in health_checks),
            checked_registry_key_refs=tuple(sorted({signal.registry_key_ref for signal in health_signals if signal.registry_key_ref})),
            conflict_refs=_conflict_refs(tuple(conflicts)),
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            passed=passed,
            health_summary_refs=("summary:health_assessment",),
            blocking_reasons=tuple(conflict.message for conflict in conflicts if conflict.blocking),
            actor_ref="actor:l5_phase6_validator",
            scope_ref="scope:l5_phase6",
            trace_ref="trace:l5_phase6_health",
            policy_ref="policy:l5_phase6_health",
            approval_ref="approval:l5_phase6_not_ticket",
            evidence_refs=("redacted_evidence:l5_phase6_health",),
            provenance_refs=("provenance:l5_phase6_health",),
            responsibility_chain_ref="responsibility:l5_phase6_health",
            accountability_ref="accountability:l5_phase6_health",
            tamper_evidence_ref="tamper:l5_phase6_health",
        )

    def _signal_conflicts(self, signal: PluginHealthSignalDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts: list[PluginPhase6Conflict] = []
        for field_name in _base_missing(signal):
            conflicts.append(_conflict(PluginPhase6ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase6ConflictSeverity.P1, field_name, "health signal missing responsibility-chain field", signal.evidence_refs))
        required = (
            ("health_signal_ref", PluginPhase6ConflictKind.HEALTH_MISSING_SIGNAL_REF_CONFLICT),
            ("signal_semantics_ref", PluginPhase6ConflictKind.HEALTH_MISSING_SIGNAL_SEMANTICS_CONFLICT),
            ("health_status_kind_ref", PluginPhase6ConflictKind.HEALTH_MISSING_STATUS_KIND_CONFLICT),
            ("no_live_probe_ref", PluginPhase6ConflictKind.HEALTH_MISSING_NO_LIVE_PROBE_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(signal, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", signal.evidence_refs))
        if not _has_refs(signal.evidence_refs):
            conflicts.append(_conflict(PluginPhase6ConflictKind.HEALTH_MISSING_EVIDENCE_CONFLICT, PluginPhase6ConflictSeverity.P1, "evidence_refs", "health signal requires redacted evidence refs"))
        if has_live_health_or_permission_locator(signal) or has_forbidden_phase6_field_name(signal) or has_forbidden_phase6_method(signal):
            conflicts.append(_conflict(PluginPhase6ConflictKind.HEALTH_LIVE_PROBE_CONFLICT, PluginPhase6ConflictSeverity.P0, "health_signal", "health signal contains live probe or locator material", signal.evidence_refs))
        return tuple(conflicts)

    def _check_conflicts(self, check: PluginHealthCheckDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts: list[PluginPhase6Conflict] = []
        for field_name in _base_missing(check):
            conflicts.append(_conflict(PluginPhase6ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase6ConflictSeverity.P1, field_name, "health check missing responsibility-chain field", check.evidence_refs))
        required = (
            ("readiness_decl_ref", PluginPhase6ConflictKind.HEALTH_CHECK_MISSING_READINESS_DECL_CONFLICT),
            ("liveness_decl_ref", PluginPhase6ConflictKind.HEALTH_CHECK_MISSING_LIVENESS_DECL_CONFLICT),
            ("safety_decl_ref", PluginPhase6ConflictKind.HEALTH_CHECK_MISSING_SAFETY_DECL_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(check, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", check.evidence_refs))
        if not _has_refs(check.required_policy_refs):
            conflicts.append(_conflict(PluginPhase6ConflictKind.HEALTH_CHECK_MISSING_REQUIRED_POLICY_CONFLICT, PluginPhase6ConflictSeverity.P1, "required_policy_refs", "health check requires policy refs", check.evidence_refs))
        if not _has_refs(check.required_evidence_refs):
            conflicts.append(_conflict(PluginPhase6ConflictKind.HEALTH_CHECK_MISSING_REQUIRED_EVIDENCE_CONFLICT, PluginPhase6ConflictSeverity.P1, "required_evidence_refs", "health check requires evidence refs", check.evidence_refs))
        if has_live_health_or_permission_locator(check) or has_forbidden_phase6_method(check):
            conflicts.append(_conflict(PluginPhase6ConflictKind.HEALTH_CHECK_EXEC_CONFLICT, PluginPhase6ConflictSeverity.P0, "health_check", "health check contains live execution material", check.evidence_refs))
        return tuple(conflicts)


class PluginIsolationDispositionValidator:
    """Pure validator for isolation-disposition declarations."""

    def review(self, declaration: PluginIsolationDispositionDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts: list[PluginPhase6Conflict] = []
        for field_name in _base_missing(declaration):
            conflicts.append(_conflict(PluginPhase6ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase6ConflictSeverity.P1, field_name, "disposition missing responsibility-chain field", declaration.evidence_refs))
        required = (
            ("disposition_kind_ref", PluginPhase6ConflictKind.DISPOSITION_MISSING_KIND_CONFLICT),
            ("health_report_ref", PluginPhase6ConflictKind.DISPOSITION_MISSING_HEALTH_REPORT_CONFLICT),
            ("isolation_decl_ref", PluginPhase6ConflictKind.DISPOSITION_MISSING_ISOLATION_BOUNDARY_CONFLICT),
            ("required_approval_ref", PluginPhase6ConflictKind.DISPOSITION_MISSING_APPROVAL_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(declaration, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", declaration.evidence_refs))
        if not _has_refs(declaration.required_policy_refs):
            conflicts.append(_conflict(PluginPhase6ConflictKind.DISPOSITION_MISSING_POLICY_CONFLICT, PluginPhase6ConflictSeverity.P1, "required_policy_refs", "disposition requires policy refs", declaration.evidence_refs))
        if not _has_refs(declaration.required_evidence_refs):
            conflicts.append(_conflict(PluginPhase6ConflictKind.DISPOSITION_MISSING_EVIDENCE_CONFLICT, PluginPhase6ConflictSeverity.P1, "required_evidence_refs", "disposition requires evidence refs", declaration.evidence_refs))
        if has_live_health_or_permission_locator(declaration) or has_forbidden_phase6_method(declaration):
            conflicts.append(_conflict(PluginPhase6ConflictKind.DISPOSITION_LIVE_ISOLATE_CONFLICT, PluginPhase6ConflictSeverity.P0, "disposition", "disposition contains live isolation or mutation material", declaration.evidence_refs))
        return tuple(conflicts)


class _PermissionValidatorBase:
    def _common_permission_conflicts(self, declaration: _PermissionPreconditionBase, *, prefix_kind: PluginPhase6ConflictKind) -> list[PluginPhase6Conflict]:
        conflicts: list[PluginPhase6Conflict] = []
        for field_name in _base_missing(declaration):
            conflicts.append(_conflict(PluginPhase6ConflictKind.AUDIT_EVIDENCE_CHAIN_MISSING_CONFLICT, PluginPhase6ConflictSeverity.P1, field_name, "permission precondition missing responsibility-chain field", declaration.evidence_refs))
        if not _has_refs(declaration.required_policy_refs):
            conflicts.append(_conflict(prefix_kind, PluginPhase6ConflictSeverity.P1, "required_policy_refs", "permission precondition requires policy refs", declaration.evidence_refs))
        if not _has_ref(declaration.required_approval_ref):
            conflicts.append(_conflict(prefix_kind, PluginPhase6ConflictSeverity.P1, "required_approval_ref", "permission precondition requires approval ref", declaration.evidence_refs))
        if not _has_ref(declaration.required_lease_ref):
            conflicts.append(_conflict(prefix_kind, PluginPhase6ConflictSeverity.P1, "required_lease_ref", "permission precondition requires lease ref", declaration.evidence_refs))
        if not _has_refs(declaration.required_evidence_refs):
            conflicts.append(_conflict(prefix_kind, PluginPhase6ConflictSeverity.P1, "required_evidence_refs", "permission precondition requires evidence refs", declaration.evidence_refs))
        if not _has_ref(declaration.permission_not_grant_ref):
            conflicts.append(_conflict(PluginPhase6ConflictKind.PHASE5_QUALITY_GATE_USED_AS_EXECUTION_AUTHORIZATION_CONFLICT, PluginPhase6ConflictSeverity.P1, "permission_not_grant_ref", "permission precondition must declare non-grant semantics", declaration.evidence_refs))
        if has_live_health_or_permission_locator(declaration) or has_forbidden_phase6_method(declaration):
            conflicts.append(_conflict(PluginPhase6ConflictKind.PHASE5_BOUNDARY_USED_AS_LIVE_PERMISSION_CONFLICT, PluginPhase6ConflictSeverity.P0, "permission", "permission precondition contains live execution or locator material", declaration.evidence_refs))
        return conflicts


class PluginRecoveryPermissionValidator(_PermissionValidatorBase):
    def review(self, declaration: PluginRecoveryPermissionPreconditionDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts = self._common_permission_conflicts(declaration, prefix_kind=PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_POLICY_CONFLICT)
        required = (
            ("recovery_plan_ref", PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_RECOVERY_PLAN_CONFLICT),
            ("checkpoint_ref", PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_CHECKPOINT_CONFLICT),
            ("recovery_point_ref", PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_RECOVERY_POINT_CONFLICT),
            ("rollback_anchor_ref", PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_ROLLBACK_ANCHOR_CONFLICT),
            ("validation_ref", PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_VALIDATION_CONFLICT),
            ("regression_ref", PluginPhase6ConflictKind.RECOVERY_PERMISSION_MISSING_REGRESSION_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(declaration, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", declaration.evidence_refs))
        return tuple(conflicts)


class PluginHotSwitchPermissionValidator(_PermissionValidatorBase):
    def review(self, declaration: PluginHotSwitchPermissionPreconditionDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts = self._common_permission_conflicts(declaration, prefix_kind=PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_READINESS_CONFLICT)
        required = (
            ("switch_boundary_decl_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_SWITCH_BOUNDARY_CONFLICT),
            ("switch_readiness_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_READINESS_CONFLICT),
            ("pre_switch_checkpoint_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_PRE_CHECKPOINT_CONFLICT),
            ("post_switch_observation_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_POST_OBSERVATION_CONFLICT),
            ("switch_rollback_route_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_ROLLBACK_ROUTE_CONFLICT),
            ("dependency_compatibility_matrix_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_DEPENDENCY_COMPATIBILITY_CONFLICT),
            ("resource_boundary_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_RESOURCE_BOUNDARY_CONFLICT),
            ("credential_boundary_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_CREDENTIAL_BOUNDARY_CONFLICT),
            ("data_governance_boundary_ref", PluginPhase6ConflictKind.HOT_SWITCH_PERMISSION_MISSING_DATA_BOUNDARY_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(declaration, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", declaration.evidence_refs))
        return tuple(conflicts)


class PluginRollbackPermissionValidator(_PermissionValidatorBase):
    def review(self, declaration: PluginRollbackPermissionPreconditionDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts = self._common_permission_conflicts(declaration, prefix_kind=PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_POLICY_CONFLICT)
        required = (
            ("rollback_anchor_ref", PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_ANCHOR_CONFLICT),
            ("rollback_route_ref", PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_ROUTE_CONFLICT),
            ("checkpoint_ref", PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_CHECKPOINT_CONFLICT),
            ("recovery_point_ref", PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_RECOVERY_POINT_CONFLICT),
            ("validation_ref", PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_VALIDATION_CONFLICT),
            ("regression_ref", PluginPhase6ConflictKind.ROLLBACK_PERMISSION_MISSING_REGRESSION_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(declaration, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", declaration.evidence_refs))
        return tuple(conflicts)


class PluginReplayPermissionValidator(_PermissionValidatorBase):
    def review(self, declaration: PluginReplayPermissionPreconditionDeclaration) -> tuple[PluginPhase6Conflict, ...]:
        conflicts = self._common_permission_conflicts(declaration, prefix_kind=PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_POLICY_CONFLICT)
        required = (
            ("replay_compatibility_ref", PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_COMPATIBILITY_CONFLICT),
            ("old_event_redaction_policy_ref", PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_OLD_EVENT_REDACTION_CONFLICT),
            ("replay_data_minimization_ref", PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_DATA_MINIMIZATION_CONFLICT),
            ("replay_resource_guard_ref", PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_RESOURCE_GUARD_CONFLICT),
            ("replay_credential_policy_ref", PluginPhase6ConflictKind.REPLAY_PERMISSION_MISSING_CREDENTIAL_POLICY_CONFLICT),
        )
        for field_name, kind in required:
            if not _has_ref(getattr(declaration, field_name)):
                conflicts.append(_conflict(kind, PluginPhase6ConflictSeverity.P1, field_name, f"{field_name} is required", declaration.evidence_refs))
        return tuple(conflicts)


@dataclass(frozen=True, slots=True)
class PluginPhase6QualityGateDecision:
    decision_ref: str
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    health_declaration_passed: bool = False
    health_assessment_passed: bool = False
    health_no_live_probe_passed: bool = False
    isolation_disposition_declaration_passed: bool = False
    isolation_no_live_disposition_passed: bool = False
    recovery_permission_precondition_passed: bool = False
    hot_switch_permission_precondition_passed: bool = False
    rollback_permission_precondition_passed: bool = False
    replay_permission_precondition_passed: bool = False
    permission_not_grant_passed: bool = False
    phase5_boundary_compatibility_passed: bool = False
    phase4_lifecycle_compatibility_passed: bool = False
    phase3_registry_compatibility_passed: bool = False
    public_projection_safety_passed: bool = False
    public_projection_second_leak_test_passed: bool = False
    audit_evidence_chain_passed: bool = False
    forbidden_scan_passed: bool = False
    compileall_passed: bool = False
    collect_only_passed: bool = False
    targeted_pytest_passed: bool = False
    plugin_host_subset_passed: bool = False
    plugin_host_subset_non_empty: bool = False
    full_pytest_passed: bool = False
    hash_compare_passed: bool = False
    test_inventory_compare_passed: bool = False
    allow_enter_l5_phase7: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_index_refs: tuple[str, ...] = field(default_factory=tuple)
    rule_source_ref: str = "rule:l5_phase6_quality_gate"
    detected_by_ref: str = "detector:l5_phase6_quality_gate"
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    approval_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    phase: str = PHASE6_PHASE
    quality_gate_digest: str = ""

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "PluginPhase6QualityGateDecision.decision_ref")
        for name in ("rule_source_ref", "detected_by_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref", "phase"):
            ensure_ref_text(getattr(self, name), f"PluginPhase6QualityGateDecision.{name}", required=False)
        for name in ("blocking_reasons", "evidence_index_refs", "regression_index_refs", "policy_refs", "provenance_refs"):
            ensure_ref_items(getattr(self, name), f"PluginPhase6QualityGateDecision.{name}")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 0:
                raise ValueError(f"PluginPhase6QualityGateDecision.{name} must be non-negative int")
        boolean_fields = (
            "health_declaration_passed",
            "health_assessment_passed",
            "health_no_live_probe_passed",
            "isolation_disposition_declaration_passed",
            "isolation_no_live_disposition_passed",
            "recovery_permission_precondition_passed",
            "hot_switch_permission_precondition_passed",
            "rollback_permission_precondition_passed",
            "replay_permission_precondition_passed",
            "permission_not_grant_passed",
            "phase5_boundary_compatibility_passed",
            "phase4_lifecycle_compatibility_passed",
            "phase3_registry_compatibility_passed",
            "public_projection_safety_passed",
            "public_projection_second_leak_test_passed",
            "audit_evidence_chain_passed",
            "forbidden_scan_passed",
            "compileall_passed",
            "collect_only_passed",
            "targeted_pytest_passed",
            "plugin_host_subset_passed",
            "plugin_host_subset_non_empty",
            "full_pytest_passed",
            "hash_compare_passed",
            "test_inventory_compare_passed",
        )
        for name in boolean_fields:
            ensure_bool(getattr(self, name), f"PluginPhase6QualityGateDecision.{name}")
        derived = self.p0_count == 0 and self.p1_count == 0 and all(getattr(self, name) for name in boolean_fields)
        object.__setattr__(self, "allow_enter_l5_phase7", derived)
        if not self.quality_gate_digest:
            object.__setattr__(self, "quality_gate_digest", phase6_declaration_digest(self, ("quality_gate_digest",)))


class PluginPhase6QualityGate:
    def decide(self, **kwargs: Any) -> PluginPhase6QualityGateDecision:
        return PluginPhase6QualityGateDecision(**kwargs)


@dataclass(frozen=True, slots=True)
class PluginPhase6PublicProjection:
    projection_ref: str
    health_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    health_assessment_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    isolation_disposition_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    recovery_permission_precondition_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    hot_switch_permission_precondition_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    rollback_permission_precondition_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    replay_permission_precondition_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    conflict_counts: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    status_text: str = "declaration_only"
    redacted_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    handoff_summary: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    trace_ref: str = ""
    responsibility_chain_ref: str = ""
    projection_digest: str = ""
    phase: str = PHASE6_PHASE

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "PluginPhase6PublicProjection.projection_ref")
        for name in ("risk_tags", "redacted_evidence_refs"):
            ensure_ref_items(getattr(self, name), f"PluginPhase6PublicProjection.{name}")
        for name in ("status_text", "trace_ref", "responsibility_chain_ref", "phase"):
            ensure_ref_text(getattr(self, name), f"PluginPhase6PublicProjection.{name}", required=False)
        for name in (
            "health_summary",
            "health_assessment_summary",
            "isolation_disposition_summary",
            "recovery_permission_precondition_summary",
            "hot_switch_permission_precondition_summary",
            "rollback_permission_precondition_summary",
            "replay_permission_precondition_summary",
            "conflict_counts",
            "quality_gate_summary",
            "handoff_summary",
        ):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                raise ValueError(f"PluginPhase6PublicProjection.{name} must be tuple")
        if not phase6_public_text_is_safe(self):
            raise ValueError("PluginPhase6PublicProjection contains unsafe disclosure")
        if not self.projection_digest:
            object.__setattr__(self, "projection_digest", phase6_declaration_digest(self, ("projection_digest",)))


class PluginPhase6ProjectionBuilder:
    def make_projection(
        self,
        *,
        health_report: PluginHealthAssessmentReport,
        disposition: PluginIsolationDispositionDeclaration,
        recovery_permission: PluginRecoveryPermissionPreconditionDeclaration,
        hot_switch_permission: PluginHotSwitchPermissionPreconditionDeclaration,
        rollback_permission: PluginRollbackPermissionPreconditionDeclaration,
        replay_permission: PluginReplayPermissionPreconditionDeclaration,
        quality_gate: PluginPhase6QualityGateDecision | None = None,
    ) -> PluginPhase6PublicProjection:
        return PluginPhase6PublicProjection(
            projection_ref="projection:l5_phase6",
            health_summary=(("health_signal_count", str(len(health_report.checked_health_signal_refs))), ("health_status_kind_refs", "redacted_status_refs")),
            health_assessment_summary=(("report_ref", health_report.report_ref), ("passed", str(health_report.passed)), ("p0_count", str(health_report.p0_count)), ("p1_count", str(health_report.p1_count)), ("blocking_reason_count", str(len(health_report.blocking_reasons)))),
            isolation_disposition_summary=(("disposition_decl_ref", disposition.disposition_decl_ref), ("disposition_kind_ref", disposition.disposition_kind_ref), ("required_approval_ref", disposition.required_approval_ref)),
            recovery_permission_precondition_summary=(("permission_decl_ref", recovery_permission.recovery_permission_decl_ref), ("precondition_kind_ref", "recovery"), ("required_lease_ref", recovery_permission.required_lease_ref), ("permission_not_grant_ref", recovery_permission.permission_not_grant_ref)),
            hot_switch_permission_precondition_summary=(("permission_decl_ref", hot_switch_permission.hot_switch_permission_decl_ref), ("precondition_kind_ref", "hot_switch"), ("required_lease_ref", hot_switch_permission.required_lease_ref), ("permission_not_grant_ref", hot_switch_permission.permission_not_grant_ref)),
            rollback_permission_precondition_summary=(("permission_decl_ref", rollback_permission.rollback_permission_decl_ref), ("precondition_kind_ref", "rollback"), ("required_lease_ref", rollback_permission.required_lease_ref), ("permission_not_grant_ref", rollback_permission.permission_not_grant_ref)),
            replay_permission_precondition_summary=(("permission_decl_ref", replay_permission.replay_permission_decl_ref), ("precondition_kind_ref", "replay"), ("required_evidence_count", str(len(replay_permission.required_evidence_refs))), ("permission_not_grant_ref", replay_permission.permission_not_grant_ref)),
            conflict_counts=(("p0", str(quality_gate.p0_count) if quality_gate else "0"), ("p1", str(quality_gate.p1_count) if quality_gate else "0")),
            risk_tags=tuple(sorted(set(disposition.risk_tags + recovery_permission.risk_tags + hot_switch_permission.risk_tags + rollback_permission.risk_tags + replay_permission.risk_tags))),
            status_text="declaration_only_not_authorization",
            redacted_evidence_refs=("redacted_evidence:l5_phase6_projection",),
            quality_gate_summary=(("allow_enter_l5_phase7", str(quality_gate.allow_enter_l5_phase7) if quality_gate else "unknown"),),
            handoff_summary=(("phase7_consumable", "health and permission precondition declarations only"),),
            trace_ref="trace:l5_phase6_projection",
            responsibility_chain_ref="responsibility:l5_phase6_projection",
        )


@dataclass(frozen=True, slots=True)
class PluginPhase6AuditIndex:
    audit_index_ref: str
    registry_key_refs: tuple[str, ...] = field(default_factory=tuple)
    health_signal_refs: tuple[str, ...] = field(default_factory=tuple)
    health_check_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    health_assessment_report_refs: tuple[str, ...] = field(default_factory=tuple)
    isolation_disposition_refs: tuple[str, ...] = field(default_factory=tuple)
    recovery_permission_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    hot_switch_permission_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    rollback_permission_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    replay_permission_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_report_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_report_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_decision_refs: tuple[str, ...] = field(default_factory=tuple)
    public_projection_refs: tuple[str, ...] = field(default_factory=tuple)
    health_event_refs: tuple[str, ...] = field(default_factory=tuple)
    disposition_event_refs: tuple[str, ...] = field(default_factory=tuple)
    permission_event_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_event_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_event_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate_event_ref: str = ""
    handoff_event_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    audit_digest: str = ""
    phase: str = PHASE6_PHASE

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_index_ref, "PluginPhase6AuditIndex.audit_index_ref")
        for name in ("quality_gate_event_ref", "handoff_event_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref", "phase"):
            ensure_ref_text(getattr(self, name), f"PluginPhase6AuditIndex.{name}", required=False)
        for name in (
            "registry_key_refs",
            "health_signal_refs",
            "health_check_decl_refs",
            "health_assessment_report_refs",
            "isolation_disposition_refs",
            "recovery_permission_decl_refs",
            "hot_switch_permission_decl_refs",
            "rollback_permission_decl_refs",
            "replay_permission_decl_refs",
            "validation_report_refs",
            "conflict_report_refs",
            "quality_gate_decision_refs",
            "public_projection_refs",
            "health_event_refs",
            "disposition_event_refs",
            "permission_event_refs",
            "conflict_event_refs",
            "validation_event_refs",
            "evidence_refs",
            "provenance_refs",
            "policy_refs",
        ):
            ensure_ref_items(getattr(self, name), f"PluginPhase6AuditIndex.{name}")
        if not self.audit_digest:
            object.__setattr__(self, "audit_digest", phase6_declaration_digest(self, ("audit_digest",)))


class PluginPhase6AuditIndexBuilder:
    def make_index(
        self,
        *,
        health_report: PluginHealthAssessmentReport,
        projection: PluginPhase6PublicProjection,
        quality_gate: PluginPhase6QualityGateDecision,
    ) -> PluginPhase6AuditIndex:
        return PluginPhase6AuditIndex(
            audit_index_ref="audit_index:l5_phase6",
            registry_key_refs=health_report.checked_registry_key_refs,
            health_signal_refs=health_report.checked_health_signal_refs,
            health_check_decl_refs=health_report.checked_health_check_decl_refs,
            health_assessment_report_refs=(health_report.report_ref,),
            quality_gate_decision_refs=(quality_gate.decision_ref,),
            public_projection_refs=(projection.projection_ref,),
            health_event_refs=("event:health_signal_declared", "event:health_check_declared"),
            disposition_event_refs=("event:isolation_disposition_declared",),
            permission_event_refs=("event:permission_precondition_declared",),
            conflict_event_refs=("event:phase6_conflicts_checked",),
            validation_event_refs=("event:phase6_validation_completed",),
            quality_gate_event_ref="event:phase6_quality_gate_decided",
            handoff_event_ref="event:phase6_handoff_declared",
            evidence_refs=health_report.evidence_refs,
            provenance_refs=health_report.provenance_refs,
            actor_ref=health_report.actor_ref,
            scope_ref=health_report.scope_ref,
            trace_ref=health_report.trace_ref,
            policy_ref=health_report.policy_ref,
            approval_ref=health_report.approval_ref,
            responsibility_chain_ref=health_report.responsibility_chain_ref,
            accountability_ref=health_report.accountability_ref,
            tamper_evidence_ref=health_report.tamper_evidence_ref,
        )


__all__ = (
    "PHASE6_PHASE",
    "PluginHealthSignalDeclaration",
    "PluginHealthCheckDeclaration",
    "PluginHealthAssessmentReport",
    "PluginIsolationDispositionDeclaration",
    "PluginRecoveryPermissionPreconditionDeclaration",
    "PluginHotSwitchPermissionPreconditionDeclaration",
    "PluginRollbackPermissionPreconditionDeclaration",
    "PluginReplayPermissionPreconditionDeclaration",
    "PluginPhase6Conflict",
    "PluginPhase6ConflictKind",
    "PluginPhase6ConflictSeverity",
    "PluginHealthValidator",
    "PluginIsolationDispositionValidator",
    "PluginRecoveryPermissionValidator",
    "PluginHotSwitchPermissionValidator",
    "PluginRollbackPermissionValidator",
    "PluginReplayPermissionValidator",
    "PluginPhase6QualityGate",
    "PluginPhase6QualityGateDecision",
    "PluginPhase6PublicProjection",
    "PluginPhase6ProjectionBuilder",
    "PluginPhase6AuditIndex",
    "PluginPhase6AuditIndexBuilder",
    "has_forbidden_phase6_field_name",
    "has_forbidden_phase6_method",
    "has_live_health_or_permission_locator",
    "phase6_declaration_digest",
    "phase6_public_text_is_safe",
)
