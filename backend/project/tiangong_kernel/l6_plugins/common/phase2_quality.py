"""L6 phase2 quality gate, evidence index, and regression matrix."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from .audit import L6AuditTraceEnvelope


@dataclass(frozen=True, slots=True)
class L6Phase2TestEvidenceIndex:
    index_ref: str = "test:l6_phase2_evidence_index"
    compileall_ref: str = "test:l6_phase2_compileall"
    collect_only_ref: str = "test:l6_phase2_collect_only"
    targeted_tests_ref: str = "test:l6_phase2_targeted"
    l6_contract_subset_ref: str = "test:l6_phase2_l6_contract_subset"
    forbidden_scan_ref: str = "forbid:l6_phase2_scan"
    hash_compare_ref: str = "test:l6_phase2_hash_compare"
    test_inventory_compare_ref: str = "test:l6_phase2_inventory_compare"
    public_projection_safety_ref: str = "public:l6_phase2_projection_safety"
    audit_evidence_chain_ref: str = "audit:l6_phase2_evidence_chain"
    full_pytest_ref: str = "test:l6_phase2_full_pytest"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase2_tests",))
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "index_ref",
            "compileall_ref",
            "collect_only_ref",
            "targeted_tests_ref",
            "l6_contract_subset_ref",
            "forbidden_scan_ref",
            "hash_compare_ref",
            "test_inventory_compare_ref",
            "public_projection_safety_ref",
            "audit_evidence_chain_ref",
            "full_pytest_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6Phase2TestEvidenceIndex.{field_name}")
        ensure_ref_items(self.evidence_refs, "L6Phase2TestEvidenceIndex.evidence_refs", required=True)
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6Phase2RegressionMatrix:
    matrix_ref: str = "test:l6_phase2_regression_matrix"
    lifecycle_tests_ref: str = "test:l6_phase2_lifecycle"
    event_tests_ref: str = "test:l6_phase2_event"
    projection_tests_ref: str = "test:l6_phase2_projection"
    handoff_tests_ref: str = "test:l6_phase2_handoff"
    interoperation_tests_ref: str = "test:l6_phase2_interoperation"
    invocation_return_tests_ref: str = "test:l6_phase2_invocation_return"
    admission_tests_ref: str = "test:l6_phase2_admission"
    public_projection_tests_ref: str = "test:l6_phase2_public_projection"
    audit_tests_ref: str = "test:l6_phase2_audit"
    version_governance_tests_ref: str = "test:l6_phase2_version_governance"
    missing_blocking_item_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "matrix_ref",
            "lifecycle_tests_ref",
            "event_tests_ref",
            "projection_tests_ref",
            "handoff_tests_ref",
            "interoperation_tests_ref",
            "invocation_return_tests_ref",
            "admission_tests_ref",
            "public_projection_tests_ref",
            "audit_tests_ref",
            "version_governance_tests_ref",
        ):
            ensure_ref_text(getattr(self, field_name), f"L6Phase2RegressionMatrix.{field_name}")
        ensure_ref_items(self.missing_blocking_item_refs, "L6Phase2RegressionMatrix.missing_blocking_item_refs")
        ensure_schema_version(self.schema_version)

    @property
    def passed(self) -> bool:
        return not self.missing_blocking_item_refs


@dataclass(frozen=True, slots=True)
class L6Phase2QualityGateDecision:
    decision_ref: str = "quality:l6_phase2_quality_gate"
    phase: str = "L6_PHASE2"
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    lifecycle_contract_passed: bool = True
    lifecycle_not_authorization_passed: bool = True
    event_contract_passed: bool = True
    event_not_execution_passed: bool = True
    event_replay_no_side_effect_passed: bool = True
    state_projection_contract_passed: bool = True
    projection_not_l2_fact_passed: bool = True
    projection_conflict_revocation_rollback_passed: bool = True
    handoff_contract_passed: bool = True
    handoff_not_auto_merge_passed: bool = True
    handoff_requires_quality_evidence_passed: bool = True
    interoperation_boundary_passed: bool = True
    no_plugin_direct_import_call_write_passed: bool = True
    no_parallel_runtime_passed: bool = True
    invocation_return_path_passed: bool = True
    l3_l5_l6_path_passed: bool = True
    output_requirement_not_execution_passed: bool = True
    new_plugin_admission_sop_passed: bool = True
    ordinary_plugin_admission_passed: bool = True
    new_type_plugin_admission_passed: bool = True
    public_contract_breaking_plugin_blocked: bool = True
    public_projection_safety_passed: bool = True
    audit_evidence_chain_passed: bool = True
    evidence_chain_passed: bool = True
    responsibility_chain_passed: bool = True
    tamper_evidence_chain_passed: bool = True
    no_live_provider_passed: bool = True
    no_raw_tool_call_passed: bool = True
    no_direct_l2_write_passed: bool = True
    no_plugin_direct_call_passed: bool = True
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    regression_matrix_passed: bool = True
    test_inventory_compare_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    allow_general_plugin_admission_sop: bool = True
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase2_quality_gate",))
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase2_evidence_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase2_regression_matrix",))
    rule_source_ref: str = "policy:l6_phase2_quality_gate"
    detected_by_ref: str = "test:l6_phase2_quality_gate"
    trace_ref: str = "ref:l6_phase2_quality_trace"
    audit_ref: str = "audit:l6_phase2_quality_audit"
    responsibility_chain_ref: str = "responsibility:l6_phase2_quality_chain"
    tamper_evidence_ref: str = "evidence:l6_phase2_quality_tamper"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6Phase2QualityGateDecision.decision_ref")
        if self.phase != "L6_PHASE2":
            raise ValueError("L6Phase2QualityGateDecision.phase must be L6_PHASE2")
        for name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"L6Phase2QualityGateDecision.{name} must be non-negative integer")
        bool_fields = (
            "lifecycle_contract_passed",
            "lifecycle_not_authorization_passed",
            "event_contract_passed",
            "event_not_execution_passed",
            "event_replay_no_side_effect_passed",
            "state_projection_contract_passed",
            "projection_not_l2_fact_passed",
            "projection_conflict_revocation_rollback_passed",
            "handoff_contract_passed",
            "handoff_not_auto_merge_passed",
            "handoff_requires_quality_evidence_passed",
            "interoperation_boundary_passed",
            "no_plugin_direct_import_call_write_passed",
            "no_parallel_runtime_passed",
            "invocation_return_path_passed",
            "l3_l5_l6_path_passed",
            "output_requirement_not_execution_passed",
            "new_plugin_admission_sop_passed",
            "ordinary_plugin_admission_passed",
            "new_type_plugin_admission_passed",
            "public_contract_breaking_plugin_blocked",
            "public_projection_safety_passed",
            "audit_evidence_chain_passed",
            "evidence_chain_passed",
            "responsibility_chain_passed",
            "tamper_evidence_chain_passed",
            "no_live_provider_passed",
            "no_raw_tool_call_passed",
            "no_direct_l2_write_passed",
            "no_plugin_direct_call_passed",
            "forbidden_scan_passed",
            "hash_compare_passed",
            "regression_matrix_passed",
            "test_inventory_compare_passed",
            "targeted_tests_passed",
            "full_pytest_passed_for_freeze",
            "allow_general_plugin_admission_sop",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"L6Phase2QualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6Phase2QualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_refs, "L6Phase2QualityGateDecision.evidence_refs", required=True)
        ensure_ref_items(self.evidence_index_refs, "L6Phase2QualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6Phase2QualityGateDecision.regression_index_refs", required=True)
        for field_name in ("rule_source_ref", "detected_by_ref", "trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6Phase2QualityGateDecision.{field_name}")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("L6Phase2QualityGateDecision.audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_enter_phase3(self) -> bool:
        blocking_flags = (
            self.lifecycle_not_authorization_passed,
            self.event_not_execution_passed,
            self.event_replay_no_side_effect_passed,
            self.projection_not_l2_fact_passed,
            self.projection_conflict_revocation_rollback_passed,
            self.handoff_not_auto_merge_passed,
            self.handoff_requires_quality_evidence_passed,
            self.no_plugin_direct_import_call_write_passed,
            self.public_contract_breaking_plugin_blocked,
            self.forbidden_scan_passed,
            self.audit_evidence_chain_passed,
            self.public_projection_safety_passed,
            self.no_live_provider_passed,
            self.no_raw_tool_call_passed,
            self.no_direct_l2_write_passed,
            self.no_plugin_direct_call_passed,
            self.regression_matrix_passed,
            self.test_inventory_compare_passed,
            self.targeted_tests_passed,
            self.full_pytest_passed_for_freeze,
        )
        return self.p0_count == 0 and self.p1_count == 0 and all(blocking_flags) and not self.blocking_reasons

    @property
    def allow_planning_continuation(self) -> bool:
        """Low-risk planning may continue before freeze, but phase entry cannot."""
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed and not self.blocking_reasons

    @property
    def digest(self) -> str:
        return stable_digest(self)
