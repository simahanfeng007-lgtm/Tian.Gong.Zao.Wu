"""L6.40 MemoryWriteFilter / EvidenceGate。

该模块只生成写入复核结论，不直接写长期记忆。真正 append-only 写入由
MemoryStoreBridge 在 runtime 治理入口显式调用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .memory_math_core import MemoryLevel, PromotionScoreVector

L6_40_MEMORY_WRITE_FILTER_SCHEMA = "tiangong.l6_40.memory_write_filter.v1"


@dataclass(frozen=True)
class MemoryWriteReview:
    review_id: str
    candidate_memory_id: str
    allow_store_append: bool
    review_required: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    planner_consumable: bool = True
    no_direct_long_term_write: bool = True
    no_raw_memory_body: bool = True
    no_memory_delete: bool = True

    def __post_init__(self) -> None:
        for field_name in ("planner_consumable", "no_direct_long_term_write", "no_raw_memory_body", "no_memory_delete"):
            ensure_bool(getattr(self, field_name), f"MemoryWriteReview.{field_name}")
        ensure_bool(self.allow_store_append, "MemoryWriteReview.allow_store_append")
        ensure_bool(self.review_required, "MemoryWriteReview.review_required")
        if not self.planner_consumable or not self.no_direct_long_term_write or not self.no_raw_memory_body or not self.no_memory_delete:
            raise ValueError("MemoryWriteReview boundary flags must remain true")
        if not isinstance(self.reasons, tuple):
            raise ValueError("MemoryWriteReview.reasons must be tuple")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_40_MEMORY_WRITE_FILTER_SCHEMA,
            "review_id": self.review_id,
            "candidate_memory_id": self.candidate_memory_id,
            "allow_store_append": self.allow_store_append,
            "review_required": self.review_required,
            "reasons": list(self.reasons),
            "planner_consumable": self.planner_consumable,
            "no_direct_long_term_write": self.no_direct_long_term_write,
            "no_raw_memory_body": self.no_raw_memory_body,
            "no_memory_delete": self.no_memory_delete,
        }


@dataclass(frozen=True)
class MemoryEvidenceGate:
    minimum_evidence_refs: int = 1
    minimum_confidence_score: float = 0.45
    privacy_block_threshold: float = 0.80
    pollution_review_threshold: float = 0.60
    conflict_review_threshold: float = 0.70

    def __post_init__(self) -> None:
        if isinstance(self.minimum_evidence_refs, bool) or not isinstance(self.minimum_evidence_refs, int) or self.minimum_evidence_refs < 0:
            raise ValueError("MemoryEvidenceGate.minimum_evidence_refs must be non-negative int")
        for field_name in ("minimum_confidence_score", "privacy_block_threshold", "pollution_review_threshold", "conflict_review_threshold"):
            ensure_score(getattr(self, field_name), f"MemoryEvidenceGate.{field_name}")

    def review(
        self,
        *,
        candidate_memory_id: str,
        memory_level: MemoryLevel | str,
        evidence_refs: tuple[str, ...],
        confidence_score: float,
        privacy_risk_score: float,
        pollution_risk_score: float,
        conflict_score: float,
        promotion: PromotionScoreVector | None = None,
    ) -> MemoryWriteReview:
        level = MemoryLevel(memory_level)
        for field_name, value in (
            ("confidence_score", confidence_score),
            ("privacy_risk_score", privacy_risk_score),
            ("pollution_risk_score", pollution_risk_score),
            ("conflict_score", conflict_score),
        ):
            ensure_score(value, f"MemoryEvidenceGate.{field_name}")
        reasons: list[str] = []
        if len(tuple(evidence_refs)) < self.minimum_evidence_refs:
            reasons.append("evidence_refs_insufficient")
        if confidence_score < self.minimum_confidence_score:
            reasons.append("confidence_below_gate")
        if privacy_risk_score >= self.privacy_block_threshold:
            reasons.append("privacy_risk_blocks_context")
        if pollution_risk_score >= self.pollution_review_threshold:
            reasons.append("pollution_review_required")
        if conflict_score >= self.conflict_review_threshold:
            reasons.append("conflict_review_required")
        if level is MemoryLevel.L5 and (privacy_risk_score > 0.0 or pollution_risk_score > 0.0):
            reasons.append("l5_only_system_rules_no_private_or_polluted_memory")
        if promotion is not None and promotion.cannot_promote:
            reasons.append("promotion_vector_rejects_auto_promotion")
        allow_store_append = not reasons
        return MemoryWriteReview(
            review_id=f"review:l6_40_memory_write_{abs(hash((candidate_memory_id, tuple(reasons)))):x}",
            candidate_memory_id=candidate_memory_id,
            allow_store_append=allow_store_append,
            review_required=bool(reasons),
            reasons=tuple(reasons),
        )
