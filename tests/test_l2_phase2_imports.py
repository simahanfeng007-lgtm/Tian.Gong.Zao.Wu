def test_l2_phase2_package_and_modules_importable():
    import tiangong_kernel.l2_state as l2_state
    from tiangong_kernel.l2_state import agent_state
    from tiangong_kernel.l2_state import continuity_state
    from tiangong_kernel.l2_state import goal_plan_state
    from tiangong_kernel.l2_state import run_state
    from tiangong_kernel.l2_state import state_lifecycle
    from tiangong_kernel.l2_state import task_state

    assert agent_state.AgentState
    assert run_state.RunState
    assert task_state.TaskState
    assert goal_plan_state.GoalPlanState
    assert state_lifecycle.LifecycleState
    assert continuity_state.ContinuityState
    assert l2_state.AgentState
    assert l2_state.RecoveryContinuityState


def test_l2_phase2_public_exports_extend_phase1_exports():
    import tiangong_kernel.l2_state as l2_state

    phase1_exports = {
        "L2_STATE_SCHEMA_VERSION",
        "L2StateMetadata",
        "L2StateRecord",
        "L2StateIdentity",
        "L2StateKind",
        "L2StateStatus",
        "L2StateStatusKind",
        "L2StateBoundary",
        "L2BoundaryStatusKind",
        "L2StateSnapshot",
        "L2SnapshotSummary",
        "L2StateDelta",
        "L2DeltaEntry",
        "L2DeltaKind",
        "L2StateInvariant",
        "L2InvariantCheck",
        "L2InvariantStatusKind",
    }
    phase2_exports = {
        "AgentAvailability",
        "AgentHealthLevel",
        "AgentHealthState",
        "AgentState",
        "RunPhase",
        "RunProgressState",
        "RunState",
        "TaskPhase",
        "TaskProgressState",
        "TaskState",
        "GoalPlanRelationKind",
        "GoalPlanState",
        "L2LifecyclePhase",
        "L2LifecycleStatus",
        "LifecycleState",
        "ContinuityKind",
        "ContinuityStatus",
        "ContinuityState",
        "CheckpointContinuityState",
        "RecoveryContinuityState",
    }
    exports = set(l2_state.__all__)
    assert phase1_exports <= exports
    assert phase2_exports <= exports
