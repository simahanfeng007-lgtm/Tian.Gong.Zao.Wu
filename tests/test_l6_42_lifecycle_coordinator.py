from __future__ import annotations

import pytest
from dataclasses import dataclass

from tiangong_agent_runtime.free_will_candidate_route import AutonomyLease, build_autonomy_lease, build_free_will_route
from tiangong_agent_runtime.lifecycle_coordinator import LifecycleCoordinator
from tiangong_agent_runtime.self_healing_execution_route import SelfHealingExecutionRoute, build_self_healing_route
from tiangong_agent_runtime.self_iteration_route import SelfIterationRoute, build_self_iteration_route
from tiangong_agent_runtime.self_learning_route import AutonomousLearningRoute, build_self_learning_route


@dataclass(frozen=True)
class DummyPlannerReport:
    task_id: str = "task:l6_42"
    run_id: str = "run:l6_42"
    failed_steps: int = 2
    timeout_steps: int = 1
    blocked_steps: int = 0
    confirmation_required_steps: int = 0


@dataclass(frozen=True)
class DummyRecoveryTicket:
    ticket_id: str = "recovery:l6_42_resume"


@dataclass(frozen=True)
class DummyQualityGate:
    evidence_id: str = "quality:l6_42"
    decision: str = "warn"


class DummyLearningReport:
    planner_hint_routes = [type("R", (), {"route_ref": "learning:l6_42_gap"})()]
    source_refs = [type("S", (), {"source_ref": "evidence:l6_42"})()]
    skill_draft_routes = [type("K", (), {"route_ref": "skill:l6_42_draft", "skill_name": "safe_skill"})()]
    tool_candidate_routes = [type("T", (), {"route_ref": "tool:l6_42_need", "tool_name": "safe_tool"})()]


class DummyIterationCandidate:
    object_ref = "suggestion:l6_42_change_candidate"


def test_lifecycle_coordinator_builds_non_executing_bundle_and_blocks_freewill_when_user_task_active():
    coordinator = LifecycleCoordinator()
    bundle = coordinator.build_bundle(
        planner_report=DummyPlannerReport(),
        recovery_ticket=DummyRecoveryTicket(),
        quality_gate=DummyQualityGate(),
        learning_report=DummyLearningReport(),
        iteration_candidates=[DummyIterationCandidate()],
        active_user_task=True,
        user_allowed_autonomy=False,
        user_requested_learning=True,
        user_confirmed_iteration=True,
        notes="unit test",
    )

    assert bundle.planner_consumable is True
    assert bundle.no_second_runtime is True
    assert bundle.no_direct_execution is True
    assert bundle.no_tool_invocation is True
    assert bundle.no_budget_mutation is True
    assert bundle.no_kernel_mutation is True
    assert bundle.invokes_tool is False
    assert bundle.mutates_budget is False
    assert bundle.mutates_kernel is False
    assert bundle.blocked_by_active_user_task is True
    assert bundle.free_will_route is not None
    assert bundle.free_will_route.candidate_level == "FW0"
    assert bundle.free_will_route.blocked is True
    assert bundle.healing_route is not None
    assert bundle.healing_route.healing_need_score > 0
    assert bundle.learning_route is not None
    assert bundle.learning_route.learning_need_score > 0
    assert bundle.iteration_route is not None
    assert bundle.iteration_route.iteration_need_score > 0


def test_self_healing_route_cannot_execute_patch_or_tool():
    route = build_self_healing_route(planner_report=DummyPlannerReport(), recovery_ticket=DummyRecoveryTicket())
    assert route.candidate_only is True
    assert route.no_patch_execution is True
    assert route.no_tool_invocation is True
    assert route.no_kernel_mutation is True
    assert route.applies_patch is False
    assert route.invokes_tool is False

    with pytest.raises(ValueError):
        SelfHealingExecutionRoute(route_id="healing:bad", applies_patch=True)


def test_autonomous_learning_route_cannot_write_or_register_assets():
    route = build_self_learning_route(learning_report=DummyLearningReport(), user_requested_learning=True)
    assert route.candidate_only is True
    assert route.no_knowledge_write is True
    assert route.no_skill_registry_write is True
    assert route.no_tool_registration is True
    assert route.writes_knowledge is False
    assert route.registers_tool is False

    with pytest.raises(ValueError):
        AutonomousLearningRoute(route_id="learning:bad", writes_knowledge=True)


def test_freewill_lease_does_not_grant_execution_and_fw5_is_blocked():
    lease = build_autonomy_lease(active_user_task=False, user_allowed_autonomy=False, idle_seconds=120, budget_pressure=0.1)
    assert lease.can_generate_candidate is True
    assert lease.grants_execution is False
    route = build_free_will_route(lease=lease, candidate_level="FW2", candidate_summary="observe")
    assert route.no_background_execution is True
    assert route.invokes_tool is False
    assert route.blocked is False

    with pytest.raises(ValueError):
        AutonomyLease(lease_id="lease:bad", grants_execution=True)
    with pytest.raises(ValueError):
        build_free_will_route(lease=lease, candidate_level="FW5")


def test_self_iteration_route_requires_gate_and_cannot_apply_or_hot_switch():
    route = build_self_iteration_route(iteration_candidates=[DummyIterationCandidate()], repeated_failure_count=3, user_confirmed_direction=True)
    assert route.candidate_only is True
    assert route.quality_gate_required is True
    assert route.rollback_required is True
    assert route.no_patch_apply is True
    assert route.no_hot_switch is True
    assert route.no_version_activation is True
    assert route.applies_patch is False
    assert route.performs_hot_switch is False

    with pytest.raises(ValueError):
        SelfIterationRoute(route_id="iteration:bad", performs_hot_switch=True)


def test_lifecycle_priority_order_keeps_user_task_and_recovery_before_learning_iteration_freewill():
    bundle = LifecycleCoordinator().build_bundle(
        planner_report=DummyPlannerReport(),
        recovery_ticket=DummyRecoveryTicket(),
        learning_report=DummyLearningReport(),
        iteration_candidates=[DummyIterationCandidate()],
        active_user_task=True,
        user_allowed_autonomy=True,
        user_requested_learning=True,
        user_confirmed_iteration=True,
    )
    priorities = [hint.priority for hint in bundle.planner_hints]
    assert priorities.index("P1_current_user_task_closure") < priorities.index("P1_current_task_failure_recovery")
    assert priorities.index("P1_current_task_failure_recovery") < priorities.index("P2_user_requested_learning")
    assert priorities.index("P2_user_requested_learning") < priorities.index("P2_user_confirmed_iteration")
    assert priorities[-1] == "P5_free_will_exploration"
