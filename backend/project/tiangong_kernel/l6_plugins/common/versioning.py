"""L6 phase2 version, compatibility, migration, rollback, and replay declarations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from .audit import L6AuditTraceEnvelope


class L6ContractChangeKind(str, Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclass(frozen=True, slots=True)
class L6VersionedContractRef:
    contract_ref: str = "ref:l6_phase2_contract"
    contract_kind_ref: str = "ref:l6_phase2_contract_kind"
    schema_version_ref: str = "ref:l6_phase2_schema_version"
    contract_version_ref: str = "ref:l6_phase2_contract_version"
    public_projection_ref: str = "public:l6_phase2_contract_ref"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "contract_ref",
            "contract_kind_ref",
            "schema_version_ref",
            "contract_version_ref",
            "public_projection_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6VersionedContractRef.{field_name}")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True, slots=True)
class L6VersionedContractSet:
    contract_set_ref: str = "ref:l6_phase2_contract_set"
    lifecycle_contract_ref: str = "lifecycle:l6_phase2_lifecycle_contract"
    event_contract_ref: str = "event:l6_phase2_event_contract"
    projection_contract_ref: str = "projection:l6_phase2_projection_contract"
    handoff_contract_ref: str = "handoff:l6_phase2_handoff_contract"
    invocation_contract_ref: str = "ref:l6_phase2_invocation_contract"
    output_contract_ref: str = "ref:l6_phase2_output_contract"
    compatibility_matrix_ref: str = "ref:l6_phase2_compatibility_matrix"
    audit_trace_envelope_ref: str = "audit:l6_phase2_audit_trace"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "contract_set_ref",
            "lifecycle_contract_ref",
            "event_contract_ref",
            "projection_contract_ref",
            "handoff_contract_ref",
            "invocation_contract_ref",
            "output_contract_ref",
            "compatibility_matrix_ref",
            "audit_trace_envelope_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6VersionedContractSet.{field_name}")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True, slots=True)
class L6CompatibilityMatrix:
    matrix_ref: str = "ref:l6_phase2_compatibility_matrix"
    plugin_ref: str = "l6:plugin_ref"
    supported_lifecycle_state_range: tuple[str, ...] = field(default_factory=lambda: ("declared", "active_declared"))
    event_contract_range_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_phase2_event_range",))
    projection_contract_range_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase2_projection_range",))
    handoff_contract_range_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_phase2_handoff_range",))
    requires_migration_for_major_change: bool = True
    requires_rollback_route_for_major_change: bool = True
    requires_replay_compatibility_for_major_change: bool = True
    grants_permit: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.matrix_ref, "L6CompatibilityMatrix.matrix_ref")
        ensure_ref_text(self.plugin_ref, "L6CompatibilityMatrix.plugin_ref")
        for field_name in (
            "supported_lifecycle_state_range",
            "event_contract_range_refs",
            "projection_contract_range_refs",
            "handoff_contract_range_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6CompatibilityMatrix.{field_name}", required=True)
        for field_name in (
            "requires_migration_for_major_change",
            "requires_rollback_route_for_major_change",
            "requires_replay_compatibility_for_major_change",
            "grants_permit",
        ):
            ensure_bool(getattr(self, field_name), f"L6CompatibilityMatrix.{field_name}")
        if self.grants_permit:
            raise ValueError("L6 compatibility matrix is not a permit")
        ensure_schema_version(self.schema_version)

    def requires_governance_for(self, change_kind: L6ContractChangeKind | str) -> bool:
        kind = L6ContractChangeKind(change_kind)
        return kind is L6ContractChangeKind.MAJOR


@dataclass(frozen=True, slots=True)
class L6LifecycleVersionPolicy:
    policy_ref: str = "policy:l6_phase2_lifecycle_version_policy"
    migration_policy_ref: str = "migration:l6_phase2_lifecycle_migration_policy"
    rollback_policy_ref: str = "rollback:l6_phase2_lifecycle_rollback_policy"
    hot_switch_policy_ref: str = "hotswitch:l6_phase2_lifecycle_hot_switch_policy"
    replay_compatibility_ref: str = "ref:l6_phase2_lifecycle_replay_compatibility"
    applies_policy: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "policy_ref",
            "migration_policy_ref",
            "rollback_policy_ref",
            "hot_switch_policy_ref",
            "replay_compatibility_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6LifecycleVersionPolicy.{field_name}")
        if self.applies_policy:
            raise ValueError("L6 lifecycle version policy is declarative only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6EventSchemaVersionPolicy:
    policy_ref: str = "policy:l6_phase2_event_schema_version_policy"
    upcast_policy_ref: str = "policy:l6_phase2_event_upcast_policy"
    replay_compatibility_ref: str = "ref:l6_phase2_event_replay_compatibility"
    applies_policy: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.policy_ref, "L6EventSchemaVersionPolicy.policy_ref")
        ensure_ref_text(self.upcast_policy_ref, "L6EventSchemaVersionPolicy.upcast_policy_ref")
        ensure_ref_text(self.replay_compatibility_ref, "L6EventSchemaVersionPolicy.replay_compatibility_ref")
        if self.applies_policy:
            raise ValueError("L6 event schema version policy is declarative only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ProjectionSchemaVersionPolicy:
    policy_ref: str = "policy:l6_phase2_projection_schema_version_policy"
    conflict_policy_ref: str = "policy:l6_phase2_projection_conflict_policy"
    revocation_policy_ref: str = "policy:l6_phase2_projection_revocation_policy"
    rollback_policy_ref: str = "rollback:l6_phase2_projection_rollback_policy"
    applies_policy: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("policy_ref", "conflict_policy_ref", "revocation_policy_ref", "rollback_policy_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6ProjectionSchemaVersionPolicy.{field_name}")
        if self.applies_policy:
            raise ValueError("L6 projection schema version policy is declarative only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6HandoffSchemaVersionPolicy:
    policy_ref: str = "policy:l6_phase2_handoff_schema_version_policy"
    compatibility_matrix_ref: str = "ref:l6_phase2_handoff_compatibility_matrix"
    no_auto_merge_policy_ref: str = "policy:l6_phase2_handoff_no_auto_merge"
    applies_policy: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.policy_ref, "L6HandoffSchemaVersionPolicy.policy_ref")
        ensure_ref_text(self.compatibility_matrix_ref, "L6HandoffSchemaVersionPolicy.compatibility_matrix_ref")
        ensure_ref_text(self.no_auto_merge_policy_ref, "L6HandoffSchemaVersionPolicy.no_auto_merge_policy_ref")
        if self.applies_policy:
            raise ValueError("L6 handoff schema version policy is declarative only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6MigrationPlanDeclaration:
    migration_plan_ref: str = "migration:l6_phase2_migration_plan"
    source_contract_ref: str = "ref:l6_phase2_source_contract"
    target_contract_ref: str = "ref:l6_phase2_target_contract"
    compatibility_matrix_ref: str = "ref:l6_phase2_compatibility_matrix"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    applies_migration: bool = False
    authorizes_migration: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in ("migration_plan_ref", "source_contract_ref", "target_contract_ref", "compatibility_matrix_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6MigrationPlanDeclaration.{field_name}")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("L6MigrationPlanDeclaration.audit_trace must be L6AuditTraceEnvelope")
        if self.applies_migration or self.authorizes_migration:
            raise ValueError("L6 migration plan declaration is not migration execution")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6RollbackRouteDeclaration:
    rollback_route_ref: str = "rollback:l6_phase2_rollback_route"
    rollback_anchor_ref: str = "rollback:l6_phase2_rollback_anchor"
    compatibility_matrix_ref: str = "ref:l6_phase2_compatibility_matrix"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    applies_rollback: bool = False
    authorizes_rollback: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rollback_route_ref, "L6RollbackRouteDeclaration.rollback_route_ref")
        ensure_ref_text(self.rollback_anchor_ref, "L6RollbackRouteDeclaration.rollback_anchor_ref")
        ensure_ref_text(self.compatibility_matrix_ref, "L6RollbackRouteDeclaration.compatibility_matrix_ref")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("L6RollbackRouteDeclaration.audit_trace must be L6AuditTraceEnvelope")
        if self.applies_rollback or self.authorizes_rollback:
            raise ValueError("L6 rollback route declaration is not rollback execution")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6HotSwitchReadinessDeclaration:
    hot_switch_readiness_ref: str = "hotswitch:l6_phase2_readiness"
    version_slot_ref: str = "ref:l6_phase2_version_slot"
    compatibility_matrix_ref: str = "ref:l6_phase2_compatibility_matrix"
    checkpoint_ref: str = "checkpoint:l6_phase2_hot_switch_checkpoint"
    observation_window_ref: str = "ref:l6_phase2_hot_switch_observation_window"
    rollback_route_ref: str = "rollback:l6_phase2_hot_switch_rollback_route"
    responsibility_chain_ref: str = "responsibility:l6_phase2_hot_switch"
    ready_for_review: bool = True
    performs_hot_switch: bool = False
    authorizes_hot_switch: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.hot_switch_readiness_ref, "L6HotSwitchReadinessDeclaration.hot_switch_readiness_ref")
        ensure_ref_text(self.version_slot_ref, "L6HotSwitchReadinessDeclaration.version_slot_ref")
        ensure_ref_text(self.compatibility_matrix_ref, "L6HotSwitchReadinessDeclaration.compatibility_matrix_ref")
        for field_name in ("checkpoint_ref", "observation_window_ref", "rollback_route_ref", "responsibility_chain_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6HotSwitchReadinessDeclaration.{field_name}")
        for field_name in ("ready_for_review", "performs_hot_switch", "authorizes_hot_switch"):
            ensure_bool(getattr(self, field_name), f"L6HotSwitchReadinessDeclaration.{field_name}")
        if self.performs_hot_switch or self.authorizes_hot_switch:
            raise ValueError("L6 hot switch readiness is not hot switch execution")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ReplayCompatibilityDeclaration:
    replay_compatibility_ref: str = "ref:l6_phase2_replay_compatibility"
    old_event_schema_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_phase2_old_event_schema",))
    new_event_schema_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_phase2_new_event_schema",))
    upcast_policy_ref: str = "policy:l6_phase2_replay_upcast"
    action_replay_allowed: bool = False
    performs_replay: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.replay_compatibility_ref, "L6ReplayCompatibilityDeclaration.replay_compatibility_ref")
        ensure_ref_items(self.old_event_schema_refs, "L6ReplayCompatibilityDeclaration.old_event_schema_refs", required=True)
        ensure_ref_items(self.new_event_schema_refs, "L6ReplayCompatibilityDeclaration.new_event_schema_refs", required=True)
        ensure_ref_text(self.upcast_policy_ref, "L6ReplayCompatibilityDeclaration.upcast_policy_ref")
        if self.action_replay_allowed or self.performs_replay:
            raise ValueError("L6 replay compatibility is not action replay")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6BreakingChangeAssessment:
    assessment_ref: str = "ref:l6_phase2_breaking_change_assessment"
    change_kind: L6ContractChangeKind | str = L6ContractChangeKind.MAJOR
    impact_summary: str = "summary:l6_phase2_breaking_change_summary"
    affected_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase2_affected_contract",))
    migration_plan_ref: str = "migration:l6_phase2_migration_plan"
    rollback_route_ref: str = "rollback:l6_phase2_rollback_route"
    replay_compatibility_ref: str = "ref:l6_phase2_replay_compatibility"
    l5_compatibility_review_ref: str = "l5:l6_phase2_l5_compat_review"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.assessment_ref, "L6BreakingChangeAssessment.assessment_ref")
        object.__setattr__(self, "change_kind", L6ContractChangeKind(self.change_kind))
        ensure_no_live_or_sensitive_text(self.impact_summary, "L6BreakingChangeAssessment.impact_summary")
        ensure_ref_items(self.affected_contract_refs, "L6BreakingChangeAssessment.affected_contract_refs", required=True)
        for field_name in ("migration_plan_ref", "rollback_route_ref", "replay_compatibility_ref", "l5_compatibility_review_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6BreakingChangeAssessment.{field_name}")
        ensure_schema_version(self.schema_version)

    @property
    def major_change_has_required_controls(self) -> bool:
        if self.change_kind is not L6ContractChangeKind.MAJOR:
            return True
        return bool(self.migration_plan_ref and self.rollback_route_ref and self.replay_compatibility_ref and self.l5_compatibility_review_ref)


@dataclass(frozen=True, slots=True)
class L6DeprecationPolicyDeclaration:
    deprecation_policy_ref: str = "policy:l6_phase2_deprecation_policy"
    tombstone_policy_ref: str = "policy:l6_phase2_tombstone_policy"
    public_projection_ref: str = "public:l6_phase2_deprecation_projection"
    applies_deprecation: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.deprecation_policy_ref, "L6DeprecationPolicyDeclaration.deprecation_policy_ref")
        ensure_ref_text(self.tombstone_policy_ref, "L6DeprecationPolicyDeclaration.tombstone_policy_ref")
        ensure_ref_text(self.public_projection_ref, "L6DeprecationPolicyDeclaration.public_projection_ref")
        if self.applies_deprecation:
            raise ValueError("L6 deprecation policy declaration is not lifecycle execution")
        ensure_schema_version(self.schema_version)
