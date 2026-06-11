"""L5 phase 4 self-healing declaration shells.

The chain described here is declarative only: failure, diagnosis, recovery plan,
checkpoint, transaction, compensation, validation, regression, postmortem, and
repair suggestion references are not executed, persisted, or used to mutate code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .lifecycle_declaration import has_forbidden_method, is_live_entry_text, lifecycle_declaration_digest
from .registry_conflict import PluginRegistryConflict, PluginRegistryConflictKind, PluginRegistryConflictSeverity


def _is_missing(value: object) -> bool:
    return value == "" or value == tuple() or value is None


def _mk_conflict(kind: PluginRegistryConflictKind, severity: PluginRegistryConflictSeverity, message: str, field_path: str, index: int) -> PluginRegistryConflict:
    return PluginRegistryConflict(
        conflict_ref=f"self_healing_conflict:{kind.value}:{index}",
        kind=kind,
        severity=severity,
        message=message,
        field_path=field_path,
        blocking=severity in (PluginRegistryConflictSeverity.P0, PluginRegistryConflictSeverity.P1),
        evidence_refs=("evidence:l5_phase4_self_healing",),
        rule_source_ref="rule:l5_phase4_self_healing",
        detected_by_ref="detector:l5_phase4_self_healing_validator",
        trace_ref="trace:l5_phase4_self_healing",
        responsibility_chain_ref="responsibility:l5_phase4_self_healing",
    )


@dataclass(frozen=True, slots=True)
class PluginRecoveryPlanDeclaration:
    recovery_plan_ref: str
    failure_ref: str = ""
    fault_ref: str = ""
    diagnosis_ref: str = ""
    root_cause_ref: str = ""
    recovery_strategy_ref: str = ""
    checkpoint_ref: str = ""
    recovery_point_ref: str = ""
    rollback_anchor_ref: str = ""
    transaction_ref: str = ""
    compensation_ref: str = ""
    validation_ref: str = ""
    regression_ref: str = ""
    audit_decl_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    risk_tags: tuple[str, ...] = field(default_factory=tuple)
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    recovery_plan_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.recovery_plan_ref, "PluginRecoveryPlanDeclaration.recovery_plan_ref")
        for name in (
            "failure_ref", "fault_ref", "diagnosis_ref", "root_cause_ref", "recovery_strategy_ref", "checkpoint_ref",
            "recovery_point_ref", "rollback_anchor_ref", "transaction_ref", "compensation_ref", "validation_ref",
            "regression_ref", "audit_decl_ref", "approval_ref", "responsibility_chain_ref", "actor_ref", "scope_ref",
            "trace_ref", "accountability_ref", "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginRecoveryPlanDeclaration.{name}", required=False)
        for name in ("evidence_refs", "policy_refs", "risk_tags", "provenance_refs"):
            ensure_ref_items(getattr(self, name), f"PluginRecoveryPlanDeclaration.{name}")
        ensure_schema_version(self.schema_version, "PluginRecoveryPlanDeclaration.schema_version")
        if not self.recovery_plan_digest:
            object.__setattr__(self, "recovery_plan_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginSelfHealingDeclaration:
    self_healing_decl_ref: str
    registry_key_ref: str
    lifecycle_ref: str
    mount_decl_ref: str
    failure_ref: str = ""
    fault_ref: str = ""
    diagnosis_ref: str = ""
    root_cause_ref: str = ""
    recovery_plan_ref: str = ""
    checkpoint_ref: str = ""
    recovery_point_ref: str = ""
    rollback_anchor_ref: str = ""
    transaction_ref: str = ""
    compensation_ref: str = ""
    validation_ref: str = ""
    regression_ref: str = ""
    postmortem_ref: str = ""
    repair_suggestion_ref: str = ""
    required_policy_refs: tuple[str, ...] = field(default_factory=tuple)
    required_permission_refs: tuple[str, ...] = field(default_factory=tuple)
    required_lease_refs: tuple[str, ...] = field(default_factory=tuple)
    required_approval_ref: str = ""
    audit_decl_ref: str = ""
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_ref: str = ""
    responsibility_chain_ref: str = ""
    severity: str = "p2"
    reversible_declared: bool = True
    side_effect_free_declared: bool = True
    actor_ref: str = ""
    scope_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    event_kind_refs: tuple[str, ...] = field(default_factory=tuple)
    self_healing_digest: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("self_healing_decl_ref", "registry_key_ref", "lifecycle_ref", "mount_decl_ref"):
            ensure_ref_text(getattr(self, name), f"PluginSelfHealingDeclaration.{name}")
        for name in (
            "failure_ref", "fault_ref", "diagnosis_ref", "root_cause_ref", "recovery_plan_ref", "checkpoint_ref",
            "recovery_point_ref", "rollback_anchor_ref", "transaction_ref", "compensation_ref", "validation_ref",
            "regression_ref", "postmortem_ref", "repair_suggestion_ref", "required_approval_ref", "audit_decl_ref",
            "trace_ref", "responsibility_chain_ref", "actor_ref", "scope_ref", "accountability_ref", "tamper_evidence_ref",
        ):
            ensure_ref_text(getattr(self, name), f"PluginSelfHealingDeclaration.{name}", required=False)
        for name in ("required_policy_refs", "required_permission_refs", "required_lease_refs", "evidence_refs", "provenance_refs", "event_kind_refs"):
            ensure_ref_items(getattr(self, name), f"PluginSelfHealingDeclaration.{name}")
        ensure_short_text(self.severity, "PluginSelfHealingDeclaration.severity", 16)
        ensure_bool(self.reversible_declared, "PluginSelfHealingDeclaration.reversible_declared")
        ensure_bool(self.side_effect_free_declared, "PluginSelfHealingDeclaration.side_effect_free_declared")
        ensure_schema_version(self.schema_version, "PluginSelfHealingDeclaration.schema_version")
        if not self.self_healing_digest:
            object.__setattr__(self, "self_healing_digest", lifecycle_declaration_digest(self))


@dataclass(frozen=True, slots=True)
class PluginSelfHealingValidationReport:
    report_ref: str
    checked_self_healing_decl_refs: tuple[str, ...] = field(default_factory=tuple)
    checked_recovery_plan_refs: tuple[str, ...] = field(default_factory=tuple)
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
    rule_source_ref: str = "rule:l5_phase4_self_healing"
    detected_by_ref: str = "detector:l5_phase4_self_healing_validator"
    responsibility_chain_ref: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.report_ref, "PluginSelfHealingValidationReport.report_ref")
        for item in self.conflict_items:
            if not isinstance(item, PluginRegistryConflict):
                raise ValueError("PluginSelfHealingValidationReport.conflict_items must contain PluginRegistryConflict")
        for name in ("checked_self_healing_decl_refs", "checked_recovery_plan_refs", "conflict_refs", "blocking_reasons", "evidence_refs"):
            ensure_ref_items(getattr(self, name), f"PluginSelfHealingValidationReport.{name}")
        for name in ("trace_ref", "rule_source_ref", "detected_by_ref", "responsibility_chain_ref"):
            ensure_ref_text(getattr(self, name), f"PluginSelfHealingValidationReport.{name}", required=False if name not in ("rule_source_ref", "detected_by_ref") else True)
        ensure_bool(self.passed, "PluginSelfHealingValidationReport.passed")
        ensure_schema_version(self.schema_version, "PluginSelfHealingValidationReport.schema_version")
        if not self.conflict_refs and self.conflict_items:
            object.__setattr__(self, "conflict_refs", tuple(item.conflict_ref for item in self.conflict_items))


@dataclass(frozen=True, slots=True)
class PluginSelfHealingQualityGateDecision:
    phase: str = "L5_PHASE4_SELF_HEALING_DECLARATION"
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    failure_fault_link_passed: bool = False
    diagnosis_chain_passed: bool = False
    recovery_plan_declaration_passed: bool = False
    checkpoint_recovery_point_passed: bool = False
    transaction_compensation_passed: bool = False
    audit_evidence_passed: bool = False
    validation_regression_required_passed: bool = False
    no_live_recovery_execution_passed: bool = False
    public_projection_safety_passed: bool = False
    allow_enter_l5_phase5: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_index_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.phase != "L5_PHASE4_SELF_HEALING_DECLARATION":
            raise ValueError("PluginSelfHealingQualityGateDecision.phase is fixed")
        for name in (
            "failure_fault_link_passed", "diagnosis_chain_passed", "recovery_plan_declaration_passed",
            "checkpoint_recovery_point_passed", "transaction_compensation_passed", "audit_evidence_passed",
            "validation_regression_required_passed", "no_live_recovery_execution_passed", "public_projection_safety_passed",
            "allow_enter_l5_phase5",
        ):
            ensure_bool(getattr(self, name), f"PluginSelfHealingQualityGateDecision.{name}")
        for name in ("blocking_reasons", "evidence_index_refs", "regression_index_refs"):
            ensure_ref_items(getattr(self, name), f"PluginSelfHealingQualityGateDecision.{name}")
        ensure_schema_version(self.schema_version, "PluginSelfHealingQualityGateDecision.schema_version")
        if self.allow_enter_l5_phase5:
            if self.p0_count or self.p1_count or not all(
                (
                    self.failure_fault_link_passed,
                    self.diagnosis_chain_passed,
                    self.recovery_plan_declaration_passed,
                    self.checkpoint_recovery_point_passed,
                    self.transaction_compensation_passed,
                    self.audit_evidence_passed,
                    self.validation_regression_required_passed,
                    self.no_live_recovery_execution_passed,
                    self.public_projection_safety_passed,
                )
            ):
                raise ValueError("self-healing quality gate cannot allow phase 5 while blocked")


@dataclass(frozen=True, slots=True)
class PluginSelfHealingValidator:
    validator_ref: str
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.validator_ref, "PluginSelfHealingValidator.validator_ref")
        ensure_schema_version(self.schema_version, "PluginSelfHealingValidator.schema_version")

    def inspect_declarations(
        self,
        self_healing_declarations: tuple[PluginSelfHealingDeclaration, ...] = tuple(),
        recovery_plans: tuple[PluginRecoveryPlanDeclaration, ...] = tuple(),
    ) -> tuple[PluginSelfHealingValidationReport, PluginSelfHealingQualityGateDecision]:
        conflicts: list[PluginRegistryConflict] = []
        index = 1

        def add(kind: PluginRegistryConflictKind, severity: PluginRegistryConflictSeverity, message: str, field_path: str) -> None:
            nonlocal index
            conflicts.append(_mk_conflict(kind, severity, message, field_path, index))
            index += 1

        if has_forbidden_method(PluginSelfHealingDeclaration) or has_forbidden_method(PluginRecoveryPlanDeclaration):
            add(PluginRegistryConflictKind.SELF_HEALING_LIVE_REPAIR_EXECUTION_CONFLICT, PluginRegistryConflictSeverity.P0, "self-healing declaration exposes forbidden method", "self_healing.method")
        for decl in self_healing_declarations:
            if not isinstance(decl, PluginSelfHealingDeclaration):
                raise ValueError("self_healing_declarations must contain PluginSelfHealingDeclaration")
            self._check_self_healing_decl(decl, add)
        for plan in recovery_plans:
            if not isinstance(plan, PluginRecoveryPlanDeclaration):
                raise ValueError("recovery_plans must contain PluginRecoveryPlanDeclaration")
            self._check_recovery_plan(plan, add)
        items = tuple(conflicts)
        p0 = sum(1 for item in items if item.severity is PluginRegistryConflictSeverity.P0)
        p1 = sum(1 for item in items if item.severity is PluginRegistryConflictSeverity.P1)
        p2 = sum(1 for item in items if item.severity is PluginRegistryConflictSeverity.P2)
        p3 = sum(1 for item in items if item.severity is PluginRegistryConflictSeverity.P3)
        passed = p0 == 0 and p1 == 0
        report = PluginSelfHealingValidationReport(
            report_ref="self_healing_validation:l5_phase4",
            checked_self_healing_decl_refs=tuple(item.self_healing_decl_ref for item in self_healing_declarations),
            checked_recovery_plan_refs=tuple(item.recovery_plan_ref for item in recovery_plans),
            conflict_items=items,
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            passed=passed,
            blocking_reasons=tuple(item.message for item in items if item.blocking),
            evidence_refs=("evidence:l5_phase4_self_healing",),
            trace_ref="trace:l5_phase4_self_healing",
            responsibility_chain_ref="responsibility:l5_phase4_self_healing",
        )
        gate = PluginSelfHealingQualityGateDecision(
            p0_count=p0,
            p1_count=p1,
            p2_count=p2,
            p3_count=p3,
            failure_fault_link_passed=not any(item.kind in (PluginRegistryConflictKind.SELF_HEALING_MISSING_FAILURE_REF_CONFLICT, PluginRegistryConflictKind.SELF_HEALING_MISSING_FAULT_REF_CONFLICT) for item in items),
            diagnosis_chain_passed=not any(item.kind in (PluginRegistryConflictKind.SELF_HEALING_MISSING_DIAGNOSIS_REF_CONFLICT, PluginRegistryConflictKind.SELF_HEALING_MISSING_ROOT_CAUSE_REF_CONFLICT) for item in items),
            recovery_plan_declaration_passed=not any(item.kind is PluginRegistryConflictKind.SELF_HEALING_MISSING_RECOVERY_PLAN_CONFLICT for item in items),
            checkpoint_recovery_point_passed=not any(item.kind in (PluginRegistryConflictKind.SELF_HEALING_MISSING_CHECKPOINT_CONFLICT, PluginRegistryConflictKind.SELF_HEALING_MISSING_RECOVERY_POINT_CONFLICT) for item in items),
            transaction_compensation_passed=not any(item.kind in (PluginRegistryConflictKind.SELF_HEALING_MISSING_TRANSACTION_CONFLICT, PluginRegistryConflictKind.SELF_HEALING_MISSING_COMPENSATION_CONFLICT) for item in items),
            audit_evidence_passed=not any(item.kind in (PluginRegistryConflictKind.SELF_HEALING_MISSING_AUDIT_CONFLICT, PluginRegistryConflictKind.SELF_HEALING_MISSING_EVIDENCE_CONFLICT) for item in items),
            validation_regression_required_passed=not any(item.kind in (PluginRegistryConflictKind.SELF_HEALING_MISSING_VALIDATION_CONFLICT, PluginRegistryConflictKind.SELF_HEALING_MISSING_REGRESSION_CONFLICT) for item in items),
            no_live_recovery_execution_passed=p0 == 0,
            public_projection_safety_passed=p0 == 0,
            allow_enter_l5_phase5=passed,
            blocking_reasons=tuple(item.message for item in items if item.blocking),
            evidence_index_refs=("evidence_index:l5_phase4_self_healing",),
            regression_index_refs=("regression_index:l5_phase4_self_healing",),
        )
        return report, gate

    def _check_self_healing_decl(self, decl: PluginSelfHealingDeclaration, add) -> None:
        required = (
            ("failure_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_FAILURE_REF_CONFLICT),
            ("fault_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_FAULT_REF_CONFLICT),
            ("diagnosis_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_DIAGNOSIS_REF_CONFLICT),
            ("root_cause_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_ROOT_CAUSE_REF_CONFLICT),
            ("recovery_plan_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_RECOVERY_PLAN_CONFLICT),
            ("checkpoint_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_CHECKPOINT_CONFLICT),
            ("recovery_point_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_RECOVERY_POINT_CONFLICT),
            ("transaction_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_TRANSACTION_CONFLICT),
            ("compensation_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_COMPENSATION_CONFLICT),
            ("audit_decl_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_AUDIT_CONFLICT),
            ("evidence_refs", PluginRegistryConflictKind.SELF_HEALING_MISSING_EVIDENCE_CONFLICT),
            ("validation_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_VALIDATION_CONFLICT),
            ("regression_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_REGRESSION_CONFLICT),
        )
        for field_name, kind in required:
            if _is_missing(getattr(decl, field_name)):
                add(kind, PluginRegistryConflictSeverity.P1, f"self-healing declaration missing {field_name}", f"self_healing.{field_name}")
        for field_name in ("failure_ref", "fault_ref", "diagnosis_ref", "root_cause_ref", "recovery_plan_ref", "postmortem_ref", "repair_suggestion_ref"):
            if is_live_entry_text(getattr(decl, field_name)):
                add(PluginRegistryConflictKind.SELF_HEALING_LIVE_REPAIR_EXECUTION_CONFLICT, PluginRegistryConflictSeverity.P0, f"self-healing field {field_name} contains live entry", f"self_healing.{field_name}")

    def _check_recovery_plan(self, plan: PluginRecoveryPlanDeclaration, add) -> None:
        required = (
            ("checkpoint_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_CHECKPOINT_CONFLICT),
            ("recovery_point_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_RECOVERY_POINT_CONFLICT),
            ("transaction_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_TRANSACTION_CONFLICT),
            ("compensation_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_COMPENSATION_CONFLICT),
            ("validation_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_VALIDATION_CONFLICT),
            ("regression_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_REGRESSION_CONFLICT),
            ("audit_decl_ref", PluginRegistryConflictKind.SELF_HEALING_MISSING_AUDIT_CONFLICT),
            ("evidence_refs", PluginRegistryConflictKind.SELF_HEALING_MISSING_EVIDENCE_CONFLICT),
        )
        for field_name, kind in required:
            if _is_missing(getattr(plan, field_name)):
                add(kind, PluginRegistryConflictSeverity.P1, f"recovery plan missing {field_name}", f"recovery_plan.{field_name}")
        for field_name in ("recovery_strategy_ref", "checkpoint_ref", "recovery_point_ref"):
            if is_live_entry_text(getattr(plan, field_name)):
                add(PluginRegistryConflictKind.SELF_HEALING_LIVE_RECOVERY_EXECUTION_CONFLICT, PluginRegistryConflictSeverity.P0, f"recovery plan field {field_name} contains live entry", f"recovery_plan.{field_name}")


__all__ = (
    "PluginRecoveryPlanDeclaration",
    "PluginSelfHealingDeclaration",
    "PluginSelfHealingValidationReport",
    "PluginSelfHealingQualityGateDecision",
    "PluginSelfHealingValidator",
)
