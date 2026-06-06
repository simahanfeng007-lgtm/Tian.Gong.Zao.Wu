from tiangong_kernel.l0_primitives.actor import ActorRef
from tiangong_kernel.l0_primitives.audit import AuditRef
from tiangong_kernel.l0_primitives.evidence import EvidenceRef
from tiangong_kernel.l0_primitives.goal import GoalRef
from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.lifecycle import LifecycleRef
from tiangong_kernel.l0_primitives.plan import PlanRef
from tiangong_kernel.l0_primitives.resource import ResourceRef
from tiangong_kernel.l0_primitives.scope import ScopeRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l0_primitives.state import (
    CheckpointRef,
    RecoveryPointRef,
    RuntimeStateRef,
    StateDeltaRef,
    StateSnapshotRef,
)
from tiangong_kernel.l1_ports.state_continuity_ports import (
    CheckpointReference,
    ContinuityEvidence,
    StateRecoveryHint,
)
from tiangong_kernel.l2_state import (
    AgentHealthState,
    AgentState,
    CheckpointContinuityState,
    ContinuityKind,
    ContinuityState,
    ContinuityStatus,
    GoalPlanRelationKind,
    GoalPlanState,
    L2LifecyclePhase,
    L2LifecycleStatus,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    L2StateStatusKind,
    LifecycleState,
    RecoveryContinuityState,
    RunPhase,
    RunProgressState,
    RunState,
    TaskPhase,
    TaskProgressState,
    TaskState,
)


def ref(prefix: str, index: int) -> RefId:
    return RefId(f"{prefix}:{index:032x}")


def typed(prefix: str, index: int, ref_type: str) -> TypedRef:
    return TypedRef(ref(prefix, index), ref_type)


def identity(index: int, kind: L2StateKind) -> L2StateIdentity:
    return L2StateIdentity(state_ref=typed("ref", index, kind.value), kind=kind)


def status() -> L2StateStatus:
    return L2StateStatus(kind=L2StateStatusKind.DECLARED, reason="phase2 fixture")


