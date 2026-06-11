"""L6 phase8 unified quality gate."""
from __future__ import annotations
from dataclasses import dataclass, field
from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from tiangong_kernel.l6_plugins.common.audit import L6AuditTraceEnvelope
from .common import L6_PHASE8

@dataclass(frozen=True)
class L6UnifiedQualityGateDecision:
    decision_ref: str = "quality:l6_phase8_unified_quality_gate"
    phase: str = L6_PHASE8
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    stage_inventory_complete_passed: bool = True
    cross_phase_compatibility_passed: bool = True
    phase1_quality_gate_passed: bool = True
    phase2_quality_gate_passed: bool = True
    phase3_quality_gate_passed: bool = True
    phase4_quality_gate_passed: bool = True
    phase5_quality_gate_passed: bool = True
    phase6_quality_gate_passed: bool = True
    phase7_quality_gate_passed: bool = True
    unified_forbidden_scan_passed: bool = True
    unified_hash_compare_passed: bool = True
    unified_test_inventory_compare_passed: bool = True
    public_projection_safety_passed: bool = True
    audit_evidence_chain_passed: bool = True
    execution_first_review_passed: bool = True
    long_chain_capability_review_passed: bool = True
    no_live_model_call_passed: bool = True
    no_raw_tool_call_passed: bool = True
    no_direct_l4_adapter_passed: bool = True
    no_direct_file_write_passed: bool = True
    no_direct_zip_creation_as_plugin_action_passed: bool = True
    no_direct_test_execution_as_plugin_action_passed: bool = True
    no_direct_l2_write_passed: bool = True
    no_direct_memory_write_delete_passed: bool = True
    no_direct_audit_write_passed: bool = True
    no_direct_budget_charge_passed: bool = True
    no_raw_secret_passed: bool = True
    no_provider_base_url_or_api_key_passed: bool = True
    no_plugin_direct_import_call_state_write_passed: bool = True
    no_parallel_runtime_or_agent_scheduler_passed: bool = True
    no_old_runtime_abilitypackage_backflow_passed: bool = True
    planner_review_package_passed: bool = True
    planner_review_covers_18_roles_passed: bool = True
    final_freeze_requires_planner_review_passed: bool = True
    total_repair_required_after_planner_review_passed: bool = True
    l7_readiness_report_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze_candidate: bool = False
    zip_integrity_passed: bool = True
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase8_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase8_regression_index",))
    trace_ref: str = "ref:l6_phase8_quality_trace"
    audit_ref: str = "audit:l6_phase8_quality"
    responsibility_chain_ref: str = "responsibility:l6_phase8_quality"
    tamper_evidence_ref: str = "evidence:l6_phase8_quality_tamper"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6UnifiedQualityGateDecision.decision_ref")
        if self.phase != L6_PHASE8: raise ValueError("phase must be L6 phase8")
        for field_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0: raise ValueError(f"{field_name} must be non-negative integer")
        for field_name in tuple(name for name in self.__dataclass_fields__ if name.endswith("_passed") or name == "full_pytest_passed_for_freeze_candidate"):
            ensure_bool(getattr(self, field_name), f"L6UnifiedQualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6UnifiedQualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L6UnifiedQualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6UnifiedQualityGateDecision.regression_index_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6UnifiedQualityGateDecision.{field_name}")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope): raise ValueError("audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_planner_review(self) -> bool:
        return self.p0_count == 0 and self.p1_count == 0 and self.planner_review_package_passed and self.planner_review_covers_18_roles_passed and not self.blocking_reasons

    @property
    def allow_l6_candidate_freeze(self) -> bool:
        bool_fields = tuple(name for name in self.__dataclass_fields__ if name.endswith("_passed") or name == "full_pytest_passed_for_freeze_candidate")
        return self.p0_count == 0 and self.p1_count == 0 and all(getattr(self, name) for name in bool_fields) and not self.blocking_reasons

    @property
    def allow_final_freeze_after_planner_review_and_repair(self) -> str:
        return "conditional"

    @property
    def allow_l7_planning(self) -> bool:
        return self.allow_l6_candidate_freeze and self.l7_readiness_report_passed

    @property
    def digest(self) -> str:
        return stable_digest(self)
