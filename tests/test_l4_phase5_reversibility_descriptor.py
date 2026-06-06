import pytest

from l4_phase5_builders import phase5_ref
from tiangong_kernel.l4_action_grounding import ReversibilityDescriptor, ReversibilityKind


def test_l4_phase5_reversibility_descriptor_allows_expected_kinds():
    kinds = {
        ReversibilityKind.REVERSIBLE,
        ReversibilityKind.PARTIALLY_REVERSIBLE,
        ReversibilityKind.IRREVERSIBLE,
        ReversibilityKind.UNKNOWN,
    }

    for index, kind in enumerate(kinds):
        descriptor = ReversibilityDescriptor(
            reversibility_ref=phase5_ref(110 + index, "reversibility"),
            reversibility_kind=kind,
            summary=kind.value,
        )
        assert descriptor.reversibility_kind is kind
        assert descriptor.enables_action is False
        assert descriptor.performs_recovery is False


def test_l4_phase5_reversibility_descriptor_rejects_recovery_behavior():
    with pytest.raises(ValueError):
        ReversibilityDescriptor(
            reversibility_ref=phase5_ref(120, "reversibility"),
            performs_recovery=True,
        )
