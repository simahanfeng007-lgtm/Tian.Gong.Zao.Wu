from l4_phase6_builders import failure_return
from tiangong_kernel.l4_action_grounding import FailureCategory, FailureRecoverabilityHint, FailureSeverity


def test_l4_phase6_failure_category_severity_and_recoverability_cover_expected_values():
    assert FailureCategory.PERMIT_MISSING.value == "permit_missing"
    assert FailureCategory.PERMIT_SCOPE_MISMATCH.value == "permit_scope_mismatch"
    assert FailureCategory.TIMEOUT.value == "timeout"
    assert FailureCategory.OBSERVATION_UNAVAILABLE.value == "observation_unavailable"
    assert FailureSeverity.INFO.value == "info"
    assert FailureSeverity.CRITICAL.value == "critical"
    assert FailureRecoverabilityHint.RETRY_POSSIBLE.value == "retry_possible"
    assert FailureRecoverabilityHint.NOT_RECOVERABLE.value == "not_recoverable"


def test_l4_phase6_failure_return_does_not_replace_l5_risk_decision():
    envelope = failure_return()

    assert envelope.failure_category is FailureCategory.TIMEOUT
    assert envelope.failure_severity is FailureSeverity.RECOVERABLE
    assert envelope.recoverability_hint is FailureRecoverabilityHint.REPLAN_RECOMMENDED
    assert envelope.replaces_l5_risk_decision is False
    assert envelope.automatic_retry is False
