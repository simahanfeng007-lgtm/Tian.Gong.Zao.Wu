"""Pure validation for L5 phase 4 lifecycle and mount declarations.

Validators in this module consume explicit in-memory declarations and return
reports only. They never read plugin files, scan directories, load modules,
mutate RegistrySnapshot, update lifecycle state, mount plugins, or call external
systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .lifecycle_declaration import (
    PluginLifecycleStateMachine,
    PluginLifecycleStatusKind,
    PluginLifecycleTransitionRule,
    PluginMountDeclaration,
    has_forbidden_method,
    is_allowed_transition,
    is_live_entry_text,
    is_runtime_status_text,
    lifecycle_declaration_digest,
    lifecycle_required_chain_fields_present,
)
from .registry_conflict import PluginRegistryConflict, PluginRegistryConflictKind, PluginRegistryConflictSeverity


def _is_missing(value: object) -> bool:
    return value == "" or value == tuple() or value is None


def _blocking(severity: PluginRegistryConflictSeverity) -> bool:
    return severity in (PluginRegistryConflictSeverity.P0, PluginRegistryConflictSeverity.P1)


def _conflict(
    conflict_ref: str,
    kind: PluginRegistryConflictKind,
    severity: PluginRegistryConflictSeverity,
    message: str,
    field_path: str,
    evidence_refs: tuple[str, ...] = ("evidence:l5_phase4_validator",),
    affected_record_refs: tuple[str, ...] = tuple(),
) -> PluginRegistryConflict:
    return PluginRegistryConflict(
        conflict_ref=conflict_ref,
        kind=kind,
        severity=severity,
        message=message,
        affected_record_refs=affected_record_refs,
        field_path=field_path,
        blocking=_blocking(severity),
        evidence_refs=evidence_refs,
        rule_source_ref="rule:l5_phase4_lifecycle_mount",
        detected_by_ref="detector:l5_phase4_lifecycle_validator",
        trace_ref="trace:l5_phase4_validation",
        responsibility_chain_ref="responsibility:l5_phase4_validation",
    )


@dataclass(frozen=True, slots=True)
class PluginLifecycleValidationReport:
    report_ref: str
    registry_snapshot_ref: str
    state_machine_ref: str
    checked_lifecycle_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_mount_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_items: tuple[PluginRegistryConflict, ...] = field(default_factory=tuple)
    conflict_refs: tuple[str, ...] = field(default_factory=tuple)
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    passed: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    rule_source_ref: str = "rule:l5_phase4_lifecycle"
    detected_by_ref: str = "detector:l5_phase4_lifecycle_validator"
    responsibility_chain_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    lifecycle_event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_event_refs: tuple[str, ...] = field(default_factory=tuple)
    report_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("report_ref", "registry_snapshot_ref", "state_machine_ref", "rule_source_ref", "detected_by_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleValidationReport.{name}")
        for item in self.conflict_items:
            if not isinstance(item, PluginRegistryConflict):
                raise ValueError("PluginLifecycleValidationReport.conflict_items must contain PluginRegistryConflict")
        for name in ("checked_lifecycle_refs", "checked_mount_decl_refs", "conflict_refs", "blocking_reasons", "evidence_refs", "provenance_refs", "lifecycle_event_kind_refs", "validation_event_refs"):
            ensure_ref_items(getattr(self, name), f"PluginLifecycleValidationReport.{name}")
        ensure_bool(self.passed, "PluginLifecycleValidationReport.passed")
        for name in ("trace_ref", "responsibility_chain_ref", "actor_ref", "scope_ref", "policy_ref", "approval_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleValidationReport.{name}", required=False)
        ensure_schema_version(self.schema_version, "PluginLifecycleValidationReport.schema_version")
        if not self.conflict_refs and self.conflict_items:
            object.__setattr__(self, "conflict_refs", tuple(item.conflict_ref for item in self.conflict_items))
        if not self.report_digest:
            object.__setattr__(self, "report_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginMountDeclarationConflictReport:
    conflict_report_ref: str
    conflict_items: tuple[PluginRegistryConflict, ...] = field(default_factory=tuple)
    conflict_summary: str = ""
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    rule_source_ref: str = "rule:l5_phase4_mount"
    detected_by_ref: str = "detector:l5_phase4_mount_validator"
    responsibility_chain_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    mount_event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    conflict_event_refs: tuple[str, ...] = field(default_factory=tuple)
    report_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.conflict_report_ref, "PluginMountDeclarationConflictReport.conflict_report_ref")
        for item in self.conflict_items:
            if not isinstance(item, PluginRegistryConflict):
                raise ValueError("PluginMountDeclarationConflictReport.conflict_items must contain PluginRegistryConflict")
        ensure_short_text(self.conflict_summary, "PluginMountDeclarationConflictReport.conflict_summary")
        for name in ("evidence_refs", "provenance_refs", "mount_event_kind_refs", "conflict_event_refs"):
            ensure_ref_items(getattr(self, name), f"PluginMountDeclarationConflictReport.{name}")
        for name in ("trace_ref", "rule_source_ref", "detected_by_ref", "responsibility_chain_ref", "actor_ref", "scope_ref", "policy_ref", "approval_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginMountDeclarationConflictReport.{name}", required=False if name not in ("rule_source_ref", "detected_by_ref") else True)
        ensure_schema_version(self.schema_version, "PluginMountDeclarationConflictReport.schema_version")
        if not self.report_digest:
            object.__setattr__(self, "report_digest", lifecycle_declaration_digest(self))

    @property
    def passed(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0


@dataclass(frozen=True, slots=True)
class PluginLifecycleValidator:
    validator_ref: str
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.validator_ref, "PluginLifecycleValidator.validator_ref")
        ensure_schema_version(self.schema_version, "PluginLifecycleValidator.schema_version")

    def validate_declarations(
        self,
        state_machine: PluginLifecycleStateMachine,
        mount_declarations: tuple[PluginMountDeclaration, ...] = tuple(),
        registry_snapshot_ref: str | None = None,
    ) -> tuple[PluginLifecycleValidationReport, PluginMountDeclarationConflictReport]:
        if not isinstance(state_machine, PluginLifecycleStateMachine):
            raise ValueError("PluginLifecycleValidator requires PluginLifecycleStateMachine")
        conflicts: list[PluginRegistryConflict] = []
        mount_conflicts: list[PluginRegistryConflict] = []
        snapshot_ref = registry_snapshot_ref or state_machine.registry_snapshot_ref

        def add(kind: PluginRegistryConflictKind, severity: PluginRegistryConflictSeverity, message: str, field_path: str, affected: tuple[str, ...] = tuple()) -> None:
            conflicts.append(_conflict(f"conflict:{kind.value}:{len(conflicts)+1}", kind, severity, message, field_path, affected_record_refs=affected))

        def add_mount(kind: PluginRegistryConflictKind, severity: PluginRegistryConflictSeverity, message: str, field_path: str, affected: tuple[str, ...] = tuple()) -> None:
            mount_conflicts.append(_conflict(f"mount_conflict:{kind.value}:{len(mount_conflicts)+1}", kind, severity, message, field_path, affected_record_refs=affected))

        self._check_state_machine(state_machine, add)
        for rule in state_machine.transition_rules:
            self._check_transition_rule(rule, add)
        for mount in mount_declarations:
            if not isinstance(mount, PluginMountDeclaration):
                raise ValueError("mount_declarations must contain PluginMountDeclaration")
            self._check_mount_declaration(mount, add_mount)

        all_conflicts = tuple(conflicts)
        all_mount = tuple(mount_conflicts)
        p0 = sum(1 for item in all_conflicts if item.severity is PluginRegistryConflictSeverity.P0)
        p1 = sum(1 for item in all_conflicts if item.severity is PluginRegistryConflictSeverity.P1)
        p2 = sum(1 for item in all_conflicts if item.severity is PluginRegistryConflictSeverity.P2)
        p3 = sum(1 for item in all_conflicts if item.severity is PluginRegistryConflictSeverity.P3)
        mp0 = sum(1 for item in all_mount if item.severity is PluginRegistryConflictSeverity.P0)
        mp1 = sum(1 for item in all_mount if item.severity is PluginRegistryConflictSeverity.P1)
        mp2 = sum(1 for item in all_mount if item.severity is PluginRegistryConflictSeverity.P2)
        mp3 = sum(1 for item in all_mount if item.severity is PluginRegistryConflictSeverity.P3)
        report = PluginLifecycleValidationReport(
            report_ref=f"lifecycle_validation:{state_machine.state_machine_ref}",
            registry_snapshot_ref=snapshot_ref,
            state_machine_ref=state_machine.state_machine_ref,
            checked_lifecycle_refs=tuple(rule.transition_ref for rule in state_machine.transition_rules),
            checked_mount_decl_refs=tuple(mount.mount_decl_ref for mount in mount_declarations),
            conflict_items=all_conflicts,
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            passed=p0 == 0 and p1 == 0,
            blocking_reasons=tuple(item.message for item in all_conflicts if item.blocking),
            evidence_refs=state_machine.evidence_refs or ("evidence:l5_phase4_lifecycle",),
            trace_ref=state_machine.trace_ref,
            responsibility_chain_ref=state_machine.responsibility_chain_ref,
            actor_ref=state_machine.actor_ref,
            scope_ref=state_machine.scope_ref,
            policy_ref=state_machine.policy_ref,
            approval_ref=state_machine.approval_ref,
            accountability_ref=state_machine.accountability_ref,
            provenance_refs=state_machine.provenance_refs,
            tamper_evidence_ref=state_machine.tamper_evidence_ref,
            lifecycle_event_kind_refs=state_machine.lifecycle_event_refs or ("event:lifecycle_validation",),
            validation_event_refs=("event:lifecycle_validation_completed",),
        )
        mount_report = PluginMountDeclarationConflictReport(
            conflict_report_ref=f"mount_conflict_report:{state_machine.state_machine_ref}",
            conflict_items=all_mount,
            conflict_summary="passed" if mp0 == 0 and mp1 == 0 else "blocked",
            p0_count=mp0,
            p1_count=mp1,
            p2_count=mp2,
            p3_count=mp3,
            evidence_refs=tuple(sorted({ref for mount in mount_declarations for ref in mount.evidence_refs})) or ("evidence:l5_phase4_mount",),
            trace_ref=state_machine.trace_ref,
            responsibility_chain_ref=state_machine.responsibility_chain_ref,
            actor_ref=state_machine.actor_ref,
            scope_ref=state_machine.scope_ref,
            policy_ref=state_machine.policy_ref,
            approval_ref=state_machine.approval_ref,
            accountability_ref=state_machine.accountability_ref,
            provenance_refs=state_machine.provenance_refs,
            tamper_evidence_ref=state_machine.tamper_evidence_ref,
            mount_event_kind_refs=("event:mount_declaration_validation",),
            conflict_event_refs=tuple(item.conflict_ref for item in all_mount),
        )
        return report, mount_report

    def _check_state_machine(self, sm: PluginLifecycleStateMachine, add) -> None:
        missing = lifecycle_required_chain_fields_present(
            sm,
            ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "responsibility_chain_ref", "accountability_ref", "provenance_refs", "tamper_evidence_ref", "evidence_refs", "lifecycle_event_refs"),
        )
        for field_name in missing:
            add(PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT, PluginRegistryConflictSeverity.P1, f"state machine missing responsibility field {field_name}", f"state_machine.{field_name}")
        if has_forbidden_method(PluginLifecycleStateMachine):
            add(PluginRegistryConflictKind.LIFECYCLE_EXECUTION_METHOD_CONFLICT, PluginRegistryConflictSeverity.P0, "state machine exposes forbidden execution method", "PluginLifecycleStateMachine")
        for forbidden_field in ("current_state", "active_state", "runtime_status", "state_store", "state_history_store", "runtime_context", "plugin_instance_ref"):
            if hasattr(sm, forbidden_field):
                add(PluginRegistryConflictKind.LIFECYCLE_STATUS_RUNTIME_CONFLICT, PluginRegistryConflictSeverity.P0, "state machine exposes runtime state field", forbidden_field)

    def _check_transition_rule(self, rule: PluginLifecycleTransitionRule, add) -> None:
        if has_forbidden_method(PluginLifecycleTransitionRule):
            add(PluginRegistryConflictKind.LIFECYCLE_EXECUTION_METHOD_CONFLICT, PluginRegistryConflictSeverity.P0, "transition rule exposes forbidden execution method", "PluginLifecycleTransitionRule")
        if not is_allowed_transition(rule):
            add(PluginRegistryConflictKind.LIFECYCLE_ILLEGAL_TRANSITION_CONFLICT, PluginRegistryConflictSeverity.P1, "transition is outside declaration-only allowed graph", rule.transition_ref)
        for field_name, kind in (
            ("guard_refs", PluginRegistryConflictKind.LIFECYCLE_MISSING_GUARD_CONFLICT),
            ("required_policy_refs", PluginRegistryConflictKind.LIFECYCLE_MISSING_POLICY_CONFLICT),
            ("audit_event_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_AUDIT_CONFLICT),
            ("required_evidence_refs", PluginRegistryConflictKind.LIFECYCLE_MISSING_EVIDENCE_CONFLICT),
            ("responsibility_chain_ref", PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT),
        ):
            if _is_missing(getattr(rule, field_name)):
                add(kind, PluginRegistryConflictSeverity.P1, f"transition missing {field_name}", f"transition.{field_name}")
        for field_name in ("actor_ref", "scope_ref", "trace_ref", "accountability_ref", "provenance_refs", "tamper_evidence_ref", "lifecycle_event_refs"):
            if _is_missing(getattr(rule, field_name)):
                add(PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT, PluginRegistryConflictSeverity.P1, f"transition missing responsibility field {field_name}", f"transition.{field_name}")
        if is_runtime_status_text(rule.to_status_kind.value):
            add(PluginRegistryConflictKind.LIFECYCLE_STATUS_RUNTIME_CONFLICT, PluginRegistryConflictSeverity.P0, "runtime status text is forbidden", "transition.to_status_kind")
        if rule.to_status_kind is PluginLifecycleStatusKind.HOT_SWITCH_DECLARED:
            for field_name, kind in (
                ("hot_switch_decl_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_HOT_SWITCH_DECL_CONFLICT),
                ("switch_readiness_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_SWITCH_READINESS_CONFLICT),
                ("pre_switch_checkpoint_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_PRE_SWITCH_CHECKPOINT_CONFLICT),
                ("post_switch_observation_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_POST_SWITCH_OBSERVATION_CONFLICT),
                ("switch_rollback_route_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_SWITCH_ROLLBACK_ROUTE_CONFLICT),
                ("required_approval_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_POLICY_CONFLICT),
            ):
                if _is_missing(getattr(rule, field_name)):
                    add(kind, PluginRegistryConflictSeverity.P1, f"hot switch declaration missing {field_name}", f"transition.{field_name}")
        if rule.to_status_kind is PluginLifecycleStatusKind.MIGRATION_DECLARED:
            for field_name, kind in (
                ("migration_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_MIGRATION_REF_CONFLICT),
                ("compatibility_check_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_COMPATIBILITY_CHECK_CONFLICT),
                ("breaking_change_check_ref", PluginRegistryConflictKind.LIFECYCLE_MISSING_BREAKING_CHANGE_CHECK_CONFLICT),
            ):
                if _is_missing(getattr(rule, field_name)) and not (field_name == "breaking_change_check_ref" and rule.breaking_change_policy_ref):
                    add(kind, PluginRegistryConflictSeverity.P1, f"migration declaration missing {field_name}", f"transition.{field_name}")
        if rule.to_status_kind is PluginLifecycleStatusKind.REPLAY_DECLARED:
            if _is_missing(rule.replay_compatibility_ref):
                add(PluginRegistryConflictKind.LIFECYCLE_MISSING_REPLAY_COMPATIBILITY_CONFLICT, PluginRegistryConflictSeverity.P1, "replay declaration missing replay compatibility ref", "transition.replay_compatibility_ref")

    def _check_mount_declaration(self, mount: PluginMountDeclaration, add_mount) -> None:
        if has_forbidden_method(PluginMountDeclaration):
            add_mount(PluginRegistryConflictKind.MOUNT_LIVE_ENTRY_CONFLICT, PluginRegistryConflictSeverity.P0, "mount declaration exposes forbidden execution method", "PluginMountDeclaration")
        for field_name, kind in (
            ("boundary_ref", PluginRegistryConflictKind.MOUNT_BOUNDARY_CONFLICT),
            ("scope_ref", PluginRegistryConflictKind.MOUNT_SCOPE_CONFLICT),
            ("policy_refs", PluginRegistryConflictKind.MOUNT_PERMISSION_DECL_CONFLICT),
            ("permission_decl_refs", PluginRegistryConflictKind.MOUNT_PERMISSION_DECL_CONFLICT),
            ("resource_decl_refs", PluginRegistryConflictKind.MOUNT_RESOURCE_DECL_CONFLICT),
            ("credential_decl_refs", PluginRegistryConflictKind.MOUNT_CREDENTIAL_DECL_CONFLICT),
            ("data_governance_decl_refs", PluginRegistryConflictKind.MOUNT_DATA_GOVERNANCE_DECL_CONFLICT),
            ("audit_decl_ref", PluginRegistryConflictKind.MOUNT_AUDIT_DECL_CONFLICT),
        ):
            if _is_missing(getattr(mount, field_name)):
                add_mount(kind, PluginRegistryConflictSeverity.P1, f"mount declaration missing {field_name}", f"mount.{field_name}", (mount.mount_decl_ref,))
        for field_name in ("actor_ref", "approval_ref", "accountability_ref", "provenance_refs", "tamper_evidence_ref", "trace_ref", "responsibility_chain_ref", "evidence_refs", "mount_event_kind_refs"):
            if _is_missing(getattr(mount, field_name)):
                add_mount(PluginRegistryConflictKind.RESPONSIBILITY_CHAIN_CONFLICT, PluginRegistryConflictSeverity.P1, f"mount declaration missing responsibility field {field_name}", f"mount.{field_name}", (mount.mount_decl_ref,))
        for field_name in ("mount_point_ref", "host_surface_ref"):
            if is_live_entry_text(getattr(mount, field_name)):
                add_mount(PluginRegistryConflictKind.MOUNT_LIVE_ENTRY_CONFLICT, PluginRegistryConflictSeverity.P0, f"{field_name} contains executable locator", f"mount.{field_name}", (mount.mount_decl_ref,))
        for field_name in ("summary",):
            if is_live_entry_text(getattr(mount, field_name)):
                add_mount(PluginRegistryConflictKind.MOUNT_PUBLIC_PROJECTION_LEAK_CONFLICT, PluginRegistryConflictSeverity.P0, f"{field_name} contains unsafe disclosure", f"mount.{field_name}", (mount.mount_decl_ref,))
        for field_name, kind in (
            ("switch_readiness_ref", PluginRegistryConflictKind.MOUNT_MISSING_SWITCH_READINESS_CONFLICT),
            ("pre_switch_checkpoint_ref", PluginRegistryConflictKind.MOUNT_MISSING_PRE_SWITCH_CHECKPOINT_CONFLICT),
            ("post_switch_observation_ref", PluginRegistryConflictKind.MOUNT_MISSING_POST_SWITCH_OBSERVATION_CONFLICT),
            ("switch_rollback_route_ref", PluginRegistryConflictKind.MOUNT_MISSING_SWITCH_ROLLBACK_ROUTE_CONFLICT),
        ):
            if _is_missing(getattr(mount, field_name)):
                add_mount(kind, PluginRegistryConflictSeverity.P2, f"mount declaration missing switch-chain reference {field_name}", f"mount.{field_name}", (mount.mount_decl_ref,))


@dataclass(frozen=True, slots=True)
class PluginLifecycleQualityGateDecision:
    phase: str = "L5_PHASE4"
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    lifecycle_validation_passed: bool = False
    mount_declaration_validation_passed: bool = False
    no_live_execution_passed: bool = False
    public_projection_safety_passed: bool = False
    registry_phase3_compatibility_passed: bool = False
    l0_l4_hash_clean: bool = False
    l5_phase1_phase3_hash_clean: bool = False
    full_pytest_passed: bool = False
    forbidden_scan_passed: bool = False
    allow_enter_l5_phase5: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_index_refs: tuple[str, ...] = field(default_factory=tuple)
    decision_ref: str = ""
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    rule_source_ref: str = "rule:l5_phase4_quality_gate"
    detected_by_ref: str = "detector:l5_phase4_quality_gate"
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    accountability_ref: str = ""
    tamper_evidence_ref: str = ""
    quality_gate_event_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.phase != "L5_PHASE4":
            raise ValueError("PluginLifecycleQualityGateDecision.phase must be L5_PHASE4")
        bool_fields = (
            "lifecycle_validation_passed", "mount_declaration_validation_passed", "no_live_execution_passed",
            "public_projection_safety_passed", "registry_phase3_compatibility_passed", "l0_l4_hash_clean",
            "l5_phase1_phase3_hash_clean", "full_pytest_passed", "forbidden_scan_passed", "allow_enter_l5_phase5",
        )
        for name in bool_fields:
            ensure_bool(getattr(self, name), f"PluginLifecycleQualityGateDecision.{name}")
        for name in ("blocking_reasons", "evidence_index_refs", "regression_index_refs", "evidence_refs", "provenance_refs"):
            ensure_ref_items(getattr(self, name), f"PluginLifecycleQualityGateDecision.{name}")
        for name in ("decision_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "rule_source_ref", "detected_by_ref", "accountability_ref", "tamper_evidence_ref", "quality_gate_event_ref"):
            ensure_ref_text(getattr(self, name), f"PluginLifecycleQualityGateDecision.{name}", required=False if name not in ("rule_source_ref", "detected_by_ref") else True)
        ensure_schema_version(self.schema_version, "PluginLifecycleQualityGateDecision.schema_version")
        if self.allow_enter_l5_phase5:
            required = (
                "decision_ref", "actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref",
                "rule_source_ref", "detected_by_ref", "accountability_ref", "tamper_evidence_ref", "quality_gate_event_ref",
            )
            missing = tuple(name for name in required if _is_missing(getattr(self, name)))
            blockers = (
                self.p0_count > 0,
                self.p1_count > 0,
                not self.lifecycle_validation_passed,
                not self.mount_declaration_validation_passed,
                not self.no_live_execution_passed,
                not self.public_projection_safety_passed,
                not self.registry_phase3_compatibility_passed,
                not self.l0_l4_hash_clean,
                not self.l5_phase1_phase3_hash_clean,
                not self.full_pytest_passed,
                not self.forbidden_scan_passed,
                bool(missing),
                not self.evidence_refs,
                not self.provenance_refs,
            )
            if any(blockers):
                raise ValueError("PluginLifecycleQualityGateDecision cannot allow phase 5 when blocking conditions exist")


@dataclass(frozen=True, slots=True)
class PluginLifecycleQualityGate:
    gate_ref: str
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.gate_ref, "PluginLifecycleQualityGate.gate_ref")
        ensure_schema_version(self.schema_version, "PluginLifecycleQualityGate.schema_version")

    def evaluate_reports(
        self,
        lifecycle_report: PluginLifecycleValidationReport,
        mount_report: PluginMountDeclarationConflictReport,
        *,
        no_live_execution_passed: bool,
        public_projection_safety_passed: bool,
        registry_phase3_compatibility_passed: bool,
        l0_l4_hash_clean: bool,
        l5_phase1_phase3_hash_clean: bool,
        full_pytest_passed: bool,
        forbidden_scan_passed: bool,
        evidence_index_refs: tuple[str, ...] = ("evidence_index:l5_phase4",),
        regression_index_refs: tuple[str, ...] = ("regression_index:l5_phase4",),
    ) -> PluginLifecycleQualityGateDecision:
        p0 = lifecycle_report.p0_count + mount_report.p0_count
        p1 = lifecycle_report.p1_count + mount_report.p1_count
        p2 = lifecycle_report.p2_count + mount_report.p2_count
        p3 = lifecycle_report.p3_count + mount_report.p3_count
        allow = all(
            (
                p0 == 0,
                p1 == 0,
                lifecycle_report.passed,
                mount_report.passed,
                no_live_execution_passed,
                public_projection_safety_passed,
                registry_phase3_compatibility_passed,
                l0_l4_hash_clean,
                l5_phase1_phase3_hash_clean,
                full_pytest_passed,
                forbidden_scan_passed,
            )
        )
        blocking_reasons = tuple(lifecycle_report.blocking_reasons) + tuple(item.message for item in mount_report.conflict_items if item.blocking)
        return PluginLifecycleQualityGateDecision(
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            lifecycle_validation_passed=lifecycle_report.passed,
            mount_declaration_validation_passed=mount_report.passed,
            no_live_execution_passed=no_live_execution_passed,
            public_projection_safety_passed=public_projection_safety_passed,
            registry_phase3_compatibility_passed=registry_phase3_compatibility_passed,
            l0_l4_hash_clean=l0_l4_hash_clean,
            l5_phase1_phase3_hash_clean=l5_phase1_phase3_hash_clean,
            full_pytest_passed=full_pytest_passed,
            forbidden_scan_passed=forbidden_scan_passed,
            allow_enter_l5_phase5=allow,
            blocking_reasons=blocking_reasons,
            evidence_index_refs=evidence_index_refs,
            regression_index_refs=regression_index_refs,
            decision_ref="quality_gate:l5_phase4",
            actor_ref=lifecycle_report.actor_ref,
            scope_ref=lifecycle_report.scope_ref,
            trace_ref=lifecycle_report.trace_ref,
            policy_ref=lifecycle_report.policy_ref,
            approval_ref=lifecycle_report.approval_ref,
            rule_source_ref="rule:l5_phase4_quality_gate",
            detected_by_ref="detector:l5_phase4_quality_gate",
            evidence_refs=lifecycle_report.evidence_refs or ("evidence:l5_phase4_quality_gate",),
            provenance_refs=lifecycle_report.provenance_refs or ("provenance:l5_phase4_quality_gate",),
            accountability_ref=lifecycle_report.accountability_ref,
            tamper_evidence_ref=lifecycle_report.tamper_evidence_ref,
            quality_gate_event_ref="event:l5_phase4_quality_gate",
        )


__all__ = (
    "PluginLifecycleValidationReport",
    "PluginMountDeclarationConflictReport",
    "PluginLifecycleValidator",
    "PluginLifecycleQualityGateDecision",
    "PluginLifecycleQualityGate",
)
