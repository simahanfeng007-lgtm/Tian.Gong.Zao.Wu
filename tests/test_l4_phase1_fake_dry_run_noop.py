from l3_phase1_builders import typed
from l4_phase1_builders import build_l4_phase1_objects
from tiangong_kernel.l4_action_grounding import ActionGroundingResultKind


def test_l4_phase1_fake_runner_returns_simulated_result_only_when_permit_ref_exists():
    objects = build_l4_phase1_objects(include_permit=True)
    result = objects["fake_runner"].run(objects["intake"], typed(4040, "l4_fake_result"), typed(4041, "l4_fake_failure"))
    assert result.result_kind is ActionGroundingResultKind.SIMULATED
    assert result.simulated is True
    assert result.real_action_performed is False
    assert ("runner", "fake") in result.payload_items


def test_l4_phase1_dry_run_runner_does_not_produce_real_action():
    objects = build_l4_phase1_objects(include_permit=True)
    result = objects["dry_runner"].run(objects["intake"], typed(4042, "l4_dry_result"), typed(4043, "l4_dry_failure"))
    assert result.result_kind is ActionGroundingResultKind.DRY_RUN
    assert result.real_action_performed is False
    assert ("real_action", "false") in result.payload_items


def test_l4_phase1_noop_runner_does_not_produce_real_action():
    objects = build_l4_phase1_objects(include_permit=True)
    result = objects["noop_runner"].run(objects["intake"], typed(4044, "l4_noop_result"), typed(4045, "l4_noop_failure"))
    assert result.result_kind is ActionGroundingResultKind.NO_OP
    assert result.real_action_performed is False
    assert ("runner", "no_op") in result.payload_items
