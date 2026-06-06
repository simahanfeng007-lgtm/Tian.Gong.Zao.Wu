from l3_phase1_builders import typed
from l4_phase2_builders import build_gate_input, requested_scope, validate
from tiangong_kernel.l4_action_grounding import (
    FakeBoundaryPermitForTestOnly,
    PermitExpiry,
    PermitValidationStatus,
    SyntheticBoundaryDecisionForTestOnly,
    TestOnlyPermitNeverProductionInvariant,
)


def test_l4_phase2_fake_boundary_permit_is_test_only():
    fake_boundary = SyntheticBoundaryDecisionForTestOnly(
        decision_ref=typed(5300, "synthetic_boundary"),
        scope=requested_scope(),
    )
    fake = FakeBoundaryPermitForTestOnly(
        permit_ref=typed(5301, "fake_permit"),
        issuer_ref=typed(5302, "fake_issuer"),
        subject_ref=typed(5303, "fake_subject"),
        action_ref=typed(5304, "fake_action"),
        scope=requested_scope(),
        expiry=PermitExpiry("2099-01-01T00:00:00Z"),
        boundary_decision_ref=fake_boundary.to_boundary_decision_ref(),
    )
    permit = fake.to_action_permit_ref()
    assert permit.test_only is True
    assert fake.production_usable is False


def test_l4_phase2_production_path_rejects_test_only_permit():
    fake = FakeBoundaryPermitForTestOnly(
        permit_ref=typed(5310, "fake_permit"),
        issuer_ref=typed(5311, "fake_issuer"),
        subject_ref=typed(5312, "fake_subject"),
        action_ref=typed(5313, "fake_action"),
        scope=requested_scope(),
        expiry=PermitExpiry("2099-01-01T00:00:00Z"),
    )
    result = validate(build_gate_input(permit=fake.to_action_permit_ref(), production_path=True))
    assert result.status is PermitValidationStatus.TEST_ONLY_REJECTED
    assert result.allowed_for_grounding is False
    assert result.l4_authorized_action is False


def test_l4_phase2_test_only_permit_invariant_blocks_production_use():
    invariant = TestOnlyPermitNeverProductionInvariant(invariant_ref=typed(5320, "test_only_invariant"))
    assert invariant.test_only_permit_allowed_in_production is False
