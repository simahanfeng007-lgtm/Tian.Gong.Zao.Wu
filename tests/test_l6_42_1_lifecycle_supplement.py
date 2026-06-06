from __future__ import annotations

import pytest

from tiangong_agent_runtime.autonomous_goal_queue import AutonomousGoal, build_autonomous_goal_queue
from tiangong_agent_runtime.free_will_candidate_route import AutonomyLease, build_autonomy_lease, build_free_will_route
from tiangong_agent_runtime.lifecycle_clock import FreeWillTimeTable, LifecycleClockTick, build_free_will_timetable
from tiangong_agent_runtime.lifecycle_coordinator import LifecycleCoordinator
from tiangong_agent_runtime.self_iteration_frontend_projection import (
    SelfIterationFrontendItem,
    UserConfirmedIterationTicket,
    build_self_iteration_frontend_projection,
    build_user_confirmed_iteration_ticket,
)
from tiangong_agent_runtime.self_iteration_route import build_self_iteration_route


class DummyLearningReport:
    planner_hint_routes = [type("R", (), {"route_ref": "learning:l6_42_1_gap"})()]


class DummyIterationCandidate:
    object_ref = "suggestion:l6_42_1_iteration_need"


def test_freewill_timetable_interval_is_dynamic_and_tick_does_not_execute():
    timetable = build_free_will_timetable(last_tick_at=1000.0, sequence_index=2)
    fast = timetable.compute_interval_seconds(curiosity=0.9, achievement=0.9, order=0.8, rest=0.1, resource_pressure=0.0, failure_pressure=0.0)
    slow = timetable.compute_interval_seconds(curiosity=0.1, achievement=0.1, order=0.2, rest=0.9, resource_pressure=0.8, failure_pressure=0.7)
    assert 180.0 <= fast <= 900.0
    assert 180.0 <= slow <= 900.0
    assert fast < slow

    tick = timetable.build_tick(
        now_seconds=2000.0,
        active_user_task=False,
        budget_pressure=0.1,
        context_pressure=0.1,
    )
    assert tick.due is True
    assert tick.can_generate_goal is True
    assert tick.no_scheduler_thread is True
    assert tick.no_direct_execution is True
    assert tick.invokes_tool is False


def test_timetable_tick_blocks_when_user_task_or_recovery_active():
    timetable = build_free_will_timetable(last_tick_at=0.0)
    tick = timetable.build_tick(
        now_seconds=2000.0,
        active_user_task=True,
        user_allowed_autonomy=False,
        recovery_priority_active=True,
        budget_pressure=0.1,
        context_pressure=0.1,
    )
    assert tick.due is True
    assert tick.can_generate_goal is False
    assert "active_user_task" in tick.blocked_reason
    assert "recovery_priority_active" in tick.blocked_reason


@pytest.mark.parametrize("bad_score", [True, float("nan"), -0.1, 1.1])
def test_timetable_rejects_bad_scores(bad_score):
    timetable = build_free_will_timetable()
    with pytest.raises(ValueError):
        timetable.compute_interval_seconds(curiosity=bad_score)


def test_autonomous_goal_queue_ranks_goals_but_remains_candidate_only():
    tick = LifecycleClockTick(tick_id="tick:test", due=True, can_generate_goal=True, active_user_task=False)
    queue = build_autonomous_goal_queue(
        source_tick=tick,
        learning_refs=["learning:gap"],
        task_refs=["goal:unfinished"],
        maintenance_refs=["maintenance:runtime"],
        review_refs=["review:failure"],
        iteration_refs=["iteration:item"],
    )
    top = queue.top_goal()
    assert top is not None
    assert top.risk_level != "A5"
    assert queue.no_background_execution is True
    assert queue.no_tool_invocation is True
    assert queue.invokes_tool is False
    assert all(goal.candidate_only for goal in queue.goals)

    with pytest.raises(ValueError):
        AutonomousGoal(goal_id="goal:bad", goal_type="task", summary="bad", risk_level="A5", status="queued")
    with pytest.raises(ValueError):
        AutonomousGoal(goal_id="goal:bad2", goal_type="task", summary="bad", invokes_tool=True)


