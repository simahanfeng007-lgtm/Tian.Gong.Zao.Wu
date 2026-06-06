"""L6.41 AffectiveExecutionRoute：情志执行力提示路由。

七情影响语言状态逻辑，六欲影响做事方式。二者均只降级为 Planner 可消费
hint，不授权、不拒绝、不调工具、不调模型、不改预算。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .affective_state import AffectiveState, clamp01

L6_41_AFFECTIVE_ROUTE_SCHEMA = "tiangong.l6_41.affective_execution_route.v2"


def _digest(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _score(value: float, field_name: str) -> None:
    ensure_score(value, field_name)


@dataclass(frozen=True)
class AffectivePlannerHint:
    style_hint: str
    language_state_logic: dict[str, Any]
    doing_mode_logic: dict[str, Any]
    candidate_priority_hint: str
    recovery_patience_hint: float
    risk_attention_hint: float
    long_chain_pacing_hint: float
    memory_modulation_hint: float
    same_risk_ranking_only: bool = True
    not_authorization: bool = True
    not_refusal: bool = True
    no_tool_dispatch: bool = True
    no_model_dispatch: bool = True
    no_budget_mutation: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.style_hint, str) or not self.style_hint.strip():
            raise ValueError("AffectivePlannerHint.style_hint must be non-empty text")
        if not isinstance(self.candidate_priority_hint, str) or not self.candidate_priority_hint.strip():
            raise ValueError("AffectivePlannerHint.candidate_priority_hint must be non-empty text")
        if not isinstance(self.language_state_logic, dict) or not isinstance(self.doing_mode_logic, dict):
            raise ValueError("AffectivePlannerHint logic fields must be dictionaries")
        for field_name in (
            "recovery_patience_hint",
            "risk_attention_hint",
            "long_chain_pacing_hint",
            "memory_modulation_hint",
        ):
            _score(getattr(self, field_name), f"AffectivePlannerHint.{field_name}")
        for field_name in (
            "same_risk_ranking_only",
            "not_authorization",
            "not_refusal",
            "no_tool_dispatch",
            "no_model_dispatch",
            "no_budget_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"AffectivePlannerHint.{field_name}")
        if not (
            self.same_risk_ranking_only
            and self.not_authorization
            and self.not_refusal
            and self.no_tool_dispatch
            and self.no_model_dispatch
            and self.no_budget_mutation
        ):
            raise ValueError("affective planner hint cannot authorize, refuse, dispatch or mutate budget")

    def public_dict(self) -> dict[str, Any]:
        return {
            "style_hint": self.style_hint,
            "language_state_logic": dict(self.language_state_logic),
            "doing_mode_logic": dict(self.doing_mode_logic),
            "candidate_priority_hint": self.candidate_priority_hint,
            "recovery_patience_hint": self.recovery_patience_hint,
            "risk_attention_hint": self.risk_attention_hint,
            "long_chain_pacing_hint": self.long_chain_pacing_hint,
            "memory_modulation_hint": self.memory_modulation_hint,
            "same_risk_ranking_only": self.same_risk_ranking_only,
            "not_authorization": self.not_authorization,
            "not_refusal": self.not_refusal,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_model_dispatch": self.no_model_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
        }


@dataclass(frozen=True)
class AffectiveExecutionRoute:
    route_id: str
    state_digest: str
    dominant_emotion: str
    dominant_desire: str
    planner_hint: AffectivePlannerHint
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_41_affective_state",))
    planner_consumable: bool = True
    route_only: bool = True
    language_state_logic_only: bool = True
    doing_mode_hint_only: bool = True
    not_authorization: bool = True
    not_refusal: bool = True
    no_tool_dispatch: bool = True
    no_model_dispatch: bool = True
    no_budget_mutation: bool = True
    no_quality_gate_override: bool = True
    schema_version: str = L6_41_AFFECTIVE_ROUTE_SCHEMA

    def __post_init__(self) -> None:
        if not isinstance(self.route_id, str) or not self.route_id.startswith("affective_route:"):
            raise ValueError("AffectiveExecutionRoute.route_id must be affective_route ref")
        if not isinstance(self.state_digest, str) or not self.state_digest:
            raise ValueError("AffectiveExecutionRoute.state_digest must be text")
        if not self.evidence_refs:
            raise ValueError("AffectiveExecutionRoute requires evidence refs")
        for ref in self.evidence_refs:
            if not isinstance(ref, str) or not ref.startswith("evidence:"):
                raise ValueError("AffectiveExecutionRoute evidence refs must be evidence refs")
        for field_name in (
            "planner_consumable",
            "route_only",
            "language_state_logic_only",
            "doing_mode_hint_only",
            "not_authorization",
            "not_refusal",
            "no_tool_dispatch",
            "no_model_dispatch",
            "no_budget_mutation",
            "no_quality_gate_override",
        ):
            ensure_bool(getattr(self, field_name), f"AffectiveExecutionRoute.{field_name}")
        if not (
            self.planner_consumable
            and self.route_only
            and self.language_state_logic_only
            and self.doing_mode_hint_only
            and self.not_authorization
            and self.not_refusal
            and self.no_tool_dispatch
            and self.no_model_dispatch
            and self.no_budget_mutation
            and self.no_quality_gate_override
        ):
            raise ValueError("affective route must remain planner hint only")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "route_id": self.route_id,
            "state_digest": self.state_digest,
            "dominant_emotion": self.dominant_emotion,
            "dominant_desire": self.dominant_desire,
            "planner_hint": self.planner_hint.public_dict(),
            "evidence_refs": list(self.evidence_refs),
            "planner_consumable": self.planner_consumable,
            "route_only": self.route_only,
            "language_state_logic_only": self.language_state_logic_only,
            "doing_mode_hint_only": self.doing_mode_hint_only,
            "not_authorization": self.not_authorization,
            "not_refusal": self.not_refusal,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_model_dispatch": self.no_model_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
            "no_quality_gate_override": self.no_quality_gate_override,
        }


class AffectiveExecutionRouter:
    """把动态情志状态降级为 Planner 可消费 hint。"""

    def route(self, state: AffectiveState) -> AffectiveExecutionRoute:
        emotion = state.emotion_vector
        desire = state.desire_vector
        language = state.language_logic.public_dict()
        doing = state.doing_logic.public_dict()
        style_hint = self._style_hint(state)
        candidate_priority_hint = self._candidate_priority_hint(state)
        risk_attention = clamp01(
            0.34 * emotion.fear
            + 0.26 * emotion.worry
            + 0.14 * emotion.surprise
            + 0.12 * emotion.anger
            + 0.14 * desire.survival
        )
        recovery_patience = clamp01(
            0.30 * emotion.thoughtfulness
            + 0.24 * desire.order
            + 0.22 * desire.survival
            + 0.14 * desire.rest
            + 0.10 * emotion.worry
        )
        long_chain_pacing = clamp01(
            0.65 * desire.rest
            + 0.25 * doing.get("pacing_compression_bias", 0.0)
            + 0.04 * state.allostatic_load
            + 0.03 * emotion.sadness
            + 0.02 * emotion.fear
            + 0.01 * emotion.worry
        )
        memory_modulation = clamp01(
            0.30 * emotion.thoughtfulness
            + 0.22 * desire.order
            + 0.18 * desire.achievement
            + 0.14 * emotion.surprise
            + 0.10 * desire.curiosity
            - 0.12 * desire.rest
        )
        hint = AffectivePlannerHint(
            style_hint=style_hint,
            language_state_logic=language,
            doing_mode_logic=doing,
            candidate_priority_hint=candidate_priority_hint,
            recovery_patience_hint=recovery_patience,
            risk_attention_hint=risk_attention,
            long_chain_pacing_hint=long_chain_pacing,
            memory_modulation_hint=memory_modulation,
        )
        return AffectiveExecutionRoute(
            route_id=f"affective_route:l6_41_{_digest(state.public_dict())}",
            state_digest=state.digest,
            dominant_emotion=state.dominant_emotion,
            dominant_desire=state.dominant_desire,
            planner_hint=hint,
        )

    def _style_hint(self, state: AffectiveState) -> str:
        dominant = state.dominant_emotion
        mapping = {
            "joy": "语言状态：表达可略微轻快，保留事实边界，禁止讨好式迎合。",
            "anger": "语言状态：加强重复错误与阻滞定位，语气保持克制，不归咎用户。",
            "worry": "语言状态：增加风险说明与不确定性标注，但不得扩大拦截范围。",
            "thoughtfulness": "语言状态：提高结构化、因果链和复核密度，适合长链规划。",
            "sadness": "语言状态：降低锐度与压迫感，保持交付导向，不减少执行。",
            "fear": "语言状态：提高 A5、凭证、隐私、不可逆副作用的解释密度，但不越权阻断。",
            "surprise": "语言状态：先提示异常输入或预测误差，再继续推进。",
        }
        return mapping[dominant]

    def _candidate_priority_hint(self, state: AffectiveState) -> str:
        dominant = state.dominant_desire
        mapping = {
            "survival": "做事方式：同风险等级内优先边界稳定、资源稳态、恢复点。",
            "curiosity": "做事方式：同风险等级内允许生成学习/探索候选，但不得抢当前任务。",
            "achievement": "做事方式：同风险等级内优先当前任务闭环、最短完成路径、产物交付。",
            "connection": "做事方式：同风险等级内加强用户意图对齐与沟通同步。",
            "order": "做事方式：同风险等级内优先清单化、验证、依赖顺序和可回放结构。",
            "rest": "做事方式：同风险等级内建议分段、压缩上下文、增加检查点；不得拒绝合法请求。",
        }
        return mapping[dominant]
