import pytest

from l4_phase6_builders import action_ref, phase6_ref
from tiangong_kernel.l4_action_grounding import FailureNormalizationFailure, ResultNormalizationFailure


def test_l4_phase6_normalization_failures_preserve_error_and_trace_refs():
    result_failure = ResultNormalizationFailure(
        normalization_failure_ref=phase6_ref(200, "result_normalization_failure"),
        action_ref=action_ref(),
        error_ref=phase6_ref(201, "error"),
        trace_ref=phase6_ref(202, "trace"),
    )
    failure_failure = FailureNormalizationFailure(
        normalization_failure_ref=phase6_ref(203, "failure_normalization_failure"),
        action_ref=action_ref(),
        error_ref=phase6_ref(204, "error"),
        trace_ref=phase6_ref(205, "trace"),
    )

    assert result_failure.error_ref is not None
    assert result_failure.trace_ref is not None
    assert result_failure.swallows_error is False
    assert failure_failure.error_ref is not None
    assert failure_failure.trace_ref is not None
    assert failure_failure.swallows_error is False


def test_l4_phase6_normalization_failures_reject_swallowing_errors():
    with pytest.raises(ValueError):
        ResultNormalizationFailure(
            normalization_failure_ref=phase6_ref(206, "result_normalization_failure"),
            action_ref=action_ref(),
            error_ref=phase6_ref(207, "error"),
            trace_ref=phase6_ref(208, "trace"),
            swallows_error=True,
        )
