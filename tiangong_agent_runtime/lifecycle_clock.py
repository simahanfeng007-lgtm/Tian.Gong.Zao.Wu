"""L6.42.1 LifecycleClock / FreeWillTimeTable 生命周期时间系统。

本模块只生成自由意志时间节律 tick。tick 是候选生成触发信号，不是后台线程、
不是执行器、不是预算授权、不是工具调用入口。Runtime 可以在安全时机调用它，
再把结果交给 LifecycleCoordinator / Planner。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

L6_42_1_LIFECYCLE_CLOCK_SCHEMA = "tiangong.l6_42_1.lifecycle_clock.v1"
MIN_FREEWILL_INTERVAL_SECONDS = 180.0
MAX_FREEWILL_INTERVAL_SECONDS = 900.0


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


def _number(value: float, field_name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric, not bool")
    numeric = float(value)
    if numeric != numeric or numeric < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    return numeric


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class LifecycleClockTick:
    """自由意志时间节点。

    每个 tick 最多触发一次自主目标候选生成。tick 本身不执行任务。
    """

    tick_id: str
    generated_at: float = field(default_factory=time)
    sequence_index: int = 0
    interval_seconds: float = MIN_FREEWILL_INTERVAL_SECONDS
    due: bool = False
    can_generate_goal: bool = False
    blocked_reason: str = ""
    active_user_task: bool = True
    user_allowed_autonomy: bool = False
    long_chain_active: bool = False
    recovery_priority_active: bool = False
    budget_pressure: float = 0.0
    context_pressure: float = 0.0
    planner_consumable: bool = True
    tick_only: bool = True
    no_scheduler_thread: bool = True
    no_direct_execution: bool = True
    no_background_execution: bool = True
    no_tool_invocation: bool = True
    no_budget_mutation: bool = True
    no_kernel_mutation: bool = True
    starts_thread: bool = False
    invokes_tool: bool = False
    mutates_budget: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.tick_id, 240):
            raise ValueError("LifecycleClockTick.tick_id must be non-empty text")
        if isinstance(self.sequence_index, bool) or not isinstance(self.sequence_index, int) or self.sequence_index < 0:
            raise ValueError("LifecycleClockTick.sequence_index must be non-negative int")
        _number(self.generated_at, "LifecycleClockTick.generated_at")
        interval = _number(self.interval_seconds, "LifecycleClockTick.interval_seconds", minimum=MIN_FREEWILL_INTERVAL_SECONDS)
        if interval > MAX_FREEWILL_INTERVAL_SECONDS:
            raise ValueError("LifecycleClockTick.interval_seconds must be within 3..15 minutes")
        for field_name in (
            "due",
            "can_generate_goal",
            "active_user_task",
            "user_allowed_autonomy",
            "long_chain_active",
            "recovery_priority_active",
            "planner_consumable",
            "tick_only",
            "no_scheduler_thread",
            "no_direct_execution",
            "no_background_execution",
            "no_tool_invocation",
            "no_budget_mutation",
            "no_kernel_mutation",
            "starts_thread",
            "invokes_tool",
            "mutates_budget",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"LifecycleClockTick.{field_name}")
        ensure_score(self.budget_pressure, "LifecycleClockTick.budget_pressure")
        ensure_score(self.context_pressure, "LifecycleClockTick.context_pressure")
        required = (
            self.planner_consumable,
            self.tick_only,
            self.no_scheduler_thread,
            self.no_direct_execution,
            self.no_background_execution,
            self.no_tool_invocation,
            self.no_budget_mutation,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("LifecycleClockTick must remain non-executing tick")
        if self.starts_thread or self.invokes_tool or self.mutates_budget or self.mutates_kernel:
            raise ValueError("LifecycleClockTick cannot start background work or mutate runtime state")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_1_LIFECYCLE_CLOCK_SCHEMA,
            "tick_id": _text(self.tick_id, 240),
            "generated_at": self.generated_at,
            "sequence_index": self.sequence_index,
            "interval_seconds": self.interval_seconds,
            "due": self.due,
            "can_generate_goal": self.can_generate_goal,
            "blocked_reason": _text(self.blocked_reason, 420),
            "active_user_task": self.active_user_task,
            "user_allowed_autonomy": self.user_allowed_autonomy,
            "long_chain_active": self.long_chain_active,
            "recovery_priority_active": self.recovery_priority_active,
            "budget_pressure": self.budget_pressure,
            "context_pressure": self.context_pressure,
            "planner_consumable": self.planner_consumable,
            "tick_only": self.tick_only,
            "no_scheduler_thread": self.no_scheduler_thread,
            "no_direct_execution": self.no_direct_execution,
            "no_background_execution": self.no_background_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_budget_mutation": self.no_budget_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
            "starts_thread": self.starts_thread,
            "invokes_tool": self.invokes_tool,
            "mutates_budget": self.mutates_budget,
            "mutates_kernel": self.mutates_kernel,
        }


@dataclass(frozen=True)
class FreeWillTimeTable:
    """自由意志时间表。

    通过数学模型把当前动机/压力映射为 3-15 分钟 interval。它只计算下一次
    候选生成窗口，不内置 while loop，不创建线程。
    """

    timetable_id: str
    min_interval_seconds: float = MIN_FREEWILL_INTERVAL_SECONDS
    max_interval_seconds: float = MAX_FREEWILL_INTERVAL_SECONDS
    last_tick_at: float = 0.0
    sequence_index: int = 0
    autonomy_enabled: bool = True
    planner_consumable: bool = True
    timetable_only: bool = True
    no_scheduler_thread: bool = True
    no_direct_execution: bool = True
    no_tool_invocation: bool = True
    no_budget_mutation: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        if not _text(self.timetable_id, 240):
            raise ValueError("FreeWillTimeTable.timetable_id must be non-empty text")
        minimum = _number(self.min_interval_seconds, "FreeWillTimeTable.min_interval_seconds", minimum=MIN_FREEWILL_INTERVAL_SECONDS)
        maximum = _number(self.max_interval_seconds, "FreeWillTimeTable.max_interval_seconds", minimum=minimum)
        if maximum > MAX_FREEWILL_INTERVAL_SECONDS:
            raise ValueError("FreeWillTimeTable.max_interval_seconds must not exceed 15 minutes")
        _number(self.last_tick_at, "FreeWillTimeTable.last_tick_at")
        if isinstance(self.sequence_index, bool) or not isinstance(self.sequence_index, int) or self.sequence_index < 0:
            raise ValueError("FreeWillTimeTable.sequence_index must be non-negative int")
        for field_name in (
            "autonomy_enabled",
            "planner_consumable",
            "timetable_only",
            "no_scheduler_thread",
            "no_direct_execution",
            "no_tool_invocation",
            "no_budget_mutation",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"FreeWillTimeTable.{field_name}")
        if not (self.planner_consumable and self.timetable_only and self.no_scheduler_thread and self.no_direct_execution and self.no_tool_invocation and self.no_budget_mutation and self.no_kernel_mutation):
            raise ValueError("FreeWillTimeTable must remain timetable-only")

    def compute_interval_seconds(
        self,
        *,
        curiosity: float = 0.5,
        achievement: float = 0.5,
        order: float = 0.5,
        rest: float = 0.3,
        resource_pressure: float = 0.0,
        failure_pressure: float = 0.0,
    ) -> float:
        for name, value in {
            "curiosity": curiosity,
            "achievement": achievement,
            "order": order,
            "rest": rest,
            "resource_pressure": resource_pressure,
            "failure_pressure": failure_pressure,
        }.items():
            ensure_score(value, f"FreeWillTimeTable.{name}")
        drive = _clamp01(0.34 * curiosity + 0.30 * achievement + 0.18 * order + 0.18 * (1.0 - rest))
        pressure = _clamp01(0.42 * resource_pressure + 0.32 * failure_pressure + 0.26 * rest)
        # drive 越高，间隔越短；pressure 越高，间隔越长。输出被硬夹在 3-15 分钟。
        normalized = _clamp01(0.62 + 0.46 * pressure - 0.54 * drive)
        interval = self.min_interval_seconds + normalized * (self.max_interval_seconds - self.min_interval_seconds)
        return round(max(self.min_interval_seconds, min(self.max_interval_seconds, interval)), 3)

    def build_tick(
        self,
        *,
        now_seconds: float | None = None,
        curiosity: float = 0.5,
        achievement: float = 0.5,
        order: float = 0.5,
        rest: float = 0.3,
        resource_pressure: float = 0.0,
        failure_pressure: float = 0.0,
        active_user_task: bool = True,
        user_allowed_autonomy: bool = False,
        long_chain_active: bool = False,
        recovery_priority_active: bool = False,
        budget_pressure: float = 0.0,
        context_pressure: float = 0.0,
        force_due: bool = False,
    ) -> LifecycleClockTick:
        now = time() if now_seconds is None else _number(now_seconds, "FreeWillTimeTable.now_seconds")
        for field_name, value in {
            "active_user_task": active_user_task,
            "user_allowed_autonomy": user_allowed_autonomy,
            "long_chain_active": long_chain_active,
            "recovery_priority_active": recovery_priority_active,
            "force_due": force_due,
        }.items():
            ensure_bool(value, f"FreeWillTimeTable.{field_name}")
        ensure_score(budget_pressure, "FreeWillTimeTable.budget_pressure")
        ensure_score(context_pressure, "FreeWillTimeTable.context_pressure")
        interval = self.compute_interval_seconds(
            curiosity=curiosity,
            achievement=achievement,
            order=order,
            rest=rest,
            resource_pressure=resource_pressure,
            failure_pressure=failure_pressure,
        )
        due = bool(force_due or self.last_tick_at <= 0 or (now - self.last_tick_at) >= interval)
        blockers: list[str] = []
        if not self.autonomy_enabled:
            blockers.append("autonomy_disabled")
        if active_user_task and not user_allowed_autonomy:
            blockers.append("active_user_task")
        if long_chain_active:
            blockers.append("long_chain_active")
        if recovery_priority_active:
            blockers.append("recovery_priority_active")
        if budget_pressure >= 0.88:
            blockers.append("budget_pressure_high")
        if context_pressure >= 0.88:
            blockers.append("context_pressure_high")
        can_generate = due and not blockers
        return LifecycleClockTick(
            tick_id=f"tick:l6_42_1_{_digest([self.timetable_id, now, self.sequence_index, interval, active_user_task, user_allowed_autonomy, blockers])}",
            generated_at=now,
            sequence_index=self.sequence_index + 1,
            interval_seconds=interval,
            due=due,
            can_generate_goal=can_generate,
            blocked_reason=",".join(blockers),
            active_user_task=active_user_task,
            user_allowed_autonomy=user_allowed_autonomy,
            long_chain_active=long_chain_active,
            recovery_priority_active=recovery_priority_active,
            budget_pressure=budget_pressure,
            context_pressure=context_pressure,
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_1_LIFECYCLE_CLOCK_SCHEMA,
            "timetable_id": _text(self.timetable_id, 240),
            "min_interval_seconds": self.min_interval_seconds,
            "max_interval_seconds": self.max_interval_seconds,
            "last_tick_at": self.last_tick_at,
            "sequence_index": self.sequence_index,
            "autonomy_enabled": self.autonomy_enabled,
            "planner_consumable": self.planner_consumable,
            "timetable_only": self.timetable_only,
            "no_scheduler_thread": self.no_scheduler_thread,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_budget_mutation": self.no_budget_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


def build_free_will_timetable(
    *,
    timetable_id: str = "timetable:l6_42_1_freewill",
    last_tick_at: float = 0.0,
    sequence_index: int = 0,
    autonomy_enabled: bool = True,
) -> FreeWillTimeTable:
    return FreeWillTimeTable(
        timetable_id=timetable_id,
        last_tick_at=last_tick_at,
        sequence_index=sequence_index,
        autonomy_enabled=autonomy_enabled,
    )
