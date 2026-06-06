import pytest

from l4_phase6_builders import action_ref, failure_return, phase6_ref, result_return
from tiangong_kernel.l4_action_grounding import ActionOutcomeEnvelope, ExecutionReturnProjection, action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase6_action_outcome_envelope_result_and_failure_are_serializable():
    result = result_return()
    failure = failure_return()
    projection = ExecutionReturnProjection()

    result_outcome = projection.from_result(result)
    failure_outcome = projection.from_failure(failure)
    primitive = action_grounding_to_primitive(result_outcome)

    assert result_outcome.result_ref == result.result_ref
    assert result_outcome.failure_ref is None
    assert failure_outcome.failure_ref == failure.failure_ref
    assert primitive["writes_l2_state"] is False
    assert action_grounding_stable_hash(result_outcome)


def test_l4_phase6_action_outcome_requires_exactly_one_result_or_failure():
    with pytest.raises(ValueError):
        ActionOutcomeEnvelope(
            outcome_ref=phase6_ref(100, "outcome"),
            action_ref=action_ref(),
        )

    with pytest.raises(ValueError):
        ActionOutcomeEnvelope(
            outcome_ref=phase6_ref(101, "outcome"),
            action_ref=action_ref(),
            result_ref=phase6_ref(102, "result"),
            failure_ref=phase6_ref(103, "failure"),
        )
