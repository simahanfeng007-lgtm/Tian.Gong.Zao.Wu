"""第八阶段统一候选晋升提示对象形状测试。"""

from dataclasses import fields, is_dataclass
from typing import get_type_hints

import tiangong_kernel.l1_ports.candidate_ports as ports


def test_candidate_promotion_hint_keeps_learning_iteration_and_evolution_candidates():
    """统一候选晋升提示必须同时保留学习、迭代、进化三类候选字段。"""
    assert is_dataclass(ports.CandidatePromotionHint)
    annotations = ports.CandidatePromotionHint.__annotations__
    assert "learning_candidate" in annotations
    assert "iteration_candidate" in annotations
    assert "evolution_candidate" in annotations
    assert "validation_refs" in annotations
    assert "verification_refs" in annotations


def test_candidate_promotion_hint_candidate_ref_is_required_and_first_field():
    """统一候选晋升提示必须以候选主引用作为必填入口。"""
    field_list = list(fields(ports.CandidatePromotionHint))
    assert field_list[0].name == "candidate_ref"
    assert "ResourceRef" in ports.CandidatePromotionHint.__annotations__["candidate_ref"]


def test_candidate_promotion_hint_request_payload_points_to_unified_hint_object():
    """候选晋升请求的 payload 必须指向修复后的统一 CandidatePromotionHint。"""
    hints = get_type_hints(ports.CandidatePromotionHintRequest)
    assert hints["payload"] is ports.CandidatePromotionHint
