"""L6 phase2 new plugin admission and public contract patch declarations."""

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
from .versioning import L6BreakingChangeAssessment, L6CompatibilityMatrix, L6MigrationPlanDeclaration, L6ReplayCompatibilityDeclaration, L6RollbackRouteDeclaration


class L6PluginAdmissionKind(str, Enum):
    ORDINARY_PLUGIN = "ordinary_plugin"
    NEW_TYPE_PLUGIN = "new_type_plugin"
    PUBLIC_CONTRACT_BREAKING_PLUGIN = "public_contract_breaking_plugin"


@dataclass(frozen=True, slots=True)
class L6PluginAdmissionDecision:
    decision_ref: str = "ref:l6_phase2_admission_decision"
    plugin_ref: str = "l6:plugin_ref"
    admission_kind: L6PluginAdmissionKind | str = L6PluginAdmissionKind.ORDINARY_PLUGIN
    manifest_ref: str = "ref:l6_manifest"
    versioned_contract_set_ref: str = "ref:l6_versioned_contract_set"
    compatibility_matrix_ref: str = "ref:l6_compatibility_matrix"
    forbidden_scan_ref: str = "forbid:l6_admission_scan"
    targeted_test_ref: str = "test:l6_admission_targeted_tests"
    public_projection_safety_ref: str = "public:l6_projection_safety"
    mini_specialty_design_ref: str = ""
    contract_patch_proposal_ref: str = ""
    l5_registration_governance_ref: str = "l5:l6_registration_governance"
    p0_count: int = 0
    p1_count: int = 0
    approved_declared: bool = True
    authorizes_execution: bool = False
    bypasses_l5: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "admission_kind", L6PluginAdmissionKind(self.admission_kind))
        for field_name in (
            "decision_ref",
            "plugin_ref",
            "manifest_ref",
            "versioned_contract_set_ref",
            "compatibility_matrix_ref",
            "forbidden_scan_ref",
            "targeted_test_ref",
            "public_projection_safety_ref",
            "l5_registration_governance_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6PluginAdmissionDecision.{field_name}")
        ensure_ref_text(self.mini_specialty_design_ref, "L6PluginAdmissionDecision.mini_specialty_design_ref", required=False)
        ensure_ref_text(self.contract_patch_proposal_ref, "L6PluginAdmissionDecision.contract_patch_proposal_ref", required=False)
        for name in ("p0_count", "p1_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"L6PluginAdmissionDecision.{name} must be non-negative integer")
        for field_name in ("approved_declared", "authorizes_execution", "bypasses_l5"):
            ensure_bool(getattr(self, field_name), f"L6PluginAdmissionDecision.{field_name}")
        if self.authorizes_execution or self.bypasses_l5:
            raise ValueError("L6 admission decision is not execution authorization and cannot bypass L5")
        if self.admission_kind is L6PluginAdmissionKind.NEW_TYPE_PLUGIN and not self.mini_specialty_design_ref:
            raise ValueError("new type L6 plugin admission requires mini specialty design")
        if self.admission_kind is L6PluginAdmissionKind.PUBLIC_CONTRACT_BREAKING_PLUGIN:
            if not self.contract_patch_proposal_ref:
                raise ValueError("public contract breaking plugin requires contract patch proposal")
            if self.approved_declared:
                raise ValueError("public contract breaking plugin must be blocked from direct admission")
        if self.p0_count > 0 or self.p1_count > 0:
            object.__setattr__(self, "approved_declared", False)
        ensure_schema_version(self.schema_version)

    @property
    def allowed_for_general_plugin_sop(self) -> bool:
        return self.approved_declared and self.p0_count == 0 and self.p1_count == 0 and self.admission_kind is not L6PluginAdmissionKind.PUBLIC_CONTRACT_BREAKING_PLUGIN


@dataclass(frozen=True, slots=True)
class L6PluginAdmissionReport:
    report_ref: str = "ref:l6_phase2_admission_report"
    decision_ref: str = "ref:l6_phase2_admission_decision"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_admission",))
    regression_matrix_ref: str = "test:l6_phase2_regression_matrix"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    public_projection_ref: str = "public:l6_admission_report"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.report_ref, "L6PluginAdmissionReport.report_ref")
        ensure_ref_text(self.decision_ref, "L6PluginAdmissionReport.decision_ref")
        ensure_ref_items(self.evidence_refs, "L6PluginAdmissionReport.evidence_refs", required=True)
        ensure_ref_text(self.regression_matrix_ref, "L6PluginAdmissionReport.regression_matrix_ref")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("L6PluginAdmissionReport.audit_trace must be L6AuditTraceEnvelope")
        ensure_ref_text(self.public_projection_ref, "L6PluginAdmissionReport.public_projection_ref")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6MiniSpecialtyDesignEnvelope:
    design_ref: str = "ref:l6_phase2_mini_specialty_design"
    plugin_type_ref: str = "ref:l6_new_type_plugin"
    design_summary: str = "summary:l6_new_type_design"
    public_contract_reuse_assessment_ref: str = "ref:l6_contract_reuse_assessment"
    namespaced_private_field_refs: tuple[str, ...] = field(default_factory=tuple)
    event_mapping_refs: tuple[str, ...] = field(default_factory=lambda: ("event:l6_new_type_mapping",))
    projection_mapping_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_new_type_mapping",))
    handoff_mapping_refs: tuple[str, ...] = field(default_factory=lambda: ("handoff:l6_new_type_mapping",))
    migration_note_ref: str = "migration:l6_new_type_migration_note"
    rollback_route_ref: str = "rollback:l6_new_type_rollback_route"
    replay_compatibility_ref: str = "ref:l6_new_type_replay_compatibility"
    changes_public_contract: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.design_ref, "L6MiniSpecialtyDesignEnvelope.design_ref")
        ensure_ref_text(self.plugin_type_ref, "L6MiniSpecialtyDesignEnvelope.plugin_type_ref")
        ensure_no_live_or_sensitive_text(self.design_summary, "L6MiniSpecialtyDesignEnvelope.design_summary")
        for field_name in (
            "public_contract_reuse_assessment_ref",
            "migration_note_ref",
            "rollback_route_ref",
            "replay_compatibility_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6MiniSpecialtyDesignEnvelope.{field_name}")
        for field_name in ("namespaced_private_field_refs", "event_mapping_refs", "projection_mapping_refs", "handoff_mapping_refs"):
            ensure_ref_items(getattr(self, field_name), f"L6MiniSpecialtyDesignEnvelope.{field_name}", required=field_name != "namespaced_private_field_refs")
        if self.changes_public_contract:
            raise ValueError("L6 mini specialty design cannot alter public contract; submit patch proposal instead")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6PublicContractPatchProposal:
    proposal_ref: str = "ref:l6_phase2_public_contract_patch_proposal"
    proposed_contract_refs: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_public_contract_patch",))
    impact_assessment_ref: str = "ref:l6_public_contract_patch_impact"
    compatibility_matrix_ref: str = "ref:l6_public_contract_patch_compatibility_matrix"
    migration_plan_ref: str = "migration:l6_public_contract_patch_migration"
    rollback_route_ref: str = "rollback:l6_public_contract_patch_rollback"
    replay_compatibility_ref: str = "ref:l6_public_contract_patch_replay"
    breaking_change_assessment_ref: str = "ref:l6_public_contract_patch_breaking_change"
    l5_compatibility_review_ref: str = "l5:l6_public_contract_patch_l5_review"
    regression_test_plan_ref: str = "test:l6_public_contract_patch_regression"
    authorizes_direct_admission: bool = False
    applies_patch: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.proposal_ref, "L6PublicContractPatchProposal.proposal_ref")
        ensure_ref_items(self.proposed_contract_refs, "L6PublicContractPatchProposal.proposed_contract_refs", required=True)
        for field_name in (
            "impact_assessment_ref",
            "compatibility_matrix_ref",
            "migration_plan_ref",
            "rollback_route_ref",
            "replay_compatibility_ref",
            "breaking_change_assessment_ref",
            "l5_compatibility_review_ref",
            "regression_test_plan_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6PublicContractPatchProposal.{field_name}")
        if self.authorizes_direct_admission or self.applies_patch:
            raise ValueError("L6 public contract patch proposal cannot directly admit plugin or apply patch")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6PublicContractPatchImpactAssessment:
    assessment_ref: str = "ref:l6_public_contract_patch_impact"
    compatibility_matrix: L6CompatibilityMatrix = field(default_factory=L6CompatibilityMatrix)
    migration_plan: L6MigrationPlanDeclaration = field(default_factory=L6MigrationPlanDeclaration)
    rollback_route: L6RollbackRouteDeclaration = field(default_factory=L6RollbackRouteDeclaration)
    replay_compatibility: L6ReplayCompatibilityDeclaration = field(default_factory=L6ReplayCompatibilityDeclaration)
    breaking_change: L6BreakingChangeAssessment = field(default_factory=L6BreakingChangeAssessment)
    impact_summary: str = "summary:l6_public_contract_patch_impact"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.assessment_ref, "L6PublicContractPatchImpactAssessment.assessment_ref")
        for field_name, expected_type in (
            ("compatibility_matrix", L6CompatibilityMatrix),
            ("migration_plan", L6MigrationPlanDeclaration),
            ("rollback_route", L6RollbackRouteDeclaration),
            ("replay_compatibility", L6ReplayCompatibilityDeclaration),
            ("breaking_change", L6BreakingChangeAssessment),
        ):
            if not isinstance(getattr(self, field_name), expected_type):
                raise ValueError(f"L6PublicContractPatchImpactAssessment.{field_name} must be {expected_type.__name__}")
        ensure_no_live_or_sensitive_text(self.impact_summary, "L6PublicContractPatchImpactAssessment.impact_summary")
        ensure_schema_version(self.schema_version)

    @property
    def has_required_controls(self) -> bool:
        return self.breaking_change.major_change_has_required_controls


