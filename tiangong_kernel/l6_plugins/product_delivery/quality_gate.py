"""L6 phase6 product-delivery quality gate."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from tiangong_kernel.l6_plugins.common.audit import L6AuditTraceEnvelope
from .common import L6_PHASE6


@dataclass(frozen=True)
class L6Phase6ProductDeliveryQualityGateDecision:
    decision_ref: str = "quality:l6_phase6_product_delivery"
    phase: str = L6_PHASE6
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    product_delivery_plugin_is_not_executor_passed: bool = True
    product_seed_is_not_product_spec_passed: bool = True
    product_plan_candidate_not_execution_plan_passed: bool = True
    artifact_structure_candidate_not_file_tree_passed: bool = True
    delivery_package_candidate_not_zip_passed: bool = True
    product_quality_gate_candidate_not_passed_result_passed: bool = True
    product_dispatch_intent_not_execution_passed: bool = True
    file_write_requirement_not_file_write_passed: bool = True
    package_build_requirement_not_zip_creation_passed: bool = True
    test_run_requirement_not_test_execution_passed: bool = True
    tool_requirement_not_tool_call_passed: bool = True
    model_requirement_not_model_call_passed: bool = True
    governance_review_required_before_dispatch_passed: bool = True
    no_live_model_call_passed: bool = True
    no_raw_tool_call_passed: bool = True
    no_direct_l4_adapter_passed: bool = True
    no_direct_file_write_passed: bool = True
    no_direct_zip_creation_passed: bool = True
    no_direct_test_execution_passed: bool = True
    no_direct_l2_write_passed: bool = True
    no_direct_memory_write_delete_passed: bool = True
    no_direct_audit_write_passed: bool = True
    no_direct_budget_charge_passed: bool = True
    no_raw_secret_passed: bool = True
    no_provider_base_url_or_api_key_passed: bool = True
    no_plugin_direct_import_call_state_write_passed: bool = True
    no_parallel_runtime_passed: bool = True
    no_old_runtime_abilitypackage_backflow_passed: bool = True
    public_projection_safety_passed: bool = True
    product_execution_first_policy_passed: bool = True
    product_long_chain_checkpoint_passed: bool = True
    product_minimal_clarification_passed: bool = True
    product_failure_recovery_passed: bool = True
    product_result_not_faked_passed: bool = True
    audit_evidence_chain_passed: bool = True
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    test_inventory_compare_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase6_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase6_regression_index",))
    trace_ref: str = "ref:l6_phase6_quality_trace"
    audit_ref: str = "audit:l6_phase6_quality"
    responsibility_chain_ref: str = "responsibility:l6_phase6_quality"
    tamper_evidence_ref: str = "evidence:l6_phase6_quality_tamper"
    digest_summary: str = "summary:l6_phase6_quality"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6Phase6ProductDeliveryQualityGateDecision.decision_ref")
        if self.phase != L6_PHASE6:
            raise ValueError("L6Phase6ProductDeliveryQualityGateDecision.phase must be L6 phase6")
        for field_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be non-negative integer")
        bool_fields = (
            "product_delivery_plugin_is_not_executor_passed", "product_seed_is_not_product_spec_passed",
            "product_plan_candidate_not_execution_plan_passed", "artifact_structure_candidate_not_file_tree_passed",
            "delivery_package_candidate_not_zip_passed", "product_quality_gate_candidate_not_passed_result_passed",
            "product_dispatch_intent_not_execution_passed", "file_write_requirement_not_file_write_passed",
            "package_build_requirement_not_zip_creation_passed", "test_run_requirement_not_test_execution_passed",
            "tool_requirement_not_tool_call_passed", "model_requirement_not_model_call_passed", "governance_review_required_before_dispatch_passed",
            "no_live_model_call_passed", "no_raw_tool_call_passed", "no_direct_l4_adapter_passed", "no_direct_file_write_passed",
            "no_direct_zip_creation_passed", "no_direct_test_execution_passed", "no_direct_l2_write_passed", "no_direct_memory_write_delete_passed",
            "no_direct_audit_write_passed", "no_direct_budget_charge_passed", "no_raw_secret_passed", "no_provider_base_url_or_api_key_passed",
            "no_plugin_direct_import_call_state_write_passed", "no_parallel_runtime_passed", "no_old_runtime_abilitypackage_backflow_passed",
            "public_projection_safety_passed", "product_execution_first_policy_passed", "product_long_chain_checkpoint_passed",
            "product_minimal_clarification_passed", "product_failure_recovery_passed", "product_result_not_faked_passed",
            "audit_evidence_chain_passed", "forbidden_scan_passed", "hash_compare_passed", "test_inventory_compare_passed",
            "targeted_tests_passed", "full_pytest_passed_for_freeze",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"L6Phase6ProductDeliveryQualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6Phase6ProductDeliveryQualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L6Phase6ProductDeliveryQualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6Phase6ProductDeliveryQualityGateDecision.regression_index_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6Phase6ProductDeliveryQualityGateDecision.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "L6Phase6ProductDeliveryQualityGateDecision.digest_summary")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_enter_phase7(self) -> bool:
        blocking_flags = (
            self.product_delivery_plugin_is_not_executor_passed,
            self.product_seed_is_not_product_spec_passed,
            self.product_plan_candidate_not_execution_plan_passed,
            self.artifact_structure_candidate_not_file_tree_passed,
            self.delivery_package_candidate_not_zip_passed,
            self.product_quality_gate_candidate_not_passed_result_passed,
            self.product_dispatch_intent_not_execution_passed,
            self.file_write_requirement_not_file_write_passed,
            self.package_build_requirement_not_zip_creation_passed,
            self.test_run_requirement_not_test_execution_passed,
            self.tool_requirement_not_tool_call_passed,
            self.model_requirement_not_model_call_passed,
            self.governance_review_required_before_dispatch_passed,
            self.no_live_model_call_passed,
            self.no_raw_tool_call_passed,
            self.no_direct_l4_adapter_passed,
            self.no_direct_file_write_passed,
            self.no_direct_zip_creation_passed,
            self.no_direct_test_execution_passed,
            self.no_direct_l2_write_passed,
            self.no_direct_memory_write_delete_passed,
            self.no_direct_audit_write_passed,
            self.no_direct_budget_charge_passed,
            self.no_raw_secret_passed,
            self.no_provider_base_url_or_api_key_passed,
            self.no_plugin_direct_import_call_state_write_passed,
            self.no_parallel_runtime_passed,
            self.no_old_runtime_abilitypackage_backflow_passed,
            self.public_projection_safety_passed,
            self.product_execution_first_policy_passed,
            self.product_long_chain_checkpoint_passed,
            self.product_minimal_clarification_passed,
            self.product_failure_recovery_passed,
            self.product_result_not_faked_passed,
            self.audit_evidence_chain_passed,
            self.forbidden_scan_passed,
            self.hash_compare_passed,
            self.test_inventory_compare_passed,
            self.targeted_tests_passed,
            self.full_pytest_passed_for_freeze,
        )
        return self.p0_count == 0 and self.p1_count == 0 and all(blocking_flags) and not self.blocking_reasons

    @property
    def allow_planning_continuation(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed and not self.blocking_reasons

    @property
    def digest(self) -> str:
        return stable_digest(self)
