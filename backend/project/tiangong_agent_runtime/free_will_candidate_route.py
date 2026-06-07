"""L6.42 FreeWill 接入路由。

自由意志只生成候选、建议或 Planner hint。它不能抢占当前用户任务，不能后台
偷偷执行真实副作用，不能绕过预算、PermitGateway、AuditBridge 或 ExecutionSpine。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

L6_42_FREE_WILL_SCHEMA = "tiangong.l6_42.free_will_candidate_route.v1"


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


def _non_negative(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{field_name} must be non-negative number")
    if float(value) != float(value):
        raise ValueError(f"{field_name} cannot be NaN")
    return float(value)


@dataclass(frozen=True)
class AutonomyLease:
    """自由意志候选租约。只决定能不能生成候选，不给执行权。"""

    lease_id: str
    active_user_task: bool = True
    user_allowed_autonomy: bool = False
    idle_seconds: float = 0.0
    budget_pressure: float = 0.0
    context_pressure: float = 0.0
    tick_ref: str = ""
    lease_started_at: float = field(default_factory=time)
    max_duration_seconds: float = 180.0
    max_budget_score: float = 0.12
    max_tool_steps: int = 3
    interruptible: bool = True
    max_candidate_level: str = "FW2"
    lease_scope: str = "candidate_generation_only"
    expires_at_ref: str = "ref:l6_42_autonomy_lease_expiry"
    grants_execution: bool = False
    grants_budget_mutation: bool = False
    grants_background_execution: bool = False
    bypasses_user_task: bool = False

    def __post_init__(self) -> None:
        if not _text(self.lease_id, 240):
            raise ValueError("AutonomyLease.lease_id must be non-empty text")
        for field_name in ("active_user_task", "user_allowed_autonomy", "interruptible", "grants_execution", "grants_budget_mutation", "grants_background_execution", "bypasses_user_task"):
            ensure_bool(getattr(self, field_name), f"AutonomyLease.{field_name}")
        _non_negative(self.idle_seconds, "AutonomyLease.idle_seconds")
        ensure_score(self.budget_pressure, "AutonomyLease.budget_pressure")
        ensure_score(self.context_pressure, "AutonomyLease.context_pressure")
        _non_negative(self.lease_started_at, "AutonomyLease.lease_started_at")
        _non_negative(self.max_duration_seconds, "AutonomyLease.max_duration_seconds")
        ensure_score(self.max_budget_score, "AutonomyLease.max_budget_score")
        if isinstance(self.max_tool_steps, bool) or not isinstance(self.max_tool_steps, int) or self.max_tool_steps < 0:
            raise ValueError("AutonomyLease.max_tool_steps must be non-negative int")
        if self.grants_execution or self.grants_budget_mutation or self.grants_background_execution or self.bypasses_user_task:
            raise ValueError("AutonomyLease cannot grant execution, background execution, budget mutation or user-task bypass")

    @property
    def can_generate_candidate(self) -> bool:
        return (not self.active_user_task or self.user_allowed_autonomy) and self.budget_pressure < 0.92

    @property
    def blocked_by_active_user_task(self) -> bool:
        return self.active_user_task and not self.user_allowed_autonomy

    def public_dict(self) -> dict[str, Any]:
        return {
            "lease_id": _text(self.lease_id, 240),
            "active_user_task": self.active_user_task,
            "user_allowed_autonomy": self.user_allowed_autonomy,
            "idle_seconds": self.idle_seconds,
            "budget_pressure": self.budget_pressure,
            "context_pressure": self.context_pressure,
            "tick_ref": _text(self.tick_ref, 240),
            "lease_started_at": self.lease_started_at,
            "max_duration_seconds": self.max_duration_seconds,
            "max_budget_score": self.max_budget_score,
            "max_tool_steps": self.max_tool_steps,
            "interruptible": self.interruptible,
            "max_candidate_level": self.max_candidate_level,
            "lease_scope": self.lease_scope,
            "expires_at_ref": self.expires_at_ref,
            "can_generate_candidate": self.can_generate_candidate,
            "blocked_by_active_user_task": self.blocked_by_active_user_task,
            "grants_execution": self.grants_execution,
            "grants_budget_mutation": self.grants_budget_mutation,
            "grants_background_execution": self.grants_background_execution,
            "bypasses_user_task": self.bypasses_user_task,
        }


@dataclass(frozen=True)
class FreeWillCandidateRoute:
    """自由意志候选路由。"""

    candidate_id: str
    lease: AutonomyLease
    candidate_level: str = "FW1"
    candidate_summary: str = "生成下一步建议"
    time_tick_ref: str = ""
    autonomous_goal_refs: list[str] = field(default_factory=list)
    planner_hint: str = ""
    generated_at: float = field(default_factory=time)
    requires_ticket: bool = False
    blocked_by_active_user_task: bool = False
    blocked_by_budget: bool = False
    planner_consumable: bool = True
    candidate_only: bool = True
    no_direct_execution: bool = True
    no_background_execution: bool = True
    no_tool_invocation: bool = True
    no_budget_mutation: bool = True
    no_policy_bypass: bool = True
    no_kernel_mutation: bool = True
    invokes_tool: bool = False
    mutates_budget: bool = False
    bypasses_policy: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.candidate_id, 240):
            raise ValueError("FreeWillCandidateRoute.candidate_id must be non-empty text")
        for field_name in (
            "requires_ticket",
            "blocked_by_active_user_task",
            "blocked_by_budget",
            "planner_consumable",
            "candidate_only",
            "no_direct_execution",
            "no_background_execution",
            "no_tool_invocation",
            "no_budget_mutation",
            "no_policy_bypass",
            "no_kernel_mutation",
            "invokes_tool",
            "mutates_budget",
            "bypasses_policy",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"FreeWillCandidateRoute.{field_name}")
        required = (
            self.planner_consumable,
            self.candidate_only,
            self.no_direct_execution,
            self.no_background_execution,
            self.no_tool_invocation,
            self.no_budget_mutation,
            self.no_policy_bypass,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("FreeWillCandidateRoute must remain candidate-only and policy-routed")
        forbidden = (self.invokes_tool, self.mutates_budget, self.bypasses_policy, self.mutates_kernel)
        if any(forbidden):
            raise ValueError("FreeWillCandidateRoute cannot execute autonomy side effects")
        if self.candidate_level in {"FW3", "FW4"} and not self.requires_ticket:
            raise ValueError("FW3/FW4 candidate must require ticket")
        if self.candidate_level == "FW5":
            raise ValueError("FW5 is A5-like and must be hard-blocked before route creation")

    @property
    def blocked(self) -> bool:
        return self.blocked_by_active_user_task or self.blocked_by_budget

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_FREE_WILL_SCHEMA,
            "candidate_id": _text(self.candidate_id, 240),
            "lease": self.lease.public_dict(),
            "candidate_level": self.candidate_level,
            "candidate_summary": _text(self.candidate_summary, 420),
            "time_tick_ref": _text(self.time_tick_ref, 240),
            "autonomous_goal_refs": [_text(item, 240) for item in self.autonomous_goal_refs[:8]],
            "planner_hint": _text(self.planner_hint, 900),
            "generated_at": self.generated_at,
            "requires_ticket": self.requires_ticket,
            "blocked_by_active_user_task": self.blocked_by_active_user_task,
            "blocked_by_budget": self.blocked_by_budget,
            "blocked": self.blocked,
            "planner_consumable": self.planner_consumable,
            "candidate_only": self.candidate_only,
            "no_direct_execution": self.no_direct_execution,
            "no_background_execution": self.no_background_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_budget_mutation": self.no_budget_mutation,
            "no_policy_bypass": self.no_policy_bypass,
            "no_kernel_mutation": self.no_kernel_mutation,
            "invokes_tool": self.invokes_tool,
            "mutates_budget": self.mutates_budget,
            "bypasses_policy": self.bypasses_policy,
            "mutates_kernel": self.mutates_kernel,
        }


def build_autonomy_lease(
    *,
    active_user_task: bool,
    user_allowed_autonomy: bool = False,
    idle_seconds: float = 0.0,
    budget_pressure: float = 0.0,
    context_pressure: float = 0.0,
    tick_ref: str = "",
    max_duration_seconds: float = 180.0,
    max_budget_score: float = 0.12,
    max_tool_steps: int = 3,
    interruptible: bool = True,
) -> AutonomyLease:
    return AutonomyLease(
        lease_id=f"lease:l6_42_autonomy_{_digest([active_user_task, user_allowed_autonomy, idle_seconds, budget_pressure, context_pressure])}",
        active_user_task=active_user_task,
        user_allowed_autonomy=user_allowed_autonomy,
        idle_seconds=idle_seconds,
        budget_pressure=budget_pressure,
        context_pressure=context_pressure,
        tick_ref=tick_ref,
        max_duration_seconds=max_duration_seconds,
        max_budget_score=max_budget_score,
        max_tool_steps=max_tool_steps,
        interruptible=interruptible,
        max_candidate_level="FW2" if active_user_task and user_allowed_autonomy else "FW1",
    )


def build_free_will_route(
    *,
    lease: AutonomyLease,
    candidate_level: str = "FW1",
    candidate_summary: str = "生成下一步建议",
    long_term_goal_refs: list[str] | None = None,
    autonomous_goal_refs: list[str] | None = None,
    time_tick_ref: str = "",
) -> FreeWillCandidateRoute:
    if candidate_level == "FW5":
        raise ValueError("FW5 cannot become a FreeWillCandidateRoute; it must be hard-blocked")
    blocked_task = lease.blocked_by_active_user_task
    blocked_budget = lease.budget_pressure >= 0.92
    if blocked_task or blocked_budget:
        candidate_level = "FW0"
    requires_ticket = candidate_level in {"FW3", "FW4"}
    goal_text = ", ".join(_text(item, 120) for item in (long_term_goal_refs or [])[:3])
    hint = "FreeWill 接入：只生成候选/建议/Planner hint，不抢当前用户任务，不后台执行。"
    auto_goal_text = ", ".join(_text(item, 120) for item in (autonomous_goal_refs or [])[:3])
    if blocked_task:
        hint += " 当前有活跃用户任务且未授权自治推进，自由意志候选降级为观察。"
    elif auto_goal_text:
        hint += f" 优先参考自主目标：{auto_goal_text}。"
    elif goal_text:
        hint += f" 可参考长期目标：{goal_text}。"
    return FreeWillCandidateRoute(
        candidate_id=f"freewill_route:{_digest([lease.public_dict(), candidate_level, candidate_summary, long_term_goal_refs])}",
        lease=lease,
        candidate_level=candidate_level,
        candidate_summary=candidate_summary,
        time_tick_ref=time_tick_ref or lease.tick_ref,
        autonomous_goal_refs=autonomous_goal_refs or [],
        planner_hint=hint,
        requires_ticket=requires_ticket,
        blocked_by_active_user_task=blocked_task,
        blocked_by_budget=blocked_budget,
    )
