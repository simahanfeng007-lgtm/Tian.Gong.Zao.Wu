"""L6.42 LifecycleCoordinator 生命周期统一协调器。

本模块把 SelfHealing / AutonomousLearning / FreeWill / SelfIteration 四条生命
周期候选路径统一收拢为 Planner 可消费的 ``LifecycleRouteBundle``。它是 runtime
外壳层协调器，不新增 Runtime，不调工具，不写文件，不改预算，不改内核，不自动修复、
不自动学习、不自动迭代、不自动合入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
import hashlib
import json

from tiangong_kernel.l6_plugins.common._common import ensure_bool, ensure_score

from .autonomous_goal_queue import AutonomousGoalQueue, build_autonomous_goal_queue
from .biodynamic_policy_core import BioDynamicState, dynamic_count_requirement
from .free_will_candidate_route import AutonomyLease, FreeWillCandidateRoute, build_autonomy_lease, build_free_will_route
from .lifecycle_clock import LifecycleClockTick
from .self_healing_execution_route import SelfHealingExecutionRoute, build_self_healing_route
from .self_iteration_frontend_projection import (
    SelfIterationFrontendProjection,
    UserConfirmedIterationTicket,
    build_self_iteration_frontend_projection,
)
from .self_iteration_route import SelfIterationRoute, build_self_iteration_route
from .self_learning_route import AutonomousLearningRoute, build_self_learning_route

L6_42_LIFECYCLE_COORDINATOR_SCHEMA = "tiangong.l6_42.lifecycle_coordinator.v1"
L6_42_1_LIFECYCLE_SUPPLEMENT_SCHEMA = "tiangong.l6_42_1.lifecycle_supplement.v1"


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


LIFECYCLE_PRIORITY_ORDER = (
    "P0_safety_data_credential_irreversible_risk",
    "P1_current_user_task_closure",
    "P1_current_task_failure_recovery",
    "P2_user_requested_learning",
    "P2_user_confirmed_iteration",
    "P3_self_healing_candidate",
    "P3_learning_after_delivery",
    "P4_iteration_after_stability",
    "P5_free_will_exploration",
)


@dataclass(frozen=True)
class LifecycleStatusRoute:
    """生命周期状态摘要。只给 Planner 看状态，不触发执行。"""

    route_id: str
    active_user_task: bool = True
    user_allowed_autonomy: bool = False
    user_requested_learning: bool = False
    user_confirmed_iteration: bool = False
    idle_seconds: float = 0.0
    budget_pressure: float = 0.0
    context_pressure: float = 0.0
    safety_or_credential_risk: bool = False
    status_summary: str = ""
    planner_consumable: bool = True
    status_only: bool = True
    no_direct_execution: bool = True
    no_budget_mutation: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        if not _text(self.route_id, 240):
            raise ValueError("LifecycleStatusRoute.route_id must be non-empty text")
        for field_name in (
            "active_user_task",
            "user_allowed_autonomy",
            "user_requested_learning",
            "user_confirmed_iteration",
            "safety_or_credential_risk",
            "planner_consumable",
            "status_only",
            "no_direct_execution",
            "no_budget_mutation",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"LifecycleStatusRoute.{field_name}")
        for field_name in ("budget_pressure", "context_pressure"):
            ensure_score(getattr(self, field_name), f"LifecycleStatusRoute.{field_name}")
        if isinstance(self.idle_seconds, bool) or not isinstance(self.idle_seconds, (int, float)) or self.idle_seconds < 0:
            raise ValueError("LifecycleStatusRoute.idle_seconds must be non-negative number")
        if not (self.planner_consumable and self.status_only and self.no_direct_execution and self.no_budget_mutation and self.no_kernel_mutation):
            raise ValueError("LifecycleStatusRoute must remain status-only")

    def public_dict(self) -> dict[str, Any]:
        return {
            "route_id": _text(self.route_id, 240),
            "active_user_task": self.active_user_task,
            "user_allowed_autonomy": self.user_allowed_autonomy,
            "user_requested_learning": self.user_requested_learning,
            "user_confirmed_iteration": self.user_confirmed_iteration,
            "idle_seconds": self.idle_seconds,
            "budget_pressure": self.budget_pressure,
            "context_pressure": self.context_pressure,
            "safety_or_credential_risk": self.safety_or_credential_risk,
            "status_summary": _text(self.status_summary, 600),
            "planner_consumable": self.planner_consumable,
            "status_only": self.status_only,
            "no_direct_execution": self.no_direct_execution,
            "no_budget_mutation": self.no_budget_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class LifecyclePlannerHint:
    hint_id: str
    source_route_id: str
    priority: str
    hint_text: str
    requires_ticket: bool = False
    blocked: bool = False
    planner_consumable: bool = True
    no_direct_execution: bool = True

    def __post_init__(self) -> None:
        for field_name in ("requires_ticket", "blocked", "planner_consumable", "no_direct_execution"):
            ensure_bool(getattr(self, field_name), f"LifecyclePlannerHint.{field_name}")
        if not self.planner_consumable or not self.no_direct_execution:
            raise ValueError("LifecyclePlannerHint must remain planner-consumable and non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "hint_id": _text(self.hint_id, 240),
            "source_route_id": _text(self.source_route_id, 240),
            "priority": self.priority,
            "hint_text": _text(self.hint_text, 900),
            "requires_ticket": self.requires_ticket,
            "blocked": self.blocked,
            "planner_consumable": self.planner_consumable,
            "no_direct_execution": self.no_direct_execution,
        }


@dataclass(frozen=True)
class LifecycleRouteBundle:
    """生命周期四路径统一输出包。"""

    bundle_id: str
    generated_at: float
    status_route: LifecycleStatusRoute
    healing_route: SelfHealingExecutionRoute | None = None
    learning_route: AutonomousLearningRoute | None = None
    free_will_route: FreeWillCandidateRoute | None = None
    iteration_route: SelfIterationRoute | None = None
    clock_tick: LifecycleClockTick | None = None
    autonomous_goal_queue: AutonomousGoalQueue | None = None
    iteration_frontend_projection: SelfIterationFrontendProjection | None = None
    user_confirmed_iteration_ticket: UserConfirmedIterationTicket | None = None
    priority_order: list[str] = field(default_factory=lambda: list(LIFECYCLE_PRIORITY_ORDER))
    planner_hints: list[LifecyclePlannerHint] = field(default_factory=list)
    blocked_by_active_user_task: bool = False
    requires_ticket: bool = False
    planner_consumable: bool = True
    coordinator_only: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_tool_invocation: bool = True
    no_model_dispatch: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_skill_registry_write: bool = True
    no_tool_registration: bool = True
    no_patch_apply: bool = True
    no_hot_switch: bool = True
    no_kernel_mutation: bool = True
    invokes_tool: bool = False
    dispatches_model: bool = False
    mutates_budget: bool = False
    writes_memory: bool = False
    writes_skill_registry: bool = False
    registers_tool: bool = False
    applies_patch: bool = False
    performs_hot_switch: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not _text(self.bundle_id, 240):
            raise ValueError("LifecycleRouteBundle.bundle_id must be non-empty text")
        for field_name in (
            "blocked_by_active_user_task",
            "requires_ticket",
            "planner_consumable",
            "coordinator_only",
            "no_second_runtime",
            "no_direct_execution",
            "no_tool_invocation",
            "no_model_dispatch",
            "no_budget_mutation",
            "no_memory_write",
            "no_skill_registry_write",
            "no_tool_registration",
            "no_patch_apply",
            "no_hot_switch",
            "no_kernel_mutation",
            "invokes_tool",
            "dispatches_model",
            "mutates_budget",
            "writes_memory",
            "writes_skill_registry",
            "registers_tool",
            "applies_patch",
            "performs_hot_switch",
            "mutates_kernel",
        ):
            ensure_bool(getattr(self, field_name), f"LifecycleRouteBundle.{field_name}")
        required = (
            self.planner_consumable,
            self.coordinator_only,
            self.no_second_runtime,
            self.no_direct_execution,
            self.no_tool_invocation,
            self.no_model_dispatch,
            self.no_budget_mutation,
            self.no_memory_write,
            self.no_skill_registry_write,
            self.no_tool_registration,
            self.no_patch_apply,
            self.no_hot_switch,
            self.no_kernel_mutation,
        )
        if not all(required):
            raise ValueError("LifecycleRouteBundle must remain non-executing coordinator output")
        forbidden = (
            self.invokes_tool,
            self.dispatches_model,
            self.mutates_budget,
            self.writes_memory,
            self.writes_skill_registry,
            self.registers_tool,
            self.applies_patch,
            self.performs_hot_switch,
            self.mutates_kernel,
        )
        if any(forbidden):
            raise ValueError("LifecycleRouteBundle cannot execute lifecycle side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_42_LIFECYCLE_COORDINATOR_SCHEMA,
            "bundle_id": _text(self.bundle_id, 240),
            "generated_at": self.generated_at,
            "status_route": self.status_route.public_dict(),
            "healing_route": self.healing_route.public_dict() if self.healing_route else None,
            "learning_route": self.learning_route.public_dict() if self.learning_route else None,
            "free_will_route": self.free_will_route.public_dict() if self.free_will_route else None,
            "iteration_route": self.iteration_route.public_dict() if self.iteration_route else None,
            "clock_tick": self.clock_tick.public_dict() if self.clock_tick is not None else None,
            "autonomous_goal_queue": self.autonomous_goal_queue.public_dict() if self.autonomous_goal_queue is not None else None,
            "iteration_frontend_projection": self.iteration_frontend_projection.public_dict() if self.iteration_frontend_projection is not None else None,
            "user_confirmed_iteration_ticket": self.user_confirmed_iteration_ticket.public_dict() if self.user_confirmed_iteration_ticket is not None else None,
            "priority_order": list(self.priority_order),
            "planner_hints": [item.public_dict() for item in self.planner_hints],
            "blocked_by_active_user_task": self.blocked_by_active_user_task,
            "requires_ticket": self.requires_ticket,
            "planner_consumable": self.planner_consumable,
            "coordinator_only": self.coordinator_only,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_invocation": self.no_tool_invocation,
            "no_model_dispatch": self.no_model_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_skill_registry_write": self.no_skill_registry_write,
            "no_tool_registration": self.no_tool_registration,
            "no_patch_apply": self.no_patch_apply,
            "no_hot_switch": self.no_hot_switch,
            "no_kernel_mutation": self.no_kernel_mutation,
            "invokes_tool": self.invokes_tool,
            "dispatches_model": self.dispatches_model,
            "mutates_budget": self.mutates_budget,
            "writes_memory": self.writes_memory,
            "writes_skill_registry": self.writes_skill_registry,
            "registers_tool": self.registers_tool,
            "applies_patch": self.applies_patch,
            "performs_hot_switch": self.performs_hot_switch,
            "mutates_kernel": self.mutates_kernel,
        }

    def summary_text(self) -> str:
        return (
            "L6.42 LifecycleCoordinator：SelfHealing / AutonomousLearning / FreeWill / SelfIteration "
            "已统一为 Planner 可消费候选包；L6.42.1 已补时间节律、自主目标队列和自我迭代前端确认投影；不新增 Runtime，不自动执行，不污染核心组。"
        )


class LifecycleCoordinator:
    """生命周期四路径统一协调器。"""

    def __init__(self) -> None:
        self._last_bundle: LifecycleRouteBundle | None = None

    @property
    def last_bundle(self) -> LifecycleRouteBundle | None:
        return self._last_bundle

    def build_status_route(
        self,
        *,
        active_user_task: bool = True,
        user_allowed_autonomy: bool = False,
        user_requested_learning: bool = False,
        user_confirmed_iteration: bool = False,
        idle_seconds: float = 0.0,
        budget_pressure: float = 0.0,
        context_pressure: float = 0.0,
        safety_or_credential_risk: bool = False,
        notes: str = "",
    ) -> LifecycleStatusRoute:
        summary = "生命周期状态：当前用户任务优先；自由意志不抢占；学习/迭代/自愈均为候选。"
        if notes:
            summary += f" 备注：{_text(notes, 180)}"
        return LifecycleStatusRoute(
            route_id=f"lifecycle_status:{_digest([active_user_task, user_allowed_autonomy, user_requested_learning, user_confirmed_iteration, idle_seconds, budget_pressure, context_pressure, safety_or_credential_risk, notes])}",
            active_user_task=active_user_task,
            user_allowed_autonomy=user_allowed_autonomy,
            user_requested_learning=user_requested_learning,
            user_confirmed_iteration=user_confirmed_iteration,
            idle_seconds=idle_seconds,
            budget_pressure=budget_pressure,
            context_pressure=context_pressure,
            safety_or_credential_risk=safety_or_credential_risk,
            status_summary=summary,
        )

    def build_bundle(
        self,
        *,
        planner_report: Any | None = None,
        recovery_ticket: Any | None = None,
        quality_gate: Any | None = None,
        replay_quality: Any | None = None,
        learning_report: Any | None = None,
        memory_evidence: Any | None = None,
        iteration_candidates: list[Any] | None = None,
        active_user_task: bool = True,
        user_allowed_autonomy: bool = False,
        user_requested_learning: bool = False,
        user_confirmed_iteration: bool = False,
        idle_seconds: float = 0.0,
        budget_pressure: float = 0.0,
        context_pressure: float = 0.0,
        safety_or_credential_risk: bool = False,
        clock_tick: LifecycleClockTick | None = None,
        autonomous_goal_queue: AutonomousGoalQueue | None = None,
        conversation_need_refs: list[str] | None = None,
        user_feedback_refs: list[str] | None = None,
        user_confirmed_iteration_ticket: UserConfirmedIterationTicket | None = None,
        long_term_goal_refs: list[str] | None = None,
        notes: str = "",
    ) -> LifecycleRouteBundle:
        status_route = self.build_status_route(
            active_user_task=active_user_task,
            user_allowed_autonomy=user_allowed_autonomy,
            user_requested_learning=user_requested_learning,
            user_confirmed_iteration=user_confirmed_iteration,
            idle_seconds=idle_seconds,
            budget_pressure=budget_pressure,
            context_pressure=context_pressure,
            safety_or_credential_risk=safety_or_credential_risk,
            notes=notes,
        )
        healing = build_self_healing_route(
            planner_report=planner_report,
            recovery_ticket=recovery_ticket,
            quality_gate=quality_gate,
            replay_quality=replay_quality,
            notes=notes,
        )
        learning = build_self_learning_route(
            learning_report=learning_report,
            memory_evidence=memory_evidence,
            user_requested_learning=user_requested_learning,
            notes=notes,
        )
        repeated_failures = int(getattr(planner_report, "failed_steps", 0) or 0) if planner_report is not None else 0
        iteration = build_self_iteration_route(
            iteration_candidates=iteration_candidates,
            repeated_failure_count=repeated_failures,
            user_confirmed_direction=user_confirmed_iteration,
            notes=notes,
        )
        iteration_frontend_projection = build_self_iteration_frontend_projection(
            iteration_route=iteration,
            conversation_need_refs=conversation_need_refs or [],
            user_feedback_refs=user_feedback_refs or [],
            notes=notes,
        )
        if clock_tick is not None and autonomous_goal_queue is None:
            autonomous_goal_queue = build_autonomous_goal_queue(
                source_tick=clock_tick,
                learning_refs=[item.route_ref if hasattr(item, "route_ref") else str(item) for item in getattr(learning_report, "planner_hint_routes", [])][:3],
                task_refs=long_term_goal_refs or [],
                maintenance_refs=["maintenance:l6_42_1_runtime_state"],
                review_refs=user_feedback_refs or [],
                iteration_refs=[item.item_id for item in iteration_frontend_projection.items[:3]],
            )
        top_goal = autonomous_goal_queue.top_goal() if autonomous_goal_queue is not None else None
        autonomous_goal_refs = [top_goal.goal_id] if top_goal is not None else []
        candidate_summary = top_goal.summary if top_goal is not None else "根据长期目标生成下一步低风险候选"
        idle_drive = min(1.0, max(0.0, idle_seconds / 900.0))
        lease_state = BioDynamicState(
            evidence=1.0 if user_allowed_autonomy else 0.55,
            drive=idle_drive,
            resource_pressure=budget_pressure,
            uncertainty_pressure=context_pressure,
            fatigue=max(budget_pressure, context_pressure),
            recovery=1.0 - max(budget_pressure, context_pressure),
            reversibility=0.86,
            user_intent=1.0 if user_allowed_autonomy else 0.35,
            inertia=1.0 if active_user_task and not user_allowed_autonomy else 0.18,
        )
        lease_score = lease_state.execution_score
        lease_duration = round(90.0 + 300.0 * lease_score, 3)
        lease_budget = round(max(0.06, min(0.22, 0.08 + 0.16 * lease_score - 0.06 * lease_state.load)), 4)
        lease_steps = dynamic_count_requirement(3, load=lease_state.load, drive=lease_score, minimum=1, maximum=6)
        lease = build_autonomy_lease(
            active_user_task=active_user_task,
            user_allowed_autonomy=user_allowed_autonomy,
            idle_seconds=idle_seconds,
            budget_pressure=budget_pressure,
            context_pressure=context_pressure,
            tick_ref=clock_tick.tick_id if clock_tick is not None else "",
            max_duration_seconds=lease_duration,
            max_budget_score=lease_budget,
            max_tool_steps=lease_steps,
            interruptible=True,
        )
        free_will = build_free_will_route(
            lease=lease,
            candidate_level="FW2" if lease.can_generate_candidate else "FW0",
            candidate_summary=candidate_summary,
            long_term_goal_refs=long_term_goal_refs or [],
            autonomous_goal_refs=autonomous_goal_refs,
            time_tick_ref=clock_tick.tick_id if clock_tick is not None else "",
        )
        hints = self._build_hints(
            status=status_route,
            healing=healing,
            learning=learning,
            free_will=free_will,
            iteration=iteration,
            safety_or_credential_risk=safety_or_credential_risk,
        )
        bundle = LifecycleRouteBundle(
            bundle_id=f"lifecycle_bundle:{_digest([status_route.public_dict(), healing.public_dict(), learning.public_dict(), free_will.public_dict(), iteration.public_dict()])}",
            generated_at=time(),
            status_route=status_route,
            healing_route=healing,
            learning_route=learning,
            free_will_route=free_will,
            iteration_route=iteration,
            clock_tick=clock_tick,
            autonomous_goal_queue=autonomous_goal_queue,
            iteration_frontend_projection=iteration_frontend_projection,
            user_confirmed_iteration_ticket=user_confirmed_iteration_ticket,
            planner_hints=hints,
            blocked_by_active_user_task=free_will.blocked_by_active_user_task,
            requires_ticket=any(item.requires_ticket for item in hints),
        )
        self._last_bundle = bundle
        return bundle

    def build_planner_hint(self) -> str:
        if self._last_bundle is None:
            return ""
        hints = [item.hint_text for item in self._last_bundle.planner_hints if not item.blocked]
        return "LifecycleCoordinator 摘要：" + "；".join(hints[:4])[:1200]

    def _build_hints(
        self,
        *,
        status: LifecycleStatusRoute,
        healing: SelfHealingExecutionRoute,
        learning: AutonomousLearningRoute,
        free_will: FreeWillCandidateRoute,
        iteration: SelfIterationRoute,
        safety_or_credential_risk: bool,
    ) -> list[LifecyclePlannerHint]:
        hints: list[LifecyclePlannerHint] = []
        if safety_or_credential_risk:
            hints.append(
                LifecyclePlannerHint(
                    hint_id=f"lifecycle_hint:{_digest(['safety', status.route_id])}",
                    source_route_id=status.route_id,
                    priority="P0_safety_data_credential_irreversible_risk",
                    hint_text="检测到安全/凭证/不可逆风险：生命周期候选不得推进真实动作，必须先进入硬边界治理。",
                    requires_ticket=True,
                )
            )
        if status.active_user_task:
            hints.append(
                LifecyclePlannerHint(
                    hint_id=f"lifecycle_hint:{_digest(['user_task', status.route_id])}",
                    source_route_id=status.route_id,
                    priority="P1_current_user_task_closure",
                    hint_text="当前用户任务闭环优先；学习、迭代、自由意志只能作为辅助候选，不抢占主任务。",
                )
            )
        if healing.healing_need_score > 0:
            hints.append(
                LifecyclePlannerHint(
                    hint_id=f"lifecycle_hint:{_digest(['healing', healing.route_id])}",
                    source_route_id=healing.route_id,
                    priority="P1_current_task_failure_recovery",
                    hint_text=healing.planner_hint,
                )
            )
        if learning.learning_need_score > 0:
            hints.append(
                LifecyclePlannerHint(
                    hint_id=f"lifecycle_hint:{_digest(['learning', learning.route_id])}",
                    source_route_id=learning.route_id,
                    priority=learning.priority,
                    hint_text=learning.planner_hint,
                )
            )
        if iteration.iteration_need_score > 0:
            hints.append(
                LifecyclePlannerHint(
                    hint_id=f"lifecycle_hint:{_digest(['iteration', iteration.route_id])}",
                    source_route_id=iteration.route_id,
                    priority=iteration.priority,
                    hint_text=iteration.planner_hint + " 自我迭代内容必须先进入前端‘自我迭代区’，用户确认后才可生成 Planner 改造计划。",
                    requires_ticket=True,
                )
            )
        hints.append(
            LifecyclePlannerHint(
                hint_id=f"lifecycle_hint:{_digest(['freewill', free_will.candidate_id])}",
                source_route_id=free_will.candidate_id,
                priority="P5_free_will_exploration",
                hint_text=free_will.planner_hint,
                requires_ticket=free_will.requires_ticket,
                blocked=free_will.blocked,
            )
        )
        priority_index = {name: idx for idx, name in enumerate(LIFECYCLE_PRIORITY_ORDER)}
        return sorted(hints, key=lambda item: priority_index.get(item.priority, 999))[:8]
