from tests.test_l2_phase2_serialization import build_phase2_objects


def test_l2_phase2_agent_run_task_reference_chain_is_composable():
    agent, run, task, *_ = build_phase2_objects()

    assert agent.active_run_ref == run.identity.state_ref
    assert agent.active_task_ref == task.identity.state_ref
    assert run.agent_ref == agent.identity.state_ref
    assert run.active_task_ref == task.identity.state_ref
    assert task.run_ref == run.identity.state_ref
    assert run.snapshot_ref is not None
    assert run.checkpoint_ref is not None
    assert run.recovery_point_ref is not None
