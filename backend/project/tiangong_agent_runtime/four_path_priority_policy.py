"""L6.43 四主路径冲突仲裁策略。

只输出仲裁结论与硬边界，不触发执行。执行链 contract 永远优先。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .four_path_public_projection import sanitize_text, stable_digest

L6_43_PRIORITY_POLICY_SCHEMA = "tiangong.l6_43.four_path_priority_policy.v1"


@dataclass(frozen=True)
class FourPathPriorityDecision:
    conflict_ref: str
    conflict: str
    winner: str
    reason: str
    hard_boundary: bool = False
    planner_consumable: bool = True
    no_direct_execution: bool = True

    def __post_init__(self) -> None:
        for field_name in ("hard_boundary", "planner_consumable", "no_direct_execution"):
            ensure_bool(getattr(self, field_name), f"FourPathPriorityDecision.{field_name}")
        if not self.planner_consumable or not self.no_direct_execution:
            raise ValueError("FourPathPriorityDecision must remain planner-only")

    def public_dict(self) -> dict[str, Any]:
        return {
            "conflict_ref": sanitize_text(self.conflict_ref, limit=160),
            "conflict": sanitize_text(self.conflict, limit=240),
            "winner": sanitize_text(self.winner, limit=120),
            "reason": sanitize_text(self.reason, limit=520),
            "hard_boundary": self.hard_boundary,
            "planner_consumable": self.planner_consumable,
            "no_direct_execution": self.no_direct_execution,
        }


@dataclass(frozen=True)
class FourPathPriorityPolicyReport:
    report_id: str
    decisions: tuple[FourPathPriorityDecision, ...] = field(default_factory=tuple)
    hard_boundaries: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    planner_consumable: bool = True
    no_direct_execution: bool = True
    execution_contract_first: bool = True
    user_task_first_over_memory: bool = True
    permit_first_over_affective: bool = True
    user_task_first_over_lifecycle: bool = True
    delivery_first_over_learning: bool = True
    stability_first_over_iteration: bool = True
    quality_gate_first_over_package: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "planner_consumable",
            "no_direct_execution",
            "execution_contract_first",
            "user_task_first_over_memory",
            "permit_first_over_affective",
            "user_task_first_over_lifecycle",
            "delivery_first_over_learning",
            "stability_first_over_iteration",
            "quality_gate_first_over_package",
        ):
            ensure_bool(getattr(self, field_name), f"FourPathPriorityPolicyReport.{field_name}")
        if not all(
            (
                self.planner_consumable,
                self.no_direct_execution,
                self.execution_contract_first,
                self.user_task_first_over_memory,
                self.permit_first_over_affective,
                self.user_task_first_over_lifecycle,
                self.delivery_first_over_learning,
                self.stability_first_over_iteration,
                self.quality_gate_first_over_package,
            )
        ):
            raise ValueError("FourPathPriorityPolicyReport boundary flags must remain true")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_43_PRIORITY_POLICY_SCHEMA,
            "report_id": sanitize_text(self.report_id, limit=160),
            "decisions": [item.public_dict() for item in self.decisions],
            "hard_boundaries": list(self.hard_boundaries),
            "planner_consumable": self.planner_consumable,
            "no_direct_execution": self.no_direct_execution,
            "execution_contract_first": self.execution_contract_first,
            "user_task_first_over_memory": self.user_task_first_over_memory,
            "permit_first_over_affective": self.permit_first_over_affective,
            "user_task_first_over_lifecycle": self.user_task_first_over_lifecycle,
            "delivery_first_over_learning": self.delivery_first_over_learning,
            "stability_first_over_iteration": self.stability_first_over_iteration,
            "quality_gate_first_over_package": self.quality_gate_first_over_package,
        }


class FourPathPriorityPolicy:
    """固定四路径冲突仲裁。"""

    def build_report(self, *, include_quality_gate: bool = True, notes: str = "") -> FourPathPriorityPolicyReport:
        decisions = (
            FourPathPriorityDecision(
                conflict_ref="conflict:memory_vs_user_task",
                conflict="Memory vs UserTask",
                winner="current_user_task",
                reason="当前用户明确任务优先；记忆只能提供摘要经验，不能覆盖本轮指令。",
            ),
            FourPathPriorityDecision(
                conflict_ref="conflict:affective_vs_permit",
                conflict="Affective vs PermitGateway",
                winner="permit_gateway",
                reason="七情六欲只影响表达和同风险排序，不得授权、拒绝或扩大拦截范围。",
            ),
            FourPathPriorityDecision(
                conflict_ref="conflict:lifecycle_vs_user_task",
                conflict="Lifecycle vs UserTask",
                winner="current_user_task",
                reason="自愈、学习、自由意志、自迭代均不得抢占当前用户任务。",
            ),
            FourPathPriorityDecision(
                conflict_ref="conflict:learning_vs_delivery",
                conflict="Learning vs Delivery",
                winner="delivery_closure",
                reason="交付闭环优先；学习候选在任务完成后沉淀。",
            ),
            FourPathPriorityDecision(
                conflict_ref="conflict:iteration_vs_stability",
                conflict="Iteration vs Stability",
                winner="rollback_and_stability",
                reason="自我迭代必须先有回滚点、验证要求和用户确认，不得自动热切换。",
            ),
            FourPathPriorityDecision(
                conflict_ref="conflict:quality_gate_vs_package",
                conflict="QualityGate vs Package/Activation",
                winner="quality_gate",
                reason="发布、打包、Skill 激活、Tool 注册、合入必须由质量门优先裁决。",
                hard_boundary=include_quality_gate,
            ),
        )
        hard_boundaries = (
            {
                "boundary_ref": "boundary:l6_43_execution_contract_only",
                "risk_level": "A5",
                "title": "唯一执行链",
                "rule": "任何真实工具调用、写文件、Provider 实调、注册、激活、发布、热切换必须回到 L6.37 ExecutionSpine/治理链。",
                "blocks_execution": True,
            },
            {
                "boundary_ref": "boundary:l6_43_no_core_pollution",
                "risk_level": "A5",
                "title": "核心组不可污染",
                "rule": "FourPath 只读核心 contract/schema/report，不修改 L0-L5、执行脊柱、Registry、Adapter、Provider、QualityGate。",
                "blocks_execution": True,
            },
            {
                "boundary_ref": "boundary:l6_43_projection_only",
                "risk_level": "A4",
                "title": "投影层只给 PlannerContext",
                "rule": "Memory/Affective/Lifecycle/P0 支撑对象必须压缩为 ref/digest/summary，不暴露散对象和原文。",
                "blocks_execution": False,
            },
        )
        report_id = f"four_path_priority:{stable_digest([item.public_dict() for item in decisions], length=16)}"
        if notes:
            report_id += f":{stable_digest(notes, length=8)}"
        return FourPathPriorityPolicyReport(report_id=report_id, decisions=decisions, hard_boundaries=hard_boundaries)
