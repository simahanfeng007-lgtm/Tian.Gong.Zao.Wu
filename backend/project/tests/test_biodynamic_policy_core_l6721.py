from tiangong_agent_runtime.biodynamic_policy_core import BioDynamicState, dynamic_threshold
from tiangong_agent_runtime.execution_policy import ExecutionPolicy, PermitStatus, RiskLevel
from tiangong_agent_runtime.forgetting_review_router import ForgetReviewRouter
from tiangong_agent_runtime.memory_math_core import ForgettingScoreVector, MemoryCategory, MemoryLevel, PromotionScoreVector
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord
from tiangong_agent_runtime.memory_write_filter import MemoryEvidenceGate


def test_dynamic_threshold_moves_with_load_and_drive() -> None:
    cautious = dynamic_threshold(0.5, load=0.9, drive=0.1, recovery=0.1)
    active = dynamic_threshold(0.5, load=0.1, drive=0.9, recovery=0.9)
    assert cautious > active


def test_execution_policy_keeps_a5_hard_boundary_but_allows_low_risk() -> None:
    policy = ExecutionPolicy.default()
    assert policy.dynamic_status(RiskLevel.A5) is PermitStatus.BLOCKED
    assert policy.dynamic_status(RiskLevel.A2) is PermitStatus.ALLOWED


def test_memory_write_gate_uses_dynamic_review_under_pressure() -> None:
    gate = MemoryEvidenceGate()
    ok_review = gate.review(
        candidate_memory_id="m1",
        memory_level=MemoryLevel.L3,
        evidence_refs=("e1",),
        confidence_score=0.78,
        privacy_risk_score=0.02,
        pollution_risk_score=0.02,
        conflict_score=0.02,
        promotion=PromotionScoreVector(success_rate=0.8, evidence_strength=0.8, stability=0.8, confidence_score=0.8, consecutive_above_threshold=3),
    )
    risky_review = gate.review(
        candidate_memory_id="m2",
        memory_level=MemoryLevel.L5,
        evidence_refs=("e1",),
        confidence_score=0.48,
        privacy_risk_score=0.24,
        pollution_risk_score=0.18,
        conflict_score=0.36,
    )
    assert ok_review.allow_store_append is True
    assert risky_review.review_required is True


def test_forgetting_router_dynamic_actions_are_review_only_not_delete() -> None:
    record = MemoryRecord(
        memory_id="mem-forget",
        memory_level=MemoryLevel.L3,
        memory_category=MemoryCategory.WORKING,
        sanitized_summary="temporary fixture",
        evidence_refs=("ev",),
    )
    decision = ForgetReviewRouter().review(
        record,
        ForgettingScoreVector(
            expiry_score=0.9,
            low_reuse_score=0.8,
            low_confidence_score=0.8,
            compression_gain=0.7,
            privacy_minimization_need=0.7,
            user_forget_signal=0.4,
        ),
    )
    assert decision.direct_delete_allowed is False
    assert decision.no_physical_delete is True
    assert any(action in decision.recommended_actions for action in ("compress", "demote", "archive", "suppress_active_recall"))


def test_biodynamic_state_pressure_reduces_execution_score() -> None:
    calm = BioDynamicState(evidence=0.8, drive=0.8, recovery=0.8)
    stressed = BioDynamicState(evidence=0.8, drive=0.8, recovery=0.2, resource_pressure=0.9, failure_pressure=0.9, conflict_pressure=0.9)
    assert calm.execution_score > stressed.execution_score
