from l3_phase1_builders import typed
from l4_phase1_builders import build_l4_phase1_objects
from tiangong_kernel.l4_action_grounding import ActionGroundingResultKind, ExecutionDisabledByDefaultFailure


def test_l4_phase1_missing_l5_permit_ref_is_rejected_by_default():
    objects = build_l4_phase1_objects(include_permit=False)
    result = objects["fake_runner"].run(
        objects["intake"],
        result_ref=typed(4030, "l4_rejected_result"),
        failure_ref=typed(4031, "l4_rejected_failure"),
    )
    assert result.result_kind is ActionGroundingResultKind.REJECTED
    assert result.real_action_performed is False
    assert result.failure is not None
    assert result.failure.l5_permit_required is True
    assert "NoLiveExecutionWithoutL5Invariant" in result.failure.blocked_invariant_names


def test_l4_phase1_disabled_failure_serializes_to_standard_failure():
    objects = build_l4_phase1_objects()
    disabled = objects["disabled"]
    failure = disabled.to_failure()
    assert isinstance(disabled, ExecutionDisabledByDefaultFailure)
    assert failure.source_request_ref == disabled.source_request_ref
    assert failure.live_action_performed is False
    assert failure.l5_permit_required is True


def test_l4_phase1_permit_invariant_only_checks_reference_presence():
    objects = build_l4_phase1_objects()
    invariant = objects["permit_invariant"]
    assert invariant.is_satisfied_by(None) is False
    assert invariant.is_satisfied_by(typed(4032, "future_l5_permit_ref")) is True
    assert invariant.grants_permission is False
