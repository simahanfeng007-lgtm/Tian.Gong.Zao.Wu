"""L6 phase4 cognitive continuity quality gate."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from tiangong_kernel.l6_plugins.common.audit import L6AuditTraceEnvelope
from .common import L6_PHASE4


@dataclass(frozen=True)
class L6Phase4CognitiveContinuityQualityGateDecision:
    decision_ref: str = "quality:l6_phase4_cognitive_continuity"
    phase: str = L6_PHASE4
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    cognitive_group_passed: bool = True
    cognitive_group_is_not_runtime_passed: bool = True
    context_continuity_not_prompt_injection_passed: bool = True
    memory_candidate_no_write_passed: bool = True
    forgetting_candidate_no_removal_passed: bool = True
    explicit_forget_goes_to_review_passed: bool = True
    tombstone_is_proposal_only_passed: bool = True
    active_recall_suppression_is_proposal_only_passed: bool = True
    belief_world_candidate_not_fact_passed: bool = True
    candidate_fact_review_not_l2_write_passed: bool = True
    cognitive_reentry_goes_through_l3_l5_passed: bool = True
    affective_projection_is_not_fact_passed: bool = True
    fatigue_projection_no_refusal_passed: bool = True
    humanized_refusal_requires_governance_reason_passed: bool = True
    resource_pressure_not_fatigue_passed: bool = True
    no_live_resource_allocation_passed: bool = True
    no_live_quota_reservation_passed: bool = True
    high_permission_budget_not_bypass_passed: bool = True
    affective_pollution_no_removal_passed: bool = True
    affective_memory_hint_no_write_passed: bool = True
    seven_emotions_no_permission_bypass_passed: bool = True
    six_desires_no_action_dispatch_passed: bool = True
    affective_public_projection_redaction_passed: bool = True
    affective_reentry_goes_through_l3_l5_passed: bool = True
    affective_direct_call_forbidden_passed: bool = True
    affective_score_not_decision_passed: bool = True
    affective_full_profile_not_public_passed: bool = True
    self_reflection_learning_not_auto_repair_passed: bool = True
    product_bridge_seed_inert_passed: bool = True
    public_projection_safety_passed: bool = True
    audit_evidence_chain_passed: bool = True
    responsibility_chain_passed: bool = True
    forbidden_scan_passed: bool = True
    hash_compare_passed: bool = True
    test_inventory_compare_passed: bool = True
    targeted_tests_passed: bool = True
    full_pytest_passed_for_freeze: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_index",))
    regression_index_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase4_regression_index",))
    trace_ref: str = "ref:l6_phase4_quality_trace"
    audit_ref: str = "audit:l6_phase4_quality"
    responsibility_chain_ref: str = "responsibility:l6_phase4_quality"
    tamper_evidence_ref: str = "evidence:l6_phase4_quality_tamper"
    digest_summary: str = "summary:l6_phase4_quality"
    audit_trace: L6AuditTraceEnvelope = field(default_factory=L6AuditTraceEnvelope)
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.decision_ref, "L6Phase4CognitiveContinuityQualityGateDecision.decision_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("L6Phase4CognitiveContinuityQualityGateDecision.phase must be L6 phase4")
        for field_name in ("p0_count", "p1_count", "p2_count", "p3_count"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be non-negative integer")
        bool_fields = (
            "cognitive_group_passed", "cognitive_group_is_not_runtime_passed", "context_continuity_not_prompt_injection_passed",
            "memory_candidate_no_write_passed", "forgetting_candidate_no_removal_passed", "explicit_forget_goes_to_review_passed",
            "tombstone_is_proposal_only_passed", "active_recall_suppression_is_proposal_only_passed", "belief_world_candidate_not_fact_passed",
            "candidate_fact_review_not_l2_write_passed", "cognitive_reentry_goes_through_l3_l5_passed", "affective_projection_is_not_fact_passed",
            "fatigue_projection_no_refusal_passed", "humanized_refusal_requires_governance_reason_passed", "resource_pressure_not_fatigue_passed",
            "no_live_resource_allocation_passed", "no_live_quota_reservation_passed", "high_permission_budget_not_bypass_passed",
            "affective_pollution_no_removal_passed", "affective_memory_hint_no_write_passed", "seven_emotions_no_permission_bypass_passed",
            "six_desires_no_action_dispatch_passed", "affective_public_projection_redaction_passed", "affective_reentry_goes_through_l3_l5_passed",
            "affective_direct_call_forbidden_passed", "affective_score_not_decision_passed", "affective_full_profile_not_public_passed",
            "self_reflection_learning_not_auto_repair_passed", "product_bridge_seed_inert_passed", "public_projection_safety_passed",
            "audit_evidence_chain_passed", "responsibility_chain_passed", "forbidden_scan_passed", "hash_compare_passed",
            "test_inventory_compare_passed", "targeted_tests_passed", "full_pytest_passed_for_freeze",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"L6Phase4CognitiveContinuityQualityGateDecision.{field_name}")
        ensure_ref_items(self.blocking_reasons, "L6Phase4CognitiveContinuityQualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L6Phase4CognitiveContinuityQualityGateDecision.evidence_index_refs", required=True)
        ensure_ref_items(self.regression_index_refs, "L6Phase4CognitiveContinuityQualityGateDecision.regression_index_refs", required=True)
        for field_name in ("trace_ref", "audit_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"L6Phase4CognitiveContinuityQualityGateDecision.{field_name}")
        ensure_no_live_or_sensitive_text(self.digest_summary, "L6Phase4CognitiveContinuityQualityGateDecision.digest_summary")
        if not isinstance(self.audit_trace, L6AuditTraceEnvelope):
            raise ValueError("audit_trace must be L6AuditTraceEnvelope")
        ensure_schema_version(self.schema_version)

    @property
    def allow_enter_phase5(self) -> bool:
        blocking_flags = (
            self.cognitive_group_passed,
            self.cognitive_group_is_not_runtime_passed,
            self.context_continuity_not_prompt_injection_passed,
            self.memory_candidate_no_write_passed,
            self.forgetting_candidate_no_removal_passed,
            self.explicit_forget_goes_to_review_passed,
            self.tombstone_is_proposal_only_passed,
            self.active_recall_suppression_is_proposal_only_passed,
            self.belief_world_candidate_not_fact_passed,
            self.candidate_fact_review_not_l2_write_passed,
            self.cognitive_reentry_goes_through_l3_l5_passed,
            self.affective_projection_is_not_fact_passed,
            self.fatigue_projection_no_refusal_passed,
            self.humanized_refusal_requires_governance_reason_passed,
            self.resource_pressure_not_fatigue_passed,
            self.no_live_resource_allocation_passed,
            self.no_live_quota_reservation_passed,
            self.high_permission_budget_not_bypass_passed,
            self.affective_pollution_no_removal_passed,
            self.affective_memory_hint_no_write_passed,
            self.seven_emotions_no_permission_bypass_passed,
            self.six_desires_no_action_dispatch_passed,
            self.affective_public_projection_redaction_passed,
            self.affective_reentry_goes_through_l3_l5_passed,
            self.affective_direct_call_forbidden_passed,
            self.affective_score_not_decision_passed,
            self.affective_full_profile_not_public_passed,
            self.self_reflection_learning_not_auto_repair_passed,
            self.product_bridge_seed_inert_passed,
            self.public_projection_safety_passed,
            self.audit_evidence_chain_passed,
            self.responsibility_chain_passed,
            self.forbidden_scan_passed,
            self.hash_compare_passed,
            self.test_inventory_compare_passed,
            self.targeted_tests_passed,
            self.full_pytest_passed_for_freeze,
        )
        return self.p0_count == 0 and self.p1_count == 0 and all(blocking_flags) and not self.blocking_reasons

    @property
    def allow_planning_continuation(self) -> bool:
        """Review-only candidates may continue; freeze/phase entry still needs full pytest evidence."""
        return self.p0_count == 0 and self.p1_count == 0 and self.targeted_tests_passed and not self.blocking_reasons

    @property
    def digest(self) -> str:
        return stable_digest(self)
