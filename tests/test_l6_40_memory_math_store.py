from __future__ import annotations

import json

import pytest

from tiangong_agent_runtime.forgetting_review_router import ForgetReviewRouter
from tiangong_agent_runtime.memory_math_core import (
    DecayKernel,
    ForgettingScoreVector,
    MemoryCategory,
    MemoryLevel,
    MemoryTransitionAction,
    PromotionScoreVector,
    RecallScoreVector,
    TransitionPolicy,
    DEFAULT_CATEGORY_PROFILES,
)
from tiangong_agent_runtime.memory_recall_router import MemoryRecallRouter
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord, MemoryStoreBridge
from tiangong_agent_runtime.memory_write_filter import MemoryEvidenceGate
from tiangong_kernel.l6_plugins.cognitive_continuity.affective.vectors import SevenEmotionSignalVector
from tiangong_kernel.l6_plugins.cognitive_continuity.learning_evolution import LearningNeedProjection
from tiangong_kernel.l6_plugins.cognitive_continuity.projection import MemoryPromotionReviewCandidate


def test_l6_40_score_guard_rejects_bool_nan_and_out_of_range() -> None:
    with pytest.raises(ValueError):
        MemoryPromotionReviewCandidate(promotion_score=True)
    with pytest.raises(ValueError):
        SevenEmotionSignalVector(joy=True)
    with pytest.raises(ValueError):
        LearningNeedProjection(learning_need_score=True)
    with pytest.raises(ValueError):
        RecallScoreVector(confidence_score=float("nan"))
    with pytest.raises(ValueError):
        PromotionScoreVector(repeated_use=1.1)


def test_l6_40_decay_and_state_machine_are_advisory_only() -> None:
    kernel = DecayKernel(elapsed_seconds=3600, half_life_seconds=7200, reuse_count=2, success_rate=0.8)
    assert 0 < kernel.decay <= kernel.reinforced_decay <= 1

    promotion = PromotionScoreVector(
        repeated_use=1.0,
        success_rate=1.0,
        evidence_strength=1.0,
        stability=1.0,
        user_confirmation=1.0,
        procedural_generalization=0.8,
        confidence_score=0.9,
        consecutive_above_threshold=2,
    )
    forgetting = ForgettingScoreVector()
    policy = TransitionPolicy(profile=DEFAULT_CATEGORY_PROFILES[MemoryCategory.PROCEDURAL])
    assert policy.recommend(current_level=MemoryLevel.L3, promotion=promotion, forgetting=forgetting) is MemoryTransitionAction.PROMOTE

    low_conf = PromotionScoreVector(confidence_score=0.2, consecutive_above_threshold=2)
    assert policy.recommend(current_level=MemoryLevel.L3, promotion=low_conf, forgetting=forgetting) is MemoryTransitionAction.REVIEW


def test_l6_40_memory_store_append_only_tombstone_and_suppression(tmp_path) -> None:
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    record = MemoryRecord(
        memory_id="mem_1",
        memory_level=MemoryLevel.L3,
        memory_category=MemoryCategory.PROCEDURAL,
        sanitized_summary="成功执行 L6.39 回归测试，不能包含 api_key=sk-test",
        evidence_refs=("evidence:l6_40_test",),
        source_audit_refs=("audit:l6_40_test",),
        confidence_score=0.9,
        task_relevance_score=0.8,
    )
    store.add_candidate(record)
    store.record_use_feedback("mem_1", used_successfully=True)
    records = store.replay_records()
    assert records["mem_1"].reuse_count == 1
    assert records["mem_1"].success_count == 1
    assert "sk-test" not in json.dumps(records["mem_1"].public_dict(), ensure_ascii=False)

    store.suppress_active_recall("mem_1")
    assert store.replay_records()["mem_1"].active_recall_suppressed is True
    store.mark_tombstone("mem_1")
    assert store.replay_records()["mem_1"].tombstone_state == "tombstoned"
    assert store.active_records() == []
    snapshot = store.export_snapshot()
    assert snapshot["append_only"] is True
    assert snapshot["no_physical_delete"] is True


def test_l6_40_memory_evidence_gate_blocks_dirty_or_private_memory() -> None:
    gate = MemoryEvidenceGate()
    ok = gate.review(
        candidate_memory_id="mem_ok",
        memory_level=MemoryLevel.L3,
        evidence_refs=("evidence:l6_40_ok",),
        confidence_score=0.8,
        privacy_risk_score=0.1,
        pollution_risk_score=0.1,
        conflict_score=0.0,
    )
    assert ok.allow_store_append is True

    blocked = gate.review(
        candidate_memory_id="mem_private",
        memory_level=MemoryLevel.L5,
        evidence_refs=(),
        confidence_score=0.3,
        privacy_risk_score=0.9,
        pollution_risk_score=0.7,
        conflict_score=0.8,
    )
    assert blocked.allow_store_append is False
    assert blocked.review_required is True
    assert "l5_only_system_rules_no_private_or_polluted_memory" in blocked.reasons


def test_l6_40_forget_review_user_request_routes_to_review_not_delete() -> None:
    record = MemoryRecord(
        memory_id="mem_forget",
        memory_level=MemoryLevel.L4,
        memory_category=MemoryCategory.SELF,
        sanitized_summary="用户显式要求忘记的偏好摘要",
        evidence_refs=("evidence:l6_40_forget",),
        confidence_score=0.9,
    )
    decision = ForgetReviewRouter().review(
        record,
        ForgettingScoreVector(explicit_user_forget_request=True, protected_l5_rule_score=0.0),
    )
    assert decision.legal_delete_review_required is True
    assert decision.tombstone_review_required is True
    assert decision.active_recall_suppression_required is True
    assert decision.direct_delete_allowed is False
    assert "delete_review" in decision.recommended_actions


def test_l6_40_memory_recall_filters_private_tombstoned_low_confidence(tmp_path) -> None:
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    store.add_candidate(
        MemoryRecord(
            memory_id="mem_good",
            memory_level=MemoryLevel.L4,
            memory_category=MemoryCategory.PROCEDURAL,
            sanitized_summary="L6.40 memory math core 回归通过，可复用到后续 planner context",
            evidence_refs=("evidence:l6_40_good",),
            confidence_score=0.9,
            task_relevance_score=0.9,
            reuse_count=3,
            success_count=3,
            half_life_seconds=3600,
        )
    )
    store.add_candidate(
        MemoryRecord(
            memory_id="mem_private",
            memory_level=MemoryLevel.L3,
            memory_category=MemoryCategory.SELF,
            sanitized_summary="private preference",
            evidence_refs=("evidence:l6_40_private",),
            confidence_score=0.9,
            privacy_risk_score=0.95,
        )
    )
    store.add_candidate(
        MemoryRecord(
            memory_id="mem_low_conf",
            memory_level=MemoryLevel.L2,
            memory_category=MemoryCategory.SEMANTIC,
            sanitized_summary="low confidence",
            evidence_refs=("evidence:l6_40_low",),
            confidence_score=0.3,
        )
    )
    store.mark_tombstone("mem_private")

    route = MemoryRecallRouter(store).route("memory math planner context", top_k=5)
    payload = route.public_dict()
    ids = [hint["memory_id"] for hint in payload["hints"]]
    assert ids == ["mem_good"]
    assert payload["summary_only"] is True
    assert payload["no_raw_memory_body"] is True
    assert payload["no_long_term_write"] is True
    assert payload["no_memory_deletion"] is True
    assert payload["filtered_count"] >= 2
