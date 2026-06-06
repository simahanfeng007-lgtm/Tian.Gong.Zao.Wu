from l3_phase4_builders import build_l3_phase4_objects
from tiangong_kernel.l3_orchestration import (
    IntentClarificationQuestionAdvice,
    IntentDegradePathAdvice,
    IntentRejectPathAdvice,
    IntentRetryPathAdvice,
    IntentValidationAdvice,
)


def test_intent_validation_and_gap_advices_are_advisory_only():
    objects = build_l3_phase4_objects()
    assert isinstance(objects["validation_advice"], IntentValidationAdvice)
    assert isinstance(objects["clarification_question"], IntentClarificationQuestionAdvice)
    assert isinstance(objects["reject_path"], IntentRejectPathAdvice)
    assert isinstance(objects["degrade_path"], IntentDegradePathAdvice)
    assert isinstance(objects["retry_path"], IntentRetryPathAdvice)
    for key in ("validation_advice", "missing_field_advice", "conflict_advice", "clarification_question", "reject_path", "degrade_path", "retry_path", "generic_transition"):
        assert objects[key].advisory_only is True, key
    assert objects["validation_result"].valid_structure_hint is False
