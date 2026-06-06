import pytest

from l4_phase6_builders import action_ref, phase6_ref, resume_ref, retry_advice, rollback_hint
from tiangong_kernel.l4_action_grounding import ExecutionResumeRef, ExecutionRetryAdviceRef, ExecutionRollbackHintRef


def test_l4_phase6_retry_resume_rollback_are_refs_only():
    retry = retry_advice()
    resume = resume_ref()
    rollback = rollback_hint()

    assert retry.automatic_retry is False
    assert retry.invokes_adapter is False
    assert resume.executes_resume is False
    assert resume.modifies_l3_plan is False
    assert rollback.executes_rollback is False
    assert rollback.restores_file is False
    assert rollback.reverses_network_action is False


def test_l4_phase6_retry_resume_rollback_reject_execution_flags():
    with pytest.raises(ValueError):
        ExecutionRetryAdviceRef(retry_advice_ref=phase6_ref(140, "retry_advice"), action_ref=action_ref(), automatic_retry=True)
    with pytest.raises(ValueError):
        ExecutionResumeRef(resume_ref=phase6_ref(141, "resume"), action_ref=action_ref(), executes_resume=True)
    with pytest.raises(ValueError):
        ExecutionRollbackHintRef(rollback_hint_ref=phase6_ref(142, "rollback_hint"), action_ref=action_ref(), executes_rollback=True)
