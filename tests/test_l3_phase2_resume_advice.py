from l3_phase2_builders import build_l3_phase2_objects
from tiangong_kernel.l3_orchestration import ResumeAdviceKind


def test_l3_phase2_resume_advices_are_references_and_suggestions_only():
    objects = build_l3_phase2_objects()
    assert objects["step_resume"].advice_kind is ResumeAdviceKind.RESUME_NEXT_STEP
    assert objects["task_resume"].step_resume_advices == (objects["step_resume"],)
    assert objects["run_resume"].task_resume_advices == (objects["task_resume"],)
    for key in ("step_resume", "task_resume", "task_interrupt", "run_resume"):
        item = objects[key]
        assert item.advisory_only is True, key
        assert not hasattr(item, "tool_call_args")
        assert not hasattr(item, "model_request")
        assert not hasattr(item, "execution_result")