@dataclass(frozen=True, slots=True)
class L6ContractPatchQualityGateDecision:
    decision_ref: str = "quality:l6_contract_patch_quality_gate"
    p0_count: int = 0
    p1_count: int = 0
    compatibility_matrix_passed: bool = True
    migration_plan_passed: bool = True
    rollback_route_passed: bool = True
    replay_compatibility_passed: bool = True
    l5_compatibility_review_passed: bool = True
    compileall_passed: bool = True
    collect_only_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    test_inventory_compare_passed: bool = True
    public_projection_safety_passed: bool = True
    audit_evidence_chain_passed: bool = True
    regression_test_plan_passed: bool = True
    applies_patch: bool = False
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_contract_patch_quality_gate",))
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6ContractPatchQualityGateDecision.decision_ref")
        for name in ("p0_count", "p1_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"L6ContractPatchQualityGateDecision.{name} must be non-negative integer")
        for field_name in (
            "compatibility_matrix_passed",
            "migration_plan_passed",
            "rollback_route_passed",
            "replay_compatibility_passed",
            "l5_compatibility_review_passed",
            "compileall_passed",
            "collect_only_passed",
            "targeted_tests_passed",
            "full_pytest_passed_for_freeze",
            "forbidden_scan_passed",
            "hash_compare_passed",
            "test_inventory_compare_passed",
            "public_projection_safety_passed",
            "audit_evidence_chain_passed",
            "regression_test_plan_passed",
            "applies_patch",
        ):
            ensure_bool(getattr(self, field_name), f"L6ContractPatchQualityGateDecision.{field_name}")
        ensure_ref_items(self.evidence_refs, "L6ContractPatchQualityGateDecision.evidence_refs", required=True)
        if self.applies_patch:
            raise ValueError("L6 contract patch quality gate cannot apply patch")
        ensure_schema_version(self.schema_version)

    @property
    def allow_planning_patch_review(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed

    @property
    def allow_freeze_contract_patch(self) -> bool:
        return (
            self.p0_count == 0
            and self.p1_count == 0
            and self.compatibility_matrix_passed
            and self.migration_plan_passed
            and self.rollback_route_passed
            and self.replay_compatibility_passed
            and self.l5_compatibility_review_passed
            and self.compileall_passed
            and self.collect_only_passed
            and self.targeted_tests_passed
            and self.full_pytest_passed_for_freeze
            and self.forbidden_scan_passed
            and self.hash_compare_passed
            and self.test_inventory_compare_passed
            and self.public_projection_safety_passed
            and self.audit_evidence_chain_passed
            and self.regression_test_plan_passed
        )


@dataclass(frozen=True, slots=True)
class L6ContractPatchPublicProjection:
    projection_ref: str = "public:l6_contract_patch_projection"
    proposal_ref: str = "ref:l6_phase2_public_contract_patch_proposal"
    impact_summary_ref: str = "summary:l6_contract_patch_impact"
    contains_raw_contract_body: bool = False
    contains_private_plugin_data: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.projection_ref, "L6ContractPatchPublicProjection.projection_ref")
        ensure_ref_text(self.proposal_ref, "L6ContractPatchPublicProjection.proposal_ref")
        ensure_ref_text(self.impact_summary_ref, "L6ContractPatchPublicProjection.impact_summary_ref")
        if self.contains_raw_contract_body or self.contains_private_plugin_data:
            raise ValueError("L6 contract patch public projection is minimal disclosure only")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ContractPatchAuditIndex:
    audit_index_ref: str = "audit:l6_contract_patch_audit_index"
    proposal_ref: str = "ref:l6_phase2_public_contract_patch_proposal"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_contract_patch",))
    responsibility_chain_ref: str = "responsibility:l6_contract_patch_chain"
    tamper_evidence_ref: str = "evidence:l6_contract_patch_tamper"
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_index_ref, "L6ContractPatchAuditIndex.audit_index_ref")
        ensure_ref_text(self.proposal_ref, "L6ContractPatchAuditIndex.proposal_ref")
        ensure_ref_items(self.evidence_refs, "L6ContractPatchAuditIndex.evidence_refs", required=True)
        ensure_ref_text(self.responsibility_chain_ref, "L6ContractPatchAuditIndex.responsibility_chain_ref")
        ensure_ref_text(self.tamper_evidence_ref, "L6ContractPatchAuditIndex.tamper_evidence_ref")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)
