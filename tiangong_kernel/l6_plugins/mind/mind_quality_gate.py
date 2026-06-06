"""L6 phase3 mind quality gate.

The gate computes phase4 eligibility from immutable evidence flags. Callers
cannot override allow_enter_phase4 directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from tiangong_kernel.l6_plugins.common.audit import L6AuditTraceEnvelope

from .common import L6_PHASE3


@dataclass(frozen=True)
class L6Phase3MindQualityGateDecision:
    decision_ref: str = "quality:l6_phase3_mind_quality_gate"
    phase: str = L6_PHASE3
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    mind_plugin_group_passed: bool = True
    mind_plugin_is_not_runtime_passed: bool = True
    mind_state_domain_passed: bool = True
    mind_state_not_l2_fact_passed: bool = True
    belief_candidate_not_fact_passed: bool = True
    world_candidate_not_canonical_state_passed: bool = True
    goal_priority_not_execution_plan_passed: bool = True
    attention_focus_not_interrupt_command_passed: bool = True
    affective_state_not_permission_passed: bool = True
    fatigue_projection_not_refusal_authority_passed: bool = True
    humanized_refusal_requires_governance_reason_passed: bool = True
    model_requirement_only_passed: bool = True
    tool_requirement_only_passed: bool = True
    no_direct_l4_adapter_passed: bool = True
    no_direct_l2_write_passed: bool = True
    no_direct_memory_write_passed: bool = True
    no_direct_audit_write_passed: bool = True
    no_direct_budget_charge_passed: bool = True
    no_raw_secret_passed: bool = True
    no_provider_base_url_or_api_key_passed: bool = True
    no_plugin_direct_import_call_state_write_passed: bool = True
    no_parallel_runtime_passed: bool = True
    mind_math_model_passed: bool = True
    score_is_not_authorization_passed: bool = True
    pollution_defense_passed: bool = True
    pollution_defense_not_value_dictatorship_passed: bool = True
    public_projection_safety_passed: bool = True
    affective_profile_minimal_disclosure_passed: bool = True
    event_projection_handoff_collaboration_passed: bool = True
    audit_evidence_chain_passed: bool = True
    responsibility_chain_passed: bool = True
    tamper_evidence_chain_passed: bool = True
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    test_inventory_compare_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase3_mind_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase3_regression_index",))
    rule_source_ref: str = "policy:l6_phase3_mind_quality_gate"
    detected_by_ref: str = "test:l6_phase3_mind_quality_gate"
    trace_ref: str = "ref:l6_phase3_mind_quality_trace"
    audit_ref: str = "audit:l6_phase3_mind_quality_audit"
    responsibility_chain_ref: str = "responsibility:l6_phase3_mind_quality_chain"
    tamper_evidence_ref: str = "evidence:l6_phase3_mind_quality_tamper"
    digest_summary: str = "summary:l6_phase3_mind_quality"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6Phase3MindQualityGateDecision.decision_ref")
        if self.phase != L6_PHASE3:
            raise ValueError("L6Phase3MindQualityGateDecision.phase must be L6 phase3")
        for field_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"L6Phase3MindQualityGateDecision.{field_name} must be non-negative integer")
        bool_fields = (
            "mind_plugin_group_passed", "mind_plugin_is_not_runtime_passed", "mind_state_domain_passed",
            "mind_state_not_l2_fact_passed", "belief_candidate_not_fact_passed", "world_candidate_not_canonical_state_passed",
            "goal_priority_not_execution_plan_passed", "attention_focus_not_interrupt_command_passed", "affective_state_not_permission_passed",
            "fatigue_projection_not_refusal_authority_passed", "humanized_refusal_requires_governance_reason_passed",
            "model_requirement_only_passed", "tool_requirement_only_passed", "no_direct_l4_adapter_passed", "no_direct_l2_write_passed",
            "no_direct_memory_write_passed", "no_direct_audit_write_passed", "no_direct_budget_charge_passed", "no_raw_secret_passed",
            "no_provider_base_url_or_api_key_passed", "no_plugin_direct_import_call_state_write_passed", "no_parallel_runtime_passed",
            "mind_math_model_passed", "score_is_not_authorization_passed", "pollution_defense_passed",
            "pollution_defense_not_value_dictatorship_passed", "public_projection_safety_passed", "affective_profile_minimal_disclosure_passed",
            "event_projection_handoff_collaboration_passed", "audit_evidence_chain_passed", "responsibility_chain_passed",
            "tamper_evidence_chain_passed", "forbidden_scan_passed", "hash_compare_passed", "test_inventory_compare_passed",
            "targeted_tests_passed", "full_pytest_passed_for_freeze",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"L6Phase3MindQualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6Phase3MindQualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L6Phase3MindQualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6Phase3MindQualityGateDecision.regression_index_refs", required=True)
        for field_name in ("rule_source_ref", "detected_by_ref", "trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6Phase3MindQualityGateDecision.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "L6Phase3MindQualityGateDecision.digest_summary")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("L6Phase3MindQualityGateDecision.audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_enter_phase4(self) -> bool:
        blocking_flags = (
            self.mind_plugin_group_passed,
            self.mind_plugin_is_not_runtime_passed,
            self.mind_state_domain_passed,
            self.mind_state_not_l2_fact_passed,
            self.belief_candidate_not_fact_passed,
            self.world_candidate_not_canonical_state_passed,
            self.goal_priority_not_execution_plan_passed,
            self.attention_focus_not_interrupt_command_passed,
            self.affective_state_not_permission_passed,
            self.fatigue_projection_not_refusal_authority_passed,
            self.humanized_refusal_requires_governance_reason_passed,
            self.model_requirement_only_passed,
            self.tool_requirement_only_passed,
            self.no_direct_l4_adapter_passed,
            self.no_direct_l2_write_passed,
            self.no_direct_memory_write_passed,
            self.no_direct_audit_write_passed,
            self.no_direct_budget_charge_passed,
            self.no_raw_secret_passed,
            self.no_provider_base_url_or_api_key_passed,
            self.no_plugin_direct_import_call_state_write_passed,
            self.no_parallel_runtime_passed,
            self.mind_math_model_passed,
            self.score_is_not_authorization_passed,
            self.pollution_defense_passed,
            self.pollution_defense_not_value_dictatorship_passed,
            self.public_projection_safety_passed,
            self.affective_profile_minimal_disclosure_passed,
            self.event_projection_handoff_collaboration_passed,
            self.audit_evidence_chain_passed,
            self.responsibility_chain_passed,
            self.tamper_evidence_chain_passed,
            self.forbidden_scan_passed,
            self.hash_compare_passed,
            self.test_inventory_compare_passed,
            self.targeted_tests_passed,
            self.full_pytest_passed_for_freeze,
        )
        return self.p0_count == 0 and self.p1_count == 0 and all(blocking_flags) and not self.blocking_reasons

    @property
    def allow_planning_continuation(self) -> bool:
        """Mind projections may keep flowing; freeze/phase entry still needs full pytest evidence."""
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed and not self.blocking_reasons

    @property
    def digest(self) -> str:
        return stable_digest(self)