def test_autonomy_lease_has_limits_and_cannot_grant_background_execution():
    lease = build_autonomy_lease(
        active_user_task=False,
        idle_seconds=600,
        budget_pressure=0.1,
        tick_ref="tick:test",
        max_duration_seconds=240,
        max_budget_score=0.2,
        max_tool_steps=4,
    )
    assert lease.can_generate_candidate is True
    assert lease.tick_ref == "tick:test"
    assert lease.max_duration_seconds == 240
    assert lease.max_tool_steps == 4
    assert lease.interruptible is True
    assert lease.grants_background_execution is False

    with pytest.raises(ValueError):
        AutonomyLease(lease_id="lease:bad", grants_background_execution=True)


def test_freewill_route_can_reference_timetable_and_autonomous_goal_without_executing():
    lease = build_autonomy_lease(active_user_task=False, tick_ref="tick:test", budget_pressure=0.1)
    route = build_free_will_route(
        lease=lease,
        candidate_level="FW2",
        autonomous_goal_refs=["autogoal:one"],
        time_tick_ref="tick:test",
    )
    assert route.time_tick_ref == "tick:test"
    assert route.autonomous_goal_refs == ["autogoal:one"]
    assert route.no_background_execution is True
    assert route.no_tool_invocation is True
    assert route.invokes_tool is False


def test_self_iteration_frontend_projection_requires_user_confirmation_and_ticket_is_not_execution():
    route = build_self_iteration_route(iteration_candidates=[DummyIterationCandidate()], repeated_failure_count=1)
    projection = build_self_iteration_frontend_projection(
        iteration_route=route,
        conversation_need_refs=["conversation_need:better_ui"],
        user_feedback_refs=["feedback:daily_need"],
    )
    assert projection.display_zone_name == "自我迭代区"
    assert projection.user_review_required is True
    assert projection.no_direct_execution is True
    assert projection.applies_patch is False
    assert projection.items
    item = projection.items[0]
    assert item.requires_user_confirmation is True
    ticket = build_user_confirmed_iteration_ticket(item=item, confirmation_note="同意生成计划")
    assert ticket.permits_planner_draft_generation is True
    assert ticket.permits_execution is False
    assert ticket.requires_quality_gate is True
    assert ticket.requires_core_pollution_check is True

    with pytest.raises(ValueError):
        SelfIterationFrontendItem(item_id="item:bad", discovered_need_summary="x", proposed_change_summary="y", applies_patch=True)
    with pytest.raises(ValueError):
        UserConfirmedIterationTicket(ticket_id="ticket:bad", item_id="item:bad", permits_execution=True)


def test_lifecycle_coordinator_integrates_clock_goal_queue_and_frontend_projection():
    tick = build_free_will_timetable(last_tick_at=0.0).build_tick(
        now_seconds=2000,
        active_user_task=False,
        budget_pressure=0.1,
        context_pressure=0.1,
    )
    bundle = LifecycleCoordinator().build_bundle(
        learning_report=DummyLearningReport(),
        iteration_candidates=[DummyIterationCandidate()],
        active_user_task=False,
        user_allowed_autonomy=False,
        user_requested_learning=True,
        user_confirmed_iteration=False,
        clock_tick=tick,
        conversation_need_refs=["conversation_need:front_iteration_zone"],
        user_feedback_refs=["feedback:normal_chat_need"],
        long_term_goal_refs=["goal:improve_self_learning"],
    )
    assert bundle.clock_tick is tick
    assert bundle.autonomous_goal_queue is not None
    assert bundle.autonomous_goal_queue.top_goal() is not None
    assert bundle.iteration_frontend_projection is not None
    assert bundle.iteration_frontend_projection.display_zone_name == "自我迭代区"
    assert bundle.free_will_route is not None
    assert bundle.free_will_route.time_tick_ref == tick.tick_id
    assert bundle.free_will_route.no_direct_execution is True
    assert bundle.no_second_runtime is True
    assert bundle.no_kernel_mutation is True
