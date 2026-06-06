"""L6.42 AutonomousLearning 接入路由。

本模块把学习缺口、成功经验、失败教训、Skill 草案和 Tool 需求压缩为
Planner 可消费的学习候选。它不写知识库、不写 Skill 注册表、不生产 Tool、
不释放工具句柄、不执行模型或工具。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

L6_42_SELF_LEARNING_SCHEMA = "tiangong.l6_42.self_learning_route.v1"


def _digest(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _text(value: Any, limit: int = 360) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    lowered = text.lower()
    for marker in ("api_key", "apikey", "authorization", "bearer ", "token", "secret", "password", "credential"):
        if marker in lowered:
            return "[redacted-sensitive-summary]"
    return text[:limit]


@dataclass(frozen=True)
class AutonomousLearningRoute:
    """Planner 可消费的自主学习接入路由。"""

    route_id: str
    generated_at: float = field(default_factory=time)
    learning_need_score: float = 0.0
    learning_gap_refs: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    skill_draft_refs: list[str] = field(default_factory=list)
    tool_need_refs: list[str] = field(default_factory=list)
    memory_promotion_refs: list[str] = field(default_factory=list)
    planner_hint: str = ""
    priority: str = "P3_learning_after_delivery"
    planner_consumable: bool = True
    candidate_only: bool = True
    review_before_activation: bool = True
    no_direct_execution: bool = True
    no_knowledge_write: bool = True
    no_skill_registry_write: bool = True
    no_skill_activation: bool = True
    no_tool_production: bool = True
    no_tool_registration: bool = True
    no_tool_invocation: bool = True
    no_model_dispatch: bool = True
    no_kernel_mutation: bool = True
    writes_knowledge: bool = False
    writes_skill_registry: bool = False
    activates_skill: bool = False
    produces_tool: bool = False
    registers_tool: bool = False
    invokes_tool: bool = False
    dispatches_model: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.route_id, 240):
            raise ValueError("AutonomousLearningRoute.route_id must be non-empty text")
        ensure_score(self.learning_need_score, "AutonomousLearningRoute.learning_need_score")
        for field_name in (
            "planner_consumable",
            "candidate_only",
            "review_before_activation",
            "no_direct_execution",
            "no_knowledge_write",
            "no_skill_registry_write",
            "no_skill_activation",
            "no_tool_production",
            "no_tool_registration",
            "no_tool_invocation",
            "no_model_dispatch",
            "no_kernel_mutation",
            "writes_knowledge",
            "writes_skill_registry",
            "activates_skill",
            "produces_tool",
            "registers_tool",
            "invokes_tool",
            "dispatches_model",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"AutonomousLearningRoute.{field_name}")
        required = (
            self.planner_consumable,
            self.candidate_only,
            self.review_before_activation,
            self.no_direct_execution,
            self.no_knowledge_write,
            self.no_skill_registry_write,
            self.no_skill_activation,
            self.no_tool_production,
            self.no_tool_registration,
            self.no_tool_invocation,
            self.no_model_dispatch,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("AutonomousLearningRoute must remain candidate-only and review-gated")
        forbidden = (
            self.writes_knowledge,
            self.writes_skill_registry,
            self.activates_skill,
            self.produces_tool,
            self.registers_tool,
            self.invokes_tool,
            self.dispatches_model,
            self.mutates_kernel,
        )
        if any(forbidden):
            raise ValueError("AutonomousLearningRoute cannot execute learning side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_SELF_LEARNING_SCHEMA,
            "route_id": _text(self.route_id, 240),
            "generated_at": self.generated_at,
            "learning_need_score": self.learning_need_score,
            "learning_gap_refs": [_text(item, 240) for item in self.learning_gap_refs],
            "evidence_refs": [_text(item, 240) for item in self.evidence_refs],
            "skill_draft_refs": [_text(item, 240) for item in self.skill_draft_refs],
            "tool_need_refs": [_text(item, 240) for item in self.tool_need_refs],
            "memory_promotion_refs": [_text(item, 240) for item in self.memory_promotion_refs],
            "planner_hint": _text(self.planner_hint, 900),
            "priority": self.priority,
            "planner_consumable": self.planner_consumable,
            "candidate_only": self.candidate_only,
            "review_before_activation": self.review_before_activation,
            "no_direct_execution": self.no_direct_execution,
            "no_knowledge_write": self.no_knowledge_write,
            "no_skill_registry_write": self.no_skill_registry_write,
            "no_skill_activation": self.no_skill_activation,
            "no_tool_production": self.no_tool_production,
            "no_tool_registration": self.no_tool_registration,
            "no_tool_invocation": self.no_tool_invocation,
            "no_model_dispatch": self.no_model_dispatch,
            "no_kernel_mutation": self.no_kernel_mutation,
            "writes_knowledge": self.writes_knowledge,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
            "produces_tool": self.produces_tool,
            "registers_tool": self.registers_tool,
            "invokes_tool": self.invokes_tool,
            "dispatches_model": self.dispatches_model,
            "mutates_kernel": self.mutates_kernel,
        }


def build_self_learning_route(
    *,
    learning_report: Any | None = None,
    memory_evidence: Any | None = None,
    user_requested_learning: bool = False,
    notes: str = "",
) -> AutonomousLearningRoute:
    """从学习合流报告和记忆证据生成学习候选。"""

    gaps: list[str] = []
    evidence: list[str] = []
    skill_refs: list[str] = []
    tool_refs: list[str] = []
    if learning_report is not None:
        for attr, target in (
            ("planner_hint_routes", gaps),
            ("source_refs", evidence),
            ("skill_draft_routes", skill_refs),
            ("tool_candidate_routes", tool_refs),
        ):
            value = getattr(learning_report, attr, None)
            if isinstance(value, list):
                for item in value[:6]:
                    ref = getattr(item, "route_ref", None) or getattr(item, "source_ref", None) or getattr(item, "tool_name", None) or getattr(item, "skill_name", None)
                    if ref:
                        target.append(_text(ref, 180))
    if memory_evidence is not None:
        ref = getattr(memory_evidence, "route_id", None) or getattr(memory_evidence, "snapshot_ref", None) or getattr(memory_evidence, "memory_id", None)
        if ref:
            evidence.append(_text(ref, 180))
    if notes and not gaps:
        gaps.append(f"learning:l6_42_manual_gap_{_digest(notes)}")
    base = 0.20 if gaps or skill_refs or tool_refs else 0.0
    need = min(1.0, base + 0.20 * bool(user_requested_learning) + 0.08 * len(skill_refs) + 0.08 * len(tool_refs))
    hint = "AutonomousLearning 接入：把学习缺口、Skill 草案和 Tool 需求压缩成 Planner hint；正式注册/激活/生产必须过质量门和执行链。"
    if user_requested_learning:
        hint += " 用户显式要求学习，本轮优先级上调但仍不直接写知识库。"
    elif notes:
        hint += f" 备注：{_text(notes, 180)}"
    return AutonomousLearningRoute(
        route_id=f"learning_route:{_digest([gaps, evidence, skill_refs, tool_refs, user_requested_learning, notes])}",
        learning_need_score=need,
        learning_gap_refs=gaps[:6],
        evidence_refs=evidence[:8],
        skill_draft_refs=skill_refs[:6],
        tool_need_refs=tool_refs[:6],
        memory_promotion_refs=[f"memory:l6_42_learning_promotion_{_digest(evidence)}"] if evidence else [],
        planner_hint=hint,
        priority="P2_user_requested_learning" if user_requested_learning else "P3_learning_after_delivery",
    )
