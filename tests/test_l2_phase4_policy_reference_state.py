import pytest

from tiangong_kernel.l2_state import PolicyReferenceState, PolicyReferenceStatus
from tests.test_l2_phase4_serialization import build_phase4_objects, identity, status, typed


def test_l2_phase4_policy_reference_records_short_policy_metadata():
    policy = build_phase4_objects()["policy"]

    assert policy.reference_status is PolicyReferenceStatus.MATCHED
    assert policy.policy_ref == typed(101, "policy")
    assert policy.policy_name == "a5-boundary-policy"
    assert policy.policy_version_ref == typed(102, "policy_version")
    assert policy.applies_to_refs
    assert policy.source_boundary_ref == typed(103, "boundary")


def test_l2_phase4_policy_reference_rejects_large_policy_body_shape():
    with pytest.raises(ValueError):
        PolicyReferenceState(
            identity=identity(710),
            status=status(),
            policy_name="line one\nline two",
        )
