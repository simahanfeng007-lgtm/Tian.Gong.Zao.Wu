import pytest

from l4_phase6_builders import action_ref, failure_return, phase6_ref, recovery_requirement
from tiangong_kernel.l4_action_grounding import (
    ActionFailureReturnEnvelope,
    FailureCategory,
    NoRetryRecoveryRollbackInL4Invariant,
    RecoveryRequirementRef,
)


def test_l4_phase6_no_retry_recovery_rollback_execution():
    envelope = failure_return()
    recovery = recovery_requirement()
    invariant = NoRetryRecoveryRollbackInL4Invariant(invariant_ref=envelope.failure_ref)

    assert envelope.automatic_retry is False
    assert envelope.executes_recovery is False
    assert envelope.executes_rollback is False
    assert recovery.implements_recovery_system is False
    assert recovery.executes_recovery is False
    assert invariant.l4_can_override is False


def test_l4_phase6_recovery_requirement_rejects_real_recovery():
    with pytest.raises(ValueError):
        RecoveryRequirementRef(
            recovery_requirement_ref=phase6_ref(180, "recovery_requirement"),
            action_ref=action_ref(),
            executes_recovery=True,
        )

    with pytest.raises(ValueError):
        ActionFailureReturnEnvelope(
            failure_return_ref=phase6_ref(181, "failure_return"),
            action_ref=action_ref(),
            failure_ref=phase6_ref(182, "failure"),
            failure_category=FailureCategory.UNKNOWN,
            executes_rollback=True,
        )
