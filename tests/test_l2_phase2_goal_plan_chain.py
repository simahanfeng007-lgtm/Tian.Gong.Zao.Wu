from tests.test_l2_phase2_serialization import build_phase2_objects


def test_l2_phase2_goal_plan_chain_links_run_task_scope_goal_and_plan():
    _, run, task, goal_plan, *_ = build_phase2_objects()

    assert run.goal_ref == goal_plan.goal_ref
    assert run.plan_ref == goal_plan.plan_ref
    assert task.goal_ref == goal_plan.goal_ref
    assert task.plan_ref == goal_plan.plan_ref
    assert run.scope_ref == goal_plan.scope_ref
    assert task.scope_ref == goal_plan.scope_ref
    assert goal_plan.run_ref == run.identity.state_ref
    assert goal_plan.task_ref == task.identity.state_ref
