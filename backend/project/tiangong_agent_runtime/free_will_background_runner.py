"""L6.73.0 自由意志后台候选运行器。

该运行器只在 Runtime 空闲/授权时生成 FreeWillCandidateRoute 和 Planner hint，
不调用工具、不写文件、不改预算、不绕过当前用户任务。它解决“后台自主运行”
的调度形态验证问题，同时保持 L6.42 自由意志候选路由的副作用边界。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from .free_will_candidate_route import FreeWillCandidateRoute, build_autonomy_lease, build_free_will_route

SCHEMA_VERSION = "tiangong.l6_73_0.free_will_background_runner.v1"


@dataclass(frozen=True)
class FreeWillBackgroundTick:
    tick_id: str
    generated_at: float = field(default_factory=time)
    active_user_task: bool = True
    user_allowed_autonomy: bool = False
    idle_seconds: float = 0.0
    background_candidate_generated: bool = False
    blocked: bool = True
    blocked_reason: str = "active_user_task"
    route: FreeWillCandidateRoute | None = None
    no_tool_invocation: bool = True
    no_file_write: bool = True
    no_budget_mutation: bool = True
    no_policy_bypass: bool = True
    no_kernel_mutation: bool = True

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "tick_id": self.tick_id,
            "generated_at": self.generated_at,
            "active_user_task": self.active_user_task,
            "user_allowed_autonomy": self.user_allowed_autonomy,
            "idle_seconds": self.idle_seconds,
            "background_candidate_generated": self.background_candidate_generated,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "route": self.route.public_dict() if self.route else None,
            "no_tool_invocation": self.no_tool_invocation,
            "no_file_write": self.no_file_write,
            "no_budget_mutation": self.no_budget_mutation,
            "no_policy_bypass": self.no_policy_bypass,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


class FreeWillBackgroundRunner:
    """自由意志后台 tick 调度器：只生产候选，不执行副作用。"""

    def tick(
        self,
        *,
        tick_id: str,
        active_user_task: bool,
        user_allowed_autonomy: bool = False,
        idle_seconds: float = 0.0,
        budget_pressure: float = 0.0,
        context_pressure: float = 0.0,
        long_term_goal_refs: list[str] | None = None,
        autonomous_goal_refs: list[str] | None = None,
    ) -> FreeWillBackgroundTick:
        effective_user_allowed_autonomy = bool(user_allowed_autonomy and not active_user_task)
        lease = build_autonomy_lease(
            active_user_task=active_user_task,
            user_allowed_autonomy=effective_user_allowed_autonomy,
            idle_seconds=idle_seconds,
            budget_pressure=budget_pressure,
            context_pressure=context_pressure,
            tick_ref=tick_id,
        )
        route = build_free_will_route(
            lease=lease,
            candidate_level="FW1" if lease.can_generate_candidate else "FW0",
            candidate_summary="后台自主候选：整理长期目标、复检待办或生成下一步 Planner hint",
            long_term_goal_refs=long_term_goal_refs or [],
            autonomous_goal_refs=autonomous_goal_refs or [],
            time_tick_ref=tick_id,
        )
        blocked_reason = "" if not route.blocked else "active_user_task" if route.blocked_by_active_user_task else "budget_pressure"
        return FreeWillBackgroundTick(
            tick_id=tick_id,
            active_user_task=active_user_task,
            user_allowed_autonomy=user_allowed_autonomy,
            idle_seconds=idle_seconds,
            background_candidate_generated=not route.blocked,
            blocked=route.blocked,
            blocked_reason=blocked_reason,
            route=route,
        )
