"""L6.40 MemoryRecallRoute：长期记忆摘要召回路由。

只输出 Planner 可消费的摘要级 hint，不暴露原始正文，不直接注入上下文，
不写长期记忆，不删除记忆。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .memory_math_core import DecayKernel, RecallScoreVector, level_weight
from .memory_store_bridge import MemoryRecord, MemoryStoreBridge

L6_40_MEMORY_RECALL_SCHEMA = "tiangong.l6_40.memory_recall_route.v1"


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:24]


def _lexical_similarity(query: str, summary: str) -> float:
    q_words = {w for w in query.lower().replace("/", " ").replace("_", " ").split() if w}
    s_words = {w for w in summary.lower().replace("/", " ").replace("_", " ").split() if w}
    if not q_words or not s_words:
        return 0.0
    return min(1.0, len(q_words & s_words) / max(1, len(q_words)))


@dataclass(frozen=True)
class PlannerMemoryHint:
    memory_id: str
    sanitized_summary: str
    recall_score: float
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    content_digest: str = ""
    summary_only: bool = True
    no_raw_memory_body: bool = True
    low_confidence_hint: bool = False

    def __post_init__(self) -> None:
        ensure_score(self.recall_score, "PlannerMemoryHint.recall_score")
        for field_name in ("summary_only", "no_raw_memory_body", "low_confidence_hint"):
            ensure_bool(getattr(self, field_name), f"PlannerMemoryHint.{field_name}")
        if not self.summary_only or not self.no_raw_memory_body:
            raise ValueError("PlannerMemoryHint must remain summary-only")

    def public_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "sanitized_summary": self.sanitized_summary,
            "recall_score": self.recall_score,
            "evidence_refs": list(self.evidence_refs),
            "content_digest": self.content_digest,
            "summary_only": self.summary_only,
            "no_raw_memory_body": self.no_raw_memory_body,
            "low_confidence_hint": self.low_confidence_hint,
        }


@dataclass(frozen=True)
class L640MemoryRecallRoute:
    route_id: str
    query_digest: str
    hints: tuple[PlannerMemoryHint, ...] = field(default_factory=tuple)
    filtered_count: int = 0
    planner_hint: str = ""
    planner_consumable: bool = True
    summary_only: bool = True
    no_raw_memory_body: bool = True
    no_direct_context_injection: bool = True
    no_long_term_write: bool = True
    no_memory_deletion: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "planner_consumable",
            "summary_only",
            "no_raw_memory_body",
            "no_direct_context_injection",
            "no_long_term_write",
            "no_memory_deletion",
        ):
            ensure_bool(getattr(self, field_name), f"L640MemoryRecallRoute.{field_name}")
        if not all((self.planner_consumable, self.summary_only, self.no_raw_memory_body, self.no_direct_context_injection, self.no_long_term_write, self.no_memory_deletion)):
            raise ValueError("L640MemoryRecallRoute boundary flags must remain true")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_40_MEMORY_RECALL_SCHEMA,
            "route_id": self.route_id,
            "query_digest": self.query_digest,
            "hints": [hint.public_dict() for hint in self.hints],
            "filtered_count": self.filtered_count,
            "planner_hint": self.planner_hint,
            "planner_consumable": self.planner_consumable,
            "summary_only": self.summary_only,
            "no_raw_memory_body": self.no_raw_memory_body,
            "no_direct_context_injection": self.no_direct_context_injection,
            "no_long_term_write": self.no_long_term_write,
            "no_memory_deletion": self.no_memory_deletion,
        }


class MemoryRecallRouter:
    def __init__(self, store: MemoryStoreBridge) -> None:
        self.store = store

    def _vector_for(self, record: MemoryRecord, query: str, *, now: float | None = None) -> RecallScoreVector:
        now_ts = float(now if now is not None else time())
        decay = DecayKernel(
            elapsed_seconds=max(0.0, now_ts - float(record.last_accessed_at)),
            half_life_seconds=record.half_life_seconds,
            reuse_count=record.reuse_count,
            success_rate=record.observed_success_rate,
        ).reinforced_decay
        return RecallScoreVector(
            task_relevance=record.task_relevance_score,
            semantic_similarity=_lexical_similarity(query, record.sanitized_summary),
            level_weight=level_weight(record.memory_level),
            freshness_decay=decay,
            reuse_signal=min(1.0, record.reuse_count / 10.0),
            success_signal=record.observed_success_rate,
            explicit_user_preference=record.importance_score if record.memory_category.value == "self_memory" else 0.0,
            procedural_fit=record.importance_score if record.memory_category.value == "procedural_memory" else 0.0,
            affective_attention_bias=0.0,
            privacy_risk=record.privacy_risk_score,
            pollution_risk=record.pollution_risk_score,
            conflict_score=record.conflict_score,
            uncertainty_score=1.0 - record.confidence_score,
            tombstone_state=record.tombstone_state,
            active_recall_suppressed=record.active_recall_suppressed,
            confidence_score=record.confidence_score,
        )

    def route(self, query: str, *, top_k: int = 5, now: float | None = None) -> L640MemoryRecallRoute:
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ValueError("top_k must be int")
        limit = max(1, min(top_k, 20))
        scored: list[tuple[float, MemoryRecord, RecallScoreVector]] = []
        filtered = 0
        for record in self.store.replay_records().values():
            vector = self._vector_for(record, query, now=now)
            if not vector.can_enter_planner_context:
                filtered += 1
                continue
            scored.append((vector.recall_score, record, vector))
        scored.sort(key=lambda item: item[0], reverse=True)
        hints = tuple(
            PlannerMemoryHint(
                memory_id=record.memory_id,
                sanitized_summary=record.sanitized_summary,
                recall_score=score,
                evidence_refs=record.evidence_refs,
                content_digest=record.content_digest,
                low_confidence_hint=vector.confidence_score < 0.60,
            )
            for score, record, vector in scored[:limit]
            if score > 0
        )
        planner_hint = "L6.40 MemoryRecallRoute：仅召回摘要级长期记忆 hint，不注入原文，不写/删 memory。"
        if hints:
            planner_hint += " top=" + "; ".join(f"{hint.memory_id}:{hint.recall_score:.2f}" for hint in hints[:5])
        return L640MemoryRecallRoute(
            route_id=f"memory_route:l6_40_{_digest((query, [h.memory_id for h in hints]))}",
            query_digest=_digest(query),
            hints=hints,
            filtered_count=filtered,
            planner_hint=planner_hint[:1200],
        )
