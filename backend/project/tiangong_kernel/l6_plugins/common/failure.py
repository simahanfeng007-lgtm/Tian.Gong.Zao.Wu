"""L6 failure, degradation, migration, rollback, and hot-switch declarations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version


class L6FailureSeverity(str, Enum):
    INFO = "info"
    P3 = "p3"
    P2 = "p2"
    P1 = "p1"
    P0 = "p0"


@dataclass(frozen=True, slots=True)
class L6FailureContract:
    failure_contract_ref: str = "decl:l6_failure_contract"
    failure_mode_refs: tuple[str, ...] = field(default_factory=lambda: ("decl:l6_failure_mode_ref",))
    severity: L6FailureSeverity | str = L6FailureSeverity.P3
    detection_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    isolation_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l5_host_isolation_required",))
    recovery_candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    writes_state: bool = False
    performs_recovery: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.failure_contract_ref, "L6FailureContract.failure_contract_ref")
        ensure_ref_items(self.failure_mode_refs, "L6FailureContract.failure_mode_refs", required=True)
        object.__setattr__(self, "severity", L6FailureSeverity(self.severity))
        ensure_ref_items(self.detection_evidence_refs, "L6FailureContract.detection_evidence_refs")
        ensure_ref_items(self.isolation_policy_refs, "L6FailureContract.isolation_policy_refs", required=True)
        ensure_ref_items(self.recovery_candidate_refs, "L6FailureContract.recovery_candidate_refs")
        if self.writes_state or self.performs_recovery:
            raise ValueError("L6 failure contract cannot write state or perform recovery")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6DegradationContract:
    degradation_contract_ref: str = "decl:l6_degradation_contract"
    trigger_refs: tuple[str, ...] = field(default_factory=lambda: ("decl:l6_degradation_trigger",))
    degraded_capability_refs: tuple[str, ...] = field(default_factory=tuple)
    fallback_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_fallback_summary",))
    audit_requirement_ref: str = "audit:l6_degradation_audit_requirement"
    degrades_by_self: bool = False
    requires_l5_host_action_ref: str = "l5:host_degradation_action_required"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.degradation_contract_ref, "L6DegradationContract.degradation_contract_ref")
        ensure_ref_items(self.trigger_refs, "L6DegradationContract.trigger_refs", required=True)
        ensure_ref_items(self.degraded_capability_refs, "L6DegradationContract.degraded_capability_refs")
        ensure_ref_items(self.fallback_summary_refs, "L6DegradationContract.fallback_summary_refs")
        ensure_ref_text(self.audit_requirement_ref, "L6DegradationContract.audit_requirement_ref")
        ensure_ref_text(self.requires_l5_host_action_ref, "L6DegradationContract.requires_l5_host_action_ref")
        if self.degrades_by_self:
            raise ValueError("L6 degradation declaration cannot self-change live host state")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6MigrationContract:
    migration_contract_ref: str = "migration:l6_migration_contract"
    source_version_ref: str = "decl:l6_source_version_ref"
    target_version_ref: str = "decl:l6_target_version_ref"
    migration_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_migration_policy_ref",))
    compatibility_matrix_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_compatibility_matrix_ref",))
    old_event_replay_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_old_event_replay_requirement",))
    minimum_migration_refs: tuple[str, ...] = field(default_factory=tuple)
    declares_plan_only: bool = True
    applies_migration: bool = False
    writes_state: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.migration_contract_ref, "L6MigrationContract.migration_contract_ref")
        ensure_ref_text(self.source_version_ref, "L6MigrationContract.source_version_ref")
        ensure_ref_text(self.target_version_ref, "L6MigrationContract.target_version_ref")
        ensure_ref_items(self.migration_policy_refs, "L6MigrationContract.migration_policy_refs", required=True)
        ensure_ref_items(self.compatibility_matrix_refs, "L6MigrationContract.compatibility_matrix_refs", required=True)
        ensure_ref_items(self.old_event_replay_refs, "L6MigrationContract.old_event_replay_refs", required=True)
        ensure_ref_items(self.minimum_migration_refs, "L6MigrationContract.minimum_migration_refs")
        if not self.declares_plan_only or self.applies_migration or self.writes_state:
            raise ValueError("L6 migration contract can only declare a plan")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6RollbackContract:
    rollback_contract_ref: str = "rollback:l6_rollback_contract"
    rollback_anchor_refs: tuple[str, ...] = field(default_factory=lambda: ("rollback:l6_anchor_ref",))
    rollback_route_refs: tuple[str, ...] = field(default_factory=lambda: ("rollback:l6_route_ref",))
    tombstone_policy_refs: tuple[str, ...] = field(default_factory=lambda: ("policy:l6_tombstone_policy_ref",))
    verification_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_rollback_verification_required",))
    declares_route_only: bool = True
    applies_rollback: bool = False
    creates_checkpoint: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rollback_contract_ref, "L6RollbackContract.rollback_contract_ref")
        ensure_ref_items(self.rollback_anchor_refs, "L6RollbackContract.rollback_anchor_refs", required=True)
        ensure_ref_items(self.rollback_route_refs, "L6RollbackContract.rollback_route_refs", required=True)
        ensure_ref_items(self.tombstone_policy_refs, "L6RollbackContract.tombstone_policy_refs", required=True)
        ensure_ref_items(self.verification_requirement_refs, "L6RollbackContract.verification_requirement_refs", required=True)
        if not self.declares_route_only or self.applies_rollback or self.creates_checkpoint:
            raise ValueError("L6 rollback contract can only declare a route")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6HotSwitchReadinessContract:
    hotswitch_contract_ref: str = "hotswitch:l6_readiness_contract"
    readiness_check_refs: tuple[str, ...] = field(default_factory=lambda: ("quality:l6_hotswitch_readiness_check",))
    pre_switch_checkpoint_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("hotswitch:l6_pre_switch_checkpoint_requirement",))
    post_switch_observation_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("hotswitch:l6_post_switch_observation_requirement",))
    switch_rollback_route_refs: tuple[str, ...] = field(default_factory=lambda: ("rollback:l6_switch_rollback_route",))
    manual_approval_refs: tuple[str, ...] = field(default_factory=lambda: ("permission:l6_hotswitch_manual_approval_required",))
    declares_readiness_only: bool = True
    performs_hot_switch: bool = False
    starts_observer: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.hotswitch_contract_ref, "L6HotSwitchReadinessContract.hotswitch_contract_ref")
        for field_name in (
            "readiness_check_refs", "pre_switch_checkpoint_requirement_refs", "post_switch_observation_requirement_refs",
            "switch_rollback_route_refs", "manual_approval_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"L6HotSwitchReadinessContract.{field_name}", required=True)
        if not self.declares_readiness_only or self.performs_hot_switch or self.starts_observer:
            raise ValueError("L6 hotswitch readiness contract cannot perform switch or start observer")
        ensure_schema_version(self.schema_version)
