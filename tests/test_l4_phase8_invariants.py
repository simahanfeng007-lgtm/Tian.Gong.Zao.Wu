import pytest

from l4_phase8_builders import phase8_ref
from tiangong_kernel.l4_execution import NoDirectL5L6ProgressionInvariant, NoPhase8LiveActionInvariant, NoSkipL4QualityGateInvariant


def test_l4_phase8_invariants_are_non_overridable():
    invariants = (
        NoDirectL5L6ProgressionInvariant(invariant_ref=phase8_ref(210, "phase8_invariant")),
        NoSkipL4QualityGateInvariant(invariant_ref=phase8_ref(211, "phase8_invariant")),
        NoPhase8LiveActionInvariant(invariant_ref=phase8_ref(212, "phase8_invariant")),
    )

    for invariant in invariants:
        assert invariant.invariant_only is True
        assert invariant.l4_can_override is False


def test_l4_phase8_invariants_reject_override():
    with pytest.raises(ValueError):
        NoDirectL5L6ProgressionInvariant(invariant_ref=phase8_ref(213, "phase8_invariant"), l4_can_override=True)
