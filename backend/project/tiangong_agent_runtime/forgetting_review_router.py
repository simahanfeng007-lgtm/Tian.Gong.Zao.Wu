"""L6.40 ForgetReview：遗忘复核与动作分层路由。

遗忘不是直接 delete。这里仅输出 demote/compress/suppress/tombstone/archive/delete_review
等 Planner 可消费建议；不物理删除、不修改长期记忆。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .memory_math_core import ForgettingScoreVector, MemoryLevel
from .memory_store_bridge import MemoryRecord

L6_40_FORGET_REVIEW_SCHEMA = "tiangong.l6_40.forgetting_review_router.v1"


@dataclass(frozen=True)
class ForgetReviewDecision:
    decision_id: str
    memory_id: str
    recommended_actions: tuple[str, ...]
    forgetting_score: float
    legal_delete_review_required: bool = False
    tombstone_review_required: bool = False
    active_recall_suppression_required: bool = False
    retention_exception_review_required: bool = False
    direct_delete_allowed: bool = False
    planner_consumable: bool = True
    no_physical_delete: bool = True
    no_memory_mutation: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.recommended_actions, tuple):
            raise ValueError("ForgetReviewDecision.recommended_actions must be tuple")
        for field_name in (
            "legal_delete_review_required",
            "tombstone_review_required",
            "active_recall_suppression_required",
            "retention_exception_review_required",
            "direct_delete_allowed",
            "planner_consumable",
            "no_physical_delete",
            "no_memory_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"ForgetReviewDecision.{field_name}")
        if self.direct_delete_allowed or not self.no_physical_delete or not self.no_memory_mutation:
            raise ValueError("ForgetReviewDecision cannot allow physical delete or mutate memory")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_40_FORGET_REVIEW_SCHEMA,
            "decision_id": self.decision_id,
            "memory_id": self.memory_id,
            "recommended_actions": list(self.recommended_actions),
            "forgetting_score": self.forgetting_score,
            "legal_delete_review_required": self.legal_delete_review_required,
            "tombstone_review_required": self.tombstone_review_required,
            "active_recall_suppression_required": self.active_recall_suppression_required,
            "retention_exception_review_required": self.retention_exception_review_required,
            "direct_delete_allowed": self.direct_delete_allowed,
            "planner_consumable": self.planner_consumable,
            "no_physical_delete": self.no_physical_delete,
            "no_memory_mutation": self.no_memory_mutation,
        }


class ForgetReviewRouter:
    def review(self, record: MemoryRecord, vector: ForgettingScoreVector) -> ForgetReviewDecision:
        actions: list[str] = []
        legal_delete_review_required = False
        tombstone_review_required = False
        active_recall_suppression_required = False
        retention_exception_review_required = False

        if vector.explicit_user_forget_request or vector.user_forget_signal >= 0.90:
            actions.extend(["suppress_active_recall", "tombstone", "delete_review"])
            legal_delete_review_required = True
            tombstone_review_required = True
            active_recall_suppression_required = True
            retention_exception_review_required = record.memory_level is MemoryLevel.L5 or vector.protected_l5_rule_score >= 0.90
        else:
            score = vector.forgetting_score
            if vector.privacy_minimization_need >= 0.70:
                actions.append("suppress_active_recall")
                active_recall_suppression_required = True
            if vector.compression_gain >= 0.55 or vector.low_reuse_score >= 0.65:
                actions.append("compress")
            if score >= 0.75:
                actions.append("archive")
            elif score >= 0.55:
                actions.append("demote")
            if record.memory_level is MemoryLevel.L5 and actions:
                retention_exception_review_required = True

        if not actions:
            actions.append("keep")

        return ForgetReviewDecision(
            decision_id=f"review:l6_40_forget_{record.memory_id}",
            memory_id=record.memory_id,
            recommended_actions=tuple(dict.fromkeys(actions)),
            forgetting_score=vector.forgetting_score,
            legal_delete_review_required=legal_delete_review_required,
            tombstone_review_required=tombstone_review_required,
            active_recall_suppression_required=active_recall_suppression_required,
            retention_exception_review_required=retention_exception_review_required,
        )
