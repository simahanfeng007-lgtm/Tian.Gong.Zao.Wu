"""L6 phase7 adaptive-collaboration quality gate."""
from __future__ import annotations
from dataclasses import dataclass, field
from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from tiangong_kernel.l6_plugins.common.audit import L6AuditTraceEnvelope
from .common import L6_PHASE7

@dataclass(frozen=True)
class L6Phase7AdaptiveCollaborationQualityGateDecision:
    decision_ref: str = "quality:l6_phase7_adaptive_collaboration"
    phase: str = L6_PHASE7
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    adaptive_plugin_is_not_executor_passed: bool = True
    learning_need_review_not_learning_execution_passed: bool = True
    skill_candidate_not_registered_skill_passed: bool = True
    skill_patch_candidate_not_skill_write_passed: bool = True
    tool_gap_requirement_not_tool_production_passed: bool = True
    self_healing_diagnosis_not_healing_execution_passed: bool = True
    repair_plan_candidate_not_code_patch_passed: bool = True
    file_patch_requirement_not_file_write_passed: bool = True
    test_run_requirement_not_test_execution_passed: bool = True
    regression_requirement_not_pytest_execution_passed: bool = True
    iteration_proposal_not_iteration_apply_passed: bool = True
    contract_patch_candidate_not_contract_patch_passed: bool = True
    evolution_candidate_review_not_evolution_execution_passed: bool = True
    collaboration_plan_not_plugin_dispatch_passed: bool = True
    handoff_aggregation_not_auto_merge_passed: bool = True
    conflict_resolution_not_decision_passed: bool = True
    long_chain_recovery_not_scheduler_state_passed: bool = True
    no_live_model_call_passed: bool = True
    no_raw_tool_call_passed: bool = True
    no_direct_l4_adapter_passed: bool = True
    no_direct_file_write_passed: bool = True
    no_direct_test_execution_passed: bool = True
    no_direct_l2_write_passed: bool = True
    no_direct_memory_write_delete_passed: bool = True
    no_direct_audit_write_passed: bool = True
    no_direct_budget_charge_passed: bool = True
    no_raw_secret_passed: bool = True
    no_provider_base_url_or_api_key_passed: bool = True
    no_plugin_direct_import_call_state_write_passed: bool = True
    no_parallel_runtime_or_agent_scheduler_passed: bool = True
    no_old_runtime_abilitypackage_backflow_passed: bool = True
    public_projection_safety_passed: bool = True
    adaptive_execution_first_policy_passed: bool = True
    adaptive_long_chain_recovery_passed: bool = True
    adaptive_collaboration_boundary_passed: bool = True
    adaptive_result_not_faked_passed: bool = True
    audit_evidence_chain_passed: bool = True
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    test_inventory_compare_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase7_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase7_regression_index",))
    trace_ref: str = "ref:l6_phase7_quality_trace"
    audit_ref: str = "audit:l6_phase7_quality"
    responsibility_chain_ref: str = "responsibility:l6_phase7_quality"
    tamper_evidence_ref: str = "evidence:l6_phase7_quality_tamper"
    digest_summary: str = "summary:l6_phase7_quality"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6Phase7AdaptiveCollaborationQualityGateDecision.decision_ref")
        if self.phase != L6_PHASE7:
            raise ValueError("L6Phase7AdaptiveCollaborationQualityGateDecision.phase must be L6 phase7")
        for field_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{field_name} must be non-negative integer")
        bool_fields = tuple(name for name in self.__dataclass_fields__ if name.endswith("_passed") or name == "full_pytest_passed_for_freeze")
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"L6Phase7AdaptiveCollaborationQualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6Phase7AdaptiveCollaborationQualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L6Phase7AdaptiveCollaborationQualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6Phase7AdaptiveCollaborationQualityGateDecision.regression_index_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6Phase7AdaptiveCollaborationQualityGateDecision.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "L6Phase7AdaptiveCollaborationQualityGateDecision.digest_summary")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_enter_phase8(self) -> bool:
        bool_fields = tuple(name for name in self.__dataclass_fields__ if name.endswith("_passed") or name == "full_pytest_passed_for_freeze")
        return self.p0_count == 0 and self.p1_count == 0 and all(getattr(self, name) for name in bool_fields) and not self.blocking_reasons

    @property
    def allow_planning_continuation(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed and not self.blocking_reasons

    @property
    def digest(self) -> str:
        return stable_digest(self)
