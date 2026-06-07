"""L5 phase 4 lifecycle and mount declaration shells.

These objects describe plugin lifecycle and mount declarations only. They do
not load plugins, hold runtime state, mutate registries, execute transitions,
create sandboxes, call L4 adapters, or expose model-callable tools.
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


class PluginLifecycleStatusKind(str, Enum):
    DECLARED = "declared"
    REGISTRY_VALIDATED = "registry_validated"
    MOUNT_DECLARED = "mount_declared"
    MOUNT_VALIDATION_FAILED = "mount_validation_failed"
    ENABLE_DECLARED = "enable_declared"
    DISABLE_DECLARED = "disable_declared"
    ISOLATE_DECLARED = "isolate_declared"
    DEGRADE_DECLARED = "degrade_declared"
    RECOVERY_DECLARED = "recovery_declared"
    ROLLBACK_DECLARED = "rollback_declared"
    HOT_SWITCH_DECLARED = "hot_switch_declared"
    MIGRATION_DECLARED = "migration_declared"
    REPLAY_DECLARED = "replay_declared"
    DEPRECATED_DECLARED = "deprecated_declared"
    ARCHIVED_DECLARED = "archived_declared"
    SWITCH_READINESS_DECLARED = "switch_readiness_declared"
    PRE_SWITCH_CHECKPOINT_DECLARED = "pre_switch_checkpoint_declared"
    POST_SWITCH_OBSERVATION_DECLARED = "post_switch_observation_declared"
    SWITCH_ROLLBACK_ROUTE_DECLARED = "switch_rollback_route_declared"
    COMPATIBILITY_CHECKED_DECLARED = "compatibility_checked_declared"
    BREAKING_CHANGE_CHECKED_DECLARED = "breaking_change_checked_declared"


_RUNTIME_STATUS_TEXTS = {
    "running",
    "started",
    "stopped_by_runtime",
    "loaded_module",
    "imported",
    "executed",
    "mounted_live",
    "hot_switched_live",
    "migrated_live",
    "rollback_applied",
    "replay_executed",
}

_FORBIDDEN_METHOD_NAMES = frozenset(
    (
        "apply",
        "transition_to",
        "next_state",
        "mutate",
        "commit",
        "validate_and_apply",
        "advance",
        "promote",
        "demote",
        "activate",
        "deactivate",
        "execute",
        "run",
        "start",
        "stop",
        "mount",
        "unmount",
        "enable",
        "disable",
        "isolate",
        "rollback",
        "hot_switch",
        "migrate",
        "replay",
        "repair",
        "diagnose",
        "recover",
        "compensate",
        "validate",
        "regress",
        "postmortem",
        "write",
        "patch",
    )
)

_ALLOWED_TRANSITIONS = frozenset(
    (
        (PluginLifecycleStatusKind.DECLARED, PluginLifecycleStatusKind.REGISTRY_VALIDATED),
        (PluginLifecycleStatusKind.REGISTRY_VALIDATED, PluginLifecycleStatusKind.MOUNT_DECLARED),
        (PluginLifecycleStatusKind.MOUNT_DECLARED, PluginLifecycleStatusKind.ENABLE_DECLARED),
        (PluginLifecycleStatusKind.MOUNT_DECLARED, PluginLifecycleStatusKind.DISABLE_DECLARED),
        (PluginLifecycleStatusKind.MOUNT_DECLARED, PluginLifecycleStatusKind.ISOLATE_DECLARED),
        (PluginLifecycleStatusKind.MOUNT_DECLARED, PluginLifecycleStatusKind.DEGRADE_DECLARED),
        (PluginLifecycleStatusKind.ENABLE_DECLARED, PluginLifecycleStatusKind.RECOVERY_DECLARED),
        (PluginLifecycleStatusKind.ENABLE_DECLARED, PluginLifecycleStatusKind.ROLLBACK_DECLARED),
        (PluginLifecycleStatusKind.ENABLE_DECLARED, PluginLifecycleStatusKind.HOT_SWITCH_DECLARED),
        (PluginLifecycleStatusKind.ENABLE_DECLARED, PluginLifecycleStatusKind.MIGRATION_DECLARED),
        (PluginLifecycleStatusKind.ENABLE_DECLARED, PluginLifecycleStatusKind.REPLAY_DECLARED),
        (PluginLifecycleStatusKind.RECOVERY_DECLARED, PluginLifecycleStatusKind.ROLLBACK_DECLARED),
        (PluginLifecycleStatusKind.ROLLBACK_DECLARED, PluginLifecycleStatusKind.ARCHIVED_DECLARED),
        (PluginLifecycleStatusKind.HOT_SWITCH_DECLARED, PluginLifecycleStatusKind.SWITCH_READINESS_DECLARED),
        (PluginLifecycleStatusKind.HOT_SWITCH_DECLARED, PluginLifecycleStatusKind.PRE_SWITCH_CHECKPOINT_DECLARED),
        (PluginLifecycleStatusKind.HOT_SWITCH_DECLARED, PluginLifecycleStatusKind.POST_SWITCH_OBSERVATION_DECLARED),
        (PluginLifecycleStatusKind.HOT_SWITCH_DECLARED, PluginLifecycleStatusKind.SWITCH_ROLLBACK_ROUTE_DECLARED),
        (PluginLifecycleStatusKind.MIGRATION_DECLARED, PluginLifecycleStatusKind.COMPATIBILITY_CHECKED_DECLARED),
        (PluginLifecycleStatusKind.MIGRATION_DECLARED, PluginLifecycleStatusKind.BREAKING_CHANGE_CHECKED_DECLARED),
        (PluginLifecycleStatusKind.REPLAY_DECLARED, PluginLifecycleStatusKind.ARCHIVED_DECLARED),
    )
)

_ALLOWED_SURFACE_KINDS = frozenset(
    (
        "control_plane_decl",
        "execution_plane_decl",
        "observation_plane_decl",
        "public_projection_decl",
        "audit_projection_decl",
        "l6_plugin_surface_decl",
    )
)

_LIVE_ENTRY_MARKERS = (
    "://",
    "\\",
    "/",
    "->",
    "<function",
    " at 0x",
    "::",
    " module ",
    "python ",
    "bash ",
    "sh ",
    "cmd.exe",
    "powershell",
)


def normalize_status_kind(value: PluginLifecycleStatusKind | str) -> PluginLifecycleStatusKind:
    if isinstance(value, PluginLifecycleStatusKind):
        return value
    try:
        return PluginLifecycleStatusKind(value)
    except ValueError as exc:
        raise ValueError(f"unsupported lifecycle status kind: {value!r}") from exc


def lifecycle_declaration_digest(value: Any) -> str:
    payload = stable_primitive(value)
    if isinstance(payload, dict):
        for excluded in (
            "lifecycle_digest",
            "mount_declaration_digest",
            "state_machine_digest",
            "quality_gate_digest",
            "projection_digest",
            "self_healing_digest",
            "recovery_plan_digest",
        ):
            payload.pop(excluded, None)
    return stable_digest(payload)


def is_runtime_status_text(value: str) -> bool:
    return value in _RUNTIME_STATUS_TEXTS


def is_live_entry_text(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    lowered = value.lower()
    if any(marker in lowered for marker in _LIVE_ENTRY_MARKERS):
        return True
    if lowered.startswith(("http:", "https:", "file:", "ws:", "wss:", "postgres:", "mysql:", "sqlite:")):
        return True
    if "=" in lowered and any(prefix in lowered for prefix in ("token=", "api_key=", "password=", "secret=")):
        return True
    # Compact import-path-like strings are not opaque declaration refs.
    if "." in value and not value.startswith(("ref:", "decl:", "policy:", "audit:", "evidence:", "mount:")):
        return True
    return False


def has_forbidden_method(cls: type) -> tuple[str, ...]:
    return tuple(sorted(name for name in _FORBIDDEN_METHOD_NAMES if callable(cls.__dict__.get(name))))


@dataclass(frozen=True, slots=True)
class PluginLifecycleStateRef:
    lifecycle_ref: str
    registry_key_ref: str
    status_kind: PluginLifecycleStatusKind | str = PluginLifecycleStatusKind.DECLARED
    status_text: str = "declared only"
    source_layer: str = "L5"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    policy_ref: str = ""
    responsibility_chain_ref: str = ""
    audit_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    lifecycle_event_refs: tuple[str, ...] = field(default_factory=tuple)
    lifecycle_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.lifecycle_ref, "PluginLifecycleStateRef.lifecycle_ref")
        ensure_ref_text(self.registry_key_ref, "PluginLifecycleStateRef.registry_key_ref")
        object.__setattr__(self, "status_kind", normalize_status_kind(self.status_kind))
        ensure_short_text(self.status_text, "PluginLifecycleStateRef.status_text")
        ensure_short_text(self.source_layer, "PluginLifecycleStateRef.source_layer", 64)
        ensure_ref_items(self.evidence_refs, "PluginLifecycleStateRef.evidence_refs")
        ensure_ref_items(self.provenance_refs, "PluginLifecycleStateRef.provenance_refs")
        ensure_ref_items(self.lifecycle_event_refs, "PluginLifecycleStateRef.lifecycle_event_refs")
        for name in ("trace_ref", "policy_ref", "responsibility_chain_ref", "audit_ref", "actor_ref", "scope_ref", "approval_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleStateRef.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginLifecycleStateRef.schema_version")
        if not self.lifecycle_digest:
            object.__setattr__(self, "lifecycle_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginLifecycleTransitionRule:
    transition_ref: str
    from_status_kind: PluginLifecycleStatusKind | str
    to_status_kind: PluginLifecycleStatusKind | str
    trigger_ref: str
    guard_refs: tuple[str, ...] = field(default_factory=tuple)
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    required_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_event_ref: str = ""
    rollback_anchor_ref: str = ""
    migration_ref: str = ""
    hot_switch_decl_ref: str = ""
    replay_compatibility_ref: str = ""
    breaking_change_policy_ref: str = ""
    switch_readiness_ref: str = ""
    pre_switch_checkpoint_ref: str = ""
    post_switch_observation_ref: str = ""
    switch_rollback_route_ref: str = ""
    compatibility_check_ref: str = ""
    breaking_change_check_ref: str = ""
    severity: str = "p3"
    reversible_declared: bool = False
    side_effect_free_declared: bool = True
    responsibility_chain_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    lifecycle_event_refs: tuple[str, ...] = field(default_factory=tuple)
    transition_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.transition_ref, "PluginLifecycleTransitionRule.transition_ref")
        object.__setattr__(self, "from_status_kind", normalize_status_kind(self.from_status_kind))
        object.__setattr__(self, "to_status_kind", normalize_status_kind(self.to_status_kind))
        ensure_ref_text(self.trigger_ref, "PluginLifecycleTransitionRule.trigger_ref")
        for name in ("guard_refs", "required_policy_refs", "required_evidence_refs", "provenance_refs", "evidence_refs", "lifecycle_event_refs"):
            ensure_ref_items(getattr(self, name), f"PluginLifecycleTransitionRule.{name}")
        for name in (
            "required_approval_ref", "audit_event_ref", "rollback_anchor_ref", "migration_ref", "hot_switch_decl_ref",
            "replay_compatibility_ref", "breaking_change_policy_ref", "switch_readiness_ref", "pre_switch_checkpoint_ref",
            "post_switch_observation_ref", "switch_rollback_route_ref", "compatibility_check_ref", "breaking_change_check_ref",
            "responsibility_chain_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "accountability_ref",
            "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleTransitionRule.{name}", required=False)
        ensure_short_text(self.severity, "PluginLifecycleTransitionRule.severity", 16)
        ensure_bool(self.reversible_declared, "PluginLifecycleTransitionRule.reversible_declared")
        ensure_bool(self.side_effect_free_declared, "PluginLifecycleTransitionRule.side_effect_free_declared")
        ensure_schema_version(self.schema_version, "PluginLifecycleTransitionRule.schema_version")
        if not self.transition_digest:
            object.__setattr__(self, "transition_digest", lifecycle_declaration_digest(self))

    @property
    def status_pair(self) -> tuple[PluginLifecycleStatusKind, PluginLifecycleStatusKind]:
        return (self.from_status_kind, self.to_status_kind)


@dataclass(frozen=True, slots=True)
class PluginLifecycleStateMachine:
    state_machine_ref: str
    registry_snapshot_ref: str
    lifecycle_version: str
    allowed_transition_refs: tuple[str, ...] = field(default_factory=tuple)
    forbidden_transition_refs: tuple[str, ...] = field(default_factory=tuple)
    transition_rules: tuple[PluginLifecycleTransitionRule, ...] = field(default_factory=tuple)
    default_status_kind: PluginLifecycleStatusKind | str = PluginLifecycleStatusKind.DECLARED
    terminal_status_kinds: tuple[PluginLifecycleStatusKind | str, ...] = field(default_factory=lambda: (PluginLifecycleStatusKind.ARCHIVED_DECLARED,))
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_ref: str = ""
    trace_ref: str = ""
    tamper_evidence_ref: str = ""
    responsibility_chain_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    lifecycle_event_refs: tuple[str, ...] = field(default_factory=tuple)
    state_machine_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.state_machine_ref, "PluginLifecycleStateMachine.state_machine_ref")
        ensure_ref_text(self.registry_snapshot_ref, "PluginLifecycleStateMachine.registry_snapshot_ref")
        ensure_short_text(self.lifecycle_version, "PluginLifecycleStateMachine.lifecycle_version", 64)
        ensure_ref_items(self.allowed_transition_refs, "PluginLifecycleStateMachine.allowed_transition_refs")
        ensure_ref_items(self.forbidden_transition_refs, "PluginLifecycleStateMachine.forbidden_transition_refs")
        for rule in self.transition_rules:
            if not isinstance(rule, PluginLifecycleTransitionRule):
                raise ValueError("PluginLifecycleStateMachine.transition_rules must contain PluginLifecycleTransitionRule")
        object.__setattr__(self, "default_status_kind", normalize_status_kind(self.default_status_kind))
        object.__setattr__(self, "terminal_status_kinds", tuple(normalize_status_kind(item) for item in self.terminal_status_kinds))
        for name in ("evidence_refs", "provenance_refs", "lifecycle_event_refs"):
            ensure_ref_items(getattr(self, name), f"PluginLifecycleStateMachine.{name}")
        for name in ("policy_ref", "trace_ref", "tamper_evidence_ref", "responsibility_chain_ref", "actor_ref", "scope_ref", "approval_ref", "accountability_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleStateMachine.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginLifecycleStateMachine.schema_version")
        if not self.state_machine_digest:
            object.__setattr__(self, "state_machine_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginMountSurfaceRef:
    host_surface_ref: str
    surface_kind: str
    surface_summary: str = ""
    boundary_ref: str = ""
    scope_ref: str = ""
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    public_visibility_summary: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    actor_ref: str = ""
    trace_ref: str = ""
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    surface_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.host_surface_ref, "PluginMountSurfaceRef.host_surface_ref")
        ensure_short_text(self.surface_kind, "PluginMountSurfaceRef.surface_kind", 64)
        if self.surface_kind not in _ALLOWED_SURFACE_KINDS:
            raise ValueError("PluginMountSurfaceRef.surface_kind must be declarative")
        ensure_short_text(self.surface_summary, "PluginMountSurfaceRef.surface_summary")
        ensure_short_text(self.public_visibility_summary, "PluginMountSurfaceRef.public_visibility_summary")
        for name in ("boundary_ref", "scope_ref", "actor_ref", "trace_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginMountSurfaceRef.{name}", required=False)
        for name in ("policy_refs", "evidence_refs", "provenance_refs", "event_kind_refs"):
            ensure_ref_items(getattr(self, name), f"PluginMountSurfaceRef.{name}")
        ensure_schema_version(self.schema_version, "PluginMountSurfaceRef.schema_version")
        if not self.surface_digest:
            object.__setattr__(self, "surface_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginMountDeclaration:
    mount_decl_ref: str
    registry_key_ref: str
    lifecycle_ref: str
    host_surface_ref: str
    mount_point_ref: str
    boundary_ref: str
    scope_ref: str = ""
    visible_to_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    permission_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    resource_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    credential_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    data_governance_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    audit_decl_ref: str = ""
    health_decl_ref: str = ""
    rollback_anchor_ref: str = ""
    version_slot_ref: str = ""
    migration_ref: str = ""
    hot_switch_decl_ref: str = ""
    replay_compatibility_ref: str = ""
    breaking_change_policy_ref: str = ""
    switch_readiness_ref: str = ""
    pre_switch_checkpoint_ref: str = ""
    post_switch_observation_ref: str = ""
    switch_rollback_route_ref: str = ""
    compatibility_check_ref: str = ""
    breaking_change_check_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    responsibility_chain_ref: str = ""
    actor_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    mount_event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    mount_declaration_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("mount_decl_ref", "registry_key_ref", "lifecycle_ref", "host_surface_ref", "mount_point_ref"):
            ensure_ref_text(getattr(self, name), f"PluginMountDeclaration.{name}")
        ensure_ref_text(self.boundary_ref, "PluginMountDeclaration.boundary_ref", required=False)
        for name in ("scope_ref", "audit_decl_ref", "health_decl_ref", "rollback_anchor_ref", "version_slot_ref", "migration_ref", "hot_switch_decl_ref", "replay_compatibility_ref", "breaking_change_policy_ref", "switch_readiness_ref", "pre_switch_checkpoint_ref", "post_switch_observation_ref", "switch_rollback_route_ref", "compatibility_check_ref", "breaking_change_check_ref", "trace_ref", "responsibility_chain_ref", "actor_ref", "approval_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginMountDeclaration.{name}", required=False)
        for name in ("visible_to_refs", "policy_refs", "permission_decl_refs", "resource_decl_refs", "credential_decl_refs", "data_governance_decl_refs", "evidence_refs", "provenance_refs", "mount_event_kind_refs"):
            ensure_ref_items(getattr(self, name), f"PluginMountDeclaration.{name}")
        ensure_short_text(self.summary, "PluginMountDeclaration.summary")
        ensure_schema_version(self.schema_version, "PluginMountDeclaration.schema_version")
        if not self.mount_declaration_digest:
            object.__setattr__(self, "mount_declaration_digest", lifecycle_declaration_digest(self))


def lifecycle_required_chain_fields_present(obj: object, fields_to_check: tuple[str, ...]) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in fields_to_check:
        value = getattr(obj, field_name, None)
        if value == "" or value == tuple() or value is None:
            missing.append(field_name)
    return tuple(missing)


def is_allowed_transition(rule: PluginLifecycleTransitionRule) -> bool:
    return rule.status_pair in _ALLOWED_TRANSITIONS


__all__ = (
    "PluginLifecycleStatusKind",
    "PluginLifecycleStateRef",
    "PluginLifecycleTransitionRule",
    "PluginLifecycleStateMachine",
    "PluginMountDeclaration",
    "PluginMountSurfaceRef",
    "has_forbidden_method",
    "is_allowed_transition",
    "is_live_entry_text",
    "is_runtime_status_text",
    "lifecycle_declaration_digest",
    "lifecycle_required_chain_fields_present",
)
