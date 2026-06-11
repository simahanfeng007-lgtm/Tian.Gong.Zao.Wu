"""L6.42.1 AutonomousGoalQueue 自由意志自主目标队列。

目标队列只保存候选目标，不执行目标。目标进入真实行动前必须被 Planner 消费，
再回到 L6.37 执行链、PermitGateway、AuditBridge 与 QualityGate。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .lifecycle_clock import LifecycleClockTick

L6_42_1_AUTONOMOUS_GOAL_QUEUE_SCHEMA = "tiangong.l6_42_1.autonomous_goal_queue.v1"
GOAL_TYPES = {"learning", "task", "maintenance", "review", "iteration"}
GOAL_STATUSES = {"queued", "planner_ready", "blocked", "completed", "discarded"}
RISK_LEVELS = {"A0", "A1", "A2", "A3", "A4", "A5"}


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


def _risk_penalty(risk_level: str) -> float:
    return {"A0": 0.0, "A1": 0.08, "A2": 0.18, "A3": 0.34, "A4": 0.58, "A5": 1.0}.get(risk_level, 1.0)


@dataclass(frozen=True)
class AutonomousGoal:
    """自由意志目标候选。"""

    goal_id: str
    goal_type: str
    summary: str
    source_tick_id: str = ""
    source_refs: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time)
    expected_value_score: float = 0.0
    risk_level: str = "A1"
    budget_estimate_score: float = 0.0
    requires_confirmation: bool = False
    status: str = "queued"
    planner_hint: str = ""
    planner_consumable: bool = True
    candidate_only: bool = True
    no_direct_execution: bool = True
    no_background_execution: bool = True
    no_tool_invocation: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_kernel_mutation: bool = True
    invokes_tool: bool = False
    mutates_budget: bool = False
    writes_memory: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.goal_id, 240):
            raise ValueError("AutonomousGoal.goal_id must be non-empty text")
        if self.goal_type not in GOAL_TYPES:
            raise ValueError("AutonomousGoal.goal_type is invalid")
        if self.risk_level not in RISK_LEVELS:
            raise ValueError("AutonomousGoal.risk_level is invalid")
        if self.status not in GOAL_STATUSES:
            raise ValueError("AutonomousGoal.status is invalid")
        ensure_score(self.expected_value_score, "AutonomousGoal.expected_value_score")
        ensure_score(self.budget_estimate_score, "AutonomousGoal.budget_estimate_score")
        for field_name in (
            "requires_confirmation",
            "planner_consumable",
            "candidate_only",
            "no_direct_execution",
            "no_background_execution",
            "no_tool_invocation",
            "no_budget_mutation",
            "no_memory_write",
            "no_kernel_mutation",
            "invokes_tool",
            "mutates_budget",
            "writes_memory",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"AutonomousGoal.{field_name}")
        required = (
            self.planner_consumable,
            self.candidate_only,
            self.no_direct_execution,
            self.no_background_execution,
            self.no_tool_invocation,
            self.no_budget_mutation,
            self.no_memory_write,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("AutonomousGoal must remain candidate-only")
        if self.invokes_tool or self.mutates_budget or self.writes_memory or self.mutates_kernel:
            raise ValueError("AutonomousGoal cannot execute side effects")
        if self.risk_level in {"A3", "A4"} and not self.requires_confirmation:
            raise ValueError("A3/A4 autonomous goals must require confirmation")
        if self.risk_level == "A5" and self.status != "blocked":
            raise ValueError("A5 autonomous goals must be blocked")

    @property
    def rank_score(self) -> float:
        if self.status == "blocked" or self.risk_level == "A5":
            return 0.0
        return max(0.0, min(1.0, self.expected_value_score - _risk_penalty(self.risk_level) - 0.24 * self.budget_estimate_score))

    def public_dict(self) -> dict[str, Any]:
        return {
            "goal_id": _text(self.goal_id, 240),
            "goal_type": self.goal_type,
            "summary": _text(self.summary, 480),
            "source_tick_id": _text(self.source_tick_id, 240),
            "source_refs": [_text(item, 240) for item in self.source_refs[:8]],
            "created_at": self.created_at,
            "expected_value_score": self.expected_value_score,
            "risk_level": self.risk_level,
            "budget_estimate_score": self.budget_estimate_score,
            "requires_confirmation": self.requires_confirmation,
            "status": self.status,
            "rank_score": self.rank_score,
            "planner_hint": _text(self.planner_hint, 900),
            "planner_consumable": self.planner_consumable,
            "candidate_only": self.candidate_only,
            "no_direct_execution": self.no_direct_execution,
            "no_background_execution": self.no_background_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_kernel_mutation": self.no_kernel_mutation,
            "invokes_tool": self.invokes_tool,
            "mutates_budget": self.mutates_budget,
            "writes_memory": self.writes_memory,
            "mutates_kernel": self.mutates_kernel,
        }


@dataclass(frozen=True)
class AutonomousGoalQueue:
    """自主目标候选队列。"""

    queue_id: str
    source_tick: LifecycleClockTick
    goals: list[AutonomousGoal] = field(default_factory=list)
    max_active_goals: int = 5
    planner_consumable: bool = True
    queue_only: bool = True
    no_direct_execution: bool = True
    no_background_execution: bool = True
    no_tool_invocation: bool = True
    no_budget_mutation: bool = True
    no_kernel_mutation: bool = True
    starts_background_work: bool = False
    invokes_tool: bool = False
    mutates_budget: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.queue_id, 240):
            raise ValueError("AutonomousGoalQueue.queue_id must be non-empty text")
        if isinstance(self.max_active_goals, bool) or not isinstance(self.max_active_goals, int) or self.max_active_goals <= 0:
            raise ValueError("AutonomousGoalQueue.max_active_goals must be positive int")
        for field_name in (
            "planner_consumable",
            "queue_only",
            "no_direct_execution",
            "no_background_execution",
            "no_tool_invocation",
            "no_budget_mutation",
            "no_kernel_mutation",
            "starts_background_work",
            "invokes_tool",
            "mutates_budget",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"AutonomousGoalQueue.{field_name}")
        if not (self.planner_consumable and self.queue_only and self.no_direct_execution and self.no_background_execution and self.no_tool_invocation and self.no_budget_mutation and self.no_kernel_mutation):
            raise ValueError("AutonomousGoalQueue must remain queue-only")
        if self.starts_background_work or self.invokes_tool or self.mutates_budget or self.mutates_kernel:
            raise ValueError("AutonomousGoalQueue cannot execute side effects")

    def sorted_goals(self) -> list[AutonomousGoal]:
        return sorted(self.goals, key=lambda goal: goal.rank_score, reverse=True)[: self.max_active_goals]

    def top_goal(self) -> AutonomousGoal | None:
        for goal in self.sorted_goals():
            if goal.status != "blocked" and goal.risk_level != "A5":
                return goal
        return None

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_1_AUTONOMOUS_GOAL_QUEUE_SCHEMA,
            "queue_id": _text(self.queue_id, 240),
            "source_tick": self.source_tick.public_dict(),
            "goals": [goal.public_dict() for goal in self.sorted_goals()],
            "top_goal_id": self.top_goal().goal_id if self.top_goal() is not None else "",
            "max_active_goals": self.max_active_goals,
            "planner_consumable": self.planner_consumable,
            "queue_only": self.queue_only,
            "no_direct_execution": self.no_direct_execution,
            "no_background_execution": self.no_background_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_budget_mutation": self.no_budget_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "starts_background_work": self.starts_background_work,
            "invokes_tool": self.invokes_tool,
            "mutates_budget": self.mutates_budget,
            "mutates_kernel": self.mutates_kernel,
        }


def build_autonomous_goal(
    *,
    goal_type: str,
    summary: str,
    source_tick_id: str,
    source_refs: list[str] | None = None,
    expected_value_score: float = 0.5,
    risk_level: str = "A1",
    budget_estimate_score: float = 0.1,
    status: str = "queued",
) -> AutonomousGoal:
    requires_confirmation = risk_level in {"A3", "A4"}
    if risk_level == "A5":
        status = "blocked"
        requires_confirmation = True
    hint = f"自主目标候选：{_text(summary, 180)}；只进入 Planner，不直接执行。"
    return AutonomousGoal(
        goal_id=f"autogoal:{_digest([goal_type, summary, source_tick_id, source_refs, expected_value_score, risk_level, budget_estimate_score])}",
        goal_type=goal_type,
        summary=summary,
        source_tick_id=source_tick_id,
        source_refs=source_refs or [],
        expected_value_score=expected_value_score,
        risk_level=risk_level,
        budget_estimate_score=budget_estimate_score,
        requires_confirmation=requires_confirmation,
        status=status,
        planner_hint=hint,
    )


def build_autonomous_goal_queue(
    *,
    source_tick: LifecycleClockTick,
    learning_refs: list[str] | None = None,
    task_refs: list[str] | None = None,
    maintenance_refs: list[str] | None = None,
    review_refs: list[str] | None = None,
    iteration_refs: list[str] | None = None,
) -> AutonomousGoalQueue:
    goals: list[AutonomousGoal] = []
    status = "queued" if source_tick.can_generate_goal else "blocked"
    blocked_suffix = "；当前 tick 未允许推进，仅保留候选" if status == "blocked" else ""
    if learning_refs:
        goals.append(build_autonomous_goal(goal_type="learning", summary=f"学习并整理近期能力缺口{blocked_suffix}", source_tick_id=source_tick.tick_id, source_refs=learning_refs[:6], expected_value_score=0.72, risk_level="A1", budget_estimate_score=0.18, status=status))
    if task_refs:
        goals.append(build_autonomous_goal(goal_type="task", summary=f"推进未完成低风险任务目标{blocked_suffix}", source_tick_id=source_tick.tick_id, source_refs=task_refs[:6], expected_value_score=0.78, risk_level="A2", budget_estimate_score=0.28, status=status))
    if maintenance_refs:
        goals.append(build_autonomous_goal(goal_type="maintenance", summary=f"检查运行状态、预算压力和恢复点{blocked_suffix}", source_tick_id=source_tick.tick_id, source_refs=maintenance_refs[:6], expected_value_score=0.62, risk_level="A0", budget_estimate_score=0.08, status=status))
    if review_refs:
        goals.append(build_autonomous_goal(goal_type="review", summary=f"复盘近期失败与用户反馈{blocked_suffix}", source_tick_id=source_tick.tick_id, source_refs=review_refs[:6], expected_value_score=0.66, risk_level="A1", budget_estimate_score=0.14, status=status))
    if iteration_refs:
        goals.append(build_autonomous_goal(goal_type="iteration", summary=f"生成自我迭代候选并等待用户确认{blocked_suffix}", source_tick_id=source_tick.tick_id, source_refs=iteration_refs[:6], expected_value_score=0.70, risk_level="A3", budget_estimate_score=0.24, status=status))
    if not goals:
        goals.append(build_autonomous_goal(goal_type="maintenance", summary=f"生成一次低风险状态复盘目标{blocked_suffix}", source_tick_id=source_tick.tick_id, source_refs=[], expected_value_score=0.50, risk_level="A0", budget_estimate_score=0.05, status=status))
    return AutonomousGoalQueue(
        queue_id=f"autogoal_queue:{_digest([source_tick.public_dict(), [goal.public_dict() for goal in goals]])}",
        source_tick=source_tick,
        goals=goals[:5],
    )
