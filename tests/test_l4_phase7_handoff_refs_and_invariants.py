import pytest

from l4_phase7_builders import l5_resource_feedback, l6_recovery_replay_requirement, phase7_ref
from tiangong_kernel.l4_action_grounding import (
    ConcurrencyScopeIsNotSchedulerInvariant,
    L4ToL5ResourceFeedback,
    L4ToL6RecoveryReplayRequirement,
    LockRefIsNotRealLockInvariant,
    NoCommitOrRollbackAuthorizationInL4Invariant,
    NoConcurrencyAuthorizationInL4Invariant,
    NoResourceBudgetAllocationInL4Invariant,
    ReplaySummaryContainsNoPlainCredentialInvariant,
    ResourceBudgetRefIsNotAllocationInvariant,
    RollbackIntentIsNotRollbackInvariant,
    TransactionRefIsNotCommitInvariant,
)


def test_l4_phase7_l5_and_l6_handoff_objects_are_refs_only():
    feedback = l5_resource_feedback()
    requirement = l6_recovery_replay_requirement()

    assert feedback.future_l5_resource_recheck_required is True
    assert feedback.future_l5_concurrency_recheck_required is True
    assert feedback.ref_only is True
    assert feedback.allocates_resource is False
    assert feedback.authorizes_concurrency is False
    assert feedback.issues_permit is False
    assert requirement.ref_only is True
    assert requirement.implements_recovery_system is False
    assert requirement.implements_replay_system is False
    assert requirement.executes_replay is False
    assert requirement.executes_rollback is False


def test_l4_phase7_handoff_objects_reject_future_layer_implementation_flags():
    with pytest.raises(ValueError):
        L4ToL5ResourceFeedback(feedback_ref=phase7_ref(170, "feedback"), allocates_resource=True)
    with pytest.raises(ValueError):
        L4ToL6RecoveryReplayRequirement(requirement_ref=phase7_ref(171, "requirement"), implements_replay_system=True)


def test_l4_phase7_invariants_are_non_overridable_refs():
    invariant_classes = (
        TransactionRefIsNotCommitInvariant,
        RollbackIntentIsNotRollbackInvariant,
        ResourceBudgetRefIsNotAllocationInvariant,
        ConcurrencyScopeIsNotSchedulerInvariant,
        LockRefIsNotRealLockInvariant,
        ReplaySummaryContainsNoPlainCredentialInvariant,
        NoResourceBudgetAllocationInL4Invariant,
        NoConcurrencyAuthorizationInL4Invariant,
        NoCommitOrRollbackAuthorizationInL4Invariant,
    )

    for index, invariant_class in enumerate(invariant_classes, start=180):
        invariant = invariant_class(invariant_ref=phase7_ref(index, "phase7_invariant"))
        assert invariant.ref_only is True
        assert invariant.l4_can_override is False
