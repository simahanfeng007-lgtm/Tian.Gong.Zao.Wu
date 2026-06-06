from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps
from tiangong_kernel.l2_state import (
    AgentState,
    L2StateIdentity,
    L2StateRecord,
    ModelFeedbackState,
    RunState,
    SkillActivationState,
    TaskState,
    ToolIntentState,
)
from tests.test_l2_phase2_serialization import build_phase2_objects
from tests.test_l2_phase3_serialization import build_phase3_chain
from tests.test_l2_phase4_serialization import build_phase4_objects


def test_l2_phase4_keeps_previous_phase_exports_importable():
    assert L2StateIdentity
    assert L2StateRecord
    assert AgentState
    assert RunState
    assert TaskState
    assert SkillActivationState
    assert ToolIntentState
    assert ModelFeedbackState


def test_l2_phase4_keeps_phase2_and_phase3_fixture_chains_serializable():
    _, run, task, *_ = build_phase2_objects()
    phase3 = build_phase3_chain()

    for item in (run, task, phase3["tool_intent"], phase3["action_intent"], phase3["feedback"]):
        payload = stable_json_dumps(item)
        digest = stable_hash(item)
        assert '"schema_version":"0.1"' in payload
        assert len(digest) == 64


def test_l2_phase4_refs_compose_with_phase1_phase2_phase3_without_mutating_them():
    objects = build_phase4_objects()
    phase3 = objects["phase3"]

    assert objects["control"].run_ref == phase3["run"].identity.state_ref
    assert objects["control"].task_ref == phase3["task"].identity.state_ref
    assert objects["boundary_check"].checked_subject_ref == phase3["tool_intent"].identity.state_ref
    assert objects["risk"].subject_ref == phase3["action_intent"].identity.state_ref
    assert objects["security"].subject_ref == phase3["effect_observation"].identity.state_ref
