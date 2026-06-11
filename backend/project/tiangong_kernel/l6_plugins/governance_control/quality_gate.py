"""L6 phase5 governance-control quality gate."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from tiangong_kernel.l6_plugins.common.audit import L6AuditTraceEnvelope
from .common import L6_PHASE5


@dataclass(frozen=True)
class L6Phase5GovernanceQualityGateDecision:
    decision_ref: str = "quality:l6_phase5_governance_control"
    phase: str = L6_PHASE5
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    governance_plugin_is_not_l5_passed: bool = True
    requirement_is_not_permit_passed: bool = True
    risk_projection_is_not_decision_passed: bool = True
    permission_requirement_not_authorization_passed: bool = True
    budget_requirement_not_allocation_passed: bool = True
    audit_requirement_not_audit_write_passed: bool = True
    credential_ref_not_secret_access_passed: bool = True
    privacy_requirement_not_data_access_passed: bool = True
    human_gate_not_confirmation_ticket_passed: bool = True
    degradation_suggestion_not_command_passed: bool = True
    execution_first_policy_passed: bool = True
    hard_boundaries_preserved_passed: bool = True
    long_chain_governance_passed: bool = True
    low_risk_continuation_passed: bool = True
    reversible_candidate_continuation_passed: bool = True
    minimal_confirmation_policy_passed: bool = True
    governance_summary_not_interrupt_passed: bool = True
    no_live_model_call_passed: bool = True
    no_raw_tool_call_passed: bool = True
    no_direct_l4_adapter_passed: bool = True
    no_direct_l2_write_passed: bool = True
    no_direct_memory_write_passed: bool = True
    no_direct_memory_delete_passed: bool = True
    no_direct_audit_write_passed: bool = True
    no_direct_budget_charge_passed: bool = True
    no_live_budget_decrement_passed: bool = True
    no_live_limiter_passed: bool = True
    no_live_resource_allocation_passed: bool = True
    no_quota_reservation_passed: bool = True
    high_permission_budget_not_bypass_passed: bool = True
    no_raw_secret_passed: bool = True
    no_provider_base_url_or_api_key_passed: bool = True
    no_plugin_direct_import_call_state_write_passed: bool = True
    no_parallel_runtime_passed: bool = True
    no_old_runtime_abilitypackage_backflow_passed: bool = True
    public_projection_safety_passed: bool = True
    audit_evidence_chain_passed: bool = True
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    test_inventory_compare_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase5_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase5_regression_index",))
    trace_ref: str = "ref:l6_phase5_quality_trace"
    audit_ref: str = "audit:l6_phase5_quality"
    responsibility_chain_ref: str = "responsibility:l6_phase5_quality"
    tamper_evidence_ref: str = "evidence:l6_phase5_quality_tamper"
    digest_summary: str = "summary:l6_phase5_quality"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6Phase5GovernanceQualityGateDecision.decision_ref")
        if self.phase != L6_PHASE5:
            raise ValueError("L6Phase5GovernanceQualityGateDecision.phase must be L6 phase5")
        for field_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be non-negative integer")
        bool_fields = (
            "governance_plugin_is_not_l5_passed", "requirement_is_not_permit_passed", "risk_projection_is_not_decision_passed",
            "permission_requirement_not_authorization_passed", "budget_requirement_not_allocation_passed", "audit_requirement_not_audit_write_passed",
            "credential_ref_not_secret_access_passed", "privacy_requirement_not_data_access_passed", "human_gate_not_confirmation_ticket_passed",
            "degradation_suggestion_not_command_passed", "execution_first_policy_passed", "hard_boundaries_preserved_passed",
            "long_chain_governance_passed", "low_risk_continuation_passed", "reversible_candidate_continuation_passed",
            "minimal_confirmation_policy_passed", "governance_summary_not_interrupt_passed", "no_live_model_call_passed", "no_raw_tool_call_passed",
            "no_direct_l4_adapter_passed", "no_direct_l2_write_passed", "no_direct_memory_write_passed", "no_direct_memory_delete_passed",
            "no_direct_audit_write_passed", "no_direct_budget_charge_passed", "no_live_budget_decrement_passed", "no_live_limiter_passed",
            "no_live_resource_allocation_passed", "no_quota_reservation_passed", "high_permission_budget_not_bypass_passed",
            "no_raw_secret_passed", "no_provider_base_url_or_api_key_passed",
            "no_plugin_direct_import_call_state_write_passed", "no_parallel_runtime_passed", "no_old_runtime_abilitypackage_backflow_passed",
            "public_projection_safety_passed", "audit_evidence_chain_passed", "forbidden_scan_passed", "hash_compare_passed",
            "test_inventory_compare_passed", "targeted_tests_passed", "full_pytest_passed_for_freeze",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"L6Phase5GovernanceQualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6Phase5GovernanceQualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L6Phase5GovernanceQualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6Phase5GovernanceQualityGateDecision.regression_index_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6Phase5GovernanceQualityGateDecision.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "L6Phase5GovernanceQualityGateDecision.digest_summary")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_enter_phase6(self) -> bool:
        blocking_flags = (
            self.governance_plugin_is_not_l5_passed,
            self.requirement_is_not_permit_passed,
            self.risk_projection_is_not_decision_passed,
            self.permission_requirement_not_authorization_passed,
            self.budget_requirement_not_allocation_passed,
            self.audit_requirement_not_audit_write_passed,
            self.credential_ref_not_secret_access_passed,
            self.privacy_requirement_not_data_access_passed,
            self.human_gate_not_confirmation_ticket_passed,
            self.degradation_suggestion_not_command_passed,
            self.execution_first_policy_passed,
            self.hard_boundaries_preserved_passed,
            self.long_chain_governance_passed,
            self.low_risk_continuation_passed,
            self.reversible_candidate_continuation_passed,
            self.minimal_confirmation_policy_passed,
            self.governance_summary_not_interrupt_passed,
            self.no_live_model_call_passed,
            self.no_raw_tool_call_passed,
            self.no_direct_l4_adapter_passed,
            self.no_direct_l2_write_passed,
            self.no_direct_memory_write_passed,
            self.no_direct_memory_delete_passed,
            self.no_direct_audit_write_passed,
            self.no_direct_budget_charge_passed,
            self.no_live_budget_decrement_passed,
            self.no_live_limiter_passed,
            self.no_live_resource_allocation_passed,
            self.no_quota_reservation_passed,
            self.high_permission_budget_not_bypass_passed,
            self.no_raw_secret_passed,
            self.no_provider_base_url_or_api_key_passed,
            self.no_plugin_direct_import_call_state_write_passed,
            self.no_parallel_runtime_passed,
            self.no_old_runtime_abilitypackage_backflow_passed,
            self.public_projection_safety_passed,
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
        """Governance hints may summarize/degrade during work; phase freeze still needs full pytest evidence."""
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed and not self.blocking_reasons

    @property
    def digest(self) -> str:
        return stable_digest(self)