def build_phase2_objects():
    actor_ref = ActorRef(ref("actor", 1))
    scope_ref = ScopeRef(ref("scope", 2))
    goal_ref = GoalRef(ref("goal", 3))
    plan_ref = PlanRef(ref("plan", 4))
    runtime_ref = RuntimeStateRef(ref("runtime", 5))
    snapshot_ref = StateSnapshotRef(ref("snapshot", 6))
    delta_ref = StateDeltaRef(ref("delta", 7))
    checkpoint_ref = CheckpointRef(ref("checkpoint", 8), snapshot_ref=snapshot_ref)
    recovery_ref = RecoveryPointRef(ref("recovery", 9), checkpoint_ref=checkpoint_ref)
    run_identity = identity(15, L2StateKind.RUN)
    task_identity = identity(17, L2StateKind.TASK)
    agent_health = AgentHealthState(
        identity=identity(12, L2StateKind.AGENT),
        status=status(),
        actor_ref=actor_ref,
        scope_ref=scope_ref,
        runtime_state_ref=runtime_ref,
    )
    agent = AgentState(
        identity=identity(13, L2StateKind.AGENT),
        status=status(),
        actor_ref=actor_ref,
        scope_ref=scope_ref,
        runtime_state_ref=runtime_ref,
        health=agent_health,
        active_run_ref=run_identity.state_ref,
        active_task_ref=task_identity.state_ref,
        current_snapshot_ref=snapshot_ref,
        last_delta_ref=delta_ref,
    )
    run_progress = RunProgressState(
        identity=identity(14, L2StateKind.RUN),
        status=status(),
        phase=RunPhase.ACTIVE,
        completed_units=1,
    )
    run = RunState(
        identity=run_identity,
        status=status(),
        phase=RunPhase.ACTIVE,
        agent_ref=agent.identity.state_ref,
        scope_ref=scope_ref,
        goal_ref=goal_ref,
        plan_ref=plan_ref,
        active_task_ref=task_identity.state_ref,
        progress=run_progress,
        snapshot_ref=snapshot_ref,
        checkpoint_ref=checkpoint_ref,
        recovery_point_ref=recovery_ref,
    )
    task_progress = TaskProgressState(
        identity=identity(16, L2StateKind.TASK),
        status=status(),
        phase=TaskPhase.ACTIVE,
        completed_steps=1,
    )
    task = TaskState(
        identity=task_identity,
        status=status(),
        phase=TaskPhase.ACTIVE,
        run_ref=run.identity.state_ref,
        scope_ref=scope_ref,
        goal_ref=goal_ref,
        plan_ref=plan_ref,
        progress=task_progress,
    )
    goal_plan = GoalPlanState(
        identity=identity(18, L2StateKind.GOAL_PLAN),
        status=status(),
        goal_ref=goal_ref,
        plan_ref=plan_ref,
        relation=GoalPlanRelationKind.PLAN_FOR_GOAL,
        scope_ref=scope_ref,
        run_ref=run.identity.state_ref,
        task_ref=task.identity.state_ref,
    )
    lifecycle = LifecycleState(
        identity=identity(19, L2StateKind.BASE),
        status=status(),
        phase=L2LifecyclePhase.OPERATION,
        lifecycle_status=L2LifecycleStatus.ACTIVE,
        lifecycle_ref=LifecycleRef(ref("lifecycle", 20)),
        target_state_ref=run.identity.state_ref,
        previous_state_ref=agent.identity.state_ref,
        next_expected_state_ref=task.identity.state_ref,
    )
    continuity = ContinuityState(
        identity=identity(21, L2StateKind.RUN),
        status=status(),
        kind=ContinuityKind.CHECKPOINT,
        continuity_status=ContinuityStatus.AVAILABLE,
        runtime_state_ref=runtime_ref,
        snapshot_ref=snapshot_ref,
        state_delta_ref=delta_ref,
        checkpoint_ref=checkpoint_ref,
        recovery_point_ref=recovery_ref,
        previous_state_ref=agent.identity.state_ref,
        next_expected_state_ref=task.identity.state_ref,
    )
    checkpoint_continuity = CheckpointContinuityState(
        identity=identity(22, L2StateKind.RUN),
        status=status(),
        checkpoint_ref=checkpoint_ref,
        snapshot_ref=snapshot_ref,
        state_delta_ref=delta_ref,
        checkpoint_reference=CheckpointReference(checkpoint_ref=checkpoint_ref, snapshot_ref=snapshot_ref),
        continuity=continuity,
    )
    recovery_hint = StateRecoveryHint(
        hint_ref=ResourceRef(ref("resource", 23)),
        recovery_point_ref=recovery_ref,
    )
    continuity_evidence = ContinuityEvidence(
        evidence_ref=EvidenceRef(ref("evidence", 24)),
        audit_ref=AuditRef(ref("audit", 25)),
        snapshot_ref=snapshot_ref,
    )
    recovery_continuity = RecoveryContinuityState(
        identity=identity(26, L2StateKind.RECOVERY),
        status=status(),
        recovery_point_ref=recovery_ref,
        recovery_hint=recovery_hint,
        continuity_evidence=continuity_evidence,
        continuity=continuity,
        recoverable=True,
        resume_hint="resume from checkpoint reference only",
    )
    return (
        agent,
        run,
        task,
        goal_plan,
        lifecycle,
        continuity,
        checkpoint_continuity,
        recovery_continuity,
    )


def test_l2_phase2_objects_are_stably_serializable_and_hashable():
    for item in build_phase2_objects():
        first = stable_json_dumps(item)
        second = stable_json_dumps(item)
        digest = stable_hash(item)
        assert first == second
        assert '"schema_version":"0.1"' in first
        assert len(digest) == 64
