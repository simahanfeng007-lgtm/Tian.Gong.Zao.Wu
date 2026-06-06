from l3_phase1_builders import typed
from l4_phase1_builders import build_l4_phase1_objects
from l4_phase2_builders import build_gate_input, full_permit, validate
from tiangong_kernel.l4_action_grounding import (
    ActionGroundingResultKind,
    NoLiveActionWithoutL5PermitInvariant,
    PermitValidationStatus,
)


def test_l4_phase2_no_l5_permit_cannot_enter_live_action_path():
    result = validate(build_gate_input(permit=None))
    invariant = NoLiveActionWithoutL5PermitInvariant(invariant_ref=typed(5400, "no_live_action"))
    assert invariant.live_action_without_l5_permit is False
    assert result.allowed_for_grounding is False
    assert result.real_action_performed is False


def test_l4_phase2_dry_run_noop_fake_still_do_not_perform_real_actions():
    phase1 = build_l4_phase1_objects(include_permit=True)
    fake = phase1["fake_runner"].run(phase1["intake"], typed(5401, "fake_result"), typed(5402, "fake_failure"))
    dry = phase1["dry_runner"].run(phase1["intake"], typed(5403, "dry_result"), typed(5404, "dry_failure"))
    noop = phase1["noop_runner"].run(phase1["intake"], typed(5405, "noop_result"), typed(5406, "noop_failure"))
    assert fake.result_kind is ActionGroundingResultKind.SIMULATED
    assert dry.result_kind is ActionGroundingResultKind.DRY_RUN
    assert noop.result_kind is ActionGroundingResultKind.NO_OP
    assert fake.real_action_performed is False
    assert dry.real_action_performed is False
    assert noop.real_action_performed is False


def test_l4_phase2_structural_gate_pass_still_does_not_enable_live_action():
    result = validate(build_gate_input(permit=full_permit()))
    assert result.status is PermitValidationStatus.ACCEPTED
    assert result.allowed_for_grounding is True
    assert result.l4_authorized_action is False
    assert result.real_action_performed is False
