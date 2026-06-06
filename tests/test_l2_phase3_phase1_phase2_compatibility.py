from tiangong_kernel.l0_primitives.identity import RefId, TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash
from tiangong_kernel.l2_state import (
    AgentState,
    ContinuityState,
    L2StateIdentity,
    L2StateKind,
    L2StateStatus,
    RunState,
    TaskState,
)
from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_keeps_phase1_and_phase2_objects_importable_and_hashable():
    identity = L2StateIdentity(
        state_ref=TypedRef(RefId("ref:00000000000000000000000000000001"), "l2_state"),
        kind=L2StateKind.BASE,
    )
    status = L2StateStatus(reason="compatibility")
    for item in (
        AgentState(identity=identity, status=status),
        RunState(identity=identity, status=status),
        TaskState(identity=identity, status=status),
        ContinuityState(identity=identity, status=status),
    ):
        assert len(stable_hash(item)) == 64


def test_l2_phase3_can_reference_previous_phase_state_refs():
    chain = build_phase3_chain()
    assert chain["skill_visibility"].run_ref == chain["run"].identity.state_ref
    assert chain["skill_visibility"].task_ref == chain["task"].identity.state_ref
    assert chain["model_request"].run_ref == chain["run"].identity.state_ref
    assert chain["tool_intent"].task_ref == chain["task"].identity.state_ref
