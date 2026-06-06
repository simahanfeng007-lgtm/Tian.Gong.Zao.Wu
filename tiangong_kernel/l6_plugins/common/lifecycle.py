"""L6 plugin lifecycle declarations.

Lifecycle values are declarations only. They do not transition plugins, enable
plugins, disable plugins, isolate plugins, recover plugins, migrate plugins, or
perform hot switch behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest, stable_primitive


class L6PluginLifecycleState(str, Enum):
    DECLARED = "declared"
    REGISTERED = "registered"
    VALIDATED = "validated"
    HOST_ACCEPTED = "host_accepted"
    GOVERNANCE_PENDING = "governance_pending"
    PERMISSION_PENDING = "permission_pending"
    BUDGET_PENDING = "budget_pending"
    CREDENTIAL_PENDING = "credential_pending"
    READY_FOR_ORCHESTRATION = "ready_for_orchestration"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ISOLATED = "isolated"
    DISABLED = "disabled"
    MIGRATION_PENDING = "migration_pending"
    ROLLBACK_PENDING = "rollback_pending"
    RETIRED = "retired"
    ARCHIVED = "archived"


_TERMINAL_STATES = frozenset((L6PluginLifecycleState.DISABLED, L6PluginLifecycleState.ISOLATED, L6PluginLifecycleState.RETIRED, L6PluginLifecycleState.ARCHIVED))

_ALLOWED_DECLARED_TRANSITIONS = frozenset(
    (
        (L6PluginLifecycleState.DECLARED, L6PluginLifecycleState.REGISTERED),
        (L6PluginLifecycleState.REGISTERED, L6PluginLifecycleState.VALIDATED),
        (L6PluginLifecycleState.VALIDATED, L6PluginLifecycleState.HOST_ACCEPTED),
        (L6PluginLifecycleState.HOST_ACCEPTED, L6PluginLifecycleState.GOVERNANCE_PENDING),
        (L6PluginLifecycleState.GOVERNANCE_PENDING, L6PluginLifecycleState.PERMISSION_PENDING),
        (L6PluginLifecycleState.PERMISSION_PENDING, L6PluginLifecycleState.BUDGET_PENDING),
        (L6PluginLifecycleState.BUDGET_PENDING, L6PluginLifecycleState.CREDENTIAL_PENDING),
        (L6PluginLifecycleState.CREDENTIAL_PENDING, L6PluginLifecycleState.READY_FOR_ORCHESTRATION),
        (L6PluginLifecycleState.READY_FOR_ORCHESTRATION, L6PluginLifecycleState.ACTIVE),
        (L6PluginLifecycleState.ACTIVE, L6PluginLifecycleState.DEGRADED),
        (L6PluginLifecycleState.ACTIVE, L6PluginLifecycleState.ISOLATED),
        (L6PluginLifecycleState.ACTIVE, L6PluginLifecycleState.DISABLED),
        (L6PluginLifecycleState.ACTIVE, L6PluginLifecycleState.MIGRATION_PENDING),
        (L6PluginLifecycleState.ACTIVE, L6PluginLifecycleState.ROLLBACK_PENDING),
        (L6PluginLifecycleState.DEGRADED, L6PluginLifecycleState.ISOLATED),
        (L6PluginLifecycleState.DEGRADED, L6PluginLifecycleState.DISABLED),
        (L6PluginLifecycleState.MIGRATION_PENDING, L6PluginLifecycleState.DEGRADED),
        (L6PluginLifecycleState.ROLLBACK_PENDING, L6PluginLifecycleState.DEGRADED),
        (L6PluginLifecycleState.DISABLED, L6PluginLifecycleState.RETIRED),
        (L6PluginLifecycleState.RETIRED, L6PluginLifecycleState.ARCHIVED),
    )
)


def normalize_lifecycle_state(value: L6PluginLifecycleState | str) -> L6PluginLifecycleState:
    if isinstance(value, L6PluginLifecycleState):
        return value
    try:
        return L6PluginLifecycleState(value)
    except ValueError as exc:
        raise ValueError(f"unsupported L6 lifecycle state: {value!r}") from exc


def is_declared_lifecycle_transition_allowed(from_state: L6PluginLifecycleState | str, to_state: L6PluginLifecycleState | str) -> bool:
    return (normalize_lifecycle_state(from_state), normalize_lifecycle_state(to_state)) in _ALLOWED_DECLARED_TRANSITIONS


@dataclass(frozen=True, slots=True)
class L6PluginLifecycleDeclaration:
    lifecycle_ref: str = "lifecycle:l6_plugin_default"
    current_state: L6PluginLifecycleState | str = L6PluginLifecycleState.DECLARED
    allowed_transition_refs: tuple[str, ...] = field(default_factory=lambda: ("lifecycle:declared_sequence_only",))
    l5_host_controls_terminal_states: bool = True
    plugin_self_unblocks_terminal_states: bool = False
    readiness_is_authorization: bool = False
    active_means_external_action_allowed: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.lifecycle_ref, "L6PluginLifecycleDeclaration.lifecycle_ref")
        object.__setattr__(self, "current_state", normalize_lifecycle_state(self.current_state))
        ensure_ref_items(self.allowed_transition_refs, "L6PluginLifecycleDeclaration.allowed_transition_refs", required=True)
        if not self.l5_host_controls_terminal_states:
            raise ValueError("L6 lifecycle terminal states must remain controlled by L5 host governance")
        if self.plugin_self_unblocks_terminal_states:
            raise ValueError("L6 plugin cannot self-unblock disabled or isolated states")
        if self.readiness_is_authorization:
            raise ValueError("L6 readiness cannot be treated as authorization")
        if self.active_means_external_action_allowed:
            raise ValueError("L6 active state cannot grant external action")
        ensure_ref_items(self.evidence_refs, "L6PluginLifecycleDeclaration.evidence_refs")
        ensure_schema_version(self.schema_version)

    @property
    def terminal_state_host_locked(self) -> bool:
        return self.current_state in _TERMINAL_STATES and self.l5_host_controls_terminal_states


def lifecycle_declaration_digest(value: L6PluginLifecycleDeclaration) -> str:
    return stable_digest(stable_primitive(value))

_PHASE2_LIFECYCLE_STATES = frozenset(
    (
        "declared",
        "manifest_validated",
        "registered_with_l5",
        "lifecycle_contract_validated",
        "event_contract_validated",
        "projection_contract_validated",
        "handoff_contract_validated",
        "admission_candidate",
        "admission_rejected",
        "admission_approved_declared",
        "orchestration_ready_declared",
        "active_declared",
        "degraded_declared",
        "isolated_declared",
        "disabled_declared",
        "deprecated_declared",
        "migration_required_declared",
        "migration_plan_declared",
        "rollback_route_declared",
        "hot_switch_readiness_declared",
        "replay_compatibility_declared",
        "contract_patch_candidate",
        "contract_patch_frozen",
        "archived_declared",
    )
)


@dataclass(frozen=True, slots=True)
class L6PluginLifecycleContract:
    lifecycle_contract_ref: str = "lifecycle:l6_phase2_lifecycle_contract"
    plugin_ref: str = "l6:plugin_ref"
    plugin_version_ref: str = "ref:l6_plugin_version"
    manifest_version_ref: str = "ref:l6_manifest_version"
    contract_version_ref: str = "ref:l6_contract_version"
    lifecycle_schema_version: str = L6_COMMON_SCHEMA_VERSION
    lifecycle_state: str = "declared"
    previous_state_ref: str = "lifecycle:l6_previous_state_ref"
    requested_transition_ref: str = "lifecycle:l6_requested_transition_ref"
    next_allowed_state_refs: tuple[str, ...] = field(default_factory=lambda: ("lifecycle:manifest_validated",))
    transition_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_phase2_lifecycle_transition",))
    transition_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase2_lifecycle",))
    supported_lifecycle_state_range: tuple[str, ...] = field(default_factory=lambda: ("lifecycle:declared", "lifecycle:archived_declared"))
    version_slot_ref: str = "ref:l6_version_slot"
    compatibility_matrix_ref: str = "ref:l6_compatibility_matrix"
    migration_policy_ref: str = "migration:l6_migration_policy"
    migration_plan_ref: str = "migration:l6_migration_plan"
    rollback_policy_ref: str = "rollback:l6_rollback_policy"
    rollback_anchor_ref: str = "rollback:l6_rollback_anchor"
    rollback_route_ref: str = "rollback:l6_rollback_route"
    hot_switch_policy_ref: str = "hotswitch:l6_hot_switch_policy"
    hot_switch_readiness_ref: str = "hotswitch:l6_hot_switch_readiness"
    replay_compatibility_ref: str = "ref:l6_replay_compatibility"
    breaking_change_assessment_ref: str = "ref:l6_breaking_change_assessment"
    deprecation_policy_ref: str = "policy:l6_deprecation_policy"
    tombstone_policy_ref: str = "policy:l6_tombstone_policy"
    l5_lifecycle_binding_ref: str = "l5:l6_lifecycle_binding"
    l5_quality_gate_ref: str = "l5:l6_quality_gate"
    audit_trace_envelope_ref: str = "audit:l6_phase2_lifecycle_trace"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase2_lifecycle",))
    trace_ref: str = "ref:l6_phase2_lifecycle_trace"
    responsibility_chain_ref: str = "responsibility:l6_phase2_lifecycle_chain"
    accountability_ref: str = "responsibility:l6_phase2_lifecycle_accountability"
    tamper_evidence_ref: str = "evidence:l6_phase2_lifecycle_tamper"
    public_projection_ref: str = "public:l6_phase2_lifecycle_projection"
    authorization_ref: str = ""
    active_is_permit: bool = False
    ready_for_orchestration_is_permit: bool = False
    registered_with_l5_is_tool_authorization: bool = False
    migration_plan_executes: bool = False
    rollback_route_executes: bool = False
    hot_switch_readiness_executes: bool = False
    replay_compatibility_executes: bool = False
    contract_patch_auto_applies: bool = False
    plugin_self_unblocks_isolated_disabled: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "lifecycle_contract_ref",
            "plugin_ref",
            "plugin_version_ref",
            "manifest_version_ref",
            "contract_version_ref",
            "previous_state_ref",
            "requested_transition_ref",
            "version_slot_ref",
            "compatibility_matrix_ref",
            "migration_policy_ref",
            "migration_plan_ref",
            "rollback_policy_ref",
            "rollback_anchor_ref",
            "rollback_route_ref",
            "hot_switch_policy_ref",
            "hot_switch_readiness_ref",
            "replay_compatibility_ref",
            "breaking_change_assessment_ref",
            "deprecation_policy_ref",
            "tombstone_policy_ref",
            "l5_lifecycle_binding_ref",
            "l5_quality_gate_ref",
            "audit_trace_envelope_ref",
            "trace_ref",
            "responsibility_chain_ref",
            "accountability_ref",
            "tamper_evidence_ref",
            "public_projection_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6PluginLifecycleContract.{field_name}")
        ensure_ref_text(self.authorization_ref, "L6PluginLifecycleContract.authorization_ref", required=False)
        ensure_schema_version(self.lifecycle_schema_version, "lifecycle_schema_version")
        if self.lifecycle_state not in _PHASE2_LIFECYCLE_STATES:
            raise ValueError("unsupported L6 phase2 lifecycle state")
        for field_name in (
            "next_allowed_state_refs",
            "transition_policy_refs",
            "transition_evidence_refs",
            "supported_lifecycle_state_range",
            "evidence_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6PluginLifecycleContract.{field_name}", required=field_name != "next_allowed_state_refs")
        inert_flags = (
            self.active_is_permit,
            self.ready_for_orchestration_is_permit,
            self.registered_with_l5_is_tool_authorization,
            self.migration_plan_executes,
            self.rollback_route_executes,
            self.hot_switch_readiness_executes,
            self.replay_compatibility_executes,
            self.contract_patch_auto_applies,
            self.plugin_self_unblocks_isolated_disabled,
        )
        if any(inert_flags):
            raise ValueError("L6 lifecycle contract states are declarations, not authorization or execution")
        ensure_schema_version(self.schema_version)

    @property
    def lifecycle_is_authorization(self) -> bool:
        return False

    @property
    def isolated_or_disabled_host_locked(self) -> bool:
        return self.lifecycle_state in {"isolated_declared", "disabled_declared"} and not self.plugin_self_unblocks_isolated_disabled

    @property
    def digest(self) -> str:
        return stable_digest(stable_primitive(self))
